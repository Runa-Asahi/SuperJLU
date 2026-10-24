"""无头 UI 自检：在本机随机端口启动网页服务，用真实本地数据请求 /、/api/data、/api/session，
再经 API 跑一次空教室查询。只打印计数（ASCII JSON），不打印任何数据值。

    python -m jlu_toolkit.ui_check [--no-rooms] [--seats 100]
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer


def _walk(nodes, seen=None):
    seen = set() if seen is None else seen
    n_nodes = n_courses = depth = 0
    for n in nodes or []:
        if not isinstance(n, dict) or n.get("code") in seen:
            continue
        seen.add(n.get("code"))
        a, b, d = _walk(n.get("children"), seen)
        n_nodes += 1 + a
        n_courses += len(n.get("courses") or []) + b
        depth = max(depth, d + 1)
    return n_nodes, n_courses, depth


def run(rooms: bool = True, seats: int = 100, root=None) -> dict:
    from . import ui
    store = ui.Store(root or ui.data_dir())
    handler = ui.make_handler(store)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    auth = {ui.TOKEN_HEADER: handler.auth_token}

    def get(path):
        with urllib.request.urlopen(urllib.request.Request(base + path, headers=auth), timeout=60) as r:
            return r.status, r.read()

    def post(path, body):
        req = urllib.request.Request(base + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json", **auth})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    out: dict = {}
    try:
        st, html = get("/")
        out["page"] = {"status": st, "bytes": len(html), "has_script": b"<script>" in html}
        st, raw = get("/api/data")
        d = json.loads(raw)
        comp = d.get("completion") or {}
        pc = d.get("plan_courses") or {}
        nodes, placed, depth = _walk(comp.get("tree"))
        cs = pc.get("courses") or []
        out["data"] = {
            "status": st, "keys": len(d),
            "courses_schedule": len(d.get("courses") or []), "grades": len(d.get("grades") or []),
            "exams": len(d.get("exams") or []),
            "official_gpa_items": len((d.get("official_gpa") or {}).get("items") or []),
            "tree_nodes": nodes, "tree_depth": depth, "tree_courses_placed": placed,
            "tree_nodes_earned_gt0": sum(1 for _ in _iter(comp.get("tree")) if (_.get("earned") or 0) > 0),
            "unmatched": len(comp.get("unmatched") or []),
            "plan_courses": len(cs),
            "plan_done": sum(1 for c in cs if c.get("status_code") == "done"),
            "plan_via": (pc.get("source") or {}).get("plan", {}).get("via"),
            "tree_via": (pc.get("source") or {}).get("tree", {}).get("via"),
        }
        try:
            st, raw = get("/api/session")
            s = json.loads(raw)
            out["session"] = {"status": st, "keys": sorted(k for k in s if k.isascii())[:12],
                              "expired": s.get("session_expired", s.get("expired"))}
        except Exception as e:  # noqa: BLE001
            out["session"] = {"error": type(e).__name__}
        if rooms:
            st, cj = post("/api/rooms/campuses", {})
            camps = cj.get("campuses") or []
            out["rooms"] = {"campuses_status": st, "campuses": len(camps)}
            if camps:
                code = camps[0]["code"]
                st, bj = post("/api/rooms/buildings", {"campus": code})
                out["rooms"]["buildings_first_campus"] = len(bj.get("buildings") or [])
                st, rj = post("/api/rooms", {"campus": code, "periods": "1-2", "seat_min": seats})
                out["rooms"].update({"query_status": st, "rooms": len(rj.get("rooms") or []),
                                     "total": rj.get("total"), "ok": rj.get("ok", st == 200)})
    finally:
        httpd.shutdown()
    return out


def _iter(nodes, seen=None):
    seen = set() if seen is None else seen
    for n in nodes or []:
        if isinstance(n, dict) and n.get("code") not in seen:
            seen.add(n.get("code"))
            yield n
            yield from _iter(n.get("children"), seen)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m jlu_toolkit.ui_check")
    ap.add_argument("--no-rooms", action="store_true", help="不查询空教室（不访问教务）")
    ap.add_argument("--seats", type=int, default=100)
    a = ap.parse_args(argv)
    try:
        res = run(not a.no_rooms, a.seats)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": type(e).__name__}))
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
