"""课表个人修改层（原型）：教务课表 + 调停课合并之后，再叠加同学自己的增 / 删 / 改。

设计要点
  - schedule.csv 始终只放「教务原课表（+ 调停课）」，刷新照常整份覆盖；
    个人修改单独存在 schedule_overlay.json，刷新永远不碰它。
  - 读取时按顺序合并：教务 → 调停课 → 个人修改（纯函数，可重复执行，不会叠加）。
  - 每条修改指向一个稳定键 ``课程名|星期|起-止节``（有教学班 ID 时另存 jxbid，优先按
    「教学班 + 星期 + 节次」认课），并记下修改时看到的教务原样（base）。
    刷新后若教务那门课变了（周次 / 教室 / 教师），修改照常生效，但标记「教务有变动」；
    若教务已找不到那门课，修改不丢，标记「未生效」，等同学选择保留为自定义课或删掉。

schedule_overlay.json（明文，按学期分开；旧版不分学期的 {"version": 1, "ops": [...]} 自动归到当前学期）::

    {"version": 2, "terms": {"2026-2027-1": [...]}}   # 每学期一个列表，条目有三种
    [
      {"id": "a1", "op": "add",  "course": {name, teacher, location, weekday, start, end, weeks}},
      {"id": "h1", "op": "hide", "target": "高等数学|1|1-2", "weeks": [8] | null, "base": {...}},
      {"id": "e1", "op": "edit", "target": "高等数学|1|1-2", "weeks": [9] | null,
       "set": {"location": "逸夫楼301", ...}, "base": {...}}
    ]
"""
from __future__ import annotations

import secrets
from dataclasses import replace
from typing import Iterable, Optional

from . import core

VERSION = 2
OPS = ("add", "hide", "edit")
EDITABLE = ("name", "teacher", "location", "weekday", "start", "end")


def course_key(c) -> str:
    g = (lambda k: c[k]) if isinstance(c, dict) else (lambda k: getattr(c, k))
    return f"{g('name')}|{g('weekday')}|{g('start')}-{g('end')}"


def base_of(c: core.Course) -> dict:
    return {"weeks": sorted(c.weeks), "location": c.location, "teacher": c.teacher}


def new_id() -> str:
    return secrets.token_hex(4)


def _course(d: dict) -> core.Course:
    """校验并规范化用户提交的课程；不合法抛 ValueError（给界面显示中文原因）。"""
    name = str(d.get("name") or "").strip()[:60]
    if not name:
        raise ValueError("课程名不能为空")
    try:
        wd, s, e = int(d.get("weekday")), int(d.get("start")), int(d.get("end"))
    except (TypeError, ValueError):
        raise ValueError("请选择星期和节次") from None
    if not (1 <= wd <= 7 and 1 <= s <= e <= 20):
        raise ValueError("星期或节次超出范围")
    weeks = sorted({int(w) for w in (d.get("weeks") or []) if 1 <= int(w) <= 30})
    if not weeks:
        raise ValueError("请至少选择一周")
    return core.Course(name, str(d.get("teacher") or "").strip()[:40],
                       str(d.get("location") or "").strip()[:60] or "待定", wd, s, e, weeks)


def _row(c: core.Course, src: str, oid: str = "") -> dict:
    return {**c.__dict__, "weeks": list(c.weeks), "key": course_key(c), "src": src, "oid": oid}


