"""`jlu-toolkit ui`：本地网页界面（标准库 http.server，仅监听 127.0.0.1）。

数据目录：~/.config/jlu-toolkit/data/
  schedule.csv / grades.csv / exams.csv —— 由「从教务刷新」或 CLI fetch 生成
  schemes.json  —— 命名绩点方案（保研/综测…）：{"方案名": ["学期|课程", ...]}
  settings.json —— {"first_monday": "YYYY-MM-DD"}
  schedule_overlay.json —— 同学自己对课表的增/删/改（刷新不覆盖，见 overlay.py）
所有数据只在本机；网页不引用任何外部资源。
"""
from __future__ import annotations

import datetime as dt
import base64
import binascii
import json
import os
import re
import shutil
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from . import core, exams as ex, jwxt
from .web_login import LoginFlow
from .ui_page import PAGE

ALLOWED_HOSTS = ("127.0.0.1", "localhost")

TEACHING_ACTIONS = {
    "/api/rooms": "空教室查询", "/api/rooms/campuses": "校区加载",
    "/api/rooms/day-period": "全天空闲加载",
    "/api/rooms/day": "全天空闲加载",
    "/api/rooms/buildings": "教学楼加载", "/api/rooms/types": "教室类型加载",
    "/api/rooms/fields": "查询条件加载", "/api/grades/refresh": "成绩同步",
    "/api/refresh": "教务同步", "/api/session/keepalive": "会话检查",
}


def teaching_error(path: str, error: Exception) -> tuple[str, bool]:
    """Keep endpoint probing diagnostics out of normal student-facing errors."""
    action = TEACHING_ACTIONS.get(path)
    if not action:
        return str(error), False
    if isinstance(error, jwxt.NetworkError) and error.kind == "certificate":
        return "安全连接验证失败，请检查设备时间和网络后重试。", False
    if isinstance(error, jwxt.LoginError):
        return "请在「更多 → 登录」选择当前网络对应的方式，登录后重试。", True
    return f"{action}失败，请检查网络或在「更多 → 登录」切换登录方式后重试。", True


def data_dir() -> Path:
    d = jwxt.config_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


import hmac as _hmac
import secrets as _secrets
SSO_NONCE = _secrets.token_urlsafe(18)  # 每次启动换新；只经同源 /api/links 下发

