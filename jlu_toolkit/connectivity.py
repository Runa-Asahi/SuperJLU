"""Anonymous, fixed-destination HTTPS checks. Never loads or changes a session."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import ssl
import sys
import time
import urllib.parse

TARGETS = (
    ("cas", "统一认证", "https://cas.jlu.edu.cn/tpass/login"),
    ("jwxt", "教务系统", "https://iedu.jlu.edu.cn/"),
    ("oa", "学校 OA（直连检测）", "https://oa.jlu.edu.cn/defaultroot/"),
    ("vpn", "WebVPN 门户", "https://vpn.jlu.edu.cn/"),
)


def check_one(target, timeout=6):
    from . import jwxt
    sid, name, url = target
    started = time.monotonic()
    result = {"id": sid, "name": name, "host": urllib.parse.urlsplit(url).hostname,
              "port": 443, "reachable": False, "authentication_checked": False}
    c = jwxt.JwxtClient(timeout=timeout, route="direct")
    try:
        code, _, final, _ = c._request(url)
        result.update(reachable=200 <= code < 400, http_status=code,
                      final_host=urllib.parse.urlsplit(final).hostname,
                      transport="system" if c._native_hosts else "python")
    except jwxt.NetworkError as error:
        result.update(error_kind=error.kind, error=str(error))
    result["milliseconds"] = round((time.monotonic() - started) * 1000)
    return result


def _by_id(services):
    return {s.get("id"): s for s in services if isinstance(s, dict) and s.get("id")}


def advice_from_services(services):
    """Plain-language hint from anonymous direct probes. Never claims VPN/OA proven."""
    by = _by_id(services)
    cas, jwxt, oa, vpn = by.get("cas"), by.get("jwxt"), by.get("oa"), by.get("vpn")
    if not all((cas, jwxt, oa, vpn)):
        return None
    if not (cas.get("reachable") and vpn.get("reachable")):
        return None
    if jwxt.get("reachable") and oa.get("reachable"):
        return None
    parts = []
    if not jwxt.get("reachable"):
        parts.append("教务直连未通")
    if not oa.get("reachable"):
        parts.append("学校 OA 直连未通")
    head = "、".join(parts) if parts else "校内入口直连未通"
    # Do not claim OA-via-VPN works on this device; only guide login mode.
    return (f"{head}，但统一认证与 WebVPN 门户可达，多见于校外网络。"
            f"请到「更多 → 登录」选择「校外 WebVPN」后再登录/同步；"
            f"本检测只测直连，不代表教务或 OA 已通过应用内 WebVPN 验收。")


def check_all():
    with ThreadPoolExecutor(max_workers=len(TARGETS)) as executor:
        results = list(executor.map(check_one, TARGETS))
    out = {"ok": True, "checked_at": dt.datetime.now().isoformat(timespec="seconds"),
           "python": sys.version.split()[0], "tls_library": ssl.OPENSSL_VERSION,
           "services": results,
           "note": "仅检测直连 HTTPS，不验证账号。学校 OA 可经校园网或学校 VPN 访问；应用内 WebVPN 模式下教务与 OA 同步均走 VPN。学院官网独立访问。"}
    hint = advice_from_services(results)
    if hint:
        out["hint"] = hint
        out["pattern"] = "offcampus_direct_gap"
    from . import netstatus
    device_hint = netstatus.current_direct_hint()
    if device_hint:
        out["device_hint"] = device_hint
    return out