def apply_overlay(courses: Iterable[core.Course], ops: Iterable[dict]
                  ) -> tuple[list[dict], list[dict]]:
    """返回 (带来源标记的课表行, 问题列表)。不修改入参。

    行的 src：official 教务原样 / edited 被改过的那几周 / custom 自己加的课。
    问题 kind：missing 教务已找不到目标（修改未生效）/ changed 教务在你修改后有变动。
    """
    courses = list(courses)
    orig = [_row(c, "official") for c in courses]
    rows = [_row(c, "official") for c in courses]
    issues: list[dict] = []
    for op in ops or []:
        kind, oid = op.get("op"), str(op.get("id") or "")
        try:
            if kind == "add":
                rows.append(_row(_course(op.get("course") or {}), "custom", oid))
                continue
            if kind not in ("hide", "edit"):
                continue
            target = op.get("target")
            scope = set(op["weeks"]) if op.get("weeks") else None
            hits = [r for r in rows if r["src"] == "official" and _match(r, op)
                    and (scope is None or scope & set(r["weeks"]))]
            if not hits:
                if not op.get("quiet"):
                    issues.append({"oid": oid, "kind": "missing", "target": target, "op": kind,
                                   **_who(target),
                                   "message": "教务课表里已找不到这门课（可能调课或取消了），这条修改暂未生效"})
                continue
            base = op.get("base")
            if base and not any(_same_base(base, _base_row(b), scope) for b in orig if _match(b, op)):
                issues.append({"oid": oid, "kind": "changed", "target": target, "op": kind,
                               **_who(target),
                               "message": "你修改之后教务又更新了这门课，请核对一下"})
            for r in hits:
                take = sorted(set(r["weeks"]) & scope) if scope is not None else list(r["weeks"])
                r["weeks"] = [w for w in r["weeks"] if w not in take]
                if kind == "edit" and take:
                    patch = {k: v for k, v in (op.get("set") or {}).items() if k in EDITABLE}
                    c = replace(_course({**r, **patch, "weeks": take}), jxbid=r.get("jxbid", ""),
                                kch=r.get("kch", ""))
                    rows.append(_row(c, "edited", oid) | {"from": target})
        except (ValueError, TypeError, KeyError):
            issues.append({"oid": oid, "kind": "invalid", "op": kind, "message": "这条修改的数据已损坏，已跳过"})
    return [r for r in rows if r["weeks"]], issues


def _who(target) -> dict:
    try:
        return parse_target(target)
    except (ValueError, AttributeError):
        return {}


def _same_base(saved: dict, now: dict, scope: Optional[set]) -> bool:
    """只按周修改时，只关心那几周还在、教室教师没变；整门修改才比较全部周次。"""
    if saved.get("location") != now["location"] or saved.get("teacher") != now["teacher"]:
        return False
    if scope is None:
        return saved.get("weeks") == now["weeks"]
    return scope <= set(now["weeks"]) or not (scope & set(saved.get("weeks") or []))


def _as_course(r: dict) -> core.Course:
    return core.Course(r["name"], r["teacher"], r["location"], r["weekday"], r["start"], r["end"],
                       list(r["weeks"]), r.get("jxbid", ""), r.get("kch", ""), r.get("adj", ""))


def _base_row(r: dict) -> dict:
    return {"weeks": sorted(r["weeks"]), "location": r["location"], "teacher": r["teacher"]}


def _match(r: dict, op: dict) -> bool:
    """有教学班 ID 时按「教学班 + 星期 + 节次」认课（同名课不会认错，改名也认得出）；否则按课程名。"""
    j = op.get("jxbid")
    if j and r.get("jxbid"):
        t = _who(op.get("target"))
        return r["jxbid"] == j and (r["weekday"], r["start"], r["end"]) == (
            t.get("weekday"), t.get("start"), t.get("end"))
    return r.get("key") == op.get("target")


def _find(official, op: dict) -> Optional[core.Course]:
    return next((c for c in official if _match(_row(c, "official"), op)), None)


def to_courses(rows: Iterable[dict]) -> list[core.Course]:
    return [_as_course(r) for r in rows]


# ---- 文档：按学期分开存（v2）；兼容 v1 {"ops": [...]} ----

def empty() -> dict:
    return {"version": VERSION, "terms": {}}


def _clean_ops(ops) -> list:
    return [o for o in (ops if isinstance(ops, list) else [])
            if isinstance(o, dict) and o.get("op") in OPS and o.get("id")]


def normalize(raw, term: str = "") -> dict:
    """任何版本的文档 → v2。v1（不分学期）和学期未知时存的修改，归到当前学期。

    结构不对抛 ValueError（导入备份时给同学看）。"""
    if not isinstance(raw, dict):
        raise ValueError("这不是 SuperJLU 课表修改备份文件")
    if isinstance(raw.get("terms"), dict):
        terms = {str(k): _clean_ops(v.get("ops") if isinstance(v, dict) else v)
                 for k, v in raw["terms"].items()}
    elif isinstance(raw.get("ops"), list):
        terms = {"": _clean_ops(raw["ops"])}
    else:
        raise ValueError("这不是 SuperJLU 课表修改备份文件")
    if term and "" in terms:
        terms[term] = terms.get(term, []) + terms.pop("")
    return {"version": VERSION, "terms": {k: v for k, v in terms.items() if v}}


