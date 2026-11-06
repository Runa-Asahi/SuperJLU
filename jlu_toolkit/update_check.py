"""Quiet "new version available" check against the public GitHub release.

Read-only: one anonymous GET to the public releases API, no account data sent.
Never raises and never forces an update; the UI only shows a small hint.
"""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import os
import urllib.request

from . import __version__

LATEST_TAG_RE = re.compile(r"/releases/tag/(v?\d+(?:\.\d+){0,2}[^/?#\s]*)")
DEADLINE = 15           # 整次检查最多等这么久，避免 DNS/VPN 卡住让界面一直没反应


def current_version():
    """本机版本号：安卓优先用 APK 的 versionName（由 jlu_android 注入），再退回包内常量。"""
    for v in (os.environ.get("SUPERJLU_APP_VERSION"), __version__):
        v = str(v or "").strip().lstrip("vV")
        if parse_version(v):
            return v
    return str(__version__ or "").strip().lstrip("vV") or "未知"

REPO = "Runa-Asahi/SuperJLU"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
# 国内网盘镜像：同步文件夹链接，发版后手动同步安装包；版本检查仍走 GitHub。
MIRRORS = {
    "quark": {"label": "夸克网盘", "url": "https://pan.quark.cn/s/216d5fbd8095", "note": "同步文件夹"},
    "baidu": {"label": "百度网盘", "url": "https://pan.baidu.com/s/50ch5v2DmkgXIirwbN-1Brw", "note": "同步文件夹"},
}
TTL = 6 * 3600          # 成功结果缓存 6 小时
FAIL_TTL = 30 * 60      # 失败后 30 分钟内不再重试
_lock = threading.Lock()
_cache: dict = {"at": 0.0, "ttl": 0, "result": None}


def parse_version(s):
    """'v1.2.3' / '1.2' / 'v1.2.3-beta' -> (1, 2, 3); None if unparseable."""
    m = re.match(r"^\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(s or ""))
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def is_newer(latest, current):
    a, b = parse_version(latest), parse_version(current)
    return bool(a and b and a > b)


def _safe_url(u):
    u = str(u or "")
    return u if u.startswith(f"https://github.com/{REPO}/releases") else RELEASES_PAGE


def _safe_mirror_url(u, prefix):
    u = str(u or "")
    return u if u.startswith(prefix) else ""


def mirrors_payload():
    """国内备用下载：固定同步文件夹链接（不是按版本号的直链）。"""
    return {
        "quark": {
            "label": str(MIRRORS["quark"]["label"]),
            "url": _safe_mirror_url(MIRRORS["quark"]["url"], "https://pan.quark.cn/"),
            "note": str(MIRRORS["quark"]["note"]),
        },
        "baidu": {
            "label": str(MIRRORS["baidu"]["label"]),
            "url": _safe_mirror_url(MIRRORS["baidu"]["url"], "https://pan.baidu.com/"),
            "note": str(MIRRORS["baidu"]["note"]),
        },
        "note": "同步文件夹，打开后自行选择最新安装包",
    }


def _with_mirrors(payload):
    out = dict(payload)
    out["mirrors"] = mirrors_payload()
    return out


def summarize(release, current=None):
    """Turn a GitHub release JSON into the small payload the UI needs."""
    current = current or current_version()
    if not isinstance(release, dict) or not release.get("tag_name") or release.get("draft") or release.get("prerelease"):
        return _with_mirrors({"ok": True, "current": current, "has_update": False})
    tag = str(release.get("tag_name") or "")
    latest = tag.lstrip("vV") or None
    out = {"ok": True, "current": current, "latest": latest,
           "has_update": is_newer(tag, current), "url": _safe_url(release.get("html_url"))}
    if release.get("published_at"):
        out["published_at"] = str(release["published_at"])[:10]
    return _with_mirrors(out)


def _request(url=API, accept="application/vnd.github+json"):
    return urllib.request.Request(url, headers={
        "Accept": accept, "User-Agent": f"SuperJLU/{current_version()}"})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _open_urllib(req, timeout):
    try:
        return urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout)
    except urllib.error.HTTPError as e:  # 3xx/4xx 也要拿到状态码和 Location
        return e


