"""教务元数据：校历、节次时间、官方学分绩点、学业完成/培养方案。

字段名依据吉大 explore 报告（2026-10）与 Youwenqwq/ysu-sdk（同为金智 EMAP）：
  校历   wdkb/modules/xskcb/cxxljc.do   {XN, XQ}           → XQKSRQ, ZZC, ZJXZC
  节次   wdkb/modules/jshkcb/jc.do                         → DM/PX, MC, KSSJ, JSSJ, SFSY, XXXQ
  当前学期 wdkb/modules/jshkcb/dqxnxq.do                     → DM, QSSYRQ
  绩点   cjcx/modules/cjcx/cxzxfaxfjd.do  {XH1..XH6=学号}    → PPJDCX, PPJDZG, BXKPPJD, JQPJF ...
  培养方案 xsfacx/modules/pyfacxepg/grpyfacx.do               → PYFAMC, ZSYQXF, YWCXF, XH, PYFADM
  学业完成 xywccx/modules/xywccx/cxxsscfa.do  {SCLBDM=04}     → YQXF, WCXF, XKXF, JSSFTG, CZSJ
  课组明细 xywccx/modules/xywccx/cxscfakz.do {XH,PYFADM,BYNJDM,SCLBDM} → KZM, KZH, YQXF, WCXF, WCMS, SFTG
个人取值（学号等）只用于请求体，绝不写入日志或报告。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.parse
from collections import Counter
from typing import Optional

from . import jwxt

from . import endpoints as _EP  # noqa: E402

APP_WDKB = jwxt.REF_SCHEDULE
APP_CJCX = jwxt.REF_GRADES
APP_XSFACX = "https://iedu.jlu.edu.cn/jwapp/sys/xsfacx/*default/index.do"
APP_XYWCCX = "https://iedu.jlu.edu.cn/jwapp/sys/xywccx/*default/index.do"

EP_CALENDAR = _EP.KNOWN["calendar"].path
EP_PERIODS = _EP.KNOWN["periods"].path
EP_GPA = "/jwapp/sys/cjcx/modules/cjcx/cxzxfaxfjd.do"
# 吉大成绩页真实官方绩点（浏览器 DevTools）：rxylgpacx / rxylgpacxcx.do
# 浏览器实测：路径里是字面量 modules*cjcx（不是 modules/cjcx）
EP_GPA_RXYL = _EP.KNOWN["official_gpa"].path
EP_GPA_RXYL_ENC = _EP.KNOWN["official_gpa_enc"].path  # * 被编码时的回退
EP_GPA_RXYL_SLASH = "/jwapp/sys/cjcx/modules/cjcx/rxylgpacx/rxylgpacxcx.do"
EP_GPA_RXYL_ALT = "/jwapp/sys/cjcx/modules/rxylgpacx/rxylgpacxcx.do"
EP_RXYL_META = "/jwapp/sys/cjcx/modules*cjcx/rxylgpacx.do"
EP_RXYL_META_ENC = "/jwapp/sys/cjcx/modules%2Acjcx/rxylgpacx.do"
EP_RXYL_META_SLASH = "/jwapp/sys/cjcx/modules/cjcx/rxylgpacx.do"
EP_GPA_JLU = "/jwapp/sys/cjcx/modules/cjcx/cxxspjjdxx.do"
EP_GPA_TERM = "/jwapp/sys/cjcx/modules/cjcx/cxsfwfcsj.do"
EP_GPA_TERM_ALT = "/jwapp/sys/cjcx/modules/cjcx/cxcjcxsfkf.do"
GPA_CANDIDATES = [
    (EP_GPA_RXYL, "page"),       # 浏览器实测：仅 pageSize/pageNumber，无学号
    (EP_GPA_RXYL_ENC, "page"),
    (EP_GPA_RXYL_SLASH, "page"),
    (EP_GPA_RXYL_ALT, "page"),
    (EP_GPA_JLU, "XH"),
    (EP_GPA_TERM, "XH"),
    (EP_GPA_TERM_ALT, "XH"),
    (EP_GPA, "XH1..6"),
    (EP_GPA, "XH"),
]
RXYL_MODULE = "rxylgpacx"
# 真正的「汇总绩点」字段；缺这些就不是官方绩点（防 cxxscj 单科成绩误认）
SUMMARY_GPA_KEYS = frozenset({
    "GPA", "PJJD", "JQPJF", "PJF", "XQPJF", "SSPJF",
    "SYBXKGPA", "SYBXXXKGPA", "XQBXKGPA", "XQBXXXKGPA",
    "PPJDCX", "PPJDZG", "BXKPPJD", "XWKPJJDCX", "XWKPJJDZG", "XWKJQPJF",
    "ZGCJGPA",  # 吉大 rxylgpacxcx：最高成绩 GPA（官方）
})
COURSE_GPA_BLOCK = ("cxxscj", "xscjcx", "/xscj/", "cxxszhxqkb")  # 单科成绩/课表，绝不当官方绩点
EP_PLAN_COURSES = "/jwapp/sys/jwpubapp/modules/pyfa/kzkccx.do"


class Unavailable(jwxt.JwxtError):
    """接口在吉大不存在/无数据：不是故障。"""
EP_PLAN = _EP.KNOWN["plan_row"].path
EP_COMPLETION = _EP.KNOWN["completion"].path
EP_COMPLETION_GROUPS = _EP.KNOWN["completion_groups"].path

# 官方绩点字段 → 中文标签（吉大 cxxspjjdxx + ysu-sdk 同款）
GPA_FIELDS = [
    # —— 吉大 rxylgpacxcx（官方，浏览器实测）——
    ("ZGCJGPA", "官方GPA（最高成绩）"),
    ("CJDPM", "成绩排名"),
    ("XZNJ", "年级"),
    ("YXDM", "学院"),
    ("ZYDM", "专业"),
    ("BJDM", "班级"),
    # —— 吉大成绩页「平均绩点信息」cxxspjjdxx ——
    ("PJJD", "平均绩点"),
    ("JQPJF", "加权平均分"),
    ("PJF", "平均分"),
    ("SYBXKGPA", "全部必修课绩点"),
    ("SYBXXXKGPA", "全部必修+选修绩点"),
    ("XQBXKGPA", "本学期必修课绩点"),
    ("XQBXXXKGPA", "本学期必修+选修绩点"),
    ("XQPJF", "本学期平均分"),
    # —— 学期统计 cxcjcxsfkf / cxsfwfcsj ——
    ("GPA", "绩点（学期统计）"),
    ("JDF", "绩点分"),
    ("HDXF", "获得学分"),
    ("XKXF", "选课学分"),
    # —— 其他金智部署常见字段 ——
    ("PPJDCX", "平均学分绩点（初修）"),
    ("PPJDZG", "平均学分绩点（最高）"),
    ("BXKPPJD", "必修课平均学分绩点"),
    ("XWKPJJDCX", "学位课绩点（初修）"),
    ("XWKPJJDZG", "学位课绩点（最高）"),
    ("SSPJF", "算术平均分"),
    ("XWKJQPJF", "学位课加权平均分"),
    ("BXKHDXF", "必修课已获学分"),
    ("XXKHDXF", "选修课已获学分"),
    ("XWKHDXF", "学位课已获学分"),
    ("BXKBJGXF", "必修课不及格学分"),
]


# ───────────────────────── 纯解析（可单测） ─────────────────────────

def _s(v) -> str:
    return jwxt._emap_str(v)


def _f(v) -> Optional[float]:
    try:
        return float(_s(v))
    except ValueError:
        return None


def _rows(data: dict, key: str) -> list:
    blk = (data.get("datas") or {}).get(key) or {}
    rows = blk.get("rows") if isinstance(blk, dict) else None
    return rows if isinstance(rows, list) else []


def norm_time(v) -> str:
    """'0800' / '8:00' / '08:00:00' / 800 → '08:00'；无法识别返回 ''。"""
    s = _s(v)
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", s)
    if not m and re.fullmatch(r"\d{3,4}", s):
        m = re.fullmatch(r"(\d{1,2})(\d{2})", s)
    if not m:
        return ""
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return ""
    return f"{h:02d}:{mi:02d}"


def _date(v) -> str:
    s = _s(v)
    m = re.match(r"(\d{4})[-/.]?(\d{1,2})[-/.]?(\d{1,2})", s)
    if not m:
        return ""
    try:
        return dt.date(*map(int, m.groups())).isoformat()
    except ValueError:
        return ""


def parse_calendar(row: dict, term: str = "") -> dict:
    start = _date(row.get("XQKSRQ"))
    first_monday = ""
    if start:
        d = dt.date.fromisoformat(start)
        first_monday = (d - dt.timedelta(days=d.weekday())).isoformat()
    xn, xq = _s(row.get("XN")), _s(row.get("XQ"))
    return {
        "term": term or (f"{xn}-{xq}" if xn and xq else ""),
        "start_date": start,
        "first_monday": first_monday,
        "total_weeks": int(_f(row.get("ZZC")) or 0),
        "teaching_weeks": int(_f(row.get("ZJXZC")) or 0),
    }


def parse_periods(rows: list) -> dict:
    """→ {"1": ["08:00","08:45"], ...}。多校区时取出现最多的 XXXQ；跳过 SFSY=0。"""
    usable = [r for r in rows if _s(r.get("SFSY")) not in ("0", "否", "false")]
    camp = Counter(_s(r.get("XXXQ")) for r in usable).most_common(1)
    if camp:
        usable = [r for r in usable if _s(r.get("XXXQ")) == camp[0][0]]
    out: dict = {}
    for r in usable:
        sec = _f(r.get("DM")) or _f(r.get("PX")) or _f(re.sub(r"\D", "", _s(r.get("MC"))) or None)
        a, b = norm_time(r.get("KSSJ")), norm_time(r.get("JSSJ"))
        if sec and a and b:
            out.setdefault(str(int(sec)), [a, b])
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))


_CODE_FIELD = re.compile(r"^[A-Z][A-Z0-9_]{1,30}$")
_SKIP_GPA_KEYS = frozenset({
    "XH", "XM", "WID", "SFFB", "XNXQDM", "XNXQ", "XN", "XQ", "PYFADM", "PYFAMC", "TJLX",
    "pageSize", "pageNumber", "totalSize", "extParams",
})


def parse_official_gpa(row: dict, captions: Optional[dict] = None) -> dict:
    """解析官方绩点行：尽量保留全部字段。

    - 跳过 ``*_DISPLAY`` 键本身，但对基键优先用 DISPLAY 值（代码→可读）
    - 标签：元数据 caption > 内置 GPA_FIELDS > 字段名
    - 跳过学号等标识字段
    """
    caps = captions or {}
    known = dict(GPA_FIELDS)
    items, seen = [], set()

    def label_for(k: str) -> str:
        return caps.get(k) or known.get(k) or k

    def value_for(k: str):
        disp = row.get(k + "_DISPLAY")
        if disp not in (None, ""):
            return _s(disp)
        return _s(row.get(k))

    # 已知顺序优先
    for k, _lab in GPA_FIELDS:
        if k in seen or k not in row:
            continue
        v = value_for(k)
        if v:
            items.append({"key": k, "label": label_for(k), "value": v})
            seen.add(k)
    # 其余字段
    for k in row:
        if not isinstance(k, str) or k.endswith("_DISPLAY"):
            continue
        if k in seen or k in _SKIP_GPA_KEYS or not _CODE_FIELD.match(k):
            continue
        v = value_for(k)
        if not v:
            continue
        items.append({"key": k, "label": label_for(k), "value": v})
        seen.add(k)
    return {"plan": _s(row.get("PYFAMC")), "items": items}



def parse_completion(summary: dict, plan: dict, groups: list) -> dict:
    gs = []
    for g in groups:
        req, done = _f(g.get("YQXF")), _f(g.get("WCXF"))
        missing = max(0.0, req - done) if req is not None and done is not None else None
        passed = _s(g.get("SFTG")) in ("1", "是", "true", "通过")
        gs.append({
            "name": _s(g.get("KZM")) or _s(g.get("KCXZDM_DISPLAY")) or "未命名课组",
            "code": _s(g.get("KZH")),
            "parent": _s(g.get("FKZH")),
            "nature": _s(g.get("KCXZDM_DISPLAY")),
            "required": req,
            "earned": done,
            "courses_done": int(_f(g.get("WCMS")) or 0),
            "earned_source": "jw" if done is not None else None,
            "passed": passed,
            "missing": round(missing, 2) if missing is not None else None,
        })
    req = _f(summary.get("YQXF"))
    done = _f(summary.get("WCXF"))
    if req is None:
        req = _f(plan.get("ZSYQXF"))
    if done is None:
        done = _f(plan.get("YWCXF"))
    return {
        "plan": _s(summary.get("PYFAMC")) or _s(plan.get("PYFAMC")),
        "required": req,
        "earned": done,
        "selected": _f(summary.get("XKXF")),
        "missing": round(max(0.0, req - (done or 0)), 2) if req is not None else None,
        "passed": _s(summary.get("JSSFTG") or summary.get("ZSSFTG")) in ("1", "是", "true", "通过"),
        "calculated_at": _s(summary.get("CZSJ")),
        "groups": sorted(gs, key=lambda g: (g["passed"], -(g["missing"] or 0))),
    }


def _passed(score: str) -> bool:
    from . import core
    s = (score or "").strip()
    if s in ("通过", "合格"):
        return True
    p = core.score_to_point(s) if s else None
    return bool(p and p > 0)


def derive_group_earned(completion: dict, plan_courses: list, grades) -> dict:
    """教务课组无 WCXF 时：按「培养方案课程 → 课组」映射 + 已通过成绩推算各课组已获学分。

    课程按课程名匹配（成绩 CSV 无课程号）；父课组（FKZH）汇总子课组。
    """
    passed: dict = {}
    for g in grades or []:
        if _passed(g.score):
            passed[g.name.strip()] = max(passed.get(g.name.strip(), 0.0), float(g.credit))
    direct: dict = {}
    seen: set = set()
    for c in plan_courses:
        kzh, name = _s(c.get("KZH")), _s(c.get("KCM"))
        if not kzh or not name or (kzh, name) in seen:
            continue
        seen.add((kzh, name))
        if name in passed:
            direct[kzh] = direct.get(kzh, 0.0) + passed[name]
    groups = completion.get("groups") or []
    children: dict = {}
    for g in groups:
        if g.get("parent"):
            children.setdefault(g["parent"], []).append(g["code"])

    memo: dict = {}

    def total(code, depth=0):
        if code in memo:
            return memo[code]
        v = direct.get(code, 0.0)
        if depth < 10:
            v += sum(total(ch, depth + 1) for ch in children.get(code, []))
        memo[code] = v
        return v

    changed = 0
    for g in groups:
        if g.get("code") and g.get("earned") in (None, 0):
            got = round(total(g["code"]), 2)
            if g.get("earned") is None or got > 0:
                g["earned"] = got
                g["earned_source"] = "derived"
                changed += 1
                if g.get("required") is not None:
                    g["missing"] = round(max(0.0, g["required"] - g["earned"]), 2)
                    g["passed"] = g["missing"] == 0
    completion["groups"] = sorted(groups, key=lambda g: (g["passed"], -(g["missing"] or 0)))
    completion["groups_derived"] = changed
    return completion


# ───────────────────────── 网络（需会话） ─────────────────────────

def _post(client: "jwxt.JwxtClient", path: str, fields: dict, app: str) -> dict:
    code, text, _ = client.post_raw(path, fields, app)
    if code != 200:
        raise jwxt.JwxtError(f"{path} HTTP {code}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        if "loginForm" in text:
            raise jwxt.LoginError("会话已失效，请重新登录") from e
        raise jwxt.JwxtError(f"{path} 返回非 JSON") from e
    if not isinstance(data, dict):
        raise jwxt.JwxtError(f"{path} 返回格式异常")
    return data


def fetch_calendar(client, term: Optional[str] = None) -> dict:
    term = term or client.current_semester() or ""
    xn, _, xq = term.rpartition("-")
    client.enter_emap_app(APP_WDKB)
    rows = _rows(_post(client, EP_CALENDAR, {"XN": xn, "XQ": xq}, APP_WDKB), "cxxljc")
    if not rows:
        raise jwxt.JwxtError("校历为空")
    cal = parse_calendar(rows[0], term)
    if not cal["first_monday"]:
        raise jwxt.JwxtError("校历缺少学期开始日期 XQKSRQ")
    return cal


def fetch_periods(client) -> dict:
    client.enter_emap_app(APP_WDKB)
    p = parse_periods(_rows(_post(client, EP_PERIODS, {}, APP_WDKB), "jc"))
    if not p:
        raise jwxt.JwxtError("节次时间为空或格式无法识别")
    return p


def _plan_row(client) -> dict:
    client.enter_emap_app(APP_XSFACX)
    rows = _rows(_post(client, EP_PLAN, {}, APP_XSFACX), "grpyfacx")
    return rows[0] if rows else {}


def gpa_from_jw_points(grades) -> Optional[dict]:
    """用教务返回的单科绩点按学分加权（与自算公式无关）。无教务绩点则 None。"""
    tot = pts = 0.0
    n = 0
    for g in grades or []:
        jp = getattr(g, "jw_point", None)
        if jp is None or not g.credit:
            continue
        tot += g.credit
        pts += jp * g.credit
        n += 1
    if not n:
        return None
    return {"plan": "", "source": "grades_jw_point",
            "items": [{"key": "JW_WEIGHTED", "label": "教务单科绩点学分加权（全部课程）",
                       "value": f"{pts / tot:.3f}"},
                      {"key": "JW_COUNT", "label": "含教务绩点的课程数", "value": str(n)}]}


GPA_ACTION_HINT = re.compile(r"(rxylgpa|pjjd|spjjd|xfjd|pjxfjd|pjxf|jqpjf|sspjf|gpa|jdtj|xftj|cxzxfa|cxpj|xspj|sfwfcsj|cjcxsfkf)", re.I)


def _xh_fields(xh: str, fields: list[str], term: str = "") -> dict:
    f = set(fields)
    out = {}
    if any(k.startswith("XH") and k[2:].isdigit() for k in f):
        out = {k: xh for k in f if k.startswith("XH")}
    elif "XH" in f or not f:
        out = {"XH": xh}
    elif any(k.startswith("XH") for k in f):
        out = {k: xh for k in f if k.startswith("XH")}
    else:
        out = {"XH": xh, **{f"XH{i}": xh for i in range(1, 7)}}
    # XNXQDM：有学期就传；没有则不传（查累计），避免误查空学期
    if "XNXQDM" in f and term:
        out["XNXQDM"] = term
    return out


def _gpaish(name: str, url: str, fields: list[str]) -> bool:
    if is_course_endpoint(url) or is_course_endpoint(name):
        return False
    blob = f"{name} {url} {' '.join(fields)}"
    return bool(GPA_ACTION_HINT.search(blob))



def response_shape(obj, max_paths: int = 40) -> dict:
    """脱敏响应形状：路径→类型；列表记长度；dict.rows 记字段名。不含任何值。"""
    paths, labels = {}, []

    def walk(x, path="$"):
        if len(paths) >= max_paths:
            return
        if isinstance(x, dict):
            paths[path] = "object"
            # 若本层就有绩点字段
            hit = [k for k, _ in GPA_FIELDS if k in x]
            if hit:
                labels.extend(hit)
                paths[path + "{fields}"] = sorted(x.keys())[:40]
            for k, v in x.items():
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            paths[path] = f"array[{len(x)}]"
            if x and isinstance(x[0], dict):
                paths[path + "[0].fields"] = sorted(x[0].keys())[:40]
                labels.extend(k for k, _ in GPA_FIELDS if k in x[0])
                walk(x[0], path + "[0]")
        else:
            paths[path] = type(x).__name__

    walk(obj)
    return {"paths": paths, "gpa_keys_seen": sorted(set(labels))}


def is_summary_gpa_row(row: dict) -> bool:
    """必须含至少一个汇总绩点字段；单科成绩行（ZCJ/KCM/XFJD）不算。"""
    if not isinstance(row, dict):
        return False
    if not SUMMARY_GPA_KEYS.intersection(row.keys()):
        return False
    # 典型单科行：有课程名+成绩，却没有汇总键以外的「像汇总」——已有汇总键则放行
    return True


def is_course_endpoint(url: str) -> bool:
    u = (url or "").lower()
    return any(b in u for b in COURSE_GPA_BLOCK)


def extract_gpa_payload(obj) -> Optional[dict]:
    """只取出含汇总绩点字段的一行/一块；空 rows / 单科成绩行一律忽略。"""
    if not isinstance(obj, dict):
        return None

    def pick(row):
        return row if is_summary_gpa_row(row) else None

    for name, blk in (obj.get("datas") or {}).items() if isinstance(obj.get("datas"), dict) else ():
        if isinstance(blk, dict):
            rows = blk.get("rows")
            if isinstance(rows, list):
                for r in rows:
                    hit = pick(r)
                    if hit:
                        return hit
            hit = pick(blk)
            if hit:
                return hit
        if isinstance(blk, list):
            for r in blk:
                hit = pick(r)
                if hit:
                    return hit
    if isinstance(obj.get("datas"), list):
        for r in obj["datas"]:
            hit = pick(r)
            if hit:
                return hit
    hit = pick(obj)
    if hit:
        return hit
    for alt in ("data", "result", "rows"):
        v = obj.get(alt)
        if isinstance(v, dict):
            hit = pick(v)
            if hit:
                return hit
        if isinstance(v, list):
            for r in v:
                hit = pick(r)
                if hit:
                    return hit
    return None


def _param_variants(xh: str, action_fields: list[str], term: str = "", *, page_first: bool = False) -> list[tuple[str, str, dict]]:
    """(variant_name, method, form) — 针对 cxxspjjdxx 等实测 200 空行的情况穷举。"""
    f = set(action_fields or [])
    vs = []
    if page_first:
        vs.append(("POST:pageSize+pageNumber", "POST", {"pageSize": "10", "pageNumber": "1"}))
    if xh:
        vs.append(("POST:XH", "POST", {"XH": xh}))
        vs.append(("POST:XH1..6", "POST", {f"XH{i}": xh for i in range(1, 7)}))
        vs.append(("POST:XH+*order", "POST", {"XH": xh, "*order": "-XNXQDM"}))
        qs = json.dumps([{"name": "XH", "value": xh, "linkOpt": "AND", "builder": "equal"}], ensure_ascii=False)
        vs.append(("POST:querySetting(XH)", "POST", {"querySetting": qs}))
        vs.append(("POST:requestParamStr(XH)", "POST",
                   {"requestParamStr": json.dumps({"XH": xh}, ensure_ascii=False)}))
        if term or "XNXQDM" in f:
            t = term or ""
            if t:
                vs.append(("POST:XH+XNXQDM", "POST", {"XH": xh, "XNXQDM": t}))
                vs.append(("POST:querySetting(XH,XNXQDM)", "POST", {
                    "querySetting": json.dumps([
                        {"name": "XH", "value": xh, "linkOpt": "AND", "builder": "equal"},
                        {"name": "XNXQDM", "value": t, "linkOpt": "AND", "builder": "equal"},
                    ], ensure_ascii=False)}))
        if "TJLX" in f:
            for tjlx in ("1", "2", "0", "all"):
                vs.append((f"POST:XH+TJLX={tjlx}", "POST", {"XH": xh, "TJLX": tjlx}))
        vs.append(("GET:XH", "GET", {"XH": xh}))
        vs.append(("GET:XH+XNXQDM" if term else "GET:XH", "GET",
                   {"XH": xh, **({"XNXQDM": term} if term else {})}))
    # 元数据字段全量：只填学号相关，其它留空（避免 WID 报错）
    if xh and f:
        base = _xh_fields(xh, list(f), term)
        vs.append(("POST:meta_fields", "POST", base))
    vs.append(("POST:empty", "POST", {}))  # 最后：看无参时的响应形状
    # 去重
    seen, out = set(), []
    for name, method, form in vs:
        key = (method, tuple(sorted(form.items())))
        if key not in seen:
            seen.add(key); out.append((name, method, form))
    return out


CJCX_REFERER = APP_CJCX + "?EMAP_LANG=zh"  # 浏览器 cURL 无带 hash
CJCX_REFERER_HASH = APP_CJCX + "?EMAP_LANG=zh#/cjcx"


def _request_json(client, url: str, method: str, form: dict) -> tuple[int, object]:
    """POST 走 post_raw（已带 X-Requested-With / Origin）；Referer 用成绩页 #/cjcx。"""
    if method == "GET":
        full = "https://iedu.jlu.edu.cn" + url + (("?" + urllib.parse.urlencode(form)) if form else "")
        code, text, _, _ = client._request(full, headers={
            "Referer": CJCX_REFERER,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        })
    else:
        code, text, _ = client.post_raw(url, form, CJCX_REFERER)
    try:
        return code, json.loads(text) if text else {}
    except (json.JSONDecodeError, ValueError):
        return code, text


