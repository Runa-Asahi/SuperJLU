"""课表的唯一读取入口：教务原课表 → 调停课（按设置）→ 个人修改。

App 界面、iCal 导出、命令行（fetch / ics / today）和 MCP 工具都从这里读，保证看到的是同一份课表。

数据目录里的文件（均为明文，不属于加密个人缓存）：
  schedule.csv              教务原课表（刷新整份覆盖，不含调课）
  schedule_meta.json        {"term": 学期代码}（刷新课表时写）
  schedule_adjustments.json 调停课 {"term", "fetched_at", "items": [...]}
  schedule_overlay.json     个人修改（见 overlay.py）
  settings.json             {"apply_adjustments": bool}（缺省为开）
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Optional

from . import adjust, core, overlay as ov


def _json(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def current_term(root: Path) -> str:
    """课表所属学期：刷新课表时记下的学期代码，没有就用校历的。"""
    meta = _json(Path(root) / "schedule_meta.json", {}) or {}
    cal = _json(Path(root) / "calendar.json", {}) or {}
    return str((meta.get("term") if isinstance(meta, dict) else "")
               or (cal.get("term") if isinstance(cal, dict) else "") or "")


def adjustments_enabled(root: Path) -> bool:
    s = _json(Path(root) / "settings.json", {}) or {}
    v = s.get("apply_adjustments") if isinstance(s, dict) else None
    return v is None or bool(v)


def jwxt_courses(root: Path) -> list[core.Course]:
    f = Path(root) / "schedule.csv"
    return core.load_courses(str(f)) if f.exists() else []


def load_adjustments(root: Path, term: Optional[str] = None) -> list[adjust.Adjustment]:
    """本学期已取到的调停课；学期不符或文件损坏时为空。"""
    d = _json(Path(root) / "schedule_adjustments.json", None)
    if not isinstance(d, dict) or not isinstance(d.get("items"), list):
        return []
    term = current_term(root) if term is None else term
    if term and d.get("term") and d["term"] != term:
        return []
    out = []
    for x in d["items"]:
        try:
            out.append(adjust.Adjustment.from_dict(x))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def load_overlay(root: Path, term: Optional[str] = None) -> dict:
    term = current_term(root) if term is None else term
    try:
        return ov.normalize(_json(Path(root) / "schedule_overlay.json", None) or ov.empty(), term)
    except ValueError:
        return ov.empty()


def _hint_rows(rows: list[dict], adjs: Iterable[adjust.Adjustment], enabled: bool) -> None:
    """ISTK 提示：教务把这门课标为有调/停课，但我们没有对应的调课记录（或设置关着）时提醒一句。"""
    known = {a.jxbid for a in adjs if a.jxbid} | {a.name for a in adjs}
    for r in rows:
        if r.get("istk") and r["src"] == "official" and not r.get("adj"):
            if not enabled:
                r["hint"] = "教务标记这门课有调课或停课；已关闭「自动应用调课/停课」，课表按原始安排显示。"
            elif not (r.get("jxbid") in known or r["name"] in known):
                r["hint"] = "教务标记这门课有调课或停课，但没读到具体安排，请以教务通知为准。"


def build(official: list[core.Course], adjs: list[adjust.Adjustment], ops: list,
          enabled: bool = True) -> dict:
    """纯函数：合并出界面要的全部内容。rows 的 src：official / edited / custom / cancelled（停课，灰显）。"""
    cancelled: list[core.Course] = []
    notes: list[dict] = []
    cs = list(official)
    if enabled and adjs:
        cs, notes, cancelled = adjust.merge(cs, adjs)
    rows, issues = ov.apply_overlay(cs, ops)
    _hint_rows(rows, adjs, enabled)
    for c in cancelled:
        rows.append({**c.__dict__, "weeks": list(c.weeks), "key": ov.course_key(c), "src": "cancelled",
                     "oid": ""})
    return {"rows": rows, "issues": issues, "notes": notes,
            "applied": sum(1 for n in notes if not n["skipped"]), "adjustments": adjs}


def view(root: Path) -> dict:
    root = Path(root)
    term = current_term(root)
    enabled = adjustments_enabled(root)
    out = build(jwxt_courses(root), load_adjustments(root, term),
                ov.term_ops(load_overlay(root, term), term), enabled)
    out.update(term=term, enabled=enabled)
    return out


def to_courses(rows: Iterable[dict]) -> list[core.Course]:
    """真正要上的课（不含灰显的停课）：给 iCal、命令行、MCP 用。"""
    return ov.to_courses(r for r in rows if r.get("src") != "cancelled")


def courses(root: Path) -> list[core.Course]:
    """唯一的课表读取函数：与 App 看到的完全一致。"""
    return to_courses(view(root)["rows"])


def root_for_csv(csv_path) -> Path:
    """命令行 / MCP 给的是 schedule.csv 路径：它所在目录就是数据目录（没有调课/修改文件时等同原 CSV）。"""
    return Path(csv_path).expanduser().resolve().parent


def courses_from_csv(csv_path) -> list[core.Course]:
    p = Path(csv_path).expanduser()
    if p.name != "schedule.csv":  # 任意名字的 CSV：按原样读，不去猜旁边的文件
        return core.load_courses(str(p))
    return courses(root_for_csv(p))
