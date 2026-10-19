"""课表调停课（调课 / 停课 / 补课 / 换教室）合并 —— 原型，字段待真实账号验证。

数据源（只读查询，均在 wdkb「我的课表」应用内）：
  - 个人调课课程  POST /jwapp/sys/wdkb/modules/xskcb/xsdkkc.do   datas.xsdkkc.rows
      参数 XNXQDM（可选 SKZC 周次）。字段名参照金智 EMAP 通用部署
      （公开项目 Youwenqwq/ysu-sdk 记录的 Tkjg 模型）：
        KCM 课程名  JXBID 教学班
        SKXQ / KSJC / JSJC / ZCMC        调整前 星期 / 起节 / 止节 / 周次
        XSKXQ / XKSJC / XJSJC / XZCMC    调整后 星期 / 起节 / 止节 / 周次
        XJASDM（新教室代码，可能带 _DISPLAY）  SQSJ 申请时间
      吉大是否部署、字段是否一致：**尚未用真实账号验证**。
  - 整体调课记录  POST /jwapp/sys/wdkb/modules/jshkcb/cxztdkjl.do datas.cxztdkjl.rows
      全校批次（节假日整体调课）。2026-10-15 explore 实测：HTTP 200 / code 0 / 0 行，字段未知。

合并规则（纯函数，可重复执行不会叠加）：
  1) 有「调整前」：从课表里找同名、同星期、节次重叠的课，去掉对应周次；没找到则视为课表已含该调整，跳过。
  2) 有「调整后」：按新时间/新教室补一条；若课表已有完全相同的课覆盖这些周，则不重复添加。
  3) 停课 = 只有调整前；补课 = 只有调整后；换教室 = 时间不变、只换地点。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Iterable, Optional

from . import core

EP_ADJUSTED = "/jwapp/sys/wdkb/modules/xskcb/xsdkkc.do"
EP_OVERALL = "/jwapp/sys/wdkb/modules/jshkcb/cxztdkjl.do"


@dataclass(frozen=True)
class Slot:
    weekday: int
    start: int
    end: int
    weeks: tuple


@dataclass(frozen=True)
class Adjustment:
    name: str
    old: Optional[Slot] = None
    new: Optional[Slot] = None
    new_location: str = ""
    kind: str = ""          # 调课 / 停课 / 补课 / 换教室（推断或取自 TKLXDM_DISPLAY）
    applied_at: str = ""    # SQSJ
    raw_keys: tuple = field(default=(), compare=False)


def _s(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return str(v).strip()


def _int(v) -> int:
    try:
        return int(float(_s(v)))
    except ValueError:
        return 0


def parse_weeks_text(text: str) -> list[int]:
    """'1-16周' / '3,5,7周' / '1-15(单)' / '0101…' 位图 → [周]。"""
    t = _s(text)
    if not t:
        return []
    if re.fullmatch(r"[01]{4,}", t):
        return [i + 1 for i, ch in enumerate(t) if ch == "1"]
    t = (t.replace("第", "").replace("（", "(").replace("）", ")").replace("，", ",")
          .replace("、", ","))
    t = re.sub(r"\((单|双)周?\)", r"\1", t)
    t = t.replace("周", "")
    try:
        return sorted(set(core.parse_weeks(t)))
    except ValueError:
        return []


def _slot(row: dict, wd: str, ks: str, js: str, zc: str, bitmap: str) -> Optional[Slot]:
    weekday, start, end = _int(row.get(wd)), _int(row.get(ks)), _int(row.get(js))
    weeks = parse_weeks_text(row.get(bitmap)) or parse_weeks_text(row.get(zc))
    if not (1 <= weekday <= 7 and start >= 1 and end >= start and weeks):
        return None
    return Slot(weekday, start, end, tuple(weeks))


def row_to_adjustment(row: dict) -> Optional[Adjustment]:
    name = _s(row.get("KCM"))
    if not name:
        return None
    old = _slot(row, "SKXQ", "KSJC", "JSJC", "ZCMC", "SKZC")
    new = _slot(row, "XSKXQ", "XKSJC", "XJSJC", "XZCMC", "XSKZC")
    loc = _s(row.get("XJASMC")) or _s(row.get("XJASDM_DISPLAY")) or _s(row.get("XJASDM"))
    if new is None and loc and old is not None:
        new = old  # 只换教室：时间不变
    if old is None and new is None:
        return None
    kind = _s(row.get("TKLXDM_DISPLAY")) or (
        "停课" if new is None else "补课" if old is None else
        "换教室" if old == new else "调课")
    return Adjustment(name, old, new, loc, kind, _s(row.get("SQSJ")), tuple(sorted(row)))


def _overlap(c: core.Course, s: Slot) -> bool:
    return c.weekday == s.weekday and c.start <= s.end and s.start <= c.end


def apply_adjustments(courses: Iterable[core.Course], adjustments: Iterable[Adjustment]
                      ) -> tuple[list[core.Course], list[dict]]:
    """返回 (合并后课表, 变动说明)。不修改入参。"""
    out = [replace(c, weeks=list(c.weeks)) for c in courses]
    notes: list[dict] = []
    for a in adjustments:
        note = {"course": a.name, "kind": a.kind, "removed_weeks": [], "added_weeks": [],
                "skipped": ""}
        template: Optional[core.Course] = None
        if a.old is not None:
            gone = set(a.old.weeks)
            for i, c in enumerate(out):
                if c.name == a.name and _overlap(c, a.old) and gone & set(c.weeks):
                    template = template or c
                    hit = sorted(gone & set(c.weeks))
                    note["removed_weeks"] = sorted(set(note["removed_weeks"]) | set(hit))
                    out[i] = replace(c, weeks=[w for w in c.weeks if w not in gone])
        if a.new is not None:
            if template is None:
                template = next((c for c in out if c.name == a.name), None)
            loc = a.new_location or (template.location if template else "") or "待定"
            weeks = [w for w in a.new.weeks if not any(
                c.name == a.name and c.weekday == a.new.weekday and c.start == a.new.start
                and c.end == a.new.end and c.location == loc and w in c.weeks for c in out)]
            if weeks:
                out.append(core.Course(a.name, template.teacher if template else "", loc,
                                       a.new.weekday, a.new.start, a.new.end, weeks))
                note["added_weeks"] = weeks
        if not note["removed_weeks"] and not note["added_weeks"]:
            note["skipped"] = "课表中未找到原安排或已包含该调整"
        notes.append(note)
    return [c for c in out if c.weeks], notes


def fetch_adjustments(client, xnxqdm: str) -> list[Adjustment]:
    """只读查询个人调课课程；接口不存在/无权限时抛 JwxtError 由调用方忽略。"""
    from . import jwxt
    client.enter_emap_app(jwxt.REF_SCHEDULE)
    data = client._post_form(EP_ADJUSTED, {"XNXQDM": xnxqdm, "*order": "-SQSJ"}, jwxt.REF_SCHEDULE)
    rows = ((data.get("datas") or {}).get("xsdkkc") or {}).get("rows") or []
    return [a for a in (row_to_adjustment(r) for r in rows if isinstance(r, dict)) if a]
