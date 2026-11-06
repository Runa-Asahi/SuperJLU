"""整份课表分享：导出可转发的 JSON，导入时覆盖本地课表。

与「我的课表修改」备份（overlay）不同：这里导出的是同学当前看到的完整课表
（教务 + 调停课 + 个人修改合并后的结果），不含账号、密码、会话等敏感信息。

文件格式（version 1）::

    {
      "kind": "superjlu.schedule.share",
      "version": 1,
      "term": "2026-2027-1",
      "first_monday": "2026-09-07",
      "periods": {"1": ["08:00", "08:45"], ...},
      "courses": [{name, teacher, location, weekday, start, end, weeks}, ...]
    }
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Iterable, Optional

from . import core


class TermMismatch(ValueError):
    """分享学期与本地当前学期不一致，需要 confirm_term。"""

    def __init__(self, share_term: str, local_term: str):
        self.share_term = share_term
        self.local_term = local_term
        super().__init__(
            f"分享课表属于 {share_term} 学期，与你当前 {local_term} 学期不同，仍会覆盖现有课表。请再次确认。"
        )

KIND = "superjlu.schedule.share"
VERSION = 1
MAX_BYTES = 512 * 1024
MAX_COURSES = 400
MAX_WEEKS = 30
FILENAME = "superjlu-schedule.json"

TOP_KEYS = frozenset({"kind", "version", "term", "first_monday", "periods", "courses"})
COURSE_KEYS = frozenset({"name", "teacher", "location", "weekday", "start", "end", "weeks",
                         "jxbid", "kch"})
SENSITIVE = frozenset({
    "password", "passwd", "pwd", "secret", "token", "cookie", "cookies", "session",
    "sessions", "credential", "credentials", "auth", "authorization", "keyring",
    "private_key", "access_token", "refresh_token", "api_key",
})


def _reject_sensitive(obj: Any, *, skip_courses: bool = False) -> None:
    """只按精确键名拦截敏感字段；courses 交给 _parse_course 白名单，避免误杀。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in SENSITIVE:
                raise ValueError("分享文件里不能包含账号或登录信息")
            if skip_courses and k == "courses":
                continue  # 每门课字段由 COURSE_KEYS 白名单校验
            _reject_sensitive(v)
    elif isinstance(obj, list):
        for v in obj[: MAX_COURSES + 5]:
            _reject_sensitive(v)


def _course_dict(c) -> dict:
    g = (lambda k: c.get(k, "")) if isinstance(c, dict) else (lambda k: getattr(c, k, ""))
    weeks = sorted({int(w) for w in (g("weeks") or []) if 1 <= int(w) <= MAX_WEEKS})
    name = str(g("name") or "").strip()[:60]
    if not name:
        raise ValueError("课程名不能为空")
    wd, s, e = int(g("weekday")), int(g("start")), int(g("end"))
    if not (1 <= wd <= 7 and 1 <= s <= e <= 20):
        raise ValueError("星期或节次超出范围")
    if not weeks:
        raise ValueError("请至少选择一周")
    out = {
        "name": name,
        "teacher": str(g("teacher") or "").strip()[:40],
        "location": str(g("location") or "").strip()[:60] or "待定",
        "weekday": wd,
        "start": s,
        "end": e,
        "weeks": weeks,
    }
    jxbid = str(g("jxbid") or "").strip()[:40]
    kch = str(g("kch") or "").strip()[:40]
    if jxbid:
        out["jxbid"] = jxbid
    if kch:
        out["kch"] = kch
    return out


def _parse_course(d: dict) -> core.Course:
    if not isinstance(d, dict):
        raise ValueError("课程条目格式不对")
    if set(d) - COURSE_KEYS:
        raise ValueError("分享文件含有无法识别的课程字段")
    c = _course_dict(d)
    return core.Course(c["name"], c["teacher"], c["location"], c["weekday"], c["start"], c["end"],
                       c["weeks"], c.get("jxbid", ""), c.get("kch", ""))