# 本地接口令牌：只监听 127.0.0.1 挡不住同机的其它程序（Android 上任何有联网权限的 App
# 都能连 127.0.0.1:18765 读成绩、换 CAS 票据），所以除图标外的请求都要带令牌——
# 浏览器 / WebView 用 HttpOnly Cookie，原生代码（Android Java、自检脚本）用请求头。
# 令牌存在私有配置目录，重启后不变，已打开的标签页和书签照常可用。
TOKEN_COOKIE = "superjlu_t"
TOKEN_HEADER = "X-SuperJLU-Token"
TOKEN_FILE = "ui_token"
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_PUBLIC_PATHS = ("/favicon.svg", "/favicon.ico")
_PAGE_PATHS = ("/", "/index.html")
LOCKED_PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SuperJLU</title></head>
<body style="font-family:system-ui,sans-serif;max-width:32em;margin:15vh auto;padding:0 16px;line-height:1.7">
<h2>请从 SuperJLU 打开界面</h2>
<p>为保护你的账号和成绩，本地界面只接受 SuperJLU 自己打开的页面。
请点系统托盘里的「打开 SuperJLU」，或重新运行 SuperJLU。</p>
<p>命令行启动时，请使用终端里打印的完整地址。</p></body></html>"""


def token_path() -> Path:
    return jwxt.config_dir() / TOKEN_FILE


def load_or_create_token() -> str:
    """读取（缺失或损坏时生成）本地接口令牌，文件权限 0600。"""
    p = token_path()
    try:
        t = p.read_text(encoding="utf-8").strip()
        if _TOKEN_RE.match(t):
            return t
    except OSError:
        pass
    t = _secrets.token_urlsafe(32)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(TOKEN_FILE + ".tmp")
    tmp.write_text(t, encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, p)
    return t


def launch_url(base: str, token: Optional[str] = None) -> str:
    """打开界面用的地址：服务端校验 ?t= 后种 Cookie，再 302 回不带令牌的 /。"""
    return base.rstrip("/") + "/?t=" + (token or load_or_create_token())


def _token_ok(headers, token: str) -> bool:
    got = headers.get(TOKEN_HEADER) or ""
    if not got:
        for part in (headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == TOKEN_COOKIE:
                got = v
                break
    return bool(got) and _hmac.compare_digest(got.encode(), token.encode())


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.lock = threading.Lock()
        # Public room availability only; bounded, short-lived, memory-only cache.
        self.room_day_lock = threading.Lock()
        self.room_day_cache: dict = {}
        self.room_day_warm = None

    def p(self, name: str) -> Path:
        return self.root / name

    def _json(self, name: str, default):
        from . import secure_store
        if name in secure_store.PERSONAL_CACHES:
            return secure_store.load_json(self.p(name), default)
        try:
            return json.loads(self.p(name).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write_json(self, name: str, obj) -> None:
        from . import secure_store
        if name in secure_store.PERSONAL_CACHES:
            secure_store.save_json(self.p(name), obj)
            return
        self.p(name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 课表：读取统一走 timetable.py（App / iCal / 命令行 / MCP 同一份） ----
    OVERLAY = "schedule_overlay.json"
    OVERLAY_UNDO = "schedule_overlay.undo.json"

    def jwxt_courses(self) -> list[core.Course]:
        """教务原课表（schedule.csv，刷新整份覆盖；不含调课）。"""
        from . import timetable
        return timetable.jwxt_courses(self.root)

    def adjustments_enabled(self) -> bool:
        from . import timetable
        return timetable.adjustments_enabled(self.root)

    def _adjustments(self) -> list:
        from . import timetable
        return timetable.load_adjustments(self.root, self.current_term())

    def official_courses(self) -> list[core.Course]:
        """教务课表 + 调停课（设置开着时）；个人修改叠加在它之上。"""
        cs = self.jwxt_courses()
        if self.adjustments_enabled():
            adjs = self._adjustments()
            if adjs:
                from . import adjust
                cs, _ = adjust.apply_adjustments(cs, adjs)
        return cs

    def timetable_view(self) -> dict:
        from . import timetable
        return timetable.view(self.root)

    def adjustments_info(self, v: Optional[dict] = None) -> dict:
        from . import adjust
        v = v or self.timetable_view()
        d = self._json("schedule_adjustments.json", None)
        d = d if isinstance(d, dict) else {}
        adjs = v["adjustments"]
        applied = v["applied"]
        if not v["enabled"] and adjs:  # 关着时也告诉同学「有几处」
            applied = sum(1 for n in adjust.apply_adjustments(self.jwxt_courses(), adjs)[1] if not n["skipped"])
        return {"enabled": v["enabled"], "count": len(adjs), "applied": applied,
                "cancelled": sum(1 for r in v["rows"] if r["src"] == "cancelled"),
                "fetched_at": d.get("fetched_at") if adjs else None}

    def current_term(self) -> str:
        from . import timetable
        return timetable.current_term(self.root)

    def overlay_doc(self) -> dict:
        from . import timetable
        return timetable.load_overlay(self.root, self.current_term())

    def overlay_ops(self) -> list:
        from . import overlay as ov
        return ov.term_ops(self.overlay_doc(), self.current_term())

    def schedule_view(self) -> tuple[list[dict], list[dict]]:
        v = self.timetable_view()
        return v["rows"], v["issues"]

    def courses(self) -> list[core.Course]:
        """同学看到的课表 = 教务 + 调停课 + 个人修改（日历导出等都用这个；不含灰显的停课）。"""
        from . import timetable
        return timetable.courses(self.root)

    def overlay_action(self, body: dict) -> None:
        from . import overlay as ov
        action, oid = body.get("action"), str(body.get("id") or "")
        with self.lock:
            term = self.current_term()
            doc = self.overlay_doc()
            ops = ov.term_ops(doc, term)
            official = self.official_courses()
            undo = self.p(self.OVERLAY_UNDO)
            if action in ("add", "hide", "edit"):
                ops = ops + [ov.make_op(action, body, official)]
            elif action == "update":
                ops = ov.update(ops, oid, body)
            elif action == "remove":
                ops = ov.remove(ops, oid)
            elif action == "ack":
                ops = ov.ack(ops, oid, official)
            elif action == "detach":
                ops = ov.detach(ops, oid)
            elif action == "reset":  # 恢复教务原样（本学期）；留一份可撤销
                if not ops:
                    return
                self._write_json(self.OVERLAY_UNDO, {"term": term, "ops": ops})
                self._write_json(self.OVERLAY, ov.with_ops(doc, term, []))
                return
            elif action == "undo_reset":
                prev = self._json(self.OVERLAY_UNDO, None)
                if not isinstance(prev, dict) or prev.get("term") != term:
                    raise ValueError("没有可以撤销的恢复操作")
                ops = ov.term_ops(ov.normalize({"terms": {term: prev.get("ops")}}), term) + ops
            elif action == "import":
                doc = ov.merge_import(doc, ov.normalize(body.get("doc"), term))
                ops = ov.term_ops(doc, term)
            else:
                raise ValueError("未知的课表修改操作")
            self._write_json(self.OVERLAY, ov.with_ops(doc, term, ops))
            if undo.exists():
                undo.unlink()

    def grades(self) -> list[core.Grade]:
        f = self.p("grades.csv")
        return core.load_grades(str(f)) if f.exists() else []

    def exams(self) -> list[ex.Exam]:
        f = self.p("exams.csv")
        return ex.load_exams(str(f)) if f.exists() else []

    def schemes(self) -> dict:
        return self._json("schemes.json", {})

    def grade_records(self, source: str = "jwxt") -> list[dict]:
        from . import grade_calculator as calc
        imported = self._json("imported_grades.json", None) if source == "import" else None
        try:
            grades = [core.Grade(**g) for g in imported["grades"]] if imported else None
        except (TypeError, KeyError, ValueError):
            imported = None  # 导入文件损坏或格式过旧：退回教务成绩，不让 /api/data 整体 500
            grades = None
        if grades is None:
            grades = self.grades()
        plan = self._json("plan_courses.json", {}) or {}
        occurrences = {}
        records = []
        for g in grades:
            nature = g.nature
            if not nature and not imported:
                matches = [c for c in plan.get("courses", []) if c.get("name") == g.name
                           and (not c.get("term") or c.get("term") == g.term)]
                labels = {c.get("nature") or c.get("category") for c in matches}
                if len(labels) == 1:
                    nature = next(iter(labels)) or ""
            nature = nature or "未标注"
            signature = (g.term, g.name, nature)
            ordinal = occurrences.get(signature, 0) + 1
            occurrences[signature] = ordinal
            key = json.dumps([*signature, ordinal], ensure_ascii=False, separators=(",", ":"))
            score = calc.parse_score(g.score)
            ungraded = not imported and g.score == "通过"
            point = g.jw_point if g.jw_point is not None else (None if imported else core.score_to_point(g.score))
            course = calc.Course(key, g.term, g.name, nature, g.score, score or 0, g.credit,
                                 point or 0, score is not None, point is not None)
            records.append({**g.__dict__, "key": key, "legacy_key": f"{g.term}|{g.name}",
                            "nature": nature, "numeric_score": score, "score_valid": score is not None,
                            "ungraded": ungraded,
                            "point": point, "point_source": ("reported" if g.jw_point is not None
                                                            else "missing" if imported else "estimated"),
                            "required": calc.nature_category(nature) == "必修",
                            "builtin": course.as_dict()["builtin"]})
        return records

    def import_grades(self, filename: str, payload: str) -> None:
        from . import grade_calculator as calc
        if not isinstance(filename, str) or not isinstance(payload, str):
            raise ValueError("无效的成绩单")
        try:
            data = base64.b64decode(payload, validate=True)
        except (ValueError, binascii.Error) as e:
            raise ValueError("成绩单编码无效") from e
        if len(data) > calc.MAX_UPLOAD_BYTES:
            raise ValueError("成绩单超过 5 MB")
        courses = calc.courses_from_bytes(filename, data)
        grades = [core.Grade(c.name, c.credit, c.grade, c.term,
                            c.gpa if c.gpa_valid else None, c.nature).__dict__ for c in courses]
        with self.lock:
            self._write_json("imported_grades.json", {"filename": Path(filename).name,
                             "grades": grades, "notes": courses.import_notes})

    def settings(self) -> dict:
        return self._json("settings.json", {})

    def calendar(self) -> dict:
        return self._json("calendar.json", {})

    def periods(self) -> dict:
        return self._json("periods.json", {})

    def first_monday(self) -> Optional[str]:
        """手动覆盖优先，否则用教务校历。"""
        return self.settings().get("first_monday") or self.calendar().get("first_monday") or None

    def save_scheme(self, name: str, keys: list[str], base: Optional[str] = None,
                    source: str = "jwxt") -> None:
        name = (name or "").strip()[:40]
        if not name:
            raise ValueError("方案名不能为空")
        if name in ("__postgraduate__", "__scholarship__", "__all__"):
            raise ValueError("请使用其他模板名称")
        if base is not None and base not in ("postgraduate", "scholarship", "comprehensive"):
            raise ValueError("未知的基础模板")
        if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys):
            raise ValueError("无效的课程选择")
        with self.lock:
            s = self.schemes()
            s[name] = sorted({str(k) for k in keys})
            self._write_json("schemes.json", s)
            rules = self._json("scheme_rules.json", {})
            if base:
                previous = rules.get(name, {})
                overrides = dict(previous.get("overrides", {})) if previous.get("base") == base else {}
                for g in self.grade_records(source):
                    if (g["key"] in keys) != g["builtin"][base]:
                        overrides[g["key"]] = g["key"] in keys
                    else:
                        overrides.pop(g["key"], None)
                rules[name] = {"base": base, "overrides": overrides}
            else:
                rules.pop(name, None)
            self._write_json("scheme_rules.json", rules)

    def delete_scheme(self, name: str) -> None:
        with self.lock:
            s = self.schemes()
            s.pop(name, None)
            self._write_json("schemes.json", s)
            rules = self._json("scheme_rules.json", {})
            rules.pop(name, None)
            self._write_json("scheme_rules.json", rules)

    def save_settings(self, upd: dict) -> None:
        fm = upd.get("first_monday")
        if fm == "":
            with self.lock:
                s = self.settings()
                s.pop("first_monday", None)
                self._write_json("settings.json", s)
            return
        if fm:
            d = dt.date.fromisoformat(fm)
            if d.weekday() != 0:
                raise ValueError("第一周起始日必须是星期一")
        with self.lock:
            s = self.settings()
            s.update({k: v for k, v in upd.items() if k in ("first_monday",)})
            if "apply_adjustments" in upd:
                s["apply_adjustments"] = bool(upd["apply_adjustments"])
            if "grade_help_seen" in upd:
                s["grade_help_seen"] = bool(upd["grade_help_seen"])
            self._write_json("settings.json", s)

    def _schedule_snapshot(self) -> dict:
        v = self.timetable_view()
        rows, issues = v["rows"], v["issues"]
        doc, term = self.overlay_doc(), self.current_term()
        ops = doc["terms"].get(term, [])
        undo = self._json(self.OVERLAY_UNDO, None)
        return {"courses": rows, "schedule_issues": issues, "schedule_ops": ops,
                "schedule_adjust": self.adjustments_info(v),
                "schedule_edits": len(ops), "schedule_term": term,
                "schedule_other_terms": sum(len(v) for k, v in doc["terms"].items() if k != term),
                "schedule_can_undo_reset": isinstance(undo, dict) and undo.get("term") == term
                                           and bool(undo.get("ops"))}

    def snapshot(self, source: str = "jwxt") -> dict:
        gs = self.grades()
        saved_import = self._json("imported_grades.json", None)
        try:
            if not isinstance(saved_import, dict):
                raise TypeError
            [core.Grade(**g) for g in saved_import["grades"]]
        except (TypeError, KeyError, ValueError):
            saved_import = None  # 损坏或过旧的导入文件当作不存在
        imported = saved_import if source == "import" else None
        mtimes = [self.p(n).stat().st_mtime for n in ("schedule.csv", "grades.csv", "exams.csv")
                  if self.p(n).exists()]
        return {
            **self._schedule_snapshot(),
            "grades": self.grade_records(source),
            "grade_source": "import" if imported else "jwxt",
            "has_imported_grades": saved_import is not None,
            "grade_filename": imported.get("filename") if imported else None,
            "grade_notes": imported.get("notes", []) if imported else [],
            "exams": [e.to_dict() for e in ex.upcoming(self.exams(), dt.datetime(1970, 1, 1))],
            "schemes": self.schemes(),
            "scheme_rules": self._json("scheme_rules.json", {}),
            "settings": self.settings(),
            "calendar": self.calendar(),
            "periods": self.periods(),
            "first_monday": self.first_monday(),
            "first_monday_source": ("manual" if self.settings().get("first_monday")
                                    else "calendar" if self.calendar().get("first_monday") else None),
            "official_gpa": self._json("official_gpa.json", None),
            "completion": self._json("completion.json", None),
            "plan_courses": self._json("plan_courses.json", None),
            "gpa_all": core.gpa(gs),
            "updated": (dt.datetime.fromtimestamp(max(mtimes)).isoformat(timespec="minutes")
                        if mtimes else None),
            **cache_info(self),
        }


# 首次登录后全量同步所需的本地缓存；缺任一则 needs_bootstrap=True
BOOTSTRAP_CACHE_FILES = (
    "schedule.csv",
    "grades.csv",
    "exams.csv",
    "calendar.json",
    "completion.json",
)


def needs_bootstrap(store: Store) -> bool:
    """本地还缺课表/成绩/考试/校历/学业任一缓存时，登录后应自动全量刷新。"""
    # 全量同步完成过一次就不再每次启动重来（有的同学没有考试或课组数据，对应缓存永远不会生成）
    if store.p("bootstrap_done").exists():
        return False
    from . import secure_store
    # completion.json 等个人缓存加密后落盘为 *.enc，必须用 secure_store 判断是否存在
    return any(not (store.p(n).exists() or secure_store.json_exists(store.p(n)))
               for n in BOOTSTRAP_CACHE_FILES)


def cache_info(store: Store) -> dict:
    """{offline, cached_at, needs_bootstrap}：教务会话不可用但本地有缓存时 offline=True。只读本地。"""
    from . import secure_store
    times = [v.get("updated_at") for v in secure_store.cache_meta(store.root).values() if isinstance(v, dict)]
    for n in ("schedule.csv", "grades.csv", "exams.csv"):
        if store.p(n).exists():
            times.append(dt.datetime.fromtimestamp(store.p(n).stat().st_mtime).isoformat(timespec="seconds"))
    cached_at = max((t for t in times if t), default=None)
    st = jwxt.session_status()
    return {
        "offline": bool(cached_at) and st["state"] != jwxt.SESSION_OK,
        "cached_at": cached_at,
        "needs_bootstrap": needs_bootstrap(store), "bootstrapped": store.p("bootstrap_done").exists(),
    }


def refresh_from_jwxt(store: Store) -> dict:
    """用已保存会话拉取全部数据；不做交互登录。"""
    from .sync import sync_all

    client = _client()
    result = sync_all(client, store.root)
    try:
        store.p("bootstrap_done").write_text(dt.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    except OSError:
        pass
    return result


GRADE_AUTO_SYNC_INTERVAL = 600  # 秒；页面自动同步的最短间隔，手动同步不受限


def refresh_grades_from_jwxt(store: Store, automatic: bool = False) -> dict:
    """Refresh the current login's transcript without fetching unrelated modules."""
    import time
    gp = store.p("grades.csv")
    if automatic and gp.exists() and time.time() - gp.stat().st_mtime < GRADE_AUTO_SYNC_INTERVAL:
        return {"ok": True, "count": len(store.grades()), "skipped": True}
    client = _client()
    grades = client.fetch_grades()
    # Only replace the cache after the request succeeds; retain it while offline.
    with store.lock:
        jwxt.export_grades_csv(grades, str(store.p("grades.csv")))
    client.save_session()
    return {"ok": True, "count": len(grades)}