def probe_gpa(client, log=print) -> dict:
    """扫描 cjcx 应用：动作/字段名列表 + 绩点候选试调用结果（无个人数值）。"""
    from . import emap
    app = emap.App("cjcx", "cjcx")
    report = emap.explore_app(client, app)
    extra = emap.module_meta(client, app, [RXYL_MODULE])
    report["meta"].update(extra["modules"])
    report.setdefault("meta_trace", []).extend(extra.get("trace") or [])
    captions = {}
    for info in report["meta"].values():
        captions.update(info.get("captions") or {})
        for a in info.get("actions") or []:
            captions.update(a.get("captions") or {})
    report["captions"] = dict(captions)
    actions = []
    for m, info in report["meta"].items():
        for a in info["actions"]:
            url = app.abs(a["url"])
            actions.append({"module": m, "name": a["name"], "url": url, "fields": a["fields"],
                            "gpaish": _gpaish(a["name"], url, a["fields"]) or "rxylgpacx" in url})
    for u in report["action_urls"]:
        if not any(a["url"] == u for a in actions):
            actions.append({"module": "", "name": "", "url": u, "fields": [],
                            "gpaish": _gpaish("", u, [])})
    report["actions"] = actions
    actions = [a for a in actions if not is_course_endpoint(a["url"])]
    candidates = [a for a in actions if a["gpaish"]] + [
        {"module": "guess", "name": n, "url": p,
         "fields": list(captions) if "rxylgpacx" in p else [], "gpaish": True}
        for p, n in [(p, p.rsplit("/", 1)[-1]) for p, _ in GPA_CANDIDATES]
        if not any(a["url"] == p for a in actions)]
    seen, uniq = set(), []
    for a in candidates:
        if a["url"] not in seen:
            seen.add(a["url"]); uniq.append(a)
    uniq.sort(key=lambda a: (0 if "modules*cjcx" in a["url"] or "modules%2Acjcx" in a["url"]
                             else 1 if "rxylgpacx" in a["url"]
                             else 2 if "cxxspjjdxx" in a["url"]
                             else 3 if ("cxsfwfcsj" in a["url"] or "cxcjcxsfkf" in a["url"]) else 4, a["url"]))
    plan = _plan_row(client)
    xh = _s(plan.get("XH"))
    term = ""
    try:
        term = client.current_semester() or ""
    except Exception:
        pass
    report["has_xh"] = bool(xh)
    report["has_term"] = bool(term)
    tries = []
    # 优先动作多试几种参数；其它动作只试 XH / meta_fields
    for a in uniq:
        variants = _param_variants(xh, a["fields"], term, page_first=("rxylgpacx" in a["url"]))
        if not any(s in a["url"] for s in ("rxylgpacx", "cxxspjjdxx", "cxsfwfcsj", "cxcjcxsfkf")):
            variants = [v for v in variants if v[0] in ("POST:XH", "POST:meta_fields", "POST:XH1..6", "POST:empty")][:3]
        for vname, method, form in variants:
            item = {"url": a["url"], "name": a["name"] or a["url"].rsplit("/", 1)[-1],
                    "variant": vname, "param_names": sorted(form)}
            try:
                code, obj = _request_json(client, a["url"], method, form)
                item["status"] = code
                if isinstance(obj, (dict, list)):
                    item["shape"] = response_shape(obj)
                    if isinstance(obj, dict):
                        item["code"] = _s(obj.get("code"))[:8]
                        if isinstance(obj.get("msg"), str):
                            item["msg"] = re.sub(r"\d{5,}", "#", obj["msg"])[:60]
                    payload = extract_gpa_payload(obj) if isinstance(obj, dict) else None
                    if payload:
                        g = parse_official_gpa(payload, captions)
                        item["matched_labels"] = [i["key"] for i in g["items"]]
                        item["payload_fields"] = sorted(payload.keys())[:40]
                        item["field_captions"] = {i["key"]: i["label"] for i in g["items"]}
                else:
                    item["non_json_bytes"] = len(obj or "")
            except jwxt.JwxtError as e:
                item["error"] = type(e).__name__
            tries.append(item)
            shape_brief = ""
            if item.get("shape"):
                paths = item["shape"].get("paths") or {}
                # 紧凑：只挑 datas / rows / gpa 相关
                keep = [f"{k}:{v}" for k, v in paths.items()
                        if "datas" in k or "rows" in k or "fields" in k][:6]
                shape_brief = "; ".join(keep) or list(paths.items())[:3]
            log(f"[绩点] {item['name']} / {vname} → {item.get('status')} code={item.get('code')} "
                f"match={item.get('matched_labels')} shape={shape_brief}")
            if item.get("matched_labels"):
                break  # 该动作已命中，不再试其它变体
    report["tries"] = tries
    report["hit"] = next(({"url": t["url"], "variant": t["variant"], "matched_labels": t["matched_labels"]}
                          for t in tries if t.get("matched_labels")), None)
    # 脱敏：去掉可能含学号的请求体
    return {k: report[k] for k in ("discover", "meta", "meta_trace", "actions", "tries", "hit", "has_xh", "captions")}