def _periods(raw) -> dict:
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ValueError("节次表格式不对")
    out = {}
    for k, v in list(raw.items())[:40]:
        try:
            n = int(k)
        except (TypeError, ValueError):
            raise ValueError("节次表键必须是节次号") from None
        if not 1 <= n <= 20:
            raise ValueError("节次号超出范围")
        if not (isinstance(v, (list, tuple)) and len(v) == 2):
            raise ValueError("节次表每项应是 [开始, 结束]")
        a, b = str(v[0]).strip()[:8], str(v[1]).strip()[:8]
        if not a or not b:
            raise ValueError("节次时间不能为空")
        out[str(n)] = [a, b]
    return out


def build(courses: Iterable, term: str = "", first_monday: str = "",
          periods: Optional[dict] = None) -> dict:
    """从当前课表构造分享文档（不含敏感字段）。"""
    rows = []
    for c in courses:
        if isinstance(c, dict) and c.get("src") == "cancelled":
            continue
        rows.append(_course_dict(c))
        if len(rows) > MAX_COURSES:
            raise ValueError("课表课程过多，无法分享")
    fm = str(first_monday or "").strip()[:10]
    if fm and len(fm) != 10:
        raise ValueError("开学日期格式不对")
    return {
        "kind": KIND,
        "version": VERSION,
        "term": str(term or "").strip()[:32],
        "first_monday": fm,
        "periods": _periods(periods or {}),
        "courses": rows,
    }


def dumps(doc: dict) -> bytes:
    body = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    if len(body) > MAX_BYTES:
        raise ValueError("课表分享文件过大")
    return body


def parse(raw) -> dict:
    """校验并规范化分享文件；返回可安全导入的文档。"""
    if isinstance(raw, (bytes, bytearray)):
        if len(raw) > MAX_BYTES:
            raise ValueError("课表分享文件过大（上限 512 KB）")
        try:
            text = bytes(raw).decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("课表分享文件不是 UTF-8 文本") from e
        raw = text
    if isinstance(raw, str):
        if len(raw.encode("utf-8")) > MAX_BYTES:
            raise ValueError("课表分享文件过大（上限 512 KB）")
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError("这不是 SuperJLU 课表分享文件") from e
    if not isinstance(raw, dict):
        raise ValueError("这不是 SuperJLU 课表分享文件")
    _reject_sensitive(raw, skip_courses=True)
    if set(raw) - TOP_KEYS:
        raise ValueError("分享文件含有无法识别的字段")
    if raw.get("kind") != KIND:
        raise ValueError("这不是 SuperJLU 课表分享文件")
    try:
        ver = int(raw.get("version"))
    except (TypeError, ValueError):
        raise ValueError("分享文件版本无法识别") from None
    if ver != VERSION:
        raise ValueError(f"不支持的课表分享版本（{ver}）")
    courses_raw = raw.get("courses")
    if not isinstance(courses_raw, list):
        raise ValueError("分享文件缺少课程列表")
    if len(courses_raw) > MAX_COURSES:
        raise ValueError("分享课表课程过多")
    courses = [_parse_course(x) for x in courses_raw]
    term = str(raw.get("term") or "").strip()[:32]
    fm = str(raw.get("first_monday") or "").strip()[:10]
    if fm:
        try:
            d = dt.date.fromisoformat(fm)
        except ValueError as e:
            raise ValueError("开学日期格式不对") from e
        if d.weekday() != 0:
            raise ValueError("开学日期必须是星期一")
    return {
        "kind": KIND,
        "version": VERSION,
        "term": term,
        "first_monday": fm,
        "periods": _periods(raw.get("periods")),
        "courses": courses,
    }


def is_share_doc(raw) -> bool:
    """粗判：Android 收到任意 JSON 时决定要不要当课表分享处理。"""
    try:
        if isinstance(raw, (bytes, bytearray)):
            if len(raw) > MAX_BYTES or len(raw) < 20:
                return False
            raw = bytes(raw).decode("utf-8")
        if isinstance(raw, str):
            if "superjlu.schedule.share" not in raw:
                return False
            raw = json.loads(raw)
        return isinstance(raw, dict) and raw.get("kind") == KIND
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return False
