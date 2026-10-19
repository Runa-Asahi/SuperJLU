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
    assert ov.apply_overlay(fresh, ov.ack(ops, ops[0]["id"], fresh))[1] == []


def test_missing_target_is_reported_not_dropped_and_can_detach():
    ops = [ov.make_op("edit", {"target": K, "weeks": [5], "set": {"location": "逸夫楼301"}}, BASE)]
    rows, issues = ov.apply_overlay([ENG], ops)  # 教务里高数没了
    assert [i["kind"] for i in issues] == ["missing"] and not by_src(rows, "edited")
    assert issues[0]["name"] == "高等数学" and issues[0]["weekday"] == 1
    rows, issues = ov.apply_overlay([ENG], ov.detach(ops, ops[0]["id"]))
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


def test_ack_missing_goes_quiet_until_course_returns():
    ops = [ov.make_op("hide", {"target": K, "weeks": [3]}, BASE)]
    quiet = ov.ack(ops, ops[0]["id"], [ENG])
    assert ov.apply_overlay([ENG], quiet)[1] == []
    rows, issues = ov.apply_overlay(BASE, quiet)  # 课又回来了：照常生效
    assert issues == [] and 3 not in [r for r in rows if r["name"] == "高等数学"][0]["weeks"]


def test_update_custom_and_edit():
    add = ov.make_op("add", {"course": {"name": "社团", "weekday": 6, "start": 1, "end": 2, "weeks": [3]}}, BASE)
    edit = ov.make_op("edit", {"target": K, "set": {"location": "逸夫楼301"}}, BASE)
    ops = ov.update([add, edit], add["id"], {"course": {**add["course"], "weeks": [3, 4], "location": "体育馆"}})
    ops = ov.update(ops, edit["id"], {"set": {"location": "逸夫楼302"}})
    rows, _ = ov.apply_overlay(BASE, ops)
    assert by_src(rows, "custom")[0]["weeks"] == [3, 4]
    assert by_src(rows, "edited")[0]["location"] == "逸夫楼302"
    with pytest.raises(ValueError, match="修改的内容"):  # 改回和教务一样不算修改
        ov.make_op("edit", {"target": K, "set": {"location": MATH.location}}, BASE)


def test_normalize_v1_and_terms():
    v1 = {"version": 1, "ops": [{"id": "a", "op": "hide", "target": K}, {"id": "", "op": "hide"}, "junk"]}
    assert ov.normalize(v1, "2026-2027-1") == {"version": 2, "terms": {"2026-2027-1": [v1["ops"][0]]}}
    assert ov.normalize(v1, "") == {"version": 2, "terms": {"": [v1["ops"][0]]}}
    v2 = {"version": 2, "terms": {"2025-2026-2": [v1["ops"][0]], "x": {"ops": []}}}
    assert ov.normalize(v2, "2026-2027-1")["terms"] == {"2025-2026-2": [v1["ops"][0]]}
    with pytest.raises(ValueError, match="备份文件"):
        ov.normalize([1, 2])


def _store(tmp_path, term="2026-2027-1"):
    jwxt.export_courses_csv(BASE, str(tmp_path / "schedule.csv"))
    (tmp_path / "schedule_meta.json").write_text(json.dumps({"term": term}), encoding="utf-8")
    return ui.Store(tmp_path)


def test_store_per_term_and_legacy_migration(tmp_path):
    (tmp_path / "schedule_overlay.json").write_text(json.dumps(
        {"version": 1, "ops": [{"id": "old", "op": "hide", "target": K}]}), encoding="utf-8")
    st = _store(tmp_path)
    assert [o["id"] for o in st.overlay_ops()] == ["old"]  # 旧文件归到当前学期
    st.overlay_action({"action": "hide", "target": "大学英语|3|3-4", "weeks": [2]})
    saved = json.loads((tmp_path / "schedule_overlay.json").read_text(encoding="utf-8"))
    assert saved["version"] == 2 and list(saved["terms"]) == ["2026-2027-1"]
    # 换学期：上学期的修改不套到新课表上，也不丢
    (tmp_path / "schedule_meta.json").write_text(json.dumps({"term": "2026-2027-2"}), encoding="utf-8")
    snap = st.snapshot()
    assert snap["schedule_edits"] == 0 and snap["schedule_other_terms"] == 2 and snap["schedule_issues"] == []
    assert snap["schedule_term"] == "2026-2027-2"
    # 学期代码缺失时退回校历
    (tmp_path / "schedule_meta.json").unlink()
    (tmp_path / "calendar.json").write_text(json.dumps({"term": "2026-2027-1"}), encoding="utf-8")
    assert st.current_term() == "2026-2027-1" and len(st.overlay_ops()) == 2