def _call_gpa_action(client, url: str, fields: list[str], xh: str, term: str = "",
                     captions: Optional[dict] = None) -> Optional[dict]:
    if is_course_endpoint(url):
        return None
    for vname, method, form in _param_variants(xh, fields, term):
        try:
            code, obj = _request_json(client, url, method, form)
        except jwxt.JwxtError:
            continue
        if not isinstance(obj, dict) or code != 200:
            continue
        payload = extract_gpa_payload(obj)
        if not payload:
            continue
        g = parse_official_gpa(payload, captions)
        if g["items"]:
            g["source"] = "official"
            g["endpoint"] = url
            g["variant"] = vname
            return g
    return None



def _star_paths(*paths: str) -> list[str]:
    """保留字面量 *；若调用方需要再附带 %2A 回退。"""
    out = []
    for p in paths:
        if p and p not in out:
            out.append(p)
    return out


def fetch_rxyl_captions(client) -> dict:
    """拉取 rxylgpacx 模块元数据中的字段 caption（无个人数据）。"""
    from . import emap
    caps = {}
    for path in _star_paths(EP_RXYL_META, EP_RXYL_META_ENC, EP_RXYL_META_SLASH,
                            "/jwapp/sys/cjcx/modules/rxylgpacx.do"):
        for method, form in (("GET", None), ("POST", {}), ("POST", {"*json": "1"})):
            try:
                if method == "GET":
                    code, obj = _request_json(client, path + "?*json=1", "GET", {})
                else:
                    code, obj = _request_json(client, path, "POST", form or {})
            except (jwxt.JwxtError, Exception):
                continue
            if isinstance(obj, dict):
                caps.update(emap.parse_captions(obj))
            if caps:
                return caps
    return caps