def _client() -> "jwxt.JwxtClient":
    c = jwxt.JwxtClient()
    if not c.load_session():
        from . import sessions
        if c.route == "webvpn" and sessions.load_cookies("vpn"):
            for cookie in jwxt.jar_from_list(sessions.load_cookies("cas") or []):
                c.jar.set_cookie(cookie)
            if c.has_cas_cookie():
                return c
        raise jwxt.LoginError("没有已保存的会话，请在「更多 → 登录」中登录")
    return c


# 吉大六个校区（教务代码表 01–06）；前端同样内置，接口取不到时也用这份
CAMPUSES = [{"code": "01", "name": "前卫校区"}, {"code": "02", "name": "南岭校区"},
            {"code": "03", "name": "新民校区"}, {"code": "04", "name": "朝阳校区"},
            {"code": "05", "name": "南湖校区"}, {"code": "06", "name": "和平校区"}]


def campuses_api(store: Store) -> dict:
    from . import rooms
    cache = store.p("campuses.json")
    if cache.exists():
        return {"campuses": json.loads(cache.read_text(encoding="utf-8"))}
    try:
        c = _client()
    except Exception:  # noqa: BLE001  无会话时直接给内置列表
        return {"campuses": CAMPUSES}
    lst = rooms.list_campuses(c)
    cache.write_text(json.dumps(lst, ensure_ascii=False), encoding="utf-8")
    c.save_session()
    return {"campuses": lst}


def build_room_query(store: Store, body: dict, term: str = ""):
    """UI / CLI / MCP 共用：body 字段 campus,date,periods,building,kind,seat_min,seat_max,
    exam_min,exam_max,mode(date|week),weeks,weekday,extra{}。"""
    from . import rooms
    mode = str(body.get("mode") or "date")
    start, end = rooms.parse_periods_arg(str(body.get("periods") or "1-2"))
    campus = str(body.get("campus") or "")
    if not campus:
        raise ValueError("请选择校区")
    i = lambda k: int(body.get(k) or 0)  # noqa: E731
    if mode == "week":
        weeks = rooms.expand_weeks(str(body.get("weeks") or ""))
        if not weeks:
            raise ValueError("按周次查询需要周次，如 6 或 6-8")
        weekday = i("weekday")
        if not 1 <= weekday <= 7:
            raise ValueError("按周次查询需要星期 1-7")
        date, week = "", int(weeks.split(",")[0])
    else:
        date = str(body.get("date") or dt.date.today().isoformat())
        dt.date.fromisoformat(date)
        week, weekday = rooms.week_and_weekday(date, store.first_monday())
        weeks = ""
    extra = body.get("extra") or {}
    if not isinstance(extra, dict):
        raise ValueError("extra 应为 {字段: 值}")
    return rooms.RoomQuery(campus, date, start, end, str(body.get("building") or ""),
                           term or store.calendar().get("term", ""), week, weekday,
                           kind=str(body.get("kind") or ""), seat_min=i("seat_min"), seat_max=i("seat_max"),
                           exam_min=i("exam_min"), exam_max=i("exam_max"), mode=mode, weeks=weeks,
                           extra={str(k): str(v) for k, v in extra.items()})