def test_store_undo_reset_is_per_term_and_cleared_by_new_edits(tmp_path):
    st = _store(tmp_path)
    st.overlay_action({"action": "hide", "target": K})
    st.overlay_action({"action": "reset"})
    assert st.snapshot()["schedule_can_undo_reset"]
    st.overlay_action({"action": "hide", "target": "大学英语|3|3-4"})
    assert not st.snapshot()["schedule_can_undo_reset"]
    with pytest.raises(ValueError, match="撤销"):
        st.overlay_action({"action": "undo_reset"})


def test_import_merges_terms(tmp_path):
    st = _store(tmp_path)
    st.overlay_action({"action": "hide", "target": K})
    st.overlay_action({"action": "import", "doc": {"version": 2, "terms": {
        "2025-2026-2": [{"id": "z", "op": "hide", "target": "x|1|1-2"}]}}})
    assert set(st.overlay_doc()["terms"]) == {"2026-2027-1", "2025-2026-2"} and len(st.overlay_ops()) == 1
    with pytest.raises(ValueError, match="备份文件"):
        st.overlay_action({"action": "import", "doc": "hello"})


def test_http_overlay_endpoints(tmp_path):
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    st = _store(tmp_path)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(st))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def post(body):
            req = urllib.request.Request(base + "/api/schedule/overlay", json.dumps(body).encode(),
                                         {"Content-Type": "application/json", "Host": "127.0.0.1"})
            try:
                with urllib.request.urlopen(req) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        code, j = post({"action": "hide", "target": K, "weeks": [1]})
        assert code == 200 and j["ok"] and j["schedule_edits"] == 1
        code, j = post({"action": "hide", "target": "没有|1|1-2"})
        assert code == 400 and "找不到" in j["error"]
        with urllib.request.urlopen(base + "/api/schedule/overlay") as r:
            assert "attachment" in r.headers["Content-Disposition"]
            assert json.loads(r.read())["terms"]["2026-2027-1"][0]["op"] == "hide"
    finally:
        srv.shutdown()


def test_schedule_edit_ui_js():
    import shutil
    import subprocess
    from pathlib import Path
    node = shutil.which("node")
    if not node:
        pytest.skip("node 不可用")
    r = subprocess.run([node, str(Path(__file__).parent / "js_schedule_edit_test.js")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr


def test_page_has_schedule_edit_ui_without_tech_words():
    import re
    from jlu_toolkit.ui_page import PAGE
    for s in ("＋ 添加课程", "本周不上", "删除这门课", "只改本周", "所有周", "我知道了", "保留为自定义课",
              "删掉这条修改", "我的课表修改", "导出备份", "导入备份", "恢复教务原样", "撤销恢复",
              "自动应用调课/停课", 'content:"调"'):
        assert s in PAGE, s
    card = PAGE[PAGE.index('id="kb-edits-card"'):PAGE.index("数据与隐私")]
    visible = re.sub(r"<[^>]+>", "", card)
    assert not re.search(r"json|overlay|SUPERJLU_|命令行|终端", visible, re.I), visible
    assert "SUPERJLU_APPLY_ADJUSTMENTS" not in PAGE


def test_overlay_targets_match_by_jxbid():
    mine = C("大学物理", 1, 1, 2, range(1, 9))
    mine = core.Course(*[getattr(mine, k) for k in ("name", "teacher", "location", "weekday", "start", "end", "weeks")], "JXB-1")
    other = core.Course("大学物理", "乙", "B", 1, 1, 2, list(range(1, 9)), "JXB-2")
    op = ov.make_op("hide", {"target": "大学物理|1|1-2", "jxbid": "JXB-2", "weeks": [3]}, [mine, other])
    assert op["jxbid"] == "JXB-2"
    rows, issues = ov.apply_overlay([mine, other], [op])
    assert issues == []
    assert 3 in [r for r in rows if r["jxbid"] == "JXB-1"][0]["weeks"]
    assert 3 not in [r for r in rows if r["jxbid"] == "JXB-2"][0]["weeks"]
    # 教务改了课程名，教学班不变：修改照样认得出
    renamed = core.Course("大学物理（双语）", "乙", "B", 1, 1, 2, list(range(1, 9)), "JXB-2")
    rows, issues = ov.apply_overlay([renamed], [op])
    assert issues == [] and 3 not in rows[0]["weeks"]
    # 旧修改（没存 jxbid）仍按课程名认
    legacy = {k: v for k, v in op.items() if k != "jxbid"}
    rows, issues = ov.apply_overlay([core.Course("大学物理", "乙", "B", 1, 1, 2, list(range(1, 9)))], [legacy])
    assert issues == [] and 3 not in rows[0]["weeks"]