def _open_native(req, timeout):
    """Android/Windows system HTTPS stack (system CA store), redirects not followed."""
    from . import network
    if not network.native_available():
        raise OSError("no native transport")
    return network.native_open(req, timeout)


def _api(opener, timeout):
    r = opener(_request(), timeout)
    code = getattr(r, "code", 200)
    if code == 404:
        return {}  # 仓库还没有正式版：视为没有更新，而不是失败
    if code >= 400:
        raise OSError(f"api HTTP {code}")
    return json.loads(r.read(200_000).decode("utf-8"))


def _page(opener, timeout):
    """api.github.com 被拦/限流时的备用：releases/latest 会 302 到 /releases/tag/vX.Y.Z。"""
    r = opener(_request(RELEASES_PAGE, "text/html"), timeout)
    code = getattr(r, "code", 200)
    loc = str((getattr(r, "headers", None) or {}).get("Location") or "")
    m = LATEST_TAG_RE.search(loc) if 300 <= code < 400 else None
    if not m:
        if code in (301, 302, 303, 307, 308) and loc.rstrip("/").endswith("/releases"):
            return {}  # 没有正式版
        raise OSError(f"page HTTP {code}")
    tag = m.group(1)
    return {"tag_name": tag, "html_url": f"https://github.com/{REPO}/releases/tag/{tag}"}


def _attempts():
    return [("native-api", lambda t: _api(_open_native, t)),
            ("native-page", lambda t: _page(_open_native, t)),
            ("urllib-api", lambda t: _api(_open_urllib, t)),
            ("urllib-page", lambda t: _page(_open_urllib, t))]


class CheckFailed(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _brief(e):
    name = type(e).__name__
    msg = str(e).split("\n")[0][:80]
    return f"{name}: {msg}" if msg else name


def _fetch(timeout):
    # 安卓内置 Python 的 ssl 拿不到系统 CA：先走系统 HTTPS（与教务同一通道），
    # api.github.com 不通再看 github.com 的 releases/latest 跳转，最后才退回 urllib。
    reasons = []
    for name, fn in _attempts():
        if name.startswith("native") and not _native_ok():
            continue
        try:
            return fn(timeout)
        except Exception as e:  # noqa: BLE001
            reasons.append(f"{name} {_brief(e)}")
    raise CheckFailed("; ".join(reasons)[:400] or "no transport")


def _native_ok():
    try:
        from . import network
        return network.native_available()
    except Exception:  # noqa: BLE001
        return False


def _with_deadline(fetch, timeout, deadline):
    box = {}

    def run():
        try:
            box["v"] = fetch(timeout)
        except BaseException as e:  # noqa: BLE001
            box["e"] = e
    t = threading.Thread(target=run, name="jlu-update", daemon=True)
    t.start()
    t.join(deadline)
    if t.is_alive():
        raise CheckFailed(f"timeout after {deadline}s")
    if "e" in box:
        raise box["e"]
    return box["v"]


def check(force=False, timeout=6, fetch=None, now=None, deadline=DEADLINE):
    now = time.time() if now is None else now
    with _lock:
        c = _cache
        if not force and c["result"] is not None and now - c["at"] < c["ttl"]:
            return dict(c["result"], cached=True)
    try:
        result, ttl = summarize(_with_deadline(fetch or _fetch, timeout, deadline)), TTL
    except Exception as e:  # noqa: BLE001
        # 查不到就安静地当作没有更新，不打扰用户；原因只放进「技术信息」。
        reason = e.reason if isinstance(e, CheckFailed) else _brief(e)
        result, ttl = _with_mirrors({"ok": True, "current": current_version(), "has_update": False,
                       "unavailable": True, "reason": reason}), FAIL_TTL
    result["checked_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(now))
    with _lock:
        _cache.update(at=now, ttl=ttl, result=result)
    return dict(result)


def local():
    """不联网：只报本机版本。"""
    return _with_mirrors({"ok": True, "current": current_version(), "has_update": False})