def rooms_api(store: Store, body: dict) -> dict:
    from . import rooms
    q = build_room_query(store, body)
    c = _client()
    found, prof = rooms.query_rooms_any(c, q, store.p("rooms_profile.json"), store.first_monday())
    c.save_session()
    if store.room_day_lock.acquire(blocking=False):
        try:
            import time
            store.room_day_warm = (_room_session_scope(c), time.monotonic())
        finally:
            store.room_day_lock.release()
    hidden = 0
    if body.get("hide_special"):
        kept = [r for r in found if not rooms.is_special_room(r)]
        hidden, found = len(found) - len(kept), kept
    week = q.week if 1 <= (q.week or 0) <= 30 else 0
    return {"mode": q.mode, "date": q.date, "week": week, "weeks": q.weeks, "weekday": q.weekday,
            "periods": [q.start, q.end], "total": prof.get("total"), "hidden_special": hidden,
            "rooms": [r.to_dict() for r in found]}


def room_day_period_api(store: Store, body: dict) -> dict:
    """Compatibility endpoint for a single complete period observation."""
    q = build_room_query(store, body)
    if q.mode != "date" or q.start != q.end or not 1 <= q.start <= 12:
        raise ValueError("全天概览需要单个日期和第 1–12 节中的单节查询")
    return _room_day_batch(store, body, [q.start], partial=False)["records"][0]


def room_day_api(store: Store, body: dict) -> dict:
    """At most four concurrent queries, using isolated copies of a warmed session."""
    if "day_ranges" in body:
        ranges = body["day_ranges"]
        if ("day_periods" in body or not isinstance(ranges, list) or not 1 <= len(ranges) <= 4
                or any(not isinstance(r, list) or len(r) != 2
                       or any(type(p) is not int for p in r)
                       or r[0] not in (1, 3, 5, 7, 9, 11) or r[1] != r[0] + 1
                       for r in ranges)
                or len({tuple(r) for r in ranges}) != len(ranges)):
            raise ValueError("每批需指定 1–4 个不重复的两节时段（1–2 至 11–12）")
        return _room_day_batch(store, body, [tuple(r) for r in ranges], partial=True)
    periods = body.get("day_periods")
    if (not isinstance(periods, list) or not 1 <= len(periods) <= 4
            or any(type(p) is not int or not 1 <= p <= 12 for p in periods)
            or len(set(periods)) != len(periods)):
        raise ValueError("每批需指定 1–4 个不重复的节次（第 1–12 节）")
    return _room_day_batch(store, body, periods, partial=True)


def _room_query_client(parent):
    """Independent opener and cookie jar; workers never refresh or save sessions."""
    import copy
    child = jwxt.JwxtClient(timeout=parent.timeout, debug=parent.debug, route=parent.route)
    for cookie in parent.jar:
        child.jar.set_cookie(copy.copy(cookie))
    child._native_hosts = set(parent._native_hosts)
    child._logged_in = parent._logged_in
    child._restore_saved_cas = False
    child._vpn_cookies_loaded = True
    child._cas_tried = True
    child._rebuild_opener()
    return child


def _room_session_scope(client):
    import hashlib
    return hashlib.sha256(json.dumps(
        [client.route, jwxt.jar_to_list(client.jar)], sort_keys=True, ensure_ascii=True,
    ).encode()).hexdigest()


def _room_day_batch(store: Store, body: dict, periods: list, partial: bool) -> dict:
    """Bounded parallel reads; complete pagination, isolated clients, partial retry.

    The batch lock caps each Store at four school queries, including concurrent
    HTTP callers. Only the coordinator prepares/saves authentication. Workers
    use immutable profile/metadata snapshots and never write profile files.
    """
    import copy
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from . import rooms

    first = periods[0][0] if isinstance(periods[0], tuple) else periods[0]
    base = build_room_query(store, {**body, "periods": str(first)})
    if base.mode != "date":
        raise ValueError("全天概览需要单个日期")
    profile = store.p("rooms_profile.json")
    if not profile.exists():
        raise ValueError("请先查询空教室，再加载全天空闲")
    c = _client()  # Cache still requires a saved session, including after logout.
    if not store.room_day_lock.acquire(blocking=False):
        raise ValueError("全天空闲正在加载，请稍后重试")
    try:
        now, scope = time.monotonic(), _room_session_scope(c)
        store.room_day_cache = {k: v for k, v in store.room_day_cache.items() if now - v[0] < 300}
        queries = {}
        for period in periods:
            q = copy.deepcopy(base)
            q.start, q.end = period if isinstance(period, tuple) else (period, period)
            queries[period] = q

        def key_for(period):
            return (scope, json.dumps(queries[period].__dict__, sort_keys=True, ensure_ascii=True))

        records = {p: {**store.room_day_cache[key_for(p)][1], "cached": True}
                   for p in periods if key_for(p) in store.room_day_cache}
        missing = [p for p in periods if p not in records]
        errors = {}
        if missing:
            try:
                # Warm once per route/session, not once per period or batch.
                warm = store.room_day_warm
                if not warm or warm[0] != scope or now - warm[1] >= 60:
                    c.enter_emap_app(rooms.APP)
                    c.save_session()
                    scope = _room_session_scope(c)
                    store.room_day_warm = (scope, time.monotonic())
                meta = rooms.cached_meta(c)
                profile_data = json.loads(profile.read_text(encoding="utf-8"))
                if not isinstance(profile_data, dict):
                    raise ValueError("请重新查询空教室以更新查询配置")
                # Construct independent clients before starting any workers.
                clients = {p: _room_query_client(c) for p in missing}
                def query(period):
                    found, _ = rooms.query_rooms(
                        clients[period], queries[period], profile, meta=copy.deepcopy(meta),
                        max_tries=1, require_complete=True, enter_app=False,
                        profile_data=copy.deepcopy(profile_data))
                    result = {"date": base.date, "complete": True,
                              "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                              # Full metadata lets time changes filter the complete
                              # inventories locally, including special-room rules.
                              "rooms": [{**r.to_dict(), "special": rooms.is_special_room(r)} for r in found]}
                    result["range" if isinstance(period, tuple) else "period"] = (
                        list(period) if isinstance(period, tuple) else period)
                    return result
                with ThreadPoolExecutor(max_workers=min(4, len(missing)), thread_name_prefix="room-day") as pool:
                    futures = {pool.submit(query, p): p for p in missing}
                    for future in as_completed(futures):
                        period = futures[future]
                        try:
                            result = future.result()
                        except jwxt.JwxtError as error:
                            errors[period] = error
                            continue
                        key = key_for(period)
                        if len(store.room_day_cache) >= 36 and key not in store.room_day_cache:
                            del store.room_day_cache[min(store.room_day_cache, key=lambda k: store.room_day_cache[k][0])]
                        store.room_day_cache[key] = (time.monotonic(), result)
                        records[period] = {**result, "cached": False}
            except jwxt.JwxtError as error:
                errors.update({p: error for p in missing if p not in records})
        ordered = [records[p] for p in periods if p in records]
        if errors:
            # Never save an older successful worker's cookies over expiry.
            store.room_day_warm = None
            error = next((e for e in errors.values() if isinstance(e, jwxt.LoginError)), next(iter(errors.values())))
            if not partial:
                raise error
            message, action = teaching_error("/api/rooms/day", error)
            return {"date": base.date, "records": ordered, "partial": True,
                    "failed_period": next(p for p in periods if p in errors),
                    "failed_periods": [p for p in periods if p in errors],
                    "error": message, "connection_action": action,
                    "session_expired": isinstance(error, jwxt.SessionExpiredError)}
        return {"date": base.date, "records": ordered, "partial": False}
    finally:
        store.room_day_lock.release()


