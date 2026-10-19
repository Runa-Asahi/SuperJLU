"""课表统一读取：停课灰显、ISTK 提示、命令行 / MCP / iCal / App 同一份课表、安卓 WebView 渲染检查。"""
import importlib.util
import json
import sys
import types
import urllib.request
from pathlib import Path
from unittest import mock

import pytest

from jlu_toolkit import adjust, cli, core, jwxt, overlay as ov, timetable, ui

TERM = "2026-2027-1"
JXB = "202620271ae2255100401"


def _courses():
    return [core.Course("计算机组成原理", "某老师", "逸夫楼第十阶梯", 5, 3, 4, list(range(1, 13)), JXB, "ae22551004"),
            core.Course("高等数学", "王五", "经信A101", 1, 1, 2, list(range(1, 17)))]


MOVE = adjust.Adjustment("计算机组成原理", adjust.Slot(5, 3, 4, (6,)), adjust.Slot(4, 3, 4, (13,)),
                         "第三教学楼第七阶梯", "调课", "2026-09-28 13:42:53", (), JXB)
STOP = adjust.Adjustment("高等数学", adjust.Slot(1, 1, 2, (8,)), None, "", "停课", "2026-10-01 09:00:00")


def seed(root: Path, adjs=(MOVE, STOP), ops=(), settings=None):
    root.mkdir(parents=True, exist_ok=True)
    jwxt.export_courses_csv(_courses(), str(root / "schedule.csv"))
    (root / "schedule_meta.json").write_text(json.dumps({"term": TERM}), encoding="utf-8")
    (root / "schedule_adjustments.json").write_text(json.dumps(
        {"term": TERM, "items": [a.to_dict() for a in adjs]}, ensure_ascii=False), encoding="utf-8")
    if ops:
        (root / "schedule_overlay.json").write_text(json.dumps(
            {"version": 2, "terms": {TERM: list(ops)}}, ensure_ascii=False), encoding="utf-8")
    if settings is not None:
        (root / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return root


def test_cancelled_lessons_are_shown_greyed_and_respect_toggle(tmp_path):
    v = timetable.view(seed(tmp_path))
    (g,) = [r for r in v["rows"] if r["src"] == "cancelled"]
    assert (g["name"], g["weekday"], g["weeks"]) == ("高等数学", 1, [8])
    assert g["adj"].startswith("停课：原 周一 第1-2节 第8周 · 经信A101") and "2026-10-01" in g["adj"]
    # 真正上课的课表里没有第 8 周高数，也没有灰显那条
    math = [c for c in timetable.courses(tmp_path) if c.name == "高等数学"]
    assert len(math) == 1 and 8 not in math[0].weeks
    snap = ui.Store(tmp_path).snapshot()
    assert snap["schedule_adjust"]["cancelled"] == 1
    # 关掉设置：不灰显、不调课
    ui.Store(tmp_path).save_settings({"apply_adjustments": False})
    v = timetable.view(tmp_path)
    assert not [r for r in v["rows"] if r["src"] in ("cancelled",) or r.get("adj")]
    assert 8 in [c for c in timetable.courses(tmp_path) if c.name == "高等数学"][0].weeks


def test_overlay_cannot_target_cancelled_ghost(tmp_path):
    seed(tmp_path)
    st = ui.Store(tmp_path)
    with pytest.raises(ValueError):  # 灰显的停课行不是可修改的目标
        st.overlay_action({"action": "hide", "target": "不存在|1|1-2"})
    st.overlay_action({"action": "hide", "target": "高等数学|1|1-2", "weeks": [9]})
    rows = st.snapshot()["courses"]
    assert [r for r in rows if r["src"] == "cancelled"][0]["weeks"] == [8]


def test_istk_flag_roundtrip_and_hint(tmp_path):
    row = {"KCM": "线性代数", "SKXQ": 2, "KSJC": 1, "JSJC": 2, "SKZC": "1111", "JASMC": "A", "SKJS": "x/1",
           "JXBID": "J9", "ISTK": "1", "ISTK_DISPLAY": "是"}
    c = jwxt.row_to_course(row)
    assert c.istk is True
    assert jwxt.row_to_course({**row, "ISTK": "0", "ISTK_DISPLAY": "否"}).istk is False
    jwxt.export_courses_csv([c], str(tmp_path / "schedule.csv"))
    (back,) = core.load_courses(str(tmp_path / "schedule.csv"))
    assert back.istk is True and back.jxbid == "J9"
    v = timetable.build([back], [], [], True)
    assert "没读到具体安排" in v["rows"][0]["hint"]
    v = timetable.build([back], [], [], False)
    assert "已关闭" in v["rows"][0]["hint"]
    stop = adjust.Adjustment("线性代数", adjust.Slot(2, 1, 2, (3,)), None, kind="停课", jxbid="J9")
    v = timetable.build([back], [stop], [], True)
    assert not any(r.get("hint") for r in v["rows"])


def test_cli_today_ics_and_store_read_same_view(tmp_path, monkeypatch, capsys):
    op = ov.make_op("edit", {"target": "高等数学|1|1-2", "weeks": [9], "set": {"location": "逸夫楼301"}},
                    _courses())
    root = seed(tmp_path / "data", ops=[op])
    monkeypatch.setattr(ui, "data_dir", lambda: root)
    expect = timetable.courses(root)
    assert expect == ui.Store(root).courses()
    # today：第 13 周周四有调过来的计组；第 6 周周五没有
    cli.main(["today", "--week", "13", "--weekday", "4"])
    assert "计算机组成原理 @ 第三教学楼第七阶梯" in capsys.readouterr().out
    cli.main(["today", str(root / "schedule.csv"), "--week", "6", "--weekday", "5"])
    assert "计算机组成原理" not in capsys.readouterr().out
    cli.main(["today", "--week", "9", "--weekday", "1"])
    assert "高等数学 @ 逸夫楼301" in capsys.readouterr().out
    cli.main(["today", "--week", "8", "--weekday", "1"])
    assert "高等数学" not in capsys.readouterr().out  # 停课
    # ics：与 App 的 /api/ics 同一份
    out = tmp_path / "a.ics"
    cli.main(["ics", "--first-monday", "2026-09-07", "-o", str(out)])
    text = out.read_text(encoding="utf-8")
    assert text.count("SUMMARY:计算机组成原理") == 12 and "LOCATION:第三教学楼第七阶梯" in text
    assert text.count("SUMMARY:高等数学") == 15
    # 普通文件名的 CSV 照原样读（兼容 examples/）
    other = tmp_path / "x.csv"
    jwxt.export_courses_csv(_courses(), str(other))
    assert timetable.courses_from_csv(other) == _courses()


def test_cli_fetch_exports_merged_view(tmp_path, monkeypatch):
    root = seed(tmp_path / "data", ops=[{"id": "h", "op": "hide", "target": "高等数学|1|1-2", "weeks": [2]}])
    monkeypatch.setattr(ui, "data_dir", lambda: root)
    cl = mock.Mock()
    cl.current_semester.return_value = TERM
    cl.fetch_schedule.return_value = _courses()
    monkeypatch.setattr(adjust, "fetch_adjustments", lambda c, t: [MOVE, STOP])
    cs, extra = cli._fetch_merged_schedule(cl, None, str(tmp_path / "out.csv"))
    assert "调课 2 处" in extra and "个人修改 1 处" in extra
    math = [c for c in cs if c.name == "高等数学"][0]
    assert 2 not in math.weeks and 8 not in math.weeks
    assert any(c.weekday == 4 and c.weeks == [13] for c in cs)
    # 调课读不到：照样导出
    monkeypatch.setattr(adjust, "fetch_adjustments", mock.Mock(side_effect=jwxt.SessionExpiredError()))
    cs, _ = cli._fetch_merged_schedule(cl, TERM, str(tmp_path / "out.csv"))
    assert 8 in [c for c in cs if c.name == "高等数学"][0].weeks
    # 导出到数据目录本身：只写教务原样，避免 App 再合并一次
    cs, extra = cli._fetch_merged_schedule(cl, TERM, str(root / "schedule.csv"))
    assert cs == _courses() and "教务原样" in extra


def test_mcp_courses_on_day_uses_shared_view(tmp_path, monkeypatch):
    root = seed(tmp_path / "data")
    monkeypatch.setattr(ui, "data_dir", lambda: root)
    tools = {}

    class FakeMCP:
        def __init__(self, *_):
            pass

        def tool(self):
            return lambda f: tools.setdefault(f.__name__, f)

        def run(self):
            pass
    fake = types.ModuleType("mcp.server.fastmcp")
    fake.FastMCP = FakeMCP
    monkeypatch.setitem(sys.modules, "mcp", types.ModuleType("mcp"))
    monkeypatch.setitem(sys.modules, "mcp.server", types.ModuleType("mcp.server"))
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fake)
    from jlu_toolkit import mcp_server
    monkeypatch.delenv("JLU_SCHEDULE_CSV", raising=False)
    mcp_server.main()
    got = tools["courses_on_day"](13, 4)
    assert [c["location"] for c in got] == ["第三教学楼第七阶梯"]
    assert tools["courses_on_day"](8, 1) == []  # 停课不算
    monkeypatch.setenv("JLU_SCHEDULE_CSV", str(root / "schedule.csv"))
    assert [c["location"] for c in tools["courses_on_day"](13, 4)] == ["第三教学楼第七阶梯"]


