"""调停课合并原型：全部用模拟数据，不访问教务。"""
import json
from unittest import mock

from jlu_toolkit import adjust, core, jwxt, sync


def C(name, wd, s, e, weeks, loc="经信A101", teacher="王五"):
    return core.Course(name, teacher, loc, wd, s, e, list(weeks))


BASE = [C("高等数学", 1, 1, 2, range(1, 17)), C("大学英语", 3, 3, 4, range(1, 17), loc="外语楼201")]


def row(**kw):
    r = {"KCM": "高等数学", "JXBID": "x", "SQSJ": "2026-10-10 09:00:00"}
    r.update(kw)
    return r


def test_parse_weeks_text():
    assert adjust.parse_weeks_text("1-4周") == [1, 2, 3, 4]
    assert adjust.parse_weeks_text("第3周") == [3]
    assert adjust.parse_weeks_text("3，5、7周") == [3, 5, 7]
    assert adjust.parse_weeks_text("1-7(单)") == [1, 3, 5, 7]
    assert adjust.parse_weeks_text("1-6周（双周）") == [2, 4, 6]
    assert adjust.parse_weeks_text("0011") == [3, 4]
    assert adjust.parse_weeks_text("") == [] and adjust.parse_weeks_text("待定") == []


def test_row_kinds():
    move = adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周",
                                        XSKXQ="5", XKSJC="5", XJSJC="6", XZCMC="8周", XJASDM_DISPLAY="经信B202"))
    assert move.kind == "调课" and move.old.weeks == (8,) and move.new.weekday == 5
    assert move.new_location == "经信B202"
    assert adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")).kind == "停课"
    assert adjust.row_to_adjustment(row(XSKXQ=6, XKSJC=1, XJSJC=2, XZCMC="9周")).kind == "补课"
    room = adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="5-6周", XJASMC="逸夫楼301"))
    assert room.kind == "换教室" and room.new == room.old
    assert adjust.row_to_adjustment(row(TKLXDM_DISPLAY="调课", SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")).kind == "调课"
    assert adjust.row_to_adjustment({"KCM": "x"}) is None
    assert adjust.row_to_adjustment({"SKXQ": 1}) is None


def test_move_course_and_idempotent():
    a = adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周",
                                     XSKXQ=5, XKSJC=5, XJSJC=6, XZCMC="8周"))
    out, notes = adjust.apply_adjustments(BASE, [a])
    math = [c for c in out if c.name == "高等数学"]
    assert [c.weeks for c in math if c.weekday == 1] == [[w for w in range(1, 17) if w != 8]]
    added = [c for c in math if c.weekday == 5]
    assert len(added) == 1 and added[0].weeks == [8] and added[0].location == "经信A101"
    assert added[0].teacher == "王五"
    assert notes[0]["removed_weeks"] == [8] and notes[0]["added_weeks"] == [8]
    # 再合并一次（或教务课表本身已含调整）：不重复
    again, notes2 = adjust.apply_adjustments(out, [a])
    assert sorted((c.weekday, c.weeks) for c in again) == sorted((c.weekday, c.weeks) for c in out)
    assert notes2[0]["skipped"]
    # 入参未被修改
    assert BASE[0].weeks == list(range(1, 17))


def test_cancel_makeup_and_room():
    cancel = adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="1-16周"))
    out, _ = adjust.apply_adjustments(BASE, [cancel])
    assert all(c.name != "高等数学" for c in out)  # 整门停课后空课被丢弃
    makeup = adjust.row_to_adjustment(row(KCM="大学英语", XSKXQ=7, XKSJC=1, XJSJC=2, XZCMC="10周"))
    out, _ = adjust.apply_adjustments(BASE, [makeup])
    sun = [c for c in out if c.weekday == 7]
    assert sun[0].location == "外语楼201" and sun[0].weeks == [10]
    room = adjust.row_to_adjustment(row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="5-6周", XJASMC="逸夫楼301"))
    out, _ = adjust.apply_adjustments(BASE, [room])
    moved = [c for c in out if c.location == "逸夫楼301"]
    assert len(moved) == 1 and moved[0].weeks == [5, 6] and moved[0].weekday == 1
    assert core.courses_on(out, 5, 1)[0].location == "逸夫楼301"
    assert core.courses_on(out, 4, 1)[0].location == "经信A101"


def test_unmatched_old_slot_is_skipped():
    a = adjust.row_to_adjustment(row(KCM="不存在的课", SKXQ=2, KSJC=1, JSJC=2, ZCMC="3周"))
    out, notes = adjust.apply_adjustments(BASE, [a])
    assert out == BASE and notes[0]["skipped"]


def _client(rows):
    cl = mock.Mock()
    cl.fetch_schedule.return_value = list(BASE)
    cl.current_semester.return_value = "2026-2027-1"
    def post(path, form, ref):
        if path == adjust.EP_ADJUSTED:
            return {"code": "0", "datas": {"xsdkkc": {"rows": rows}}}
        raise jwxt.JwxtError("mock: 其他接口不可用")
    cl._post_form.side_effect = post
    for m in ("fetch_grades", "fetch_exams", "post_raw", "_request"):
        getattr(cl, m).side_effect = jwxt.JwxtError("mock")
    return cl


def test_fetch_adjustments_parses_rows():
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周"), {"bad": 1}])
    adjs = adjust.fetch_adjustments(cl, "2026-2027-1")
    assert len(adjs) == 1
    path, form, _ = cl._post_form.call_args[0]
    assert path == adjust.EP_ADJUSTED and form["XNXQDM"] == "2026-2027-1"


def _run_sync_schedule(cl, tmp_path):
    # 只跑课表一步：其余步骤在 mock 上会抛异常，由 sync 自行记录失败
    s = sync.sync_all(cl, tmp_path, "2026-2027-1")
    return s["schedule"]


def test_sync_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPERJLU_APPLY_ADJUSTMENTS", raising=False)
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")])
    s = _run_sync_schedule(cl, tmp_path)
    assert "adjustments" not in s
    assert all(c[0] != adjust.EP_ADJUSTED for c, _ in cl._post_form.call_args_list)
    assert not (tmp_path / "schedule_adjustments.json").exists()


def test_sync_flag_applies_and_failure_is_harmless(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPERJLU_APPLY_ADJUSTMENTS", "1")
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")])
    s = _run_sync_schedule(cl, tmp_path)
    assert s["adjustments"] == {"rows": 1, "applied": 1}
    loaded = core.load_courses(tmp_path / "schedule.csv")
    assert 8 not in [c for c in loaded if c.name == "高等数学"][0].weeks
    notes = json.loads((tmp_path / "schedule_adjustments.json").read_text(encoding="utf-8"))
    assert notes["changes"][0]["kind"] == "停课"

    cl2 = _client([])
    cl2._post_form.side_effect = RuntimeError("boom")
    s2 = _run_sync_schedule(cl2, tmp_path / "b")
    assert s2["ok"] and s2["count"] == 2 and s2["adjustments"] == {"error": "RuntimeError"}


def test_sync_records_schedule_term_and_keeps_overlay(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPERJLU_APPLY_ADJUSTMENTS", raising=False)
    (tmp_path / "schedule_overlay.json").write_text('{"version": 2, "terms": {"x": []}}', encoding="utf-8")
    _run_sync_schedule(_client([]), tmp_path)
    assert json.loads((tmp_path / "schedule_meta.json").read_text(encoding="utf-8")) == {"term": "2026-2027-1"}
    assert (tmp_path / "schedule_overlay.json").read_text(encoding="utf-8") == '{"version": 2, "terms": {"x": []}}'
