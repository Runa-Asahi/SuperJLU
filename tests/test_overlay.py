"""课表个人修改层：纯函数 + Store/接口集成，全部本地模拟数据。"""
import json

import pytest

from jlu_toolkit import adjust, core, jwxt, overlay as ov, ui


def C(name, wd, s, e, weeks, loc="经信A101", teacher="王五"):
    return core.Course(name, teacher, loc, wd, s, e, list(weeks))


MATH = C("高等数学", 1, 1, 2, range(1, 17))
ENG = C("大学英语", 3, 3, 4, range(1, 17), loc="外语楼201")
BASE = [MATH, ENG]
K = "高等数学|1|1-2"


def by_src(rows, src):
    return [r for r in rows if r["src"] == src]


def test_add_hide_edit():
    ops = [ov.make_op("add", {"course": {"name": "社团", "weekday": 6, "start": 1, "end": 2,
                                        "weeks": [3, 4], "location": "体育馆"}}, BASE),
           ov.make_op("hide", {"target": K, "weeks": [8]}, BASE),
           ov.make_op("edit", {"target": K, "weeks": [9], "set": {"location": "逸夫楼301"}}, BASE)]
    rows, issues = ov.apply_overlay(BASE, ops)
    assert issues == []
    math = [r for r in by_src(rows, "official") if r["name"] == "高等数学"][0]
    assert 8 not in math["weeks"] and 9 not in math["weeks"] and len(math["weeks"]) == 14
    (ed,) = by_src(rows, "edited")
    assert ed["weeks"] == [9] and ed["location"] == "逸夫楼301" and ed["from"] == K
    (cu,) = by_src(rows, "custom")
    assert cu["name"] == "社团" and cu["weeks"] == [3, 4]
    # 不修改入参
    assert MATH.weeks == list(range(1, 17))


def test_hide_whole_course_and_idempotent():
    ops = [ov.make_op("hide", {"target": K}, BASE)]
    once, _ = ov.apply_overlay(BASE, ops)
    assert [r["name"] for r in once] == ["大学英语"]
    twice, _ = ov.apply_overlay(BASE, ops)
    assert once == twice


def test_refresh_keeps_edits_and_flags_changes():
    ops = [ov.make_op("edit", {"target": K, "set": {"location": "逸夫楼301"}}, BASE)]
    # 刷新后教务把高数周次改成 1-12：修改仍生效，但标记「教务有变动」
    fresh = [C("高等数学", 1, 1, 2, range(1, 13)), ENG]
    rows, issues = ov.apply_overlay(fresh, ops)
    (ed,) = by_src(rows, "edited")
    assert ed["weeks"] == list(range(1, 13)) and ed["location"] == "逸夫楼301"
    assert [i["kind"] for i in issues] == ["changed"]
    # 同学点「我知道了」后不再提示
    doc = ov.rebase({"ops": ops}, ops[0]["id"], fresh)
    assert ov.apply_overlay(fresh, doc["ops"])[1] == []


def test_missing_target_is_reported_not_dropped_and_can_detach():
    ops = [ov.make_op("edit", {"target": K, "weeks": [5], "set": {"location": "逸夫楼301"}}, BASE)]
    rows, issues = ov.apply_overlay([ENG], ops)  # 教务里高数没了
    assert [i["kind"] for i in issues] == ["missing"] and not by_src(rows, "edited")
    doc = ov.detach({"ops": ops}, ops[0]["id"])
    rows, issues = ov.apply_overlay([ENG], doc["ops"])
    (cu,) = by_src(rows, "custom")
    assert issues == [] and cu["name"] == "高等数学" and cu["weeks"] == [5] and cu["location"] == "逸夫楼301"


def test_overlay_runs_after_adjustments():
    # 第 8 周高数被教务调到周五 5-6：原槽位第 8 周已不存在，用户对第 8 周的隐藏应提示未生效
    adj = adjust.Adjustment("高等数学", adjust.Slot(1, 1, 2, (8,)), adjust.Slot(5, 5, 6, (8,)), "经信B202")
    merged, _ = adjust.apply_adjustments(BASE, [adj])
    ops = [ov.make_op("hide", {"target": K, "weeks": [8]}, BASE),
           ov.make_op("hide", {"target": K, "weeks": [10]}, BASE)]
    rows, issues = ov.apply_overlay(merged, ops)
    assert [i["kind"] for i in issues] == ["missing"]
    assert any(r["weekday"] == 5 and r["weeks"] == [8] for r in rows)  # 调课结果保留


def test_validation_errors_are_chinese():
    with pytest.raises(ValueError, match="课程名"):
        ov.make_op("add", {"course": {"weekday": 1, "start": 1, "end": 2, "weeks": [1]}}, BASE)
    with pytest.raises(ValueError, match="找不到"):
        ov.make_op("hide", {"target": "不存在|1|1-2"}, BASE)
    with pytest.raises(ValueError, match="修改的内容"):
        ov.make_op("edit", {"target": K, "set": {"bogus": 1}}, BASE)
    with pytest.raises(ValueError):
        ov.validate_doc({"nope": 1})
    rows, issues = ov.apply_overlay(BASE, [{"id": "x", "op": "add", "course": {}}])
    assert [i["kind"] for i in issues] == ["invalid"] and len(rows) == 2


def test_store_refresh_does_not_touch_overlay(tmp_path):
    jwxt.export_courses_csv(BASE, str(tmp_path / "schedule.csv"))
    st = ui.Store(tmp_path)
    st.overlay_action({"action": "hide", "target": K, "weeks": [1]})
    st.overlay_action({"action": "add", "course": {"name": "社团", "weekday": 6, "start": 1, "end": 2,
                                                    "weeks": [1]}})
    # 模拟「从教务刷新」：schedule.csv 整份覆盖
    jwxt.export_courses_csv(BASE, str(tmp_path / "schedule.csv"))
    snap = st.snapshot()
    assert snap["schedule_edits"] == 2 and snap["schedule_issues"] == []
    assert {r["src"] for r in snap["courses"]} == {"official", "custom"}
    assert 1 not in [c for c in st.courses() if c.name == "高等数学"][0].weeks
    assert len(st.official_courses()) == 2
    # 恢复教务原样 + 撤销
    st.overlay_action({"action": "reset"})
    assert st.snapshot()["schedule_edits"] == 0 and st.snapshot()["schedule_can_undo_reset"]
    st.overlay_action({"action": "undo_reset"})
    assert st.snapshot()["schedule_edits"] == 2
    # 备份导出 → 导入
    doc = st.overlay_doc()
    st.overlay_action({"action": "reset"})
    st.overlay_action({"action": "import", "doc": json.loads(json.dumps(doc))})
    assert st.overlay_doc() == doc


def test_ics_uses_user_view(tmp_path):
    jwxt.export_courses_csv(BASE, str(tmp_path / "schedule.csv"))
    st = ui.Store(tmp_path)
    st.overlay_action({"action": "hide", "target": K})
    ics = core.to_ics(st.courses(), "2026-09-07")
    assert "高等数学" not in ics and "大学英语" in ics
