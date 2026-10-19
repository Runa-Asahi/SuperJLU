"""课表个人修改层（原型）：教务课表 + 调停课合并之后，再叠加同学自己的增 / 删 / 改。

设计要点
  - schedule.csv 始终只放「教务原课表（+ 调停课）」，刷新照常整份覆盖；
    个人修改单独存在 schedule_overlay.json，刷新永远不碰它。
  - 读取时按顺序合并：教务 → 调停课 → 个人修改（纯函数，可重复执行，不会叠加）。
  - 每条修改指向一个稳定键 ``课程名|星期|起-止节``，并记下修改时看到的教务原样（base）。
    刷新后若教务那门课变了（周次 / 教室 / 教师），修改照常生效，但标记「教务有变动」；
    若教务已找不到那门课，修改不丢，标记「未生效」，等同学选择保留为自定义课或删掉。

schedule_overlay.json::

    {"version": 1, "ops": [
      {"id": "a1", "op": "add",  "course": {name, teacher, location, weekday, start, end, weeks}},
      {"id": "h1", "op": "hide", "target": "高等数学|1|1-2", "weeks": [8] | null, "base": {...}},
      {"id": "e1", "op": "edit", "target": "高等数学|1|1-2", "weeks": [9] | null,
       "set": {"location": "逸夫楼301", ...}, "base": {...}}
    ]}
"""
from __future__ import annotations

import secrets
from dataclasses import replace
from typing import Iterable, Optional

from . import core

VERSION = 1
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
    orig: dict = {}
    for c in courses:
        orig.setdefault(course_key(c), []).append(base_of(c))
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
            hits = [r for r in rows if r["src"] == "official" and r["key"] == target
                    and (scope is None or scope & set(r["weeks"]))]
            if not hits:
                issues.append({"oid": oid, "kind": "missing", "target": target, "op": kind,
                               "message": "教务课表里已找不到这门课（可能调课或取消了），这条修改暂未生效"})
                continue
            base = op.get("base")
            if base and not any(_same_base(base, b, scope) for b in orig.get(target, [])):
                issues.append({"oid": oid, "kind": "changed", "target": target, "op": kind,
                               "message": "你修改之后教务又更新了这门课，请核对一下"})
            for r in hits:
                take = sorted(set(r["weeks"]) & scope) if scope is not None else list(r["weeks"])
                r["weeks"] = [w for w in r["weeks"] if w not in take]
                if kind == "edit" and take:
                    patch = {k: v for k, v in (op.get("set") or {}).items() if k in EDITABLE}
                    c = _course({**r, **patch, "weeks": take})
                    rows.append(_row(c, "edited", oid) | {"from": target})
        except (ValueError, TypeError, KeyError):
            issues.append({"oid": oid, "kind": "invalid", "op": kind, "message": "这条修改的数据已损坏，已跳过"})
    return [r for r in rows if r["weeks"]], issues


def _same_base(saved: dict, now: dict, scope: Optional[set]) -> bool:
    """只按周修改时，只关心那几周还在、教室教师没变；整门修改才比较全部周次。"""
    if saved.get("location") != now["location"] or saved.get("teacher") != now["teacher"]:
        return False
    if scope is None:
        return saved.get("weeks") == now["weeks"]
    return scope <= set(now["weeks"]) or not (scope & set(saved.get("weeks") or []))


def _as_course(r: dict) -> core.Course:
    return core.Course(r["name"], r["teacher"], r["location"], r["weekday"], r["start"], r["end"],
                       list(r["weeks"]))


def to_courses(rows: Iterable[dict]) -> list[core.Course]:
    return [_as_course(r) for r in rows]


# ---- 对 overlay 文档的增删（Store 调用；均返回新文档，不原地改） ----

def empty() -> dict:
    return {"version": VERSION, "ops": []}


def make_op(action: str, body: dict, official: list[core.Course]) -> dict:
    """把界面提交的动作变成一条 op；目标必须是当前教务课表里的课。"""
    if action == "add":
        c = _course(body.get("course") or {})
        return {"id": new_id(), "op": "add", "course": {**c.__dict__, "weeks": c.weeks}}
    target = body.get("target")
    match = next((c for c in official if course_key(c) == target), None)
    if match is None:
        raise ValueError("找不到要修改的课程，请刷新后重试")
    weeks = sorted({int(w) for w in body.get("weeks") or []}) or None
    op = {"id": new_id(), "op": action, "target": target, "weeks": weeks, "base": base_of(match)}
    if action == "edit":
        patch = {k: v for k, v in (body.get("set") or {}).items() if k in EDITABLE}
        if not patch:
            raise ValueError("没有要修改的内容")
        _course({**match.__dict__, **patch})  # 提前校验
        op["set"] = patch
    return op


def remove(doc: dict, oid: str) -> dict:
    return {**doc, "ops": [o for o in doc.get("ops", []) if o.get("id") != oid]}


def rebase(doc: dict, oid: str, official: list[core.Course]) -> dict:
    """「教务有变动」时同学点「我知道了」：把 base 更新成当前教务原样，不再提示。"""
    ops = []
    for o in doc.get("ops", []):
        if o.get("id") == oid and o.get("target"):
            m = next((c for c in official if course_key(c) == o["target"]), None)
            if m is not None:
                o = {**o, "base": base_of(m)}
        ops.append(o)
    return {**doc, "ops": ops}


def detach(doc: dict, oid: str) -> dict:
    """「未生效」的修改改成自定义课保留下来（只对 edit 有意义：用 base + set 还原出那门课）。"""
    ops = []
    for o in doc.get("ops", []):
        if o.get("id") == oid and o.get("op") == "edit" and o.get("base"):
            name, wd, se = o["target"].split("|")
            s, e = se.split("-")
            src = {"name": name, "weekday": int(wd), "start": int(s), "end": int(e),
                   "teacher": o["base"].get("teacher", ""), "location": o["base"].get("location", ""),
                   "weeks": o.get("weeks") or o["base"].get("weeks", [])}
            c = _course({**src, **o.get("set", {})})
            o = {"id": o["id"], "op": "add", "course": {**c.__dict__, "weeks": c.weeks}}
        ops.append(o)
    return {**doc, "ops": ops}


def validate_doc(doc) -> dict:
    """导入备份时用：结构不对抛 ValueError；未知 op 丢弃。"""
    if not isinstance(doc, dict) or not isinstance(doc.get("ops"), list):
        raise ValueError("这不是 SuperJLU 课表修改备份文件")
    ops = [o for o in doc["ops"] if isinstance(o, dict) and o.get("op") in OPS and o.get("id")]
    return {"version": VERSION, "ops": ops}
