"""空教室查询（金智 EMAP「空闲教室查询」kxjscx 应用）。

用户确认：该功能可用，但必须带校区、空闲日期、空闲节次等条件；不带条件只会返回错误包。
吉大实际的接口名/字段名尚未确认，所以本模块：
  1. 先进入应用（GET kxjscx/*default/index.do，换取 _WEU）；
  2. 读取 EMAP 模块元数据（POST modules/<模块>.do，不带动作名），拿到动作 URL、
     查询字段名、字典 URL（校区/教学楼代码表）；
  3. 按「元数据推断」加若干常见金智参数方案依次尝试，第一个返回 datas.*.rows 的组合
     会保存为 rooms_profile.json，之后直接复用。
全部为只读查询。探测输出只含状态码/code/msg/字段名。
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import emap, jwxt

# 吉大真实页面：/jwapp/sys/kxjas/*default/index.do#/kxjscx → 应用 kxjas，kxjscx 是前端路由/视图。
# （kxjscx 作为应用名会返回 #E2140 Not found app）
APP_NAME = "kxjas"
ROUTE = "kxjscx"
APP_ROOT = f"/jwapp/sys/{APP_NAME}/"
APP = f"https://iedu.jlu.edu.cn{APP_ROOT}*default/index.do"
BASE = APP_ROOT + "modules/"
KXJAS = emap.App(APP_NAME, ROUTE)
META_MODULES = ("kxjscx", "kxjas", "kxjs", "jscx")
ENDPOINTS = (
    BASE + "kxjscx/cxkxjs.do",
    BASE + "kxjscx/kxjscx.do",
    BASE + "kxjscx/cxkxjas.do",
    BASE + "kxjscx/cxkxjscx.do",
    BASE + "kxjscx/jscx.do",
    BASE + "kxjas/cxkxjas.do",
    BASE + "kxjas/kxjas.do",
)
# EMAP 前端常见的视图脚本位置（路由 #/kxjscx）
VIEW_FILES = (
    f"modules/{ROUTE}/{ROUTE}.js", f"modules/{ROUTE}.js", f"{ROUTE}/{ROUTE}.js",
    f"pages/{ROUTE}/{ROUTE}.js", f"{ROUTE}.js", "index.js", "config.js", "router.js",
    "public/js/index.js", "public/js/config.js", f"modules/{ROUTE}/{ROUTE}.html",
    f"{ROUTE}/{ROUTE}.html", "*default/config.json",
)


@dataclass
class RoomQuery:
    campus: str
    date: str  # YYYY-MM-DD
    start: int
    end: int
    building: str = ""
    term: str = ""
    week: int = 0
    weekday: int = 0  # 1-7
    kind: str = ""          # 教室类型代码
    seat_min: int = 0       # 上课座位数
    seat_max: int = 0
    exam_min: int = 0       # 考试座位数
    exam_max: int = 0
    mode: str = "date"      # date=按日期 / week=按周次
    weeks: str = ""         # 按周次：如 "6" / "6-8" / "6,8"
    extra: dict = field(default_factory=dict)  # 元数据里其它检索字段 {字段名: 值}

    @property
    def week_list(self) -> str:
        return expand_weeks(self.weeks) if self.weeks else (str(self.week) if self.week else "")

    @property
    def jc_list(self) -> str:
        return ",".join(str(i) for i in range(self.start, self.end + 1))


@dataclass
class Room:
    name: str
    building: str = ""
    campus: str = ""
    seats: str = ""
    kind: str = ""
    exam_seats: str = ""
    free_date: str = ""
    free_periods: str = ""
    free_time: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _s(v) -> str:
    return jwxt._emap_str(v)


def parse_periods_arg(s: str) -> tuple[int, int]:
    m = re.fullmatch(r"\s*(\d{1,2})\s*(?:-\s*(\d{1,2}))?\s*", s or "")
    if not m:
        raise ValueError("节次格式应为 3 或 3-4")
    a = int(m.group(1))
    b = int(m.group(2) or a)
    if not 1 <= a <= b <= 14:
        raise ValueError("节次范围应在 1-14 且起始 ≤ 结束")
    return a, b


def _period_bounds(periods: dict) -> dict[int, tuple[str, str]]:
    """把 {节次: [开始, 结束]} 规范成 {int: (HH:MM, HH:MM)}。"""
    out: dict[int, tuple[str, str]] = {}
    for k, v in (periods or {}).items():
        try:
            n = int(k)
        except (TypeError, ValueError):
            continue
        if not isinstance(v, (list, tuple)) or len(v) < 2:
            continue
        a, b = str(v[0]), str(v[1])
        if re.fullmatch(r"\d{1,2}:\d{2}", a) and re.fullmatch(r"\d{1,2}:\d{2}", b):
            out[n] = (a.zfill(5), b.zfill(5))
    return out


def study_time_for_periods(periods: dict, start: int, end: int) -> Optional[tuple[str, str]]:
    """节次范围 → 自习起止时间（第一节开始～最后一节结束）。"""
    m = _period_bounds(periods)
    if start not in m or end not in m or start > end:
        return None
    return m[start][0], m[end][1]


def periods_for_study_time(periods: dict, start: str, end: str) -> Optional[tuple[int, int]]:
    """自习时间 [start, end) 与之有重叠的节次范围；无重叠返回 None。"""
    if not start or not end or start >= end:
        return None
    m = _period_bounds(periods)
    hit = [n for n, (a, b) in m.items() if a < end and b > start]
    if not hit:
        return None
    return min(hit), max(hit)


def expand_weeks(s: str) -> str:
    """"6-8,10" → "6,7,8,10"。"""
    out: list[int] = []
    for part in re.split(r"[,，\s]+", (s or "").strip()):
        if not part:
            continue
        m = re.fullmatch(r"(\d{1,2})(?:-(\d{1,2}))?", part)
        if not m:
            raise ValueError("周次格式应为 6 / 6-8 / 6,8")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if not 1 <= a <= b <= 30:
            raise ValueError("周次范围应在 1-30 且起始 ≤ 结束")
        out += range(a, b + 1)
    return ",".join(str(i) for i in dict.fromkeys(out))


def week_and_weekday(date: str, first_monday: Optional[str]) -> tuple[int, int]:
    d = dt.date.fromisoformat(date)
    if not first_monday:
        return 0, d.isoweekday()
    return (d - dt.date.fromisoformat(first_monday)).days // 7 + 1, d.isoweekday()


# ───────────────────────── EMAP 元数据 ─────────────────────────

from .emap import _CODE, parse_meta  # noqa: E402,F401  （已并入 emap）


def parse_search_fields(obj) -> list[dict]:
    """元数据里的检索字段 → [{name, caption, xtype, dict, builder}]（只有代码/标题，无数据）。"""
    out: dict = {}

    def walk(x):
        if isinstance(x, dict):
            n = x.get("name")
            skeys = [k for k in x if isinstance(k, str) and (k.startswith("search") or k.startswith("search."))]
            if isinstance(n, str) and _CODE.match(n) and (
                    x.get("search") is True or skeys or x.get("searchable") is True):
                if (x.get("search") is not False and x.get("search.omitted") is not True
                        and x.get("search.hidden") is not True):
                    cap = x.get("caption") or x.get("title") or x.get("label") or ""
                    u = x.get("url") or x.get("dict") or ""
                    out.setdefault(n, {
                        "name": n, "caption": str(cap)[:30],
                        "xtype": str(x.get("searchxtype") or x.get("search.xtype") or x.get("xtype") or "")[:30],
                        "dict": u if isinstance(u, str) and ".do" in u else "",
                        "builder": str(x.get("search.builder") or x.get("builder") or "")[:20]})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(obj)
    return list(out.values())


def query_model_controls(obj, action_hint: str = "cxkxjs") -> list[dict]:
    """兜底：查询动作所在模型的全部 controls（名称/标题/类型/字典）。"""
    res: list[dict] = []

    def walk(x):
        if isinstance(x, dict):
            u = x.get("url")
            ctrls = x.get("controls") or x.get("fields") or x.get("items")
            if isinstance(u, str) and action_hint in u and isinstance(ctrls, list) and not res:
                for cdef in ctrls:
                    if isinstance(cdef, dict) and isinstance(cdef.get("name"), str) and _CODE.match(cdef["name"]):
                        d = cdef.get("url") or cdef.get("dict") or ""
                        res.append({"name": cdef["name"], "caption": str(cdef.get("caption") or "")[:30],
                                    "xtype": str(cdef.get("xtype") or "")[:30],
                                    "dict": d if isinstance(d, str) and ".do" in d else "",
                                    "builder": str(cdef.get("builder") or "")[:20]})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(obj)
    return res


def _meta_urls(extra_modules=()) -> list[tuple[str, str, dict]]:
    """(方法, 路径, 表单)：EMAP 元数据常见取法。"""
    out = []
    for m in dict.fromkeys(list(META_MODULES) + list(extra_modules)):
        path = BASE + m + ".do"
        out += [("POST", path, {}), ("GET", path + "?*json=1", {}), ("POST", path, {"*json": "1"}),
                ("GET", path, {})]
    return out


def _try_json(client, method: str, path: str, form: dict):
    return emap._try(client, KXJAS, method, path, form)


def fetch_meta(client, extra_modules=(), trace: Optional[list] = None) -> dict:
    merged = {"modules_ok": [], "actions": [], "fields": [], "dicts": {}, "search": []}
    for method, path, form in _meta_urls(extra_modules):
        code, obj = _try_json(client, method, path, form)
        rec = {"method": method, "path": path, "form_keys": sorted(form), "status": code}
        if isinstance(obj, dict):
            rec["keys"] = sorted(obj)[:20]
            if isinstance(obj.get("code"), (str, int)):
                rec["code"] = str(obj["code"])[:8]
            if isinstance(obj.get("msg"), str):
                rec["msg"] = re.sub(r"\d{5,}", "#", obj["msg"])[:60]
        elif isinstance(obj, str):
            rec["non_json_bytes"] = len(obj)
        if trace is not None:
            trace.append(rec)
        if not isinstance(obj, (dict, list)):
            continue
        meta = parse_meta(obj)
        if meta["actions"] or meta["fields"]:
            m = path.rsplit("/", 1)[-1].split(".do")[0]
            rec["actions"], rec["fields"] = meta["actions"], meta["fields"]
            if m not in merged["modules_ok"]:
                merged["modules_ok"].append(m)
            merged["actions"] = sorted(set(merged["actions"]) | set(meta["actions"]))
            merged["fields"] = sorted(set(merged["fields"]) | set(meta["fields"]))
            merged["dicts"].update(meta["dicts"])
            have = {s["name"] for s in merged["search"]}
            found_s = parse_search_fields(obj) or query_model_controls(obj)
            for s in found_s:
                if s["name"] not in have:
                    merged["search"].append(s)
                    if s["dict"]:
                        merged["dicts"].setdefault(s["name"], s["dict"])
    return merged


# ───────────────────────── 参数方案 ─────────────────────────

def _meta_scheme(fields: list[str]) -> Optional[Callable[[RoomQuery], dict]]:
    """按元数据字段名推断参数。"""
    f = set(fields)
    pick = lambda *cands: next((c for c in cands if c in f), None)  # noqa: E731
    campus = pick("XXXQDM", "XQDM", "XXXQ", "SZXQ")
    date = pick("KXRQ", "RQ", "CXRQ", "KXSJ")
    if not campus or not date:
        return None
    ks, js, jc = pick("KSJC", "QSJC"), pick("JSJC", "ZZJC"), pick("JC", "KXJC", "JCS")
    zc, xq = pick("ZC", "SKZC"), pick("XQJ", "SKXQ", "XQ")
    bld = pick("JXLDM", "JZWDM", "LH")

    def build(q: RoomQuery) -> dict:
        d = {campus: q.campus, date: q.date}
        if ks and js:
            d[ks], d[js] = str(q.start), str(q.end)
        if jc:
            d[jc] = q.jc_list
        if zc and q.week:
            d[zc] = str(q.week)
        if xq and xq != campus:
            d[xq] = str(q.weekday)
        if bld and q.building:
            d[bld] = q.building
        if "XNXQDM" in f and q.term:
            d["XNXQDM"] = q.term
        return d

    return build


def _qs(items) -> str:
    """items: (name, value) 或 (name, value, builder)。"""
    out = []
    for it in items:
        k, v = it[0], it[1]
        b = it[2] if len(it) > 2 else "equal"
        out.append({"name": k, "value": v, "linkOpt": "AND", "builder": b})
    return json.dumps(out, ensure_ascii=False)


SEAT_KEYS = ("SKZWS", "ZWS", "RNRS")
EXAM_KEYS = ("KSZWS", "KSRS")
KIND_KEYS = ("JASLXDM", "JSLXDM", "JASLX")
BLD_KEYS = ("JXLDM", "JZWDM", "LH")


def _filters(q: RoomQuery, f: set) -> tuple[dict, list]:
    """新增筛选：直接表单字段 + querySetting 条件（范围用 moreEqual/lessEqual）。"""
    pick = lambda ks: next((k for k in ks if k in f), ks[0])  # noqa: E731
    form, cond = {}, []
    if q.kind:
        k = pick(KIND_KEYS); form[k] = q.kind; cond.append((k, q.kind, "equal"))
    for ks, lo, hi in ((SEAT_KEYS, q.seat_min, q.seat_max), (EXAM_KEYS, q.exam_min, q.exam_max)):
        k = pick(ks)
        if lo:
            form[k + "_MIN"] = str(lo); cond.append((k, str(lo), "moreEqual"))
        if hi:
            form[k + "_MAX"] = str(hi); cond.append((k, str(hi), "lessEqual"))
    for k, v in (q.extra or {}).items():
        if v not in ("", None):
            form[k] = str(v); cond.append((k, str(v), "equal"))
    return form, cond


_DATE_KEYS = ("KXRQ", "RQ", "CXRQ", "KXSJ")
_WEEK_KEYS = ("ZC", "SKZC", "KXZC", "XQ", "XQJ", "SKXQ")

SPECIAL_ROOM_WORDS = ("实验", "机房", "计算机", "语音", "画室", "琴房", "舞蹈", "研讨", "录播",
                      "报告厅", "会议", "工作室", "制图", "体育", "专用")


def is_special_room(r) -> bool:
    """实验室、机房、语音室等专用教室（按教室类型和名称关键词判断）。"""
    text = f"{getattr(r, 'kind', '') or ''} {getattr(r, 'name', '') or ''}"
    return any(w in text for w in SPECIAL_ROOM_WORDS)


def _with_filters(fn: Callable[[RoomQuery], dict], fields) -> Callable[[RoomQuery], dict]:
    f = set(fields or [])

    def build(q: RoomQuery) -> dict:
        d = dict(fn(q))
        if q.mode == "week":
            for k in _DATE_KEYS:
                d.pop(k, None)
            wl = q.week_list
            for k in ("ZC", "SKZC", "KXZC"):
                if k in d or k in f:
                    d[k] = wl
            d.setdefault("ZC", wl)
        elif q.date and any(d.get(k) for k in _DATE_KEYS):
            # 按日期：日期已唯一确定周次和星期，不再同时提交周次/星期，
            # 避免校历首周一不准时 ZC/XQ 与日期互相矛盾导致查不到或查错。
            for k in _WEEK_KEYS:
                d.pop(k, None)
        form, cond = _filters(q, f)
        if "querySetting" in d:
            base = json.loads(d["querySetting"])
            if q.mode == "week":
                base = [c for c in base if c["name"] not in _DATE_KEYS]
                base.append({"name": "ZC", "value": q.week_list, "linkOpt": "AND", "builder": "m_value_equal"})
                base.append({"name": "XQ", "value": str(q.weekday), "linkOpt": "AND", "builder": "equal"})
            base += json.loads(_qs(cond)) if cond else []
            d["querySetting"] = json.dumps(base, ensure_ascii=False)
        else:
            d.update(form)
            if cond:
                d["querySetting"] = _qs(cond)
        return d

    return build


SCHEMES: dict[str, Callable[[RoomQuery], dict]] = {
    "form_kxrq_ksjc": lambda q: {k: v for k, v in {
        "XXXQDM": q.campus, "KXRQ": q.date, "KSJC": str(q.start), "JSJC": str(q.end),
        "XNXQDM": q.term, "ZC": str(q.week or ""), "XQ": str(q.weekday), "JXLDM": q.building,
        "pageSize": "500", "pageNumber": "1"}.items() if v},
    "form_rq_jc": lambda q: {k: v for k, v in {
        "XXXQDM": q.campus, "RQ": q.date, "JC": q.jc_list, "XNXQDM": q.term,
        "ZC": str(q.week or ""), "XQJ": str(q.weekday), "JXLDM": q.building,
        "pageSize": "500", "pageNumber": "1"}.items() if v},
    "form_zc_xq": lambda q: {k: v for k, v in {
        "XXXQDM": q.campus, "XNXQDM": q.term, "ZC": str(q.week or ""), "XQ": str(q.weekday),
        "KSJC": str(q.start), "JSJC": str(q.end), "JXLDM": q.building,
        "pageSize": "500", "pageNumber": "1"}.items() if v},
    "querySetting": lambda q: {
        "querySetting": _qs([(k, v) for k, v in (("XXXQDM", q.campus), ("KXRQ", q.date),
                             ("KSJC", str(q.start)), ("JSJC", str(q.end)), ("JXLDM", q.building)) if v]),
        "XNXQDM": q.term, "pageSize": "500", "pageNumber": "1"},
    "requestParamStr": lambda q: {"requestParamStr": json.dumps({k: v for k, v in {
        "XXXQDM": q.campus, "KXRQ": q.date, "KSJC": str(q.start), "JSJC": str(q.end),
        "XNXQDM": q.term, "ZC": q.week or "", "XQ": q.weekday, "JXLDM": q.building}.items() if v},
        ensure_ascii=False)},
}


def _rows_any(obj) -> Optional[tuple[str, list]]:
    hit = emap.rows_any(obj)
    return (hit[0], hit[1]) if hit else None


def _total(obj) -> Optional[int]:
    if not isinstance(obj, dict):
        return None
    for blk in (obj.get("datas") or {}).values():
        if isinstance(blk, dict):
            for k in ("totalSize", "total", "totalCount"):
                try:
                    return int(blk[k])
                except (KeyError, TypeError, ValueError):
                    pass
    return None


PAGE_SIZE = 200
MAX_PAGES = 60


def fetch_all_pages(client, ep: str, form: dict, first_obj, first_rows: list,
                    require_complete: bool = False) -> list:
    """按 totalSize 翻页拉全；没有 totalSize 时直到某页不足一页为止。"""
    rows = list(first_rows)
    total = _total(first_obj)
    size = int(form.get("pageSize") or 0)
    if require_complete and not size and (total is None or len(rows) < total):
        raise jwxt.JwxtError("空闲记录缺少完整分页信息，请重试")
    if not size or (total is not None and len(rows) >= total) or (total is None and len(first_rows) < size):
        return rows
    page = int(form.get("pageNumber") or 1)
    last_count = len(first_rows)
    while page < MAX_PAGES:
        page += 1
        code, text, _ = client.post_raw(ep, {**form, "pageNumber": str(page)}, APP)
        if code != 200:
            if require_complete:
                raise jwxt.JwxtError("空闲记录未获取完整，请重试")
            break
        try:
            hit = _rows_any(json.loads(text))
        except (json.JSONDecodeError, ValueError):
            if require_complete:
                raise jwxt.JwxtError("空闲记录未获取完整，请重试")
            break
        if not hit or not hit[1]:
            if require_complete and (not hit or (total is not None and len(rows) < total)):
                raise jwxt.JwxtError("空闲记录未获取完整，请重试")
            break
        rows += hit[1]
        last_count = len(hit[1])
        if (total is not None and len(rows) >= total) or len(hit[1]) < size:
            break
    if require_complete and ((total is not None and len(rows) < total)
                             or (total is None and last_count >= size and page >= MAX_PAGES)):
        raise jwxt.JwxtError("空闲记录未获取完整，请重试")
    return rows


def _paged(form: dict) -> dict:
    d = dict(form)
    if "requestParamStr" not in d:
        d["pageSize"], d["pageNumber"] = str(PAGE_SIZE), "1"
    return d


def _num(s: str) -> int:
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return 0


def post_filter(rs: list, q: RoomQuery) -> list:
    """服务端若忽略了某个筛选，本地再筛一遍（座位/类型/教学楼）。"""
    out = []
    for r in rs:
        s, e = _num(r.seats), _num(r.exam_seats)
        if q.seat_min and r.seats and s < q.seat_min: continue  # noqa: E701
        if q.seat_max and r.seats and s > q.seat_max: continue  # noqa: E701
        if q.exam_min and r.exam_seats and e < q.exam_min: continue  # noqa: E701
        if q.exam_max and r.exam_seats and e > q.exam_max: continue  # noqa: E701
        out.append(r)
    return out


def row_to_room(r: dict) -> Optional[Room]:
    first = lambda *ks: next((_s(r.get(k)) for k in ks if _s(r.get(k))), "")  # noqa: E731
    name = first("JASMC", "JSMC", "MC", "JASDM")
    if not name:
        return None
    return Room(
        name=name,
        building=first("JXLDM_DISPLAY", "JXLMC", "JZWMC", "JXLDM"),
        campus=first("XXXQDM_DISPLAY", "XXXQMC", "XQMC"),
        seats=first("SKZWS", "ZWS", "RNRS"),
        kind=first("JASLXDM_DISPLAY", "JSLXDM_DISPLAY", "JASLXMC", "JSLXMC", "JASLXDM"),
        exam_seats=first("KSZWS", "KSRS"),
        free_date=first("KXRQ", "RQ", "CXRQ"),
        free_periods=first("KXJC_DISPLAY", "KXJC", "JC", "JCS"),
        free_time=first("KXSJ", "SJ", "KXSJD"),
    )


def _abs(a: str) -> str:
    """相对 URL → /jwapp/sys/kxjas/modules/...（统一实现见 emap.App.abs）。"""
    return KXJAS.abs(a)


def discover(client, max_files: int = 30) -> dict:
    """只读：kxjas 页面发现（统一实现见 emap.discover）。"""
    return emap.discover(client, KXJAS, max_files)


def _attempts(meta: dict, profile: Optional[dict]):
    actions = [_abs(a) for a in meta.get("actions", []) if re.search(r"(kx|cx|jscx)", a)]
    actions += [_abs(a) for a in meta.get("discovered_do", []) if re.search(r"(kx|cx)", a)
                and not re.search(r"modules/\w+\.do$", a) and "code" not in a.lower()]
    from .endpoints import KNOWN
    endpoints = list(dict.fromkeys([KNOWN["rooms_query"].path] + actions + list(ENDPOINTS)))
    flds = meta.get("fields", [])
    schemes = {k: _with_filters(v, flds) for k, v in SCHEMES.items()}
    ms = _meta_scheme(flds)
    if ms:
        schemes = {"meta": _with_filters(ms, flds), **schemes}
    if profile and profile.get("endpoint") in endpoints and profile.get("scheme") in schemes:
        yield profile["endpoint"], profile["scheme"], schemes[profile["scheme"]]
    for ep in endpoints:
        for name, fn in schemes.items():
            yield ep, name, fn


def query_rooms(client, q: RoomQuery, profile_path: Optional[Path] = None,
                meta: Optional[dict] = None, max_tries: int = 40,
                require_complete: bool = False, enter_app: bool = True,
                profile_data: Optional[dict] = None) -> tuple[list[Room], dict]:
    """返回 (空教室列表, 命中的 profile)。全部失败则抛 JwxtError（附各尝试的 code/msg）。"""
    if enter_app:
        client.enter_emap_app(APP)
    if meta is None:
        meta = cached_meta(client)
    profile = profile_data
    if profile_data is None and profile_path and profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            profile = None
    errs = []
    for i, (ep, sname, fn) in enumerate(_attempts(meta, profile)):
        if i >= max_tries:
            break
        form = _paged(fn(q))
        code, text, final = client.post_raw(ep, form, APP)
        if require_complete and jwxt.looks_like_login_redirect(final, text if not text.lstrip().startswith("{") else ""):
            raise jwxt.SessionExpiredError()
        if code != 200:
            errs.append(f"{ep.rsplit('/', 1)[-1]}/{sname}:HTTP{code}")
            continue
        try:
            obj = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            errs.append(f"{ep.rsplit('/', 1)[-1]}/{sname}:非JSON")
            continue
        hit = _rows_any(obj)
        if hit is None:
            msg = re.sub(r"\d{5,}", "#", _s(obj.get("msg")))[:40] if isinstance(obj, dict) else ""
            errs.append(f"{ep.rsplit('/', 1)[-1]}/{sname}:code={_s(obj.get('code')) if isinstance(obj, dict) else '?'} {msg}")
            continue
        prof = {"endpoint": ep, "scheme": sname, "datas_key": hit[0]}
        if profile_path and profile_data is None:
            profile_path.write_text(json.dumps(prof, ensure_ascii=False), encoding="utf-8")
        raw = fetch_all_pages(client, ep, form, obj, hit[1], require_complete)
        prof["total"] = _total(obj)
        rs = [r for r in (row_to_room(x) for x in raw if isinstance(x, dict)) if r]
        if require_complete and len(rs) != len(raw):
            raise jwxt.JwxtError("空闲记录包含无法识别的教室，请重试")
        return post_filter(rs, q), prof
    raise jwxt.JwxtError("空教室查询未成功；尝试：" + "；".join(errs[:12]))


def week_dates(weeks: str, weekday: int, first_monday: str) -> list[str]:
    fm = dt.date.fromisoformat(first_monday)
    return [(fm + dt.timedelta(days=(int(w) - 1) * 7 + weekday - 1)).isoformat()
            for w in weeks.split(",") if w]


WEEKDAY_CN = "一二三四五六日"


def free_date_label(q: RoomQuery, first_monday: Optional[str] = None) -> str:
    """「空闲日期」列统一由查询条件生成，与结果标题的日期/周次/星期保持一致。"""
    if q.mode == "week":
        wd = int(q.weekday or 1)
        return f"第{q.weeks or q.week_list}周 周{WEEKDAY_CN[wd - 1]}"
    wk, wd = week_and_weekday(q.date, first_monday)
    return f"{q.date} 周{WEEKDAY_CN[wd - 1]}" + (f"（第{wk}周）" if wk > 0 else "")


def label_free_date(rs: list, q: RoomQuery, first_monday: Optional[str] = None) -> list:
    if not q.date and q.mode != "week":
        return rs
    lab = free_date_label(q, first_monday)
    for r in rs:
        r.free_date = lab
    return rs


def query_rooms_any(client, q: RoomQuery, profile_path: Optional[Path] = None,
                    first_monday: Optional[str] = None, meta: Optional[dict] = None):
    """按周次：先试服务端周次参数；失败或 0 间时按 校历首周一 换算成日期逐日查询取交集。"""
    if q.mode != "week":
        found, prof = query_rooms(client, q, profile_path, meta)
        return label_free_date(found, q, first_monday), prof
    try:
        found, prof = query_rooms(client, q, profile_path, meta)
        if found:
            prof = {**prof, "week_via": "server"}
            return label_free_date(found, q, first_monday), prof
    except jwxt.JwxtError:
        pass
    if not first_monday:
        raise jwxt.JwxtError("按周次查询需要校历首周一（先运行 jlu-toolkit sync）")
    keep: Optional[dict] = None
    prof = {}
    for d in week_dates(q.week_list, q.weekday, first_monday):
        sub = RoomQuery(**{**q.__dict__, "mode": "date", "date": d, "weeks": ""})
        sub.week, sub.weekday = week_and_weekday(d, first_monday)
        rs, prof = query_rooms(client, sub, profile_path, meta)
        cur = {(r.building, r.name): r for r in rs}
        keep = cur if keep is None else {k: v for k, v in keep.items() if k in cur}
    out = label_free_date(list((keep or {}).values()), q, first_monday)
    return out, {**prof, "week_via": "per-date", "total": len(out)}


def _meta_cache() -> Path:
    return jwxt.config_dir() / "data" / "rooms_meta.json"


def cached_meta(client, refresh: bool = False) -> dict:
    """kxjscx 元数据（字段/检索字段/字典 URL，均为代码层信息）本地缓存；没有才走发现。"""
    f = _meta_cache()
    if f.exists() and not refresh:
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
            if m.get("fields"):
                return m
        except (json.JSONDecodeError, ValueError):
            pass
    m = full_meta(client)
    if m.get("fields"):
        try:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return m


def full_meta(client, trace: Optional[list] = None, disc: Optional[dict] = None) -> dict:
    disc = disc if disc is not None else discover(client)
    meta = fetch_meta(client, disc.get("modules_seen", []), trace)
    meta["discovered_do"] = disc.get("do_paths", [])
    # 页面代码里出现的字典 URL（含 code）也收进来
    for p in meta["discovered_do"]:
        low = p.lower()
        if "code" in low or "dic" in low:
            if re.search(r"(xq|campus|xiaoqu)", low):
                meta["dicts"].setdefault("XXXQDM", p)
            elif re.search(r"(jxl|jzw|lou|building)", low):
                meta["dicts"].setdefault("JXLDM", p)
    return meta


def fetch_code_list(client, url: str, parent: dict | None = None) -> list[dict]:
    """EMAP 代码表 → [{code, name}]（校区/教学楼是公共信息）。"""
    path = _abs(url)
    code, text, _ = client.post_raw(path, parent or {}, APP)
    if code != 200:
        return []
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    hit = _rows_any(obj)
    rows = hit[1] if hit else (obj if isinstance(obj, list) else [])
    out = []
    for r in rows:
        if isinstance(r, dict):
            c = _s(r.get("id") or r.get("DM") or r.get("code"))
            n = _s(r.get("name") or r.get("MC") or r.get("text"))
            if c:
                out.append({"code": c, "name": n or c})
    return out


def campus_codes_from_jc(client) -> list[str]:
    """兜底：节次时间表里的 XXXQ 就是校区代码。"""
    from . import meta as _m
    client.enter_emap_app(_m.APP_WDKB)
    data = _m._post(client, _m.EP_PERIODS, {}, _m.APP_WDKB)
    return sorted({_s(r.get("XXXQ")) for r in _m._rows(data, "jc") if _s(r.get("XXXQ"))})


def list_campuses(client, meta: Optional[dict] = None) -> list[dict]:
    client.enter_emap_app(APP)
    meta = meta if meta is not None else cached_meta(client)
    for k in ("XXXQDM", "XQDM", "XXXQ"):
        if k in meta.get("dicts", {}):
            got = fetch_code_list(client, meta["dicts"][k])
            if got:
                return got
    return [{"code": c, "name": c} for c in campus_codes_from_jc(client)]


def list_codes(client, keys, parent: Optional[dict] = None, meta: Optional[dict] = None) -> list[dict]:
    client.enter_emap_app(APP)
    meta = meta if meta is not None else cached_meta(client)
    for k in keys:
        if k in meta.get("dicts", {}):
            got = fetch_code_list(client, meta["dicts"][k], parent)
            if got:
                return got
    return []


def list_room_types(client, meta: Optional[dict] = None) -> list[dict]:
    return list_codes(client, KIND_KEYS, None, meta)


def extra_search_fields(meta: dict) -> list[dict]:
    """元数据里除已支持外的检索字段（「更多条件」）。"""
    known = {"XXXQDM", "XQDM", "KXRQ", "RQ", "KSJC", "JSJC", "JC", "KXJC", "ZC", "XQ", "XQJ", "XNXQDM",
             *SEAT_KEYS, *EXAM_KEYS, *KIND_KEYS, *BLD_KEYS}
    return [s for s in meta.get("search", []) if s["name"] not in known]


def list_buildings(client, campus: str = "", meta: Optional[dict] = None) -> list[dict]:
    client.enter_emap_app(APP)
    meta = meta if meta is not None else cached_meta(client)
    for k in ("JXLDM", "JZWDM"):
        if k in meta.get("dicts", {}):
            allb = fetch_code_list(client, meta["dicts"][k])
            if not campus:
                return allb
            for pk in ("XXXQDM", "XQDM", "pId", "XXXQ"):
                got = fetch_code_list(client, meta["dicts"][k], {pk: campus})
                if got and len(got) < len(allb):
                    return got
            return filter_buildings(allb, campus_name(client, campus, meta))
    return []


def campus_name(client, code: str, meta: Optional[dict] = None) -> str:
    try:
        for c in list_campuses(client, meta):
            if c["code"] == code:
                return c["name"]
    except jwxt.JwxtError:
        pass
    return ""


def filter_buildings(blds: list[dict], cname: str) -> list[dict]:
    """教学楼代码表不认校区参数时：按名称前缀「前卫-」等本地过滤；匹配不到则返回全部。"""
    short = re.sub(r"(校区|校园)$", "", (cname or "").strip())
    if not short:
        return blds
    got = [b for b in blds if b["name"].startswith(short) or b["name"].startswith(short[:2] + "-")]
    return got or blds


# ───────────────────────── 探测（只打印结构） ─────────────────────────

def probe(client, first_monday: Optional[str], term: str, campuses: Optional[list[str]] = None,
          date: Optional[str] = None, periods: tuple[int, int] = (1, 2), log=print) -> dict:
    date = date or dt.date.today().isoformat()
    week, weekday = week_and_weekday(date, first_monday)
    rep: dict = {"date_is_today": date == dt.date.today().isoformat(), "week": week, "weekday": weekday,
                 "periods": list(periods)}
    try:
        client.enter_emap_app(APP)
        rep["entered"] = True
    except jwxt.JwxtError as e:
        rep["entered"] = f"{type(e).__name__}"
    disc = discover(client)
    rep["discover"] = disc
    trace: list = []
    meta = full_meta(client, trace, disc)
    rep["meta_trace"] = trace
    rep["meta"] = {"modules_ok": meta["modules_ok"], "actions": meta["actions"], "fields": meta["fields"],
                   "dict_fields": sorted(meta["dicts"]), "dict_urls": sorted(set(meta["dicts"].values())),
                   "search_fields": [{k: s[k] for k in ("name", "caption", "xtype", "builder")} | {"has_dict": bool(s["dict"])}
                                     for s in meta.get("search", [])]}
    for s in rep["meta"]["search_fields"]:
        tag = "\t(字典)" if s["has_dict"] else ""
        log(f"[检索字段] {s['name']}\t{s['caption']}\t{s['xtype']}{tag}")
    log(f"[发现] 文件 {len(disc.get('fetched', []))} 个，.do {len(disc.get('do_paths', []))} 个，"
        f"模块 {disc.get('modules_seen')}")
    log(f"[元数据] 模块={meta['modules_ok']} 动作={len(meta['actions'])} 字段={len(meta['fields'])}")
    if not campuses:
        try:
            cl = list_campuses(client, meta)
            campuses = [c["code"] for c in cl]
            rep["campus_source"] = "dict" if cl and cl[0]["name"] != cl[0]["code"] else "jc.XXXQ"
        except jwxt.JwxtError as e:
            rep["campus_source"] = f"error:{type(e).__name__}"
            campuses = []
    rep["campus_count"] = len(campuses)
    tries = []
    for camp in campuses[:3] or [""]:
        q = RoomQuery(campus=camp, date=date, start=periods[0], end=periods[1], term=term,
                      week=week, weekday=weekday)
        for ep, sname, fn in _attempts(meta, None):
            item = {"campus_idx": campuses.index(camp) if camp in campuses else -1,
                    "endpoint": ep, "scheme": sname, "param_names": sorted(fn(q))}
            try:
                code, text, _ = client.post_raw(ep, fn(q), APP)
                item["status"] = code
                obj = json.loads(text) if code == 200 and text else None
                if isinstance(obj, dict):
                    item["code"] = _s(obj.get("code"))[:6]
                    if isinstance(obj.get("msg"), str):
                        item["msg"] = re.sub(r"\d{5,}", "#", obj["msg"])[:60]
                    hit = _rows_any(obj)
                    if hit:
                        item["datas_key"], item["rows"] = hit[0], len(hit[1])
                        item["fields"] = sorted({k for r in hit[1][:20] if isinstance(r, dict) for k in r})
            except (json.JSONDecodeError, ValueError):
                item["non_json"] = True
            except jwxt.JwxtError as e:
                item["error"] = type(e).__name__
            tries.append(item)
            if "rows" in item:
                log(f"[命中] {ep} / {sname}: {item['rows']} 行")
                break
        if any("rows" in t for t in tries):
            break
    rep["tries"] = tries
    rep["hit"] = next(({"endpoint": t["endpoint"], "scheme": t["scheme"], "rows": t["rows"],
                        "fields": t["fields"]} for t in tries if "rows" in t), None)
    log(f"[空教室] 尝试 {len(tries)} 次，命中：{bool(rep['hit'])}")
    return rep
