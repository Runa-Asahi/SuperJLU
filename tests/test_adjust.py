"""调停课合并原型：全部用模拟数据，不访问教务。"""
import json

import pytest
from unittest import mock

from jlu_toolkit import adjust, core, jwxt, sync, ui


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
    def post(path, form, ref, mark_expired=True):
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


def test_sync_default_on_keeps_raw_csv_and_stores_adjustments(tmp_path):
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")])
    s = sync.sync_all(cl, tmp_path, "2026-2027-1")
    assert s["schedule_adjustments"]["rows"] == 1 and s["schedule_adjustments"]["applied"] == 1
    # schedule.csv 仍是教务原样；调课单独存、读取时合并
    loaded = core.load_courses(tmp_path / "schedule.csv")
    assert 8 in [c for c in loaded if c.name == "高等数学"][0].weeks
    saved = json.loads((tmp_path / "schedule_adjustments.json").read_text(encoding="utf-8"))
    assert saved["term"] == "2026-2027-1" and saved["items"][0]["kind"] == "停课"
    st = ui.Store(tmp_path)
    assert 8 not in [c for c in st.courses() if c.name == "高等数学"][0].weeks
    # 关掉设置：即时恢复教务原样，不用重新刷新
    st.save_settings({"apply_adjustments": False})
    assert 8 in [c for c in st.courses() if c.name == "高等数学"][0].weeks
    assert st.snapshot()["schedule_adjust"]["enabled"] is False


def test_sync_setting_off_skips_query(tmp_path):
    (tmp_path / "settings.json").write_text('{"apply_adjustments": false}', encoding="utf-8")
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")])
    s = sync.sync_all(cl, tmp_path, "2026-2027-1")
    assert "schedule_adjustments" not in s
    assert all(c[0] != adjust.EP_ADJUSTED for c, _ in cl._post_form.call_args_list)


def test_sync_adjustment_failure_is_harmless_and_keeps_last(tmp_path):
    cl = _client([row(SKXQ=1, KSJC=1, JSJC=2, ZCMC="8周")])
    sync.sync_all(cl, tmp_path, "2026-2027-1")
    before = (tmp_path / "schedule_adjustments.json").read_text(encoding="utf-8")
    for err in (jwxt.SessionExpiredError(), RuntimeError("boom")):
        cl2 = _client([])
        def post(path, form, ref, mark_expired=True, err=err):
            assert mark_expired is False  # 调课查询跳登录时不记会话过期
            raise err
        cl2._post_form.side_effect = post
        s = sync.sync_all(cl2, tmp_path, "2026-2027-1")  # 不抛 LoginError
        assert s["schedule"]["ok"] and s["schedule_adjustments"]["available"] is False
        assert (tmp_path / "schedule_adjustments.json").read_text(encoding="utf-8") == before


def test_post_form_optional_query_does_not_mark_session_expired(monkeypatch):
    c = jwxt.JwxtClient()
    marked = []
    monkeypatch.setattr(jwxt, "mark_session_expired", lambda r="": marked.append(r))
    monkeypatch.setattr(c, "try_cas_refresh", lambda: False)
    monkeypatch.setattr(c, "_request", lambda *a, **k: (
        200, "<html>loginForm</html>", "https://cas.jlu.edu.cn/tpass/login?service=x", {}))
    with pytest.raises(jwxt.LoginError):
        c._post_form(adjust.EP_ADJUSTED, {}, jwxt.REF_SCHEDULE, mark_expired=False)
    assert marked == []
    with pytest.raises(jwxt.LoginError):
        c._post_form(adjust.EP_ADJUSTED, {}, jwxt.REF_SCHEDULE)
    assert marked == [adjust.EP_ADJUSTED]


# ---- 真实数据回归（2026-10-19 吉大 2026-2027-1 实测；教师姓名/工号已替换为占位） ----

REAL_ADJ = {
    "KCM": "计算机组成原理", "KCH": "ae22551004", "JXBID": "202620271ae2255100401",
    "TKLXDM": "01", "SFECTK": "0",
    "SKXQ": 5, "KSJC": 3, "JSJC": 4, "SKZC": "0000010000000000000", "ZCMC": "6周",
    "JASMC": "前卫-逸夫楼-第十阶梯",
    "XSKXQ": 4, "XKSJC": 3, "XJSJC": 4, "XSKZC": "0000000000001000000", "XZCMC": "13周",
    "XJASDM": "781", "XJASMC": "前卫-第三教学楼-第七阶梯",
    "SQSJ": "2026-09-28 13:42:53", "YSKJS": "某老师/0000001", "XSKJS": "某老师/0000001",
}
# 教务课表两行：都还是 1-12 周（不含调课）。周五那行与实测一致；另一行的星期/节次为示意
REAL_SCHEDULE = [
    {"KCM": "计算机组成原理", "KCH": "ae22551004", "KXH": "01", "JXBID": "202620271ae2255100401",
     "SKXQ": 5, "KSJC": 3, "JSJC": 4, "SKZC": "111111111111", "ZCMC": "1-12周",
     "JASMC": "逸夫楼第十阶梯", "SKJS": "某老师/0000001", "ISTK": "0", "ISTK_DISPLAY": "否"},
    {"KCM": "计算机组成原理", "KCH": "ae22551004", "KXH": "01", "JXBID": "202620271ae2255100401",
     "SKXQ": 2, "KSJC": 1, "JSJC": 2, "SKZC": "111111111111", "ZCMC": "1-12周",
     "JASMC": "逸夫楼第十阶梯", "SKJS": "某老师/0000001", "ISTK": "0", "ISTK_DISPLAY": "否"},
]


