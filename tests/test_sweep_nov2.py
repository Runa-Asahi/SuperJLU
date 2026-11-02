"""2026-11-02 bug sweep：缓存命中时的本学期已选课、500 文案、过期的重算成功提示。"""
import json

from jlu_toolkit import academic, secure_store, ui
from jlu_toolkit.core import Course
from jlu_toolkit.ui_page import PAGE


def test_cached_sync_still_adds_newly_selected_courses(monkeypatch, tmp_path):
    row = {"XH": "u", "PYFADM": "p", "CZSJ": "T1"}
    monkeypatch.setattr(academic, "summary", lambda c: dict(row))
    monkeypatch.setattr(academic.meta, "fetch_completion",
                        lambda *a, **k: {"required": 1, "earned": 0, "groups": [], "calculated_at": "T1"})
    monkeypatch.setattr(academic.plan, "fetch_plan", lambda *a, **k: {
        "courses": [{"code": "A", "name": "高数", "status": "未修", "status_code": "todo", "group_code": "G"}],
        "count": 1, "source": {}})
    t = academic.Sync(object(), tmp_path); t.completion(); t.curriculum()
    now = [Course("高数", "", "", 1, 1, 2, [1]), Course("西方戏剧鉴赏", "", "", 3, 9, 10, [1], kch="YS3")]
    monkeypatch.setattr(academic.plan, "fetch_plan", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no fetch")))
    t = academic.Sync(object(), tmp_path, courses_now=now)
    assert t.completion()["cached"] is True
    r = t.curriculum()
    assert r["cached"] is True and r["added"] == 2
    by = {c["name"]: c for c in secure_store.load_json(tmp_path / "plan_courses.json")["courses"]}
    assert by["高数"]["status"] == "在修" and by["西方戏剧鉴赏"]["status"] == "在修"
    # 再次命中不会重复添加
    t = academic.Sync(object(), tmp_path, courses_now=now); t.completion()
    assert "added" not in t.curriculum()


def test_unexpected_server_error_has_no_technical_text():
    import inspect
    src = inspect.getsource(ui.make_handler)
    assert 'f"{type(e).__name__}: {e}"' not in src
    assert "出了点问题，请稍后再试" in src


def test_full_refresh_dismisses_old_recalc_result():
    assert 'academicJob={state:"idle",dismissed:true}' in PAGE
    assert "academicJob.dismissed&&" in PAGE