_RXYL_OK_PATH = None


def _rxyl_cache_file():
    return jwxt.config_dir() / "data" / "gpa_endpoint.txt"


def _load_rxyl_path():
    try:
        return _rxyl_cache_file().read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _save_rxyl_path(path: str) -> None:
    try:
        f = _rxyl_cache_file(); f.parent.mkdir(parents=True, exist_ok=True); f.write_text(path, encoding="utf-8")
    except OSError:
        pass


def fetch_rxyl_official_gpa(client, captions: Optional[dict] = None) -> Optional[dict]:
    """浏览器实测：POST ``.../modules*cjcx/rxylgpacx/rxylgpacxcx.do``，body=pageSize&pageNumber。"""
    form = {"pageSize": "10", "pageNumber": "1"}
    caps = captions if captions is not None else fetch_rxyl_captions(client)
    global _RXYL_OK_PATH
    order = [EP_GPA_RXYL_ENC, EP_GPA_RXYL, EP_GPA_RXYL_SLASH, EP_GPA_RXYL_ALT]  # 实测 %2A 可用
    cached = _load_rxyl_path()
    if cached in order:
        order.remove(cached); order.insert(0, cached)
    for path in order:
        try:
            code, obj = _request_json(client, path, "POST", form)
        except jwxt.JwxtError:
            continue
        if code != 200 or not isinstance(obj, dict):
            continue
        rows = []
        datas = obj.get("datas")
        if isinstance(datas, dict):
            for blk in datas.values():
                if isinstance(blk, dict) and isinstance(blk.get("rows"), list):
                    rows = [r for r in blk["rows"] if isinstance(r, dict)]
                    if rows:
                        break
                if isinstance(blk, list):
                    rows = [r for r in blk if isinstance(r, dict)]
                    if rows:
                        break
        elif isinstance(datas, list):
            rows = [r for r in datas if isinstance(r, dict)]
        # 优先含汇总键的行；官方端点若只有一行也试 parse
        chosen = next((r for r in rows if is_summary_gpa_row(r)), rows[0] if rows else None)
        if not chosen:
            continue
        # 非 star 回退路径仍必须有汇总键，避免单科误认
        if path not in (EP_GPA_RXYL, EP_GPA_RXYL_ENC) and not is_summary_gpa_row(chosen):
            continue
        g = parse_official_gpa(chosen, caps)
        if not g["items"]:
            continue
        # star 路径：若没有汇总键但有字段，仍要求至少命中一个 SUMMARY 或内置 GPA 标签
        if not is_summary_gpa_row(chosen):
            if not any(i["key"] in SUMMARY_GPA_KEYS or i["key"] in dict(GPA_FIELDS) for i in g["items"]):
                continue
        g["source"] = "official"
        g["endpoint"] = path
        g["variant"] = "POST:pageSize+pageNumber"
        g["rows"] = len(rows)
        _save_rxyl_path(path)
        return g
    return None