def test_real_row_regression(tmp_path):
    cs = [jwxt.row_to_course(r) for r in REAL_SCHEDULE]
    assert cs[0].jxbid == "202620271ae2255100401" and cs[0].kch == "ae22551004"
    assert cs[0].weeks == list(range(1, 13))
    a = adjust.row_to_adjustment(REAL_ADJ)
    assert a.kind == "调课" and a.jxbid == "202620271ae2255100401"
    assert a.old == adjust.Slot(5, 3, 4, (6,)) and a.new == adjust.Slot(4, 3, 4, (13,))  # 19 位位图
    assert a.new_location == "第三教学楼第七阶梯" and a.new_teacher == "某老师"
    out, notes = adjust.apply_adjustments(cs, [a])
    fri = [c for c in out if c.weekday == 5][0]
    assert 6 not in fri.weeks and len(fri.weeks) == 11
    tue = [c for c in out if c.weekday == 2][0]
    assert tue.weeks == list(range(1, 13))  # 另一行不受影响
    (thu,) = [c for c in out if c.weekday == 4]
    assert (thu.start, thu.end, thu.weeks, thu.location) == (3, 4, [13], "第三教学楼第七阶梯")
    assert thu.jxbid == a.jxbid and thu.kch == "ae22551004" and thu.adj.startswith("调课：原 周五 第3-4节 第6周")
    assert notes[0]["removed_weeks"] == [6] and notes[0]["added_weeks"] == [13]
    # 重复合并不叠加
    again, _ = adjust.apply_adjustments(out, [a])
    assert len([c for c in again if c.weekday == 4]) == 1 and again[-1].weeks == [13]
    # 经 CSV 往返（新 9 列）+ Store 读取时合并，课表显示「调」用的 adj 字段
    jwxt.export_courses_csv(cs, str(tmp_path / "schedule.csv"))
    (tmp_path / "schedule_adjustments.json").write_text(json.dumps(
        {"term": "2026-2027-1", "items": [a.to_dict()]}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "schedule_meta.json").write_text('{"term": "2026-2027-1"}', encoding="utf-8")
    snap = ui.Store(tmp_path).snapshot()
    adj_rows = [r for r in snap["courses"] if r.get("adj")]
    assert len(adj_rows) == 1 and adj_rows[0]["weekday"] == 4 and adj_rows[0]["jxbid"] == a.jxbid
    assert snap["schedule_adjust"] == {"enabled": True, "count": 1, "applied": 1, "cancelled": 0, "fetched_at": None}


def test_match_by_jxbid_not_name():
    # 同名不同教学班：只调自己那个班
    mine = core.Course("大学物理", "甲", "A", 1, 1, 2, list(range(1, 9)), "JXB-1")
    other = core.Course("大学物理", "乙", "B", 1, 1, 2, list(range(1, 9)), "JXB-2")
    a = adjust.Adjustment("大学物理", adjust.Slot(1, 1, 2, (3,)), None, kind="停课", jxbid="JXB-1")
    out, _ = adjust.apply_adjustments([mine, other], [a])
    assert 3 not in out[0].weeks and 3 in out[1].weeks
    # 没有教学班 ID（旧 CSV）时退回按课程名
    legacy = core.Course("大学物理", "甲", "A", 1, 1, 2, list(range(1, 9)))
    out, _ = adjust.apply_adjustments([legacy], [a])
    assert 3 not in out[0].weeks


def test_old_seven_column_csv_still_loads(tmp_path):
    f = tmp_path / "schedule.csv"
    f.write_text("课程,教师,地点,星期,开始节,结束节,周次\n高等数学,王五,经信A101,1,1,2,1-16\n", encoding="utf-8-sig")
    (c,) = core.load_courses(str(f))
    assert c.jxbid == "" and c.kch == "" and c.weeks == list(range(1, 17))


def test_room_name():
    assert adjust.room_name("前卫-第三教学楼-第七阶梯") == "第三教学楼第七阶梯"
    assert adjust.room_name("逸夫楼第十阶梯") == "逸夫楼第十阶梯"
    assert adjust.room_name("") == ""


def test_sync_records_schedule_term_and_keeps_overlay(tmp_path):
    (tmp_path / "schedule_overlay.json").write_text('{"version": 2, "terms": {"x": []}}', encoding="utf-8")
    _run_sync_schedule(_client([]), tmp_path)
    assert json.loads((tmp_path / "schedule_meta.json").read_text(encoding="utf-8")) == {"term": "2026-2027-1"}
    assert (tmp_path / "schedule_overlay.json").read_text(encoding="utf-8") == '{"version": 2, "terms": {"x": []}}'
