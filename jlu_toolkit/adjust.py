"""课表调停课（调课 / 停课 / 补课 / 换教室）合并。

数据源（只读查询，均在 wdkb「我的课表」应用内）：
  - 个人调课课程  POST /jwapp/sys/wdkb/modules/xskcb/xsdkkc.do   datas.xsdkkc.rows
      参数 XNXQDM（可选 SKZC 周次）。字段名参照金智 EMAP 通用部署
      （公开项目 Youwenqwq/ysu-sdk 记录的 Tkjg 模型）：
        KCM 课程名  JXBID 教学班
        SKXQ / KSJC / JSJC / ZCMC        调整前 星期 / 起节 / 止节 / 周次
        XSKXQ / XKSJC / XJSJC / XZCMC    调整后 星期 / 起节 / 止节 / 周次
        XJASDM 新教室代码 / XJASMC 新教室名（带校区前缀）  SQSJ 申请时间  XSKJS 新教师「姓名/工号」
      2026-10-19 用吉大真实账号（2026-2027-1）验证：已部署，字段与上面一致；另有 KCH、TKLXDM、SFECTK。
      教务课表 cxxszhxqkb **不包含**调课结果（被调走的那周仍在原 SKZC 里），所以必须合并。
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
    jxbid: str = ""         # 教学班 ID：有就按它匹配课表，没有退回课程名
    new_teacher: str = ""   # XSKJS「姓名/工号」→ 姓名

    def to_dict(self) -> dict:
        sl = lambda x: None if x is None else {"weekday": x.weekday, "start": x.start, "end": x.end,
                                               "weeks": list(x.weeks)}
        return {"name": self.name, "jxbid": self.jxbid, "kind": self.kind, "old": sl(self.old),
                "new": sl(self.new), "new_location": self.new_location, "new_teacher": self.new_teacher,
                "applied_at": self.applied_at}

    @classmethod
    def from_dict(cls, d: dict) -> "Adjustment":
        sl = lambda x: None if not x else Slot(int(x["weekday"]), int(x["start"]), int(x["end"]),
                                               tuple(int(w) for w in x["weeks"]))
        return cls(str(d["name"]), sl(d.get("old")), sl(d.get("new")), str(d.get("new_location") or ""),
                   str(d.get("kind") or ""), str(d.get("applied_at") or ""), (),
                   str(d.get("jxbid") or ""), str(d.get("new_teacher") or ""))


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
    """'1-16周' / '3,5,7周' / '1-15(单)' / '0101…' 位图 → [周]。

    位图按下标取周，长度不限：课表 SKZC 常为 12 位、调课 XSKZC 为 19 位，末尾补零不影响。"""
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


def room_name(text: str) -> str:
    """调课接口的教室带校区前缀（前卫-第三教学楼-第七阶梯），课表里是「逸夫楼第十阶梯」：去掉校区、连起来。"""
    parts = [p.strip() for p in _s(text).split("-") if p.strip()]
    if len(parts) >= 3:
        parts = parts[1:]
    return "".join(parts)


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
    loc = room_name(_s(row.get("XJASMC")) or _s(row.get("XJASDM_DISPLAY")))
    if new is None and loc and old is not None:
        new = old  # 只换教室：时间不变
    if old is None and new is None:
        return None
    kind = _s(row.get("TKLXDM_DISPLAY")) or (
        "停课" if new is None else "补课" if old is None else
        "换教室" if old == new else "调课")
    teacher = ",".join(p.split("/")[0].strip() for p in _s(row.get("XSKJS")).split(",") if p.strip())
    return Adjustment(name, old, new, loc, kind, _s(row.get("SQSJ")), tuple(sorted(row)),
                      _s(row.get("JXBID")), teacher)


def _overlap(c: core.Course, s: Slot) -> bool:
    return c.weekday == s.weekday and c.start <= s.end and s.start <= c.end


def _same(c: core.Course, a: Adjustment) -> bool:
    if a.jxbid and getattr(c, "jxbid", ""):
        return c.jxbid == a.jxbid
    return c.name == a.name


_WD = "一二三四五六日"


def _slot_text(s: Slot) -> str:
    return f"周{_WD[s.weekday - 1]} 第{s.start}-{s.end}节 第{','.join(map(str, s.weeks))}周"


def _note(a: Adjustment, template: Optional[core.Course]) -> str:
    was = f"原 {_slot_text(a.old)}" if a.old else ""
    if template is not None and template.location and a.old:
        was += f" · {template.location}"
    return f"{a.kind or '调课'}" + (f"：{was}" if was else "") + (f"（{a.applied_at[:10]} 申请）" if a.applied_at else "")


def apply_adjustments(courses: Iterable[core.Course], adjustments: Iterable[Adjustment]
                      ) -> tuple[list[core.Course], list[dict]]:
    """返回 (合并后课表, 变动说明)。不修改入参。有教学班 ID 时按它匹配，否则按课程名。"""
    out, notes, _ = merge(courses, adjustments)
    return out, notes


def merge(courses: Iterable[core.Course], adjustments: Iterable[Adjustment]
          ) -> tuple[list[core.Course], list[dict], list[core.Course]]:
    """同 apply_adjustments，另返回「停课」的那几节（周次只含停掉的周、adj 为说明），供课表灰显。"""
    out = [replace(c, weeks=list(c.weeks)) for c in courses]
    notes: list[dict] = []
    cancelled: list[core.Course] = []
    for a in adjustments:
        note = {"course": a.name, "kind": a.kind, "removed_weeks": [], "added_weeks": [],
                "skipped": "", "applied_at": a.applied_at}
        template: Optional[core.Course] = None
        if a.old is not None:
            gone = set(a.old.weeks)
            for i, c in enumerate(out):
                if _same(c, a) and _overlap(c, a.old) and gone & set(c.weeks):
                    template = template or c
                    hit = sorted(gone & set(c.weeks))
                    note["removed_weeks"] = sorted(set(note["removed_weeks"]) | set(hit))
                    out[i] = replace(c, weeks=[w for w in c.weeks if w not in gone])
                    if a.new is None:  # 停课：留一份灰显用
                        cancelled.append(replace(c, weeks=hit, adj=_note(a, c)))
        if a.new is not None:
            if template is None:
                template = next((c for c in out if _same(c, a)), None)
            loc = a.new_location or (template.location if template else "") or "待定"
            weeks = [w for w in a.new.weeks if not any(
                _same(c, a) and c.weekday == a.new.weekday and c.start == a.new.start
                and c.end == a.new.end and c.location == loc and w in c.weeks for c in out)]
            if weeks:
                out.append(core.Course(
                    template.name if template else a.name,
                    a.new_teacher or (template.teacher if template else ""), loc,
                    a.new.weekday, a.new.start, a.new.end, weeks,
                    (template.jxbid if template else "") or a.jxbid, template.kch if template else "",
                    _note(a, template)))
                note["added_weeks"] = weeks
        if not note["removed_weeks"] and not note["added_weeks"]:
            note["skipped"] = "课表中未找到原安排或已包含该调整"
        notes.append(note)
    return [c for c in out if c.weeks], notes, cancelled


def fetch_adjustments(client, xnxqdm: str) -> list[Adjustment]:
    """只读查询个人调课课程；接口不存在/无权限时抛 JwxtError 由调用方忽略。"""
    from . import jwxt
    client.enter_emap_app(jwxt.REF_SCHEDULE)
    data = client._post_form(EP_ADJUSTED, {"XNXQDM": xnxqdm, "*order": "-SQSJ"}, jwxt.REF_SCHEDULE,
                             mark_expired=False)
    rows = ((data.get("datas") or {}).get("xsdkkc") or {}).get("rows") or []
    return [a for a in (row_to_adjustment(r) for r in rows if isinstance(r, dict)) if a]