# ---- 安卓 WebView：同一页面、同一接口，角标 CSS 不被 in-app 样式盖掉 ----

ROOT = Path(__file__).resolve().parents[1]


def test_android_webview_serves_badged_timetable(tmp_path, monkeypatch):
    for k in ("XDG_CONFIG_HOME", "JLU_TOOLKIT_NO_KEYRING"):
        monkeypatch.delenv(k, raising=False)
    src = ROOT / "android" / "app" / "src" / "main" / "python" / "jlu_android.py"
    spec = importlib.util.spec_from_file_location("jlu_android_t", src)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    add = ov.make_op("add", {"course": {"name": "社团", "weekday": 6, "start": 1, "end": 2, "weeks": [6]}}, [])
    edit = ov.make_op("edit", {"target": "高等数学|1|1-2", "weeks": [6], "set": {"location": "逸夫楼301"}},
                      _courses())
    try:
        url = m.start(str(tmp_path))
        seed(tmp_path / "config" / "jlu-toolkit" / "data", ops=[add, edit])
        ua = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120 Mobile SuperJLU-Android"}
        html = urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=5).read().decode()
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url + "api/data", headers=ua),
                                                 timeout=5).read())
    finally:
        m.stop()
    kinds = {("cancelled" if r["src"] == "cancelled" else "adjusted" if r.get("adj") else r["src"])
             for r in data["courses"]}
    assert {"cancelled", "adjusted", "custom", "edited", "official"} <= kinds
    for badge in ('.cls.edited::after{content:"改"}', '.cls.custom::after{content:"自"}',
                  '.cls.adjusted::after{content:"调"', '.cls.cancelled::after{content:"停"'):
        assert badge in html, badge
    # in-app（安卓）专用样式不能隐藏课表格子或角标
    in_app = [line for line in html.splitlines() if "in-app" in line and "{" in line]
    assert not any(".cls" in line or "::after" in line for line in in_app), in_app
    # 角标规则只用老 WebView（minSdk 24 起的可更新 WebView）都支持的写法
    css = html[html.index(".cls{cursor:pointer"):html.index(".kb-tools")]
    for modern in (":has(", "@container", "&", "inset:", "@layer"):
        assert modern not in css, modern
    gradle = (ROOT / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
    assert 'include "jlu_toolkit/**"' in gradle  # 新模块 timetable.py 会随包打进 App