def _cached(store: Store, name: str, fn):
    f = store.p(name)
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    c = _client()
    v = fn(c)
    if v:
        f.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    c.save_session()
    return v


def buildings_api(store: Store, body: dict) -> dict:
    from . import rooms
    campus = str(body.get("campus") or "")
    safe = re.sub(r"\W", "_", campus)
    return {"buildings": _cached(store, f"buildings2_{safe}.json", lambda c: rooms.list_buildings(c, campus))}


def room_types_api(store: Store) -> dict:
    from . import rooms
    return {"types": _cached(store, "room_types.json", lambda c: rooms.list_room_types(c))}


def room_fields_api(store: Store) -> dict:
    """「更多条件」：元数据里额外的检索字段（名称+标题）。"""
    from . import rooms
    return {"fields": _cached(store, "room_fields2.json",
                              lambda c: [{k: s[k] for k in ("name", "caption", "xtype")}
                                         for s in rooms.extra_search_fields(rooms.full_meta(c))])}


# ───────────────────────── OA 校内通知（只读本地缓存） ─────────────────────────

def _oa_url(u) -> str:
    """只保留指向 oa.jlu.edu.cn 的链接（相对路径补全），其它一律丢弃。"""
    import urllib.parse
    from . import oa
    u = str(u or "").strip()
    if not u:
        return ""
    full = urllib.parse.urljoin(oa.BASE + "/", u)
    pr = urllib.parse.urlparse(full)
    return full if pr.scheme in ("http", "https") and pr.hostname == "oa.jlu.edu.cn" else ""


def _oa_item(i: dict, full: bool = False) -> dict:
    out = {"id": str(i.get("id") or ""), "title": str(i.get("title") or ""), "time": str(i.get("time") or ""),
           "dept": str(i.get("dept") or ""), "top": bool(i.get("top")), "url": _oa_url(i.get("url"))}
    if full:
        atts = i.get("attachments")
        out["text"] = str(i.get("text") or "")
        out["attachments"] = [{"name": str(a.get("name") or "附件"), "url": _oa_url(a.get("url"))}
                              for a in (atts if isinstance(atts, list) else []) if isinstance(a, dict) and _oa_url(a.get("url"))]
    return out


def _oa_data(store: Store) -> dict:
    d = store._json("oa_notices.json", {})
    return d if isinstance(d, dict) else {}


def _oa_known(store: Store) -> dict:
    """栏目名：内置 179577 校内通知 + data/oa_channels.json（--probe 发现）+ 缓存里记下的栏目 + 学院。"""
    from . import oa
    f = store._json("oa_channels.json", {})
    f = {str(k): str(v) for k, v in f.items()} if isinstance(f, dict) else {}
    from . import college
    oa_ch = {**oa.KNOWN_CHANNELS, **f, **(_oa_data(store).get("channels") or {})}
    lead = {k: v for k, v in oa_ch.items() if not _OA_TAIL.search(v)}
    tail = {k: v for k, v in oa_ch.items() if _OA_TAIL.search(v)}
    # 顺序：OA 常规栏目 → 可抓取学院 → 医院、动科等（仅链接学院由偏好启用后再出现）
    return {**lead, **college.channels(), **tail}


import re as _re
_OA_TAIL = _re.compile(r"医院|动科|动物")


def _resolve(cat: str, known: dict) -> str:
    from . import college, oa
    cat = str(cat or "")
    if college.is_channel(cat) or college.is_link_channel(cat):
        return cat
    return oa.resolve_category(cat, known)


def oa_channels_api(store: Store) -> dict:
    """按用户偏好返回快捷栏信息源；未引导时仍返回全部已知栏目（兼容旧客户端/测试）。"""
    from . import college
    prefs = college.load_prefs(store.root)
    if prefs.get("onboarded"):
        channels = college.channels_for_prefs(store.root)
        return {"ok": True, "channels": channels, "prefs": prefs, "filtered": True}
    # 未引导：保持旧行为（全部栏目），并附上 prefs / catalog 元数据供前端弹选学院卡
    ch = _oa_known(store)
    return {"ok": True,
            "channels": [{"id": k, "name": v, "kind": ("college" if college.is_channel(k)
                          else "link" if college.is_link_channel(k) else "oa")}
                         for k, v in ch.items()],
            "prefs": prefs, "filtered": False}


def oa_catalog_api() -> dict:
    from . import college
    return {"ok": True, "catalog": college.catalog()}


def oa_prefs_api(store: Store) -> dict:
    from . import college
    return {"ok": True, "prefs": college.load_prefs(store.root)}


def oa_prefs_save_api(store: Store, body: dict) -> dict:
    from . import college
    body = body if isinstance(body, dict) else {}
    if body.get("apply_home"):
        prefs = college.apply_home_college(store.root, str(body.get("home_college") or ""))
    else:
        prefs = college.save_prefs(store.root, body)
    channels = college.channels_for_prefs(store.root)
    return {"ok": True, "prefs": prefs, "channels": channels}


def oa_notices_api(store: Store, q: dict) -> dict:
    """GET /api/oa/notices?category=&keyword=&limit= —— 只读 data/oa_notices.json，不访问 OA。"""
    from . import oa
    d = _oa_data(store)
    known = _oa_known(store)
    ch = _resolve(q.get("category", ""), known)
    kw = q.get("keyword", "").strip()
    try:
        limit = max(1, min(500, int(q.get("limit") or 500)))
    except ValueError:
        raise ValueError("limit 应为整数")
    from . import college
    extra = {}
    if college.is_link_channel(ch):
        d = college.load(store.root)
        st = (d.get("status") or {}).get(ch) or {}
        home = college.link_home(ch) or st.get("source_url", "")
        items = []
        extra = {"source": "college", "status": st.get("status") or "link_only",
                 "hint": st.get("hint") or "该学院官网暂不支持自动抓取列表，请打开官网查看通知公告。",
                 "source_url": home}
        d = {**d, "updated": st.get("at") or d.get("updated")}
    elif college.is_channel(ch):
        d = college.load(store.root)
        src, _ = college._split(ch)
        items = [{**_oa_item(i), "url": college.safe_url(i.get("url"), src["host"])}
                 for i in ((d.get("channels_items") or {}).get(ch) or []) if isinstance(i, dict)]
        st = (d.get("status") or {}).get(ch) or {}
        extra = {"source": "college", "status": st.get("status", ""), "hint": st.get("hint", ""),
                 "source_url": college.list_url(ch)}
        d = {**d, "updated": st.get("at") or d.get("updated")}
    else:
        items = [_oa_item(i) for i in ((d.get("channels_items") or {}).get(ch) or []) if isinstance(i, dict)]
    if kw:
        items = [i for i in items if kw in i["title"] or kw in i["dept"]]
    items.sort(key=lambda i: (i["top"], i["time"], i["id"]), reverse=True)
    items = items[:limit]
    from . import college as _col
    cname = known.get(ch) or oa.KNOWN_CHANNELS.get(ch) or _col.link_channels().get(ch) or _col.channels().get(ch) or ""
    return {"ok": True, "channel": ch, "channel_name": cname,
            "count": len(items), "fetched_at": d.get("updated"), "items": items, **extra}


