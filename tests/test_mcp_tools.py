"""MCP / 命令行只读查询：默认读 App 数据目录，不需要 JLU_*_CSV；全部用临时数据，不联网。"""
import datetime as dt
import json

import pytest

from jlu_toolkit import cli, mcp_tools as T, ui, webvpn


@pytest.fixture
def root(monkeypatch):
    for k in ("JLU_SCHEDULE_CSV", "JLU_GRADES_CSV", "JLU_EXAMS_CSV"):
        monkeypatch.delenv(k, raising=False)
    return ui.data_dir()  # conftest 已把配置目录指到临时目录


def _grades(root):
    (root / "grades.csv").write_text(
        "课程,学分,成绩,学期,教务绩点,课程性质\n"
        "高等数学,4,90,2025-2026-1,3.8,必修\n"
        "大学英语,2,80,2025-2026-1,3.0,必修\n"
        "体育,1,95,2025-2026-1,4.0,必修\n"
        "电影赏析,2,70,2025-2026-2,2.0,选修\n", encoding="utf-8")


def _schedule(root):
    (root / "schedule.csv").write_text("课程,教师,地点,星期,开始节,结束节,周次\n"
                                       "计算机组成,王五,A101,1,1,2,1-16\n", encoding="utf-8")


def test_empty_data_gives_friendly_hint(root):
    for r in (T.compute_gpa(), T.list_grades(), T.exams(), T.academic_progress(), T.adjustments(),
              T.compute_gpa_with_scheme("保研加权")):
        assert T.LOGIN_HINT in r["error"] and "jlu-toolkit sync" in r["error"]


def test_grades_read_app_data_without_env(root):
    _grades(root)
    assert len(T.list_grades()) == 4
    assert len(T.list_grades("2025-2026-2")) == 1
    assert "error" not in T.compute_gpa()


def test_env_override_still_works(root, tmp_path, monkeypatch):
    f = tmp_path / "g.csv"
    f.write_text("课程,学分,成绩,学期\n线代,3,85,2024-2025-1\n", encoding="utf-8")
    monkeypatch.setenv("JLU_GRADES_CSV", str(f))
    assert [g["name"] for g in T.list_grades()] == ["线代"]


def test_gpa_schemes_builtin_and_saved(root):
    _grades(root)
    st = ui.Store(root)
    keys = [g["key"] for g in st.grade_records() if g["name"] == "高等数学"]
    st.save_scheme("只算高数", keys)
    s = T.gpa_schemes()
    assert {b["id"] for b in s["builtin"]} == {"postgraduate", "scholarship", "comprehensive"}
    assert s["saved"][0]["name"] == "只算高数"
    r = T.compute_gpa_with_scheme("只算高数")
    assert r["courses"] == 1 and r["weighted_score"] == 90 and r["weighted_gpa"] == 3.8
    sch = T.compute_gpa_with_scheme("奖学金加权")  # 必修，剔除英语、体育
    assert sch["included"] == ["高等数学"]
    pg = T.compute_gpa_with_scheme("postgraduate")  # 剔除选修、体育
    assert set(pg["included"]) == {"高等数学", "大学英语"}
    assert T.compute_gpa_with_scheme("所有课程", term="2025-2026-2")["included"] == ["电影赏析"]
    assert "找不到" in T.compute_gpa_with_scheme("不存在的方案")["error"]


def test_exams_countdown(root):
    (root / "exams.csv").write_text("课程,开始,结束,地点,座位号,考试名称,学期\n"
                                    "高数,2026-11-01T08:00,2026-11-01T10:00,A101,12,期中,x\n"
                                    "旧考,2026-01-01T08:00,2026-01-01T10:00,B1,,期末,x\n", encoding="utf-8")
    now = dt.datetime(2026, 10, 20, 8, 0)
    r = T.exams(now=now)
    assert r["count"] == 1 and r["exams"][0]["days_left"] == 12 and "12 天" in r["exams"][0]["countdown"]
    assert T.exams(include_past=True, now=now)["count"] == 2


def test_academic_progress(root):
    ui.Store(root)._write_json("completion.json", {
        "plan": "计算机 2024", "required": 160, "earned": 100, "missing": 60, "passed": False,
        "groups": [{"name": "专业必修", "required": 50, "earned": 30, "missing": 20, "passed": False},
                   {"name": "通识", "required": 10, "earned": 10, "missing": 0, "passed": True}]})
    r = T.academic_progress()
    assert r["missing"] == 60 and r["unfinished_groups"] == ["专业必修"]


def test_adjustments_and_courses_on_day(root):
    _schedule(root)
    (root / "schedule_adjustments.json").write_text(json.dumps({"items": [{
        "name": "计算机组成", "kind": "调课",
        "old": {"weekday": 1, "start": 1, "end": 2, "weeks": [5]},
        "new": {"weekday": 3, "start": 5, "end": 6, "weeks": [5]}, "new_location": "B202"}]}), encoding="utf-8")
    r = T.adjustments()
    assert r["count"] == 1 and r["auto_apply"] is True and r["applied_to_timetable"] == 1
    assert r["items"][0]["after"]["weekday_text"] == "星期三" and r["items"][0]["new_location"] == "B202"
    assert T.courses_on_day(5, 1) == []
    assert T.courses_on_day(5, 3)[0]["location"] == "B202"


def test_college_notices_cache_and_refresh(root):
    lst = T.college_notices()
    assert lst["all_channels"] > 0 and "channels" in lst
    assert "找不到" in T.college_notices("不存在学院xyz")["error"]
    html = '<ul><li><a href="info/1001/2002.htm" title="关于期中考试的通知">x</a><span>2026-10-18</span></li></ul>'
    r = T.college_notices("ccst-xytz", refresh=True, getter=lambda url, *a, **k: html)
    assert r["items"][0]["title"] == "关于期中考试的通知"
    assert T.college_notices("计算机学院·学院通知", keyword="期中")["count"] == 1


def test_cli_exams_from_app_data(root, capsys):
    (root / "exams.csv").write_text("课程,开始,结束,地点,座位号,考试名称,学期\n"
                                    "高数,2099-11-01T08:00,2099-11-01T10:00,A101,12,期中,x\n", encoding="utf-8")
    cli._main(["exams"])
    assert "高数" in capsys.readouterr().out


def test_cli_exams_no_data(root, capsys):
    with pytest.raises(SystemExit):
        cli._main(["exams"])
    assert "登录同步" in capsys.readouterr().err
    (root / "exams.csv").write_text("课程,开始,结束,地点,座位号,考试名称,学期\n", encoding="utf-8")
    cli._main(["exams"])
    assert "目前没有安排考试" in capsys.readouterr().out
    r = T.exams()
    assert r["count"] == 0 and "error" not in r


def test_cli_route_show_and_set(root, capsys):
    cli._main(["route"])
    assert "校园网直连" in capsys.readouterr().out
    cli._main(["route", "webvpn"])
    assert webvpn.mode() == "webvpn"
    cli._main(["route"])
    assert "WebVPN" in capsys.readouterr().out


def test_cli_adjustments_and_college(root, capsys):
    _schedule(root)
    cli._main(["adjustments"])
    out = capsys.readouterr().out
    assert "还没同步过调课" in out and "0 条" not in out
    assert T.adjustments()["count"] is None and T.adjustments()["synced"] is False
    (root / "schedule_adjustments.json").write_text(json.dumps({"items": []}), encoding="utf-8")
    cli._main(["adjustments"])
    assert "0 条调整" in capsys.readouterr().out
    cli._main(["college"])
    assert "栏目 id" in capsys.readouterr().out
