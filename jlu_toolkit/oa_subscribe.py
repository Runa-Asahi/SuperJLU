"""OA 通知增量同步 + 关键词订阅 + 桌面提醒（只读：只 GET 列表第 1 页）。

存储（config_dir()/data）：
  oa_seen.json           {"seeded": bool, "updated": ts, "seen": {channel: [id, ...]}}
  oa_subscriptions.json  {"rules": [{"id","keywords":[...],"depts":[...],"channel","created"}]}
  oa_matches.json        {"matches": [{"rule_id","keywords_hit":[...],"notice":{...},"matched_at"}]}
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Callable, List, Optional

from . import jwxt, oa

SEEN_FILE, SUBS_FILE, MATCH_FILE = "oa_seen.json", "oa_subscriptions.json", "oa_matches.json"
MAX_SEEN, MAX_MATCHES, MAX_RULES = 2000, 300, 100
MIN_INTERVAL = 10  # 分钟


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _root(root: Optional[Path]) -> Path:
    if root is None:
        from . import ui
        root = ui.data_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load(f: Path, default: dict) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else default
    except (OSError, ValueError):
        return default


def _dump(f: Path, d: dict) -> None:
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


# ───────── 订阅规则 ─────────

def _split(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        v = v.replace("，", ",").split(",")
    if not isinstance(v, (list, tuple)):
        raise ValueError("keywords/depts 必须是字符串或字符串数组")
    out = []
    for s in v:
        if not isinstance(s, str):
            raise ValueError("keywords/depts 只能包含字符串")
        s = s.strip()
        if len(s) > 40:
            raise ValueError(f"关键词过长（≤40 字）：{s[:10]}…")
        if s and s not in out:
            out.append(s)
    return out[:20]


def list_rules(root: Optional[Path] = None) -> List[dict]:
    return _load(_root(root) / SUBS_FILE, {"rules": []}).get("rules", [])


def add_rule(keywords, depts=None, channel: str = "", root: Optional[Path] = None) -> dict:
    kws, dps = _split(keywords), _split(depts)
    if not kws:
        raise ValueError("至少需要一个关键词")
    channel = str(channel or oa.DEFAULT_CHANNEL)
    from . import college
    if not channel.isdigit() and not college.is_channel(channel):
        raise ValueError("channel 必须是数字栏目 id 或学院栏目（如 csw-xytz）")
    r = _root(root)
    rules = list_rules(r)
    if len(rules) >= MAX_RULES:
        raise ValueError(f"订阅规则最多 {MAX_RULES} 条")
    rule = {"id": uuid.uuid4().hex[:8], "keywords": kws, "depts": dps, "channel": channel, "created": _now()}
    _dump(r / SUBS_FILE, {"rules": rules + [rule]})
    return rule


def remove_rule(rule_id: str, root: Optional[Path] = None) -> bool:
    r = _root(root)
    rules = list_rules(r)
    keep = [x for x in rules if x.get("id") != rule_id]
    if len(keep) == len(rules):
        return False
    _dump(r / SUBS_FILE, {"rules": keep})
    return True


def match(notice: dict, rule: dict) -> List[str]:
    """返回命中的关键词（标题或单位包含）；dept 过滤不满足时返回 []。"""
    if rule.get("channel") and notice.get("channel") and rule["channel"] != notice["channel"]:
        return []
    title, dept = notice.get("title", ""), notice.get("dept", "")
    if rule.get("depts") and not any(d in dept for d in rule["depts"]):
        return []
    return [k for k in rule.get("keywords", []) if k in title or k in dept]


# ───────── 增量同步 ─────────

def sync(client, channel: str = oa.DEFAULT_CHANNEL, root: Optional[Path] = None) -> dict:
    """只取第 1 页（含置顶），按 id 去重。首次运行只记录已见 id（seeded），不返回新条目。"""
    r = _root(root)
    from . import college
    if college.is_channel(channel):
        res = college.fetch(channel)
        college.save(r, res)
        if not res["ok"]:
            raise jwxt.LoginError(res["hint"])
        items = res["items"]
    else:
        code, html, final = oa.get(client, oa.list_url(channel, 1))
        if code != 200 or oa.needs_login(final, html):
            raise jwxt.LoginError("OA 列表不可访问（需校园网/VPN 或登录）")
        items = oa.parse_list(html)["items"]
    for i in items:
        # 以请求的栏目为准：详情链接里的 channelId 可能是子栏目，避免规则按栏目过滤时漏掉
        i["link_channel"] = i.get("channel", "")
        i["channel"] = channel
    st = _load(r / SEEN_FILE, {"seen": {}})
    seen_map = st.setdefault("seen", {})
    first = channel not in seen_map
    seen = seen_map.get(channel, [])
    known = set(seen)
    new = [i for i in items if i["id"] and i["id"] not in known]
    seen_map[channel] = ([i["id"] for i in new] + seen)[:MAX_SEEN]
    st.update({"updated": _now(), "seeded": True})
    _dump(r / SEEN_FILE, st)
    if items and not college.is_channel(channel):
        oa.save(r, {"channel": channel, "fetched_at": st["updated"], "items": items, "channels": {}, "page1": True})
    return {"channel": channel, "first_run": first, "fetched": len(items), "new": [] if first else new,
            "seeded": len(new) if first else 0}


def record_matches(new: List[dict], root: Optional[Path] = None) -> List[dict]:
    r = _root(root)
    rules = list_rules(r)
    hits = []
    for n in new:
        for rule in rules:
            k = match(n, rule)
            if k:
                hits.append({"rule_id": rule["id"], "keywords_hit": k, "notice": n, "matched_at": _now()})
    if hits:
        d = _load(r / MATCH_FILE, {"matches": []})
        _dump(r / MATCH_FILE, {"matches": (hits + d.get("matches", []))[:MAX_MATCHES]})
    return hits


def recent_matches(limit: int = 20, since: str = "", root: Optional[Path] = None) -> List[dict]:
    ms = _load(_root(root) / MATCH_FILE, {"matches": []}).get("matches", [])
    if since:
        ms = [m for m in ms if m.get("matched_at", "") > since]
    return ms[:max(1, limit)]


# ───────── 桌面通知（尽力而为，绝不抛异常） ─────────

def _ps_quote(s: str) -> str:
    return s.replace("'", "''")


def notify(title: str, msg: str, runner: Callable = subprocess.run) -> str:
    title, msg = title[:60], msg[:200]
    try:
        try:
            from plyer import notification  # type: ignore
            notification.notify(title=title, message=msg, app_name="SuperJLU", timeout=10)
            return "plyer"
        except Exception:  # noqa: BLE001
            pass
        if shutil.which("termux-notification"):
            runner(["termux-notification", "--title", title, "--content", msg], timeout=15, check=False)
            return "termux"
        if sys.platform.startswith("win") and shutil.which("powershell"):
            ps = ("[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]>$null;"
                  "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1);"
                  "$x=$t.GetElementsByTagName('text');"
                  f"$x.Item(0).AppendChild($t.CreateTextNode('{_ps_quote(title)}'))>$null;"
                  f"$x.Item(1).AppendChild($t.CreateTextNode('{_ps_quote(msg)}'))>$null;"
                  "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('SuperJLU')"
                  ".Show([Windows.UI.Notifications.ToastNotification]::new($t))")
            runner(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], timeout=15, check=False)
            return "powershell"
        if shutil.which("notify-send"):
            runner(["notify-send", "-a", "SuperJLU", title, msg], timeout=15, check=False)
            return "notify-send"
    except Exception:  # noqa: BLE001
        pass
    return "print"


def watch_once(client, root: Optional[Path] = None, notifier: Callable = notify,
               out: Callable = print) -> dict:
    r = _root(root)
    channels = sorted({x.get("channel") or oa.DEFAULT_CHANNEL for x in list_rules(r)} or {oa.DEFAULT_CHANNEL})
    total_new, hits = 0, []
    for i, ch in enumerate(channels):
        if i:
            time.sleep(2)  # 礼貌限速
        try:
            res = sync(client, ch, r)
        except jwxt.LoginError as e:
            from . import college
            if not college.is_channel(ch):
                raise
            out(f"[订阅] 栏目 {ch} 跳过：{e}")
            continue
        if res["first_run"]:
            out(f"[OA] 首次运行：已记录栏目 {ch} 的 {res['seeded']} 条现有通知，不发提醒")
        total_new += len(res["new"])
        hits += record_matches(res["new"], r)
    for h in hits:
        n = h["notice"]
        out(f"[OA 订阅命中] {n.get('time','')}  {n.get('title','')}（{n.get('dept','')}） 关键词：{'/'.join(h['keywords_hit'])}\n  {n.get('url','')}")
        notifier("OA 新通知：" + "/".join(h["keywords_hit"]), f"{n.get('title','')}（{n.get('dept','')}）")
    return {"new": total_new, "matches": len(hits)}


# ───────── Web API（ui.py 调用；与 CLI 同一套函数） ─────────

def api(method: str, path: str, query: dict, body: Optional[dict], root: Path):
    """返回 (status, obj)；path 不属于本模块时返回 None。"""
    base = "/api/oa/subscriptions"
    if path != base and not path.startswith(base + "/"):
        return None
    rid = path[len(base) + 1:] or (query.get("id") or [""])[0]
    try:
        if method == "GET":
            return 200, {"ok": True, "rules": list_rules(root),
                         "matches": recent_matches(int((query.get("limit") or ["20"])[0]), root=root)}
        if method == "POST" and not rid:
            if not isinstance(body, dict):
                raise ValueError("请求体必须是 JSON 对象")
            rule = add_rule(body.get("keywords"), body.get("depts"), body.get("channel") or "", root)
            return 201, {"ok": True, "rule": rule}
        if method == "DELETE" and rid:
            if not remove_rule(rid, root):
                return 404, {"ok": False, "error": f"规则不存在：{rid}"}
            return 200, {"ok": True, "removed": rid}
    except ValueError as e:
        return 400, {"ok": False, "error": str(e)}
    return 405, {"ok": False, "error": "method not allowed"}