def fetch_official_gpa(client, xh: Optional[str] = None, grades=None) -> dict:
    from . import emap
    tried = []
    xh = xh or _s(_plan_row(client).get("XH"))
    term = ""
    try:
        term = client.current_semester() or ""
    except Exception:
        pass
    client.enter_emap_app(APP_CJCX)
    # 1) 浏览器实测主路径（modules*cjcx + pageSize/pageNumber）
    try:
        hit = fetch_rxyl_official_gpa(client)
        if hit:
            return hit
    except jwxt.LoginError:
        raise
    except jwxt.JwxtError as e:
        tried.append(f"rxyl:{type(e).__name__}")
    app = emap.App("cjcx", "cjcx")
    try:
        disc = emap.discover(client, app)
        mods = list(dict.fromkeys([RXYL_MODULE] + disc.get("modules_seen", ["cjcx"])))
        mm = emap.module_meta(client, app, mods)
        captions, candidates = {}, []
        for m, info in mm["modules"].items():
            captions.update(info.get("captions") or {})
            for a in info["actions"]:
                captions.update(a.get("captions") or {})
                url = app.abs(a["url"])
                if _gpaish(a["name"], url, a["fields"]) or "rxylgpacx" in url:
                    candidates.append((url, a["fields"]))
        for path, _ in GPA_CANDIDATES:
            if path not in {u for u, _ in candidates}:
                candidates.append((path, list(captions) if "rxylgpacx" in path else []))
        def _rank(item):
            u = item[0]
            if "rxylgpacx" in u:
                return 0
            if "cxxspjjdxx" in u:
                return 1
            if "cxsfwfcsj" in u or "cxcjcxsfkf" in u:
                return 2
            return 3
        candidates.sort(key=_rank)
        if xh:
            for url, fields in candidates:
                try:
                    g = _call_gpa_action(client, url, fields, xh, term, captions)
                    if g:
                        return g
                    tried.append(f"{url.rsplit('/',1)[-1]}:empty")
                except jwxt.LoginError:
                    raise
                except jwxt.JwxtError as e:
                    tried.append(f"{url.rsplit('/',1)[-1]}:{str(e)[-12:]}")
    except jwxt.LoginError:
        raise
    except jwxt.JwxtError as e:
        tried.append(f"discover:{type(e).__name__}")
    alt = gpa_from_jw_points(grades)
    if alt:
        return alt
    raise Unavailable("未找到可用的官方绩点接口（已尝试：" + "; ".join(tried[:8]) + "）")


