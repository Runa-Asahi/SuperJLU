"""MCP / 命令行共用的只读查询函数（不依赖 mcp 包，方便测试）。

默认读 SuperJLU App 自己的数据目录（ui.data_dir()，与桌面 App、jlu-toolkit fetch/sync 同一份）；
JLU_SCHEDULE_CSV / JLU_GRADES_CSV / JLU_EXAMS_CSV 仍可作为可选覆盖。全部只读，不联网、不登录。
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from typing import Optional

from . import core
from . import exams as ex

LOGIN_HINT = "请先用新版 SuperJLU App 登录同步一次，或运行 jlu-toolkit sync"


def _root(root=None) -> Path:
    if root is not None:
        return Path(root)
    from . import ui
    return ui.data_dir()


def _store(root=None):
    from . import ui
    return ui.Store(_root(root))


def _err(what: str) -> dict:
    return {"error": f"本地还没有{what}，{LOGIN_HINT}后再试。"}


# ───────── 课表 ─────────

def courses_on_day(week: int, weekday: int, root=None) -> list:
    from . import timetable
    csv_path = os.environ.get("JLU_SCHEDULE_CSV")
    cs = timetable.courses_from_csv(csv_path) if csv_path else timetable.courses(_root(root))
    return [c.__dict__ for c in core.courses_on(cs, week, weekday)]


_WD = "一二三四五六日"


def _slot(s) -> Optional[dict]:
    if s is None:
        return None
    return {"weekday": s.weekday, "weekday_text": "星期" + _WD[s.weekday - 1] if 1 <= s.weekday <= 7 else "",
            "periods": f"{s.start}-{s.end}", "weeks": list(s.weeks)}


def adjustments(root=None) -> dict:
    """本学期调课/停课/补课/换教室记录，以及是否已自动应用到课表。"""
    from . import timetable
    r = _root(root)
    if not (r / "schedule_adjustments.json").exists() and not (r / "schedule.csv").exists():
        return _err("课表和调课记录")
    synced = (r / "schedule_adjustments.json").exists()
    v = timetable.view(r)
    items = []
    for a in v["adjustments"]:
        items.append({"course": a.name, "kind": a.kind or "调课", "before": _slot(a.old), "after": _slot(a.new),
                      "new_location": a.new_location, "new_teacher": a.new_teacher, "applied_at": a.applied_at})
    out = {"term": v.get("term", ""), "auto_apply": v["enabled"], "count": len(items),
           "applied_to_timetable": v["applied"], "items": items, "synced": synced}
    if not synced:
        out["count"] = None
        out["note"] = f"还没同步过调课信息，不代表没有调课；{LOGIN_HINT}。"
    return out


# ───────── 成绩 / 绩点 ─────────

def _grades(root=None) -> list:
    f = os.environ.get("JLU_GRADES_CSV")
    if f:
        return core.load_grades(f)
    return _store(root).grades()


def compute_gpa(term: str = "", root=None) -> dict:
    gs = _grades(root)
    if not gs:
        return _err("成绩")
    return core.gpa(gs, term or None)


def list_grades(term: str = "", root=None):
    gs = _grades(root)
    if not gs:
        return _err("成绩")
    return [g.__dict__ for g in gs if not term or g.term == term]


def _builtins() -> dict:
    from . import grade_calculator as calc
    return {b["id"]: b for b in calc.BUILTINS}


def gpa_schemes(root=None) -> dict:
    """内置模板（保研加权/奖学金加权/所有课程）+ 同学在 App 里保存的自定义方案。"""
    st = _store(root)
    rules = st._json("scheme_rules.json", {}) or {}
    saved = [{"name": n, "courses": len(keys), "base": (rules.get(n) or {}).get("base")}
             for n, keys in (st.schemes() or {}).items()]
    builtin = [{"id": b["id"], "name": b["name"], "description": b["description"]} for b in _builtins().values()]
    return {"builtin": builtin, "saved": saved}


def _resolve_scheme(name: str, st) -> tuple[str, object]:
    name = (name or "").strip()
    bs = _builtins()
    for bid, b in bs.items():
        if name in (bid, b["name"]) or (name and name in b["name"]):
            return b["name"], bid
    aliases = {"保研": "postgraduate", "奖学金": "scholarship", "全部": "comprehensive", "所有": "comprehensive"}
    for k, bid in aliases.items():
        if k in name and name not in (st.schemes() or {}):
            return bs[bid]["name"], bid
    s = st.schemes() or {}
    if name in s:
        return name, set(s[name])
    raise ValueError(f"找不到绩点方案「{name}」，可用 gpa_schemes 查看全部方案")


def compute_gpa_with_scheme(scheme: str, term: str = "", root=None) -> dict:
    """按方案（内置模板 id/名称，或自定义方案名）算加权平均分与加权绩点。"""
    st = _store(root)
    recs = st.grade_records()
    if not recs:
        return _err("成绩")
    try:
        label, sel = _resolve_scheme(scheme, st)
    except ValueError as e:
        return {"error": str(e)}
    picked = []
    for g in recs:
        if term and g["term"] != term:
            continue
        on = g["builtin"].get(sel, False) if isinstance(sel, str) else (g["key"] in sel or g["legacy_key"] in sel)
        if on and float(g["credit"] or 0) > 0:
            picked.append(g)
    credits = sum(float(g["credit"]) for g in picked)
    scored = [g for g in picked if g["score_valid"]]
    sc = sum(float(g["credit"]) for g in scored)
    pointed = [g for g in picked if g["point"] is not None]
    pc = sum(float(g["credit"]) for g in pointed)
    return {"scheme": label, "term": term or "全部学期", "courses": len(picked), "credits": round(credits, 2),
            "weighted_score": round(sum(g["numeric_score"] * float(g["credit"]) for g in scored) / sc, 3) if sc else None,
            "weighted_gpa": round(sum(g["point"] * float(g["credit"]) for g in pointed) / pc, 3) if pc else None,
            "included": [g["name"] for g in picked]}


# ───────── 考试 ─────────

def _exams(root=None) -> list:
    f = os.environ.get("JLU_EXAMS_CSV")
    if f:
        return ex.load_exams(f)
    return _store(root).exams()


def exams(include_past: bool = False, root=None, now: Optional[dt.datetime] = None):
    es = _exams(root)
    if not es:
        if os.environ.get("JLU_EXAMS_CSV") or (_root(root) / "exams.csv").exists():
            return {"count": 0, "exams": [], "note": "已经同步过考试安排，目前没有安排考试。"}
        return _err("考试安排")
    now = now or dt.datetime.now()
    lst = sorted(es, key=lambda e: (not e.start, e.start)) if include_past else ex.upcoming(es, now)
    out = []
    for e in lst:
        d = ex.countdown(e, now)
        out.append({**e.to_dict(), "countdown": ex.format_countdown(d),
                    "days_left": (d.days if d is not None and d.total_seconds() >= 0 else None)})
    return {"count": len(out), "exams": out}


# ───────── 学业进度 ─────────

def academic_progress(root=None) -> dict:
    st = _store(root)
    c = st._json("completion.json", None)
    if not isinstance(c, dict):
        return _err("学业进度")
    groups = [{"name": g.get("name"), "nature": g.get("nature"), "required": g.get("required"),
               "earned": g.get("earned"), "missing": g.get("missing"), "passed": g.get("passed")}
              for g in c.get("groups") or []]
    return {"plan": c.get("plan"), "required": c.get("required"), "earned": c.get("earned"),
            "missing": c.get("missing"), "passed": c.get("passed"), "calculated_at": c.get("calculated_at"),
            "groups": groups, "unfinished_groups": [g["name"] for g in groups if not g["passed"]]}


# ───────── 学院官网通知 ─────────

def college_notices(college: str = "", keyword: str = "", limit: int = 20, refresh: bool = False,
                    root=None, getter=None) -> dict:
    """college 为空：列出已缓存/已关注的学院栏目；否则按栏目 id 或学院名读通知。refresh 才联网（公开官网，无需登录）。"""
    from . import college as col
    from . import ui
    r = _root(root)
    names = {**col.channels(), **col.link_channels()}
    if not college:
        cached = (col.load(r).get("channels_items") or {})
        prefs = col.load_prefs(r)
        ids = [k for k in prefs.get("order", []) if k in names] + [k for k in cached if k not in prefs.get("order", [])]
        return {"channels": [{"id": k, "name": names.get(k, k), "cached": len(cached.get(k) or [])} for k in ids],
                "all_channels": len(names),
                "hint": "传入 college=栏目 id 或学院名查看通知；可先在 App「通知」里关注本学院。"}
    ch = college if college in names else next((k for k, v in names.items() if college in v), "")
    if not ch:
        return {"error": f"找不到学院栏目「{college}」"}
    if refresh and col.is_channel(ch):
        col.save(r, col.fetch(ch, getter) if getter else col.fetch(ch))
    res = ui.oa_notices_api(ui.Store(r), {"category": ch, "keyword": keyword, "limit": str(max(1, min(200, limit)))})
    if not res["items"] and not refresh and res.get("status") != "link_only":
        res["hint"] = res.get("hint") or "本地还没有这个栏目的通知，可以设 refresh=true 联网抓取（学院官网公开页面）。"
    return res