def oa_notice_api(store: Store, nid: str) -> Optional[dict]:
    """GET /api/oa/notice?id= —— 单条（含本地已缓存的正文/附件，若有）。"""
    for lst in ((_oa_data(store).get("channels_items") or {}).values()):
        for i in lst or []:
            if isinstance(i, dict) and str(i.get("id")) == nid:
                return {"ok": True, "item": _oa_item(i, full=True)}
    from . import college
    i = college.find(store.root, nid)
    if i:
        src, _ = college._split(i.get("channel", ""))
        return {"ok": True, "item": {**_oa_item(i, full=True), "url": college.safe_url(i.get("url"), src["host"]),
                                     "source": "college"}}
    return None


def oa_refresh_api(store: Store, body: dict) -> dict:
    """POST /api/oa/refresh —— 只抓第 1 页（max_pages=1），写回本地缓存。"""
    from . import oa
    from . import college
    ch = _resolve(str(body.get("category") or ""), _oa_known(store))
    if college.is_link_channel(ch) or college.is_channel(ch):
        college.save(store.root, college.fetch(ch))
        return oa_notices_api(store, {"category": ch})
    client = jwxt.JwxtClient()
    has = bool(client.load_session())
    res = oa.fetch_notices(client, ch, limit=30, max_pages=1)
    oa.save(store.root, res)
    if has:
        client.save_session()
    return oa_notices_api(store, {"category": ch})


def vpn_portal_url() -> str:
    """校园 WebVPN 入口（campus_links 里的 vpn，找不到则用默认）。"""
    try:
        for x in campus_links_api().get("links") or []:
            if isinstance(x, dict) and x.get("id") == "vpn" and _link_ok(x.get("url")):
                return str(x["url"])
    except Exception:  # noqa: BLE001
        pass
    return "https://vpn.jlu.edu.cn/"


LINK_FIELDS = ("id", "name", "icon", "url", "purpose", "login", "campus_only", "vpn_url")


def _link_ok(u) -> bool:
    import urllib.parse
    try:
        p = urllib.parse.urlsplit(str(u or ""))
    except ValueError:
        return False
    h = (p.hostname or "").lower()
    return p.scheme == "https" and (h == "jlu.edu.cn" or h.endswith(".jlu.edu.cn")) and not p.username


def _vpn_rewriter():
    """露娜 #18 的 campus.vpn_url（WebVPN 主机 AES-CFB 加密）；还没合进来时返回 None。"""
    try:
        from .campus import vpn_url  # type: ignore
    except Exception:  # noqa: BLE001 — 模块不存在或缺 cryptography 都当作暂不支持
        return None
    return vpn_url


def campus_links_api(override: Optional[Path] = None) -> dict:
    """GET /api/links —— 内置 data/campus_links.json + 可选用户覆盖（config_dir/campus_links.json）。

    覆盖规则：同 id 合并字段；"hidden": true 隐藏；新 id 追加。只返回 https://*.jlu.edu.cn 链接。
    """
    base = json.loads((Path(__file__).parent / "data" / "campus_links.json").read_text(encoding="utf-8"))
    items = {x["id"]: dict(x) for x in base.get("links", [])}
    order = list(items)
    override = override or jwxt.config_dir() / "campus_links.json"
    src, err = "builtin", None
    if override.exists():
        try:
            o = json.loads(override.read_text(encoding="utf-8"))
            for x in (o.get("links", []) if isinstance(o, dict) else o):
                if not isinstance(x, dict) or not x.get("id"):
                    continue
                i = str(x["id"])
                if i not in items:
                    order.append(i)
                items[i] = {**items.get(i, {}), **x}
            src = "override"
        except (json.JSONDecodeError, OSError, AttributeError, TypeError) as e:
            err = f"覆盖文件无效，已忽略：{e}"
    out, dropped = [], 0
    rewrite = _vpn_rewriter()
    for i in order:
        x = items[i]
        if x.get("hidden"):
            continue
        if not _link_ok(x.get("url")):
            dropped += 1
            continue
        y = {k: x[k] for k in LINK_FIELDS if k in x}
        if "vpn_url" in y and not _link_ok(y["vpn_url"]):
            y.pop("vpn_url")
        y["campus_only"] = bool(y.get("campus_only"))
        if y["id"] == "jwxt":
            y["campus_only"] = True
        if y["id"] == "xsxk":
            # This public service must not inherit an obsolete VPN override.
            y["campus_only"] = False
            y.pop("vpn_url", None)
        if y["campus_only"] and "vpn_url" not in y and rewrite is not None:
            try:
                v = rewrite(y["url"])
            except Exception:  # noqa: BLE001
                v = None
            if v and v != y["url"] and _link_ok(v):
                y["vpn_url"] = v
        out.append(y)
    r = {"ok": True, "links": out, "source": src, "dropped": dropped}
    if err:
        r["warning"] = err
    return r