def fetch_plan_courses(client, pyfadm: str, page_size: int = 500) -> list:
    out: list = []
    for page in range(1, 6):
        data = _post(client, EP_PLAN_COURSES, {"PYFADM": pyfadm, "pageSize": str(page_size),
                                               "pageNumber": str(page)}, APP_XSFACX)
        rows = _rows(data, "kzkccx")
        out += rows
        total = ((data.get("datas") or {}).get("kzkccx") or {}).get("totalSize") or 0
        if not rows or len(out) >= int(total or 0):
            break
    return out


def fetch_completion(client, grades=None) -> dict:
    # The plan supplies fallback fields; its permissions can differ from completion.
    # A rejected optional lookup must not hide a working completion application.
    plan_error = None
    try:
        plan = _plan_row(client)
    except jwxt.LoginError:
        raise
    except jwxt.JwxtError as e:
        plan, plan_error = {}, e
    client.enter_emap_app(APP_XYWCCX)
    rows = _rows(_post(client, EP_COMPLETION, {"SCLBDM": "04", "*order": "-CZSJ"}, APP_XYWCCX), "cxxsscfa")
    summary = rows[0] if rows else {}
    groups: list = []
    if summary:
        try:
            groups = _rows(_post(client, EP_COMPLETION_GROUPS, {
                "XH": _s(summary.get("XH") or plan.get("XH")),
                "PYFADM": _s(summary.get("PYFADM") or plan.get("PYFADM")),
                "BYNJDM": _s(summary.get("BYNJDM")) or "-",
                "SCLBDM": _s(summary.get("SCLBDM")) or "04",
            }, APP_XYWCCX), "cxscfakz")
        except jwxt.LoginError:
            raise
        except jwxt.JwxtError:
            groups = []
    if not summary and not plan:
        if plan_error is not None:
            raise jwxt.JwxtError(f"学业完成未返回数据，培养方案补充查询失败：{plan_error}") from plan_error
        raise jwxt.JwxtError("学业完成与培养方案均为空")
    comp = parse_completion(summary, plan, groups)
    if grades is not None and any(g.get("earned") in (None, 0) for g in comp["groups"]):
        pyfadm = _s(summary.get("PYFADM") or plan.get("PYFADM"))
        if pyfadm:
            try:
                client.enter_emap_app(APP_XSFACX)
                comp = derive_group_earned(comp, fetch_plan_courses(client, pyfadm), grades)
            except jwxt.LoginError:
                raise
            except jwxt.JwxtError:
                pass
    return comp
