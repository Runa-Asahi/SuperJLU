"""一键同步：用已保存会话把课表/成绩/考试/校历/节次/官方绩点/学业完成写入数据目录。

返回的摘要只含条数、成功/失败与非个人信息（学期代码、开学日期、节次数），
可安全打印或贴给他人；个人数值（绩点、学分、成绩）只写入本地文件。
"""
from __future__ import annotations

import json
from pathlib import Path

from . import exams as ex, jwxt, meta


def _wjson(path: Path, obj) -> None:
    from .endpoints import scrub
    from . import secure_store
    if path.name in secure_store.PERSONAL_CACHES:
        secure_store.save_json(path, scrub(obj))
        return
    path.write_text(json.dumps(scrub(obj), ensure_ascii=False, indent=1), encoding="utf-8")
    secure_store.touch_cache_meta(path)


def adjustments_enabled(root: Path) -> bool:
    """设置「自动应用调课/停课」，默认开（2026-10 已用吉大真实账号验证接口）。"""
    try:
        v = json.loads((root / "settings.json").read_text(encoding="utf-8")).get("apply_adjustments")
    except (OSError, ValueError, AttributeError):
        v = None
    return v is None or bool(v)


def _sync_adjustments(client, root: Path, term: str, courses: list) -> dict:
    """放在所有步骤之后单独跑：任何失败（含跳统一认证）都只记一笔，不算会话过期、不影响已同步的数据，
    并保留上次成功取到的调课结果。"""
    import datetime as dt
    from . import adjust
    try:
        adjs = adjust.fetch_adjustments(client, term)
        _, notes = adjust.apply_adjustments(courses, adjs)
    except Exception as e:  # noqa: BLE001
        return {"ok": True, "available": False, "error": type(e).__name__}
    _wjson(root / "schedule_adjustments.json", {
        "term": term, "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
        "items": [a.to_dict() for a in adjs], "changes": notes})
    return {"ok": True, "rows": len(adjs), "applied": sum(1 for n in notes if not n["skipped"])}


def sync_all(client: "jwxt.JwxtClient", root: Path, term: str | None = None, *, force_academic: bool = False) -> dict:
    """逐步同步；某步 LoginError 时停止后续步骤，但已成功写入的文件保留。

    失败时把已完成摘要挂到异常的 ``partial`` 上，方便 UI 仍展示刚刷到的课表等。
    """
    root.mkdir(parents=True, exist_ok=True)
    s: dict = {}
    login_err: jwxt.LoginError | None = None

    def step(name, fn):
        nonlocal login_err
        if login_err is not None:
            s[name] = {"ok": False, "error": "skipped: session expired", "skipped": True}
            return
        try:
            s[name] = fn()
        except jwxt.LoginError as e:
            s[name] = {"ok": False, "error": str(e)[:200], "login_needed": True}
            login_err = e
        except meta.Unavailable as e:
            s[name] = {"ok": True, "available": False, "note": str(e)[:300]}
        except (jwxt.JwxtError, ValueError, KeyError) as e:
            s[name] = {"ok": False, "error": str(e)[:200]}
        except Exception as e:  # noqa: BLE001 — 单个模块的意外数据不能拖垮整次刷新
            import logging
            logging.getLogger("superjlu.sync").exception("同步步骤 %s 失败", name)
            s[name] = {"ok": False, "error": f"读取出错（{type(e).__name__}）"}

    term = term or client.current_semester()
    s["term"] = term

    courses_cache: list = []

    def _courses():
        cs = client.fetch_schedule(term)
        courses_cache.extend(cs)
        # schedule.csv 只放教务原课表；调停课单独存，读取时再合并（设置里可随时开关、即时生效）
        jwxt.export_courses_csv(cs, str(root / "schedule.csv"))
        # 记下课表所属学期：个人课表修改按学期分开存（见 overlay.py）
        _wjson(root / "schedule_meta.json", {"term": term})
        return {"ok": True, "count": len(cs)}

    grades_cache: list = []

    def _grades():
        gs = client.fetch_grades()
        grades_cache.extend(gs)
        jwxt.export_grades_csv(gs, str(root / "grades.csv"))
        return {"ok": True, "count": len(gs),
                "with_jw_point": sum(1 for g in gs if getattr(g, "jw_point", None) is not None)}

    def _exams():
        es = client.fetch_exams(term)
        ex.export_exams_csv(es, str(root / "exams.csv"))
        return {"ok": True, "count": len(es)}

    def _cal():
        c = meta.fetch_calendar(client, term)
        _wjson(root / "calendar.json", c)
        return {"ok": True, **c}

    def _periods():
        p = meta.fetch_periods(client)
        _wjson(root / "periods.json", p)
        return {"ok": True, "count": len(p), "first": p.get("1"), "last_section": max(map(int, p))}

    def _gpa():
        try:
            g = meta.fetch_official_gpa(client, grades=grades_cache)
        except meta.Unavailable as e:
            _wjson(root / "official_gpa.json", {"available": False, "note": str(e)[:300], "items": []})
            raise
        _wjson(root / "official_gpa.json", g)
        return {"ok": True, "source": g.get("source"), "fields": [i["key"] for i in g["items"]]}

    from .academic import Sync as AcademicSync
    academic_sync = AcademicSync(client, root, force=force_academic,
                                 grades=grades_cache, courses_now=courses_cache)

    def _prog():
        return academic_sync.completion()

    def _plan():
        return academic_sync.curriculum()

    for name, fn in (("schedule", _courses), ("grades", _grades), ("exams", _exams),
                     ("calendar", _cal), ("periods", _periods),
                     ("official_gpa", _gpa), ("completion", _prog), ("plan_courses", _plan)):
        step(name, fn)
    if login_err is None and adjustments_enabled(root):
        s["schedule_adjustments"] = _sync_adjustments(client, root, term, courses_cache)
    try:
        client.save_session()
    except Exception:  # noqa: BLE001
        pass
    if login_err is not None:
        login_err.partial = s  # type: ignore[attr-defined]
        raise login_err
    return s