def validate_doc(doc, term: str = "") -> dict:
    return normalize(doc, term)


def term_ops(doc: dict, term: str) -> list:
    return list(doc.get("terms", {}).get(term, []))


def with_ops(doc: dict, term: str, ops: list) -> dict:
    terms = dict(doc.get("terms", {}))
    if ops:
        terms[term] = ops
    else:
        terms.pop(term, None)
    return {"version": VERSION, "terms": terms}


def merge_import(doc: dict, imported: dict) -> dict:
    """导入备份：备份里有的学期整体替换，其它学期保留。"""
    return {"version": VERSION, "terms": {**doc.get("terms", {}), **imported.get("terms", {})}}


# ---- 对某学期修改列表的增删（Store 调用；均返回新列表，不原地改） ----

def parse_target(target: str) -> dict:
    name, wd, se = str(target).rsplit("|", 2)
    s, e = se.split("-")
    return {"name": name, "weekday": int(wd), "start": int(s), "end": int(e)}


def make_op(action: str, body: dict, official: list[core.Course]) -> dict:
    """把界面提交的动作变成一条 op；目标必须是当前教务课表里的课。"""
    if action == "add":
        c = _course(body.get("course") or {})
        return {"id": new_id(), "op": "add", "course": {**c.__dict__, "weeks": c.weeks}}
    target = body.get("target")
    match = _find(official, {"target": target, "jxbid": str(body.get("jxbid") or "")})
    if match is None:
        raise ValueError("找不到要修改的课程，请刷新后重试")
    weeks = sorted({int(w) for w in body.get("weeks") or []}) or None
    op = {"id": new_id(), "op": action, "target": course_key(match), "weeks": weeks, "base": base_of(match)}
    if match.jxbid:
        op["jxbid"] = match.jxbid
    if action == "edit":
        op["set"] = _patch(body.get("set"), match.__dict__)
    return op


def _patch(raw, current: dict) -> dict:
    patch = {k: v for k, v in (raw or {}).items() if k in EDITABLE and v != current.get(k)}
    if not patch:
        raise ValueError("没有要修改的内容")
    _course({**current, **patch, "weeks": [1]})  # 提前校验
    return patch


def remove(ops: list, oid: str) -> list:
    return [o for o in ops if o.get("id") != oid]


def update(ops: list, oid: str, body: dict) -> list:
    """改一条已有修改：自定义课换内容 / 已修改的课换改法。"""
    out = []
    for o in ops:
        if o.get("id") == oid:
            if o["op"] == "add":
                c = _course(body.get("course") or {})
                o = {**o, "course": {**c.__dict__, "weeks": c.weeks}}
            elif o["op"] == "edit":
                cur = {**parse_target(o["target"]), **(o.get("base") or {})}
                o = {**o, "set": _patch(body.get("set"), cur)}
            else:
                raise ValueError("这条修改不能这样改")
        out.append(o)
    return out


def ack(ops: list, oid: str, official: list[core.Course]) -> list:
    """同学点「我知道了」：教务有变动 → 以现在的教务为准不再提示；找不到 → 先不提示（课回来了照常生效）。"""
    out = []
    for o in ops:
        if o.get("id") == oid and o.get("target"):
            m = _find(official, o)
            o = {**o, "base": base_of(m)} if m is not None else {**o, "quiet": True}
            if m is not None:
                o.pop("quiet", None)
        out.append(o)
    return out


rebase = ack  # 旧名


def detach(ops: list, oid: str) -> list:
    """「未生效」的修改保留为自定义课（用 base + set 还原出那门课）；隐藏类的修改直接去掉。"""
    out = []
    for o in ops:
        if o.get("id") == oid and o.get("target"):
            if o.get("op") != "edit" or not o.get("base"):
                continue
            src = {**parse_target(o["target"]), "teacher": o["base"].get("teacher", ""),
                   "location": o["base"].get("location", ""),
                   "weeks": o.get("weeks") or o["base"].get("weeks", [])}
            c = _course({**src, **o.get("set", {})})
            o = {"id": o["id"], "op": "add", "course": {**c.__dict__, "weeks": c.weeks}}
        out.append(o)
    return out
