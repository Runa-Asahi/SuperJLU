"""整份课表分享：导出 / 导入 / 安全校验 / HTTP。"""
from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import core, jwxt, schedule_share as ss, ui


def C(name, wd, s, e, weeks, loc="经信A101", teacher="王五"):
    return core.Course(name, teacher, loc, wd, s, e, list(weeks))


BASE = [C("高等数学", 1, 1, 2, range(1, 17)),
        C("大学英语", 3, 3, 4, range(1, 17), loc="外语楼201")]
TERM = "2026-2027-1"


def _store(tmp_path, courses=None):
    jwxt.export_courses_csv(courses or BASE, str(tmp_path / "schedule.csv"))
    (tmp_path / "schedule_meta.json").write_text(json.dumps({"term": TERM}), encoding="utf-8")
    (tmp_path / "calendar.json").write_text(
        json.dumps({"term": TERM, "first_monday": "2026-09-07"}), encoding="utf-8")
    (tmp_path / "periods.json").write_text(
        json.dumps({"1": ["08:00", "08:45"], "2": ["08:55", "09:40"]}), encoding="utf-8")
    return ui.Store(tmp_path)


def test_export_roundtrip_and_no_secrets(tmp_path):
    st = _store(tmp_path)
    st.overlay_action({"action": "add", "course": {
        "name": "社团", "weekday": 6, "start": 1, "end": 2, "weeks": [3], "location": "体育馆"}})
    doc = st.export_share()
    assert doc["kind"] == ss.KIND and doc["version"] == 1
    assert doc["term"] == TERM and doc["first_monday"] == "2026-09-07"
    assert doc["periods"]["1"] == ["08:00", "08:45"]
    names = {c["name"] for c in doc["courses"]}
    assert names == {"高等数学", "大学英语", "社团"}
    blob = json.dumps(doc)
    for bad in ("password", "cookie", "token", "session", "credential"):
        assert bad not in blob.lower()

    other = tmp_path / "other"
    other.mkdir()
    jwxt.export_courses_csv([C("旧课", 1, 1, 2, [1])], str(other / "schedule.csv"))
    (other / "schedule_meta.json").write_text(json.dumps({"term": TERM}), encoding="utf-8")
    dst = ui.Store(other)
    dst.overlay_action({"action": "add", "course": {
        "name": "应被清掉", "weekday": 2, "start": 1, "end": 2, "weeks": [1]}})
    with pytest.raises(ValueError, match="确认"):
        dst.import_share(doc, confirm=False)
    dst.import_share(doc, confirm=True)
    rows = dst.schedule_view()[0]
    assert {r["name"] for r in rows} == {"高等数学", "大学英语", "社团"}
    assert all(r["src"] == "shared" for r in rows)
    assert dst._json("schedule_meta.json", {})["source"] == "shared"
    assert dst.overlay_ops() == []
    snap = dst.snapshot()
    assert snap["schedule_shared"] is True
    assert len(snap["courses"]) == 3


def test_parse_rejects_bad_json_unknown_fields_sensitive_and_huge():
    with pytest.raises(ValueError, match="不是"):
        ss.parse("{nope")
    with pytest.raises(ValueError, match="不是"):
        ss.parse({"version": 1, "courses": []})
    with pytest.raises(ValueError, match="账号或登录"):
        ss.parse({"kind": ss.KIND, "version": 1, "courses": [], "password": "x"})
    with pytest.raises(ValueError, match="账号或登录"):
        ss.parse({"kind": ss.KIND, "version": 1, "courses": [], "nested": {"access_token": "x"}})
    with pytest.raises(ValueError, match="无法识别"):
        ss.parse({"kind": ss.KIND, "version": 1, "courses": [], "extra_field": 1})
    with pytest.raises(ValueError, match="过大"):
        ss.parse(b"{" + b"a" * (ss.MAX_BYTES + 10))
    with pytest.raises(ValueError, match="无法识别的课程字段"):
        ss.parse({"kind": ss.KIND, "version": 1, "courses": [
            {"name": "a", "weekday": 1, "start": 1, "end": 2, "weeks": [1], "evil": 1}]})
    empty = ss.parse({"kind": ss.KIND, "version": 1, "courses": []})
    assert empty["courses"] == []


def test_html_chars_in_course_name_are_kept_for_ui_escape(tmp_path):
    st = _store(tmp_path, [C("高<script>数", 1, 1, 2, [1])])
    doc = st.export_share()
    assert doc["courses"][0]["name"] == "高<script>数"
    other = tmp_path / "b"
    other.mkdir()
    dst = _store(other, [C("占位", 1, 1, 2, [1])])
    dst.import_share(doc, confirm=True)
    assert dst.schedule_view()[0][0]["name"] == "高<script>数"
    from jlu_toolkit.ui_page import PAGE
    assert "将覆盖你现有的课表" in PAGE
    assert "esc(" in PAGE


def test_http_share_endpoints(tmp_path):
    import urllib.request
    st = _store(tmp_path)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(st))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        with urllib.request.urlopen(base + "/api/schedule/share") as r:
            assert "attachment" in r.headers["Content-Disposition"]
            assert "superjlu-schedule.json" in r.headers["Content-Disposition"]
            doc = json.loads(r.read())
            assert doc["kind"] == ss.KIND and len(doc["courses"]) == 2

        def post(body):
            req = urllib.request.Request(
                base + "/api/schedule/share", json.dumps(body).encode(),
                {"Content-Type": "application/json", "Host": "127.0.0.1"})
            try:
                with urllib.request.urlopen(req) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        code, j = post({"action": "import", "doc": doc})
        assert code == 400 and "确认" in j["error"]
        doc2 = dict(doc)
        doc2["courses"] = [{"name": "分享课", "weekday": 5, "start": 5, "end": 6, "weeks": [1, 2],
                            "location": "A", "teacher": "T"}]
        code, j = post({"action": "import", "doc": doc2, "confirm": True})
        assert code == 200 and j["ok"] and j["schedule_shared"] is True
        assert [c["name"] for c in j["courses"]] == ["分享课"]
        assert all(c["src"] == "shared" for c in j["courses"])
    finally:
        srv.shutdown()


def test_page_has_share_ui_and_confirm():
    import re
    from jlu_toolkit.ui_page import PAGE
    for s in ("课表分享", "分享课表", "导入分享", "将覆盖你现有的课表",
              "/api/schedule/share", "shareSchedule", "kb-share-card"):
        assert s in PAGE, s
    card = PAGE[PAGE.index('id="kb-edits-card"'):PAGE.index('id="kb-share-card"')]
    visible = re.sub(r"<[^>]+>", "", card)
    assert not re.search(r"overlay|SUPERJLU_", visible, re.I)


def test_is_share_doc():
    ok = ss.build(BASE, TERM, "2026-09-07", {"1": ["08:00", "08:45"]})
    assert ss.is_share_doc(json.dumps(ok))
    assert not ss.is_share_doc('{"kind":"other"}')
    assert not ss.is_share_doc(b"short")