def make_handler(store: Store, login: Optional[LoginFlow] = None, token: Optional[str] = None):
    from . import webvpn
    login = login or webvpn.direct_login_flow()
    vpn_login = webvpn.login_flow()
    token = token or load_or_create_token()

    class H(BaseHTTPRequestHandler):
        server_version = "SuperJLU-UI"
        auth_token = token

        def log_message(self, fmt, *args):  # 安静
            pass

        def _sso_jump(self):
            """GET /api/sso/jump?id=&n= —— 同源 nonce 校验后 302 到带 ST 的目标；失败退回普通地址 ?sso=failed。"""
            import hmac, urllib.parse
            from . import sso
            q = {k: v[0] for k, v in urllib.parse.parse_qs(self.path.partition("?")[2]).items()}
            sid = q.get("id", "")
            if not hmac.compare_digest(q.get("n", ""), SSO_NONCE):
                return self._send(403, b"bad nonce", "text/plain")
            site = (self.headers.get("Sec-Fetch-Site") or "").lower()
            if site and site not in ("same-origin", "none"):
                return self._send(403, b"cross-site", "text/plain")
            if not sso.capable(sid):
                return self._send(404, b"not sso-capable", "text/plain")
            loc, _ok = sso.jump_url(sid)
            if not sso._jlu_https(loc):
                return self._send(502, b"bad target", "text/plain")
            return self._send(302, b"", "text/plain", {"Location": loc, "Referrer-Policy": "no-referrer"})

        def _host_ok(self) -> bool:
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ALLOWED_HOSTS

        def _gate(self) -> bool:
            """Host 校验 + 本地令牌；返回 True 表示已经回应（拒绝，或种 Cookie 后跳转）。"""
            import urllib.parse
            if not self._host_ok():
                self._send(403, b"forbidden", "text/plain")
                return True
            u = urllib.parse.urlsplit(self.path)
            if u.path in _PUBLIC_PATHS:
                return False
            t = urllib.parse.parse_qs(u.query).get("t", [""])[0]
            if self.command == "GET" and u.path in _PAGE_PATHS and t \
                    and _hmac.compare_digest(t.encode(), token.encode()):
                cookie = f"{TOKEN_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000"
                self._send(302, b"", "text/plain",
                           {"Location": "/", "Set-Cookie": cookie, "Referrer-Policy": "no-referrer"})
                return True
            if _token_ok(self.headers, token):
                return False
            if self.command == "GET" and u.path in _PAGE_PATHS:
                self._send(401, LOCKED_PAGE.encode(), "text/html; charset=utf-8",
                           {"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})
            else:
                self._json({"ok": False, "auth_required": True,
                            "error": "未授权的本地请求：请从 SuperJLU 重新打开界面"}, 401)
            return True

        def _send(self, code: int, body: bytes, ctype: str, extra: Optional[dict] = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            limit = 7_500_000 if self.path == "/api/grades/import" else 1_000_000
            if n < 0 or n > limit:
                raise ValueError("请求过大")
            return json.loads(self.rfile.read(n) or b"{}")

        def _oa_sub(self, method: str) -> bool:
            # OA 订阅接口（oa_subscribe.api）：GET/POST/DELETE /api/oa/subscriptions[/<id>]
            from urllib.parse import parse_qs, urlsplit
            from . import oa_subscribe
            u = urlsplit(self.path)
            if not u.path.startswith("/api/oa/subscriptions"):
                return False
            try:
                body = self._body() if method == "POST" else None
            except ValueError as e:
                self._json({"ok": False, "error": str(e)}, 400)
                return True
            code, obj = oa_subscribe.api(method, u.path, parse_qs(u.query), body, store.root)
            self._json(obj, code)
            return True

        def do_DELETE(self):
            if self._gate():
                return
            path = self.path.split("?")[0]
            if path.startswith("/api/login/accounts/"):
                import urllib.parse
                u = urllib.parse.unquote(path[len("/api/login/accounts/"):])
                ok = login.delete_account(u)
                return self._json({"ok": ok, "accounts": login.accounts()}, 200 if ok else 404)
            if not self._oa_sub("DELETE"):
                self._send(404, b"not found", "text/plain")

        def do_GET(self):
            if self._gate():
                return
            path = self.path.split("?")[0]
            if self._oa_sub("GET"):
                return
            if path in ("/", "/index.html"):
                from . import ui_prefs
                import html as _html
                from . import update_check
                page = PAGE.replace('<span id="upd-v"></span>', '<span id="upd-v">' + _html.escape(update_check.current_version()) + '</span>', 1)
                page = page.replace("<script>/* 首帧前应用主题", ui_prefs.inline_script(store.root) + "<script>/* 首帧前应用主题", 1)
                return self._send(200, page.encode(), "text/html; charset=utf-8",
                                  {"Content-Security-Policy": "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'"})
            if path in ("/favicon.svg", "/favicon.ico"):  # SuperJLU 官方标志
                from importlib import resources
                data = resources.files("jlu_toolkit").joinpath("data", path[1:]).read_bytes()
                ctype = "image/svg+xml" if path.endswith(".svg") else "image/x-icon"
                return self._send(200, data, ctype)
            if path == "/api/prefs":  # 界面偏好（主题等），落盘防止端口变化丢失
                from . import ui_prefs
                return self._json({"ok": True, "prefs": ui_prefs.load(store.root)})
            if path == "/api/sessions":  # 各校园站点会话状态（只读本地）
                from . import sessions
                return self._json(sessions.all_status())
            if path == "/api/session":
                # 会话状态 + 离线缓存信息（offline/cached_at），供前端显示「请重新登录」/「离线数据」；只读本地
                return self._json({**jwxt.session_status(), **cache_info(store)})
            if path == "/api/network/state":
                from . import webvpn
                return self._json(webvpn.state())
            if path == "/api/network/device":
                # 只读：Android 默认网络是 Wi-Fi 还是移动数据；桌面端恒为 unknown、无提示
                from . import netstatus
                info = netstatus.status()
                return self._json({"ok": True, **info, "direct_hint": netstatus.direct_hint(info)})
            if path == "/api/oa/webvpn":
                # Navigation only: never forwards app cookies or user input.
                self.send_response(302)
                self.send_header("Location", "https://vpn.jlu.edu.cn/")
                self.end_headers()
                return
            if path.startswith("/api/oa/"):
                import urllib.parse
                q = {k: v[0] for k, v in urllib.parse.parse_qs(self.path.partition("?")[2]).items()}
                try:
                    if path == "/api/oa/notices":
                        return self._json(oa_notices_api(store, q))
                    if path == "/api/oa/channels":
                        return self._json(oa_channels_api(store))
                    if path == "/api/oa/catalog":
                        return self._json(oa_catalog_api())
                    if path == "/api/oa/prefs":
                        return self._json(oa_prefs_api(store))
                    if path == "/api/oa/notice":
                        r = oa_notice_api(store, q.get("id", ""))
                        return self._json(r or {"ok": False, "error": "本地没有这条通知"}, 200 if r else 404)
                except ValueError as e:
                    return self._json({"ok": False, "error": str(e)}, 400)
            if path == "/api/update":  # 只读：查询公开发布页是否有新版本，不强制更新
                from . import update_check
                from urllib.parse import parse_qs, urlsplit
                q = parse_qs(urlsplit(self.path).query)
                if q.get("local") == ["1"]:  # 关闭自动检查时只显示本机版本，不联网
                    return self._json(update_check.local())
                return self._json(update_check.check(force=q.get("force") == ["1"]))
            if path == "/api/links":
                from . import sso
                j = campus_links_api()
                for x in j.get("links") or []:
                    if isinstance(x, dict) and sso.capable(x.get("id", "")):
                        x["sso_url"] = "/api/sso/jump?id=" + x["id"] + "&n=" + SSO_NONCE
                return self._json(j)
            if path == "/api/sso/jump":
                return self._sso_jump()
            if path == "/api/login/accounts":  # 只返回账号名，绝不返回密码
                return self._json({"ok": True, "accounts": login.accounts()})
            if path == "/api/login":
                return self._json({"ok": True, "saved_username": login.saved_username(),
                                   "accounts": login.accounts(),
                                   "session": jwxt.session_status()})
            if path == "/api/data":
                from urllib.parse import parse_qs
                source = parse_qs(self.path.partition("?")[2]).get("grade_source", ["jwxt"])[0]
                return self._json(store.snapshot("import" if source == "import" else "jwxt"))
            if path == "/api/schedule/overlay":  # 备份导出：只含同学自己的修改
                return self._send(200, json.dumps(store.overlay_doc(), ensure_ascii=False, indent=1).encode(),
                                  "application/json; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="superjlu-schedule-edits.json"'})
            if path == "/api/grades/colleges":
                links = json.loads((Path(__file__).parent / "data" / "grade_colleges.json").read_text(encoding="utf-8"))
                return self._json({"ok": True, "links": [x for x in links["links"] if _link_ok(x["url"])]})
            if path == "/api/ics":
                fm = store.first_monday()
                if not fm:
                    return self._json({"error": "缺少开学日期：请先刷新（自动读取校历）或在设置里手动填写"}, 400)
                body = core.to_ics(store.courses(), fm, store.periods() or None).encode()
                return self._send(200, body, "text/calendar; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="jlu-schedule.ics"'})
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if self._gate():
                return
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._send(403, b"forbidden", "text/plain")
            if self._oa_sub("POST"):
                return
            try:
                body = self._body()
                if self.path == "/api/prefs":
                    from . import ui_prefs
                    return self._json({"ok": True, "prefs": ui_prefs.update(store.root, body.get("set"), body.get("remove"))})
                elif self.path == "/api/schemes":
                    store.save_scheme(body.get("name", ""), body.get("include") or [], body.get("base"),
                                      body.get("grade_source", "jwxt"))
                elif self.path == "/api/grades/import":
                    store.import_grades(body.get("filename", ""), body.get("data", ""))
                    return self._json({"ok": True, **store.snapshot("import")})
                elif self.path == "/api/grades/source":
                    source = "import" if body.get("grade_source") == "import" else "jwxt"
                    return self._json({"ok": True, **store.snapshot(source)})
                elif self.path == "/api/grades/refresh":
                    return self._json({"ok": True, "grade_result": refresh_grades_from_jwxt(store, bool(body.get("auto"))),
                                       **store.snapshot()})
                elif self.path == "/api/schemes/delete":
                    store.delete_scheme(body.get("name", ""))
                elif self.path == "/api/schedule/overlay":
                    store.overlay_action(body)
                    return self._json({"ok": True, **store._schedule_snapshot()})
                elif self.path == "/api/settings":
                    store.save_settings(body)
                elif self.path == "/api/rooms":
                    return self._json({"ok": True, **rooms_api(store, body)})
                elif self.path == "/api/rooms/day":
                    return self._json({"ok": True, **room_day_api(store, body)})
                elif self.path == "/api/rooms/day-period":
                    return self._json({"ok": True, **room_day_period_api(store, body)})
                elif self.path == "/api/network/check":
                    from . import connectivity
                    return self._json(connectivity.check_all())
                elif self.path == "/api/network/vpn":
                    from . import webvpn
                    return self._json(webvpn.connect())
                elif self.path == "/api/network/direct":
                    from . import webvpn
                    webvpn.set_mode("direct")
                    return self._json(webvpn.state())
                elif self.path == "/api/rooms/buildings":
                    return self._json({"ok": True, **buildings_api(store, body)})
                elif self.path == "/api/rooms/types":
                    return self._json({"ok": True, **room_types_api(store)})
                elif self.path == "/api/rooms/fields":
                    return self._json({"ok": True, **room_fields_api(store)})
                elif self.path == "/api/rooms/campuses":
                    return self._json({"ok": True, **campuses_api(store)})
                elif self.path == "/api/login/start":
                    try:
                        return self._json({"ok": True, **login.start(body.get("username", ""), body.get("password", ""),
                                                                     body.get("remember", True) is not False)})
                    except jwxt.NetworkError as e:
                        from . import netstatus
                        return self._json({
                            "ok": False,
                            "error": netstatus.with_direct_hint(str(e)),
                            "network": True,
                            "vpn_hint": True,
                            "vpn_url": vpn_portal_url(),
                        }, 502)
                elif self.path == "/api/oa/prefs":
                    return self._json(oa_prefs_save_api(store, body))
                elif self.path == "/api/login/send_code":
                    return self._json({"ok": True, **login.send_code()})
                elif self.path == "/api/login/verify":
                    return self._json({"ok": True, **login.verify(wechat_code=body.get("wechat_code", ""))})
                elif self.path == "/api/login/cancel":
                    return self._json({"ok": True, **login.cancel()})
                elif self.path == "/api/vpn/login/start":
                    return self._json({"ok": True, **vpn_login.start(body.get("username", ""), body.get("password", ""),
                                                                     body.get("remember", True) is not False)})
                elif self.path == "/api/vpn/login/send_code":
                    return self._json({"ok": True, **vpn_login.send_code()})
                elif self.path == "/api/vpn/login/verify":
                    return self._json({"ok": True, **vpn_login.verify(wechat_code=body.get("wechat_code", ""))})
                elif self.path == "/api/vpn/login/cancel":
                    return self._json({"ok": True, **vpn_login.cancel()})
                elif self.path == "/api/oa/refresh":
                    try:
                        return self._json(oa_refresh_api(store, body))
                    except jwxt.NetworkError as e:
                        from . import sessions, webvpn
                        app_vpn = webvpn.mode() == "webvpn" and bool(sessions.load_cookies("vpn"))
                        if app_vpn:
                            err = (f"学校 OA 经应用内 WebVPN 暂不可用；也可在浏览器打开学校 WebVPN 查看原站。"
                                   f"学院通知可独立更新。{e}")
                        else:
                            err = (f"学校 OA 直连暂不可用；校外可在「更多 → 登录」选择「校外 WebVPN」后重试，"
                                   f"或在浏览器打开学校 WebVPN 查看原站。学院通知可独立更新。{e}")
                        return self._json({"ok": False, "error": err,
                                           "offline": True, "error_kind": e.kind,
                                           "campus_required": False, "browser_vpn_supported": True,
                                           "app_vpn_supported": app_vpn}, 502)
                    except jwxt.SessionExpiredError:
                        raise
                    except jwxt.LoginError as e:
                        return self._json({"ok": False, "error": str(e), "login_needed": True}, 400)
                elif self.path == "/api/session/keepalive":  # App 前台约 15 分钟调用一次
                    from . import sessions
                    r = sessions.keepalive()
                    if r["session"].get("session_expired"):
                        raise jwxt.SessionExpiredError()
                    return self._json({**r, **cache_info(store)})
                elif self.path == "/api/refresh":
                    # 部分模块已写入本地时也要把 snapshot 带回，避免 UI 卡在空状态只能重进
                    try:
                        result = refresh_from_jwxt(store)
                        return self._json({"ok": True, "result": result, **store.snapshot()})
                    except jwxt.LoginError as e:
                        partial = getattr(e, "partial", None)
                        body = {
                            "ok": False,
                            "error": str(e),
                            "session_expired": True,
                            "site": getattr(e, "site", "jwxt"),
                            "result": partial,
                            **store.snapshot(),
                        }
                        return self._json(body, 401)
                else:
                    return self._send(404, b"not found", "text/plain")
                return self._json({"ok": True, **store.snapshot(body.get("grade_source", "jwxt"))})
            except jwxt.NetworkError as e:
                message, connection_action = teaching_error(self.path, e)
                return self._json({"ok": False, "error": message, "error_kind": e.kind,
                                   "connection_action": connection_action,
                                   "network_error": True, "can_connect_vpn":e.can_connect_vpn,
                                   **cache_info(store)}, 502)
            except jwxt.SessionExpiredError as e:
                return self._json({"ok": False, "error": str(e), "session_expired": True,
                                   "site": getattr(e, "site", "jwxt")}, 401)
            except jwxt.JwxtError as e:
                message, connection_action = teaching_error(self.path, e)
                return self._json({"ok": False, "error": message,
                                   "connection_action": connection_action}, 400)
            except ValueError as e:
                return self._json({"ok": False, "error": str(e)}, 400)
            except Exception as e:  # noqa: BLE001
                import logging
                logging.getLogger("superjlu.desktop").exception("POST %s 失败", self.path)
                return self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    return H


def seed_demo(root: Path) -> None:
    ex_dir = Path(__file__).resolve().parent / "data" / "demo"
    for n in ("schedule.csv", "grades.csv", "exams.csv"):
        src = ex_dir / n
        if src.exists():
            shutil.copy(src, root / n)
    for n in ("calendar.json", "periods.json", "official_gpa.json", "completion.json", "plan_courses.json"):
        src = ex_dir / n
        if src.exists():
            shutil.copy(src, root / n)
    store = Store(root)
    keys = [f"{g.term}|{g.name}" for g in store.grades()
            if not g.name.startswith(("体育", "军事", "创新"))]
    store.save_scheme("保研", keys)


def serve(port: int = 8765, root: Optional[Path] = None, open_browser: bool = False) -> None:
    store = Store(root or data_dir())
    handler = make_handler(store)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = launch_url(f"http://127.0.0.1:{httpd.server_address[1]}/", handler.auth_token)
    print(f"SuperJLU 界面已启动：{url}\n数据目录：{store.root}\n按 Ctrl+C 退出。", flush=True)
    if open_browser:
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
