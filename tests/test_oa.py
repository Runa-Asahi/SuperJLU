import json
import urllib.parse

import pytest

from jlu_toolkit import oa

LIST = """<html><head><meta charset="utf-8"></head><body>
<a href="PortalInformation!jldxList.action?channelId=179577">校内通知</a>
<a href="PortalInformation!jldxList.action?channelId=179578">学术讲座</a>
<div class="li rel"><a class="font14" href="PortalInformation!getInformation.action?id=111&channelId=179577"><font color=red>[置顶]</font>放假安排</a>
<span>2026年10月01日 08:05</span><a href="#">校长办公室</a></div>
<div class="li rel"><a class="font14" href="PortalInformation!getInformation.action?id=222&channelId=179577">教务通知 选课</a>
<span>2026年10月02日 09:00</span><a href="#">教务处</a></div>
<a href="PortalInformation!jldxList.action?channelId=179577&startPage=2">2</a>
<span>共 37 页</span></body></html>"""

DETAIL = """<div class="content_t">放假安排</div><div class="content_time">2026-10-01 <span>校长办公室</span></div>
<div class="content_font"><p>正文</p></div><a href="rd/download/attachdownload.jsp?res=1">附件</a></body>"""


class Fake:
    def __init__(self, pages, login=False):
        self.pages, self.login, self.urls = pages, login, []

    def _request(self, url, data=None, headers=None, method=None, allow_redirects=True):
        assert method in (None, "GET", "POST")
        self.urls.append(url)
        if data is not None or "searchId=" in url:
            q = (data or b"").decode() + url
            ok = (data is not None and "%E" in data.decode()) or "searchId=2025" in q
            h = LIST if ok else "<html></html>"
            return 200, h, url, h.encode()
        if self.login:
            return 200, '<form id="loginForm"><input type="password" name="p"></form>', \
                "https://oa.jlu.edu.cn/defaultroot/login.jsp", b""
        if "getInformation" in url:
            return 200, DETAIL, url, DETAIL.encode()
        if url.endswith("jldx_left.js"):
            h = "var m=[{u:'PortalInformation!jldxList.action?channelId=190002',t:'放假安排'}];"
            return 200, h, url, h.encode()
        if "login.jsp" in url:
            h = '<script src="js/jldx_left.js"></script><a href="x?channelId=190001"><span>学术讲座</span></a><form action="/defaultroot/login.jsp"><input name="userAccount"><input type="password" name="userPassword"></form>'
            return 200, h, url, h.encode()
        page = int(url.split("startPage=")[1].split("&")[0]) if "startPage=" in url else 1
        h = LIST if page <= self.pages else "<html></html>"
        if page > 1:
            h = h.replace("id=111", f"id=1{page}1").replace("id=222", f"id=2{page}2")
        return 200, h, url, h.encode()


def test_parse_list():
    r = oa.parse_list(LIST)
    assert [i["id"] for i in r["items"]] == ["111", "222"]
    a, b = r["items"]
    assert a["top"] and a["title"] == "放假安排" and a["dept"] == "校长办公室" and a["time"] == "2026-10-01 08:05"
    assert not b["top"] and b["url"].endswith("id=222&channelId=179577")
    assert r["channels"] == {"179577": "校内通知", "179578": "学术讲座"} and r["total_pages"] == 37


def test_detail():
    d = oa.parse_detail(DETAIL)
    assert d["title"] == "放假安排" and d["text"] == "正文" and len(d["attachments"]) == 1
    assert d["attachments"][0]["name"] == "附件" and "attachdownload" in d["attachments"][0]["url"]


def test_fetch_and_save(tmp_path):
    c = Fake(pages=3)
    r = oa.fetch_notices(c, limit=5, max_pages=5)
    assert r["count"] == 5 and len({i["id"] for i in r["items"]}) == 5
    oa._search_pref = ()  # 强制本地过滤
    r2 = oa.fetch_notices(Fake(1), keyword="教务")
    oa._search_pref = None
    assert [i["id"] for i in r2["items"]] == ["222"]
    oa.save(tmp_path, r)
    oa.save(tmp_path, r2)
    d = json.loads((tmp_path / "oa_notices.json").read_text(encoding="utf-8"))
    assert len(d["channels_items"]["179577"]) == 5 and d["channels"]["179578"] == "学术讲座"
    assert d["channels_updated"]["179577"] == r2["fetched_at"]
    assert oa.channel_fetched_at(d, "179577") == r2["fetched_at"]


def test_login_needed():
    with pytest.raises(oa.jwxt.LoginError):
        oa.fetch_notices(Fake(1, login=True))


def test_probe_ascii_no_titles():
    rep = oa.probe(Fake(2), anon_client=Fake(2))
    s = json.dumps(rep)
    assert s.isascii() and "放假" not in json.dumps(rep, ensure_ascii=False)
    assert rep["list"]["rows"] == 2 and rep["list"]["categories"] == 2 and rep["detail"]["has_title"]
    assert rep["login_page"]["input_names"] == ["userAccount", "userPassword"]
    assert rep["session_reuse"]["ok"]


def test_read_only_guard():
    with pytest.raises(ValueError):
        oa.get(Fake(1), oa.BASE + "/WorkFlowAction!submit.action")


def test_category():
    assert oa.resolve_category("", {}) == "179577"
    assert oa.resolve_category("讲座", {"179578": "学术讲座"}) == "179578"


def test_cli_main_oa_probe_and_notices(monkeypatch, capsys, tmp_path):
    from jlu_toolkit import cli, jwxt, ui
    monkeypatch.setattr(jwxt.JwxtClient, "load_session", lambda self: False)
    monkeypatch.setattr(jwxt.JwxtClient, "_request", lambda self, url, **kw: Fake(2)._request(url, **kw))
    monkeypatch.setattr(ui, "data_dir", lambda: tmp_path)
    cli.main(["oa", "--probe"])
    rep = json.loads(capsys.readouterr().out)
    assert rep["list"]["rows"] == 2 and rep["saved_session"] is False
    cli.main(["oa", "notices", "--limit", "3", "--json"])
    assert json.loads(capsys.readouterr().out)["count"] == 3
    assert (tmp_path / "oa_notices.json").exists()


def test_cli_all_handlers_defined():
    import re
    from jlu_toolkit import cli
    src = open(cli.__file__, encoding="utf-8").read()
    for name in set(re.findall(r"\b(_cmd_\w+)\(x\)", src)):
        assert callable(getattr(cli, name, None)), name


ROW = ('<div class="li rel"><a class="font14" href="PortalInformation!getInformation.action?id={id}&channelId={ch}">'
       '{t}</a><span>2026年10月0{d}日 08:00</span><a href="#">单位</a></div>')
POOL = [("501", "179577", "2025 教务通知", 1), ("502", "179578", "2025 讲座", 2),
        ("503", "179577", "放假", 3), ("504", "179579", "通知 2025", 4)]


class Server(Fake):
    """模拟实测：GET/POST searchId UTF-8 无 channelId 才过滤（跨栏目）；带 channelId 忽略；GBK 中文 0 行。"""

    def _request(self, url, data=None, headers=None, method=None, allow_redirects=True):
        if "searchId" in url or data is not None:
            self.urls.append(url)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if data is not None:
            q = urllib.parse.parse_qs(data.decode("ascii"))
        raw = (data or b"").decode() + url
        if "searchId" in q or "searchId=" in raw:
            if "channelId" in q:
                return Fake._request(self, oa.list_url(), None, headers, None, allow_redirects)
            kw = None
            try:
                src = data.decode() if data is not None else urllib.parse.urlparse(url).query
                kw = urllib.parse.unquote(src.split("searchId=")[1].split("&")[0], errors="strict")
            except UnicodeDecodeError:
                pass
            rows = [r for r in POOL if kw and kw in r[2]]
            h = "".join(ROW.format(id=i, ch=c, t=tt, d=d) for i, c, tt, d in rows) or "<html></html>"
            return 200, h, url, h.encode()
        return Fake._request(self, url, data, headers, method, allow_redirects)


def test_search_variants_real_behaviour():
    sv = oa.search_variants(Server(1))
    assert sv["get_searchId_utf8"]["filters"] and sv["post_searchId_utf8"]["filters"]
    assert not sv["get_searchId_utf8_ch"]["filters"] and sv["get_searchId_utf8_ch"]["rare"]["rows"] == 2
    assert sv["get_searchId_gbk"]["cjk"]["rows"] == 0 and sv["get_searchId_utf8"]["rare"]["rows"] == 0
    assert sv["get_searchId_utf8"]["ascii"] == {"rows": 3, "overlap": 0, "hits": 3}


def test_filters_tolerates_body_matches(monkeypatch):
    real = oa.parse_list
    def fuzzy(h):  # 5 行里 1 行标题不含关键字（正文命中）→ 80% 仍判定为过滤
        r = real(h)
        if any(i["id"] == "501" for i in r["items"]):
            r["items"] = r["items"][:1] * 4 + [{**r["items"][0], "id": "x", "title": "其他"}]
        return r
    monkeypatch.setattr(oa, "parse_list", fuzzy)
    assert oa.search_variants(Server(1))["get_searchId_utf8"]["filters"]


def test_notices_server_search_and_channel_filter():
    oa._search_pref = None
    c = Server(1)
    r = oa.fetch_notices(c, keyword="2025", limit=10)
    assert r["search"] == "server" and [i["id"] for i in r["items"]] == ["501", "502", "504"]
    assert "channelId" not in c.urls[-1] and "searchId=2025" in c.urls[-1]
    r = oa.fetch_notices(Server(1), channel="179577", keyword="2025", channel_filter=True)
    assert [i["id"] for i in r["items"]] == ["501"] and r["channel_filtered"]
    c = Server(1)
    r = oa.fetch_notices(c, keyword="教务")
    assert r["count"] == 1 and "searchId=%E6%95%99%E5%8A%A1" in c.urls[0]


def test_channels_discovery():
    d = oa.discover_channels(Fake(1))
    assert d["channels"]["190001"] == "学术讲座" and d["channels"]["190002"] == "放假安排"
    assert d["sources"]["jldx_left.js"] == 1


def test_channel_fetched_at_prefers_per_channel():
    d = {"updated": "2026-11-01T10:00:00",
         "channels_updated": {"179577": "2026-11-01T10:00:00", "179578": "2026-11-02T18:00:00"}}
    assert oa.channel_fetched_at(d, "179577") == "2026-11-01T10:00:00"
    assert oa.channel_fetched_at(d, "179578") == "2026-11-02T18:00:00"
    assert oa.channel_fetched_at({"updated": "2026-10-01T00:00:00"}, "179577") == "2026-10-01T00:00:00"


def test_fetch_detail_and_merge(tmp_path):
    item = {"id": "111", "title": "放假安排", "channel": "179577",
            "url": oa.DETAIL + "?id=111&channelId=179577"}
    d = oa.fetch_detail(Fake(1), item)
    assert d["text"] == "正文" and len(d["attachments"]) == 1
    oa.save(tmp_path, {"channel": "179577", "fetched_at": "2026-11-02T12:00:00",
                       "items": [{"id": "111", "title": "放假安排", "dept": "校长办公室",
                                  "time": "2026-10-01 08:05", "top": True, "channel": "179577",
                                  "url": item["url"]}], "channels": {}})
    merged = oa.merge_detail(tmp_path, "111", d)
    assert merged["text"] == "正文" and merged["attachments"][0]["name"] == "附件"
    cached = json.loads((tmp_path / "oa_notices.json").read_text(encoding="utf-8"))
    assert cached["channels_items"]["179577"][0]["text"] == "正文"


def _row(i, t, d, top=False, extra=""):
    mark = "<font class=red>[置顶]</font>" if top else ""
    return (f'<div class="li rel"><a class="font14" href="PortalInformation!getInformation.action?id={i}&channelId=179577">'
            f'{mark}{extra}{t}</a><a class="column">示例处</a><span class="time">{d}&nbsp;08:00</span></div>')


def test_font_without_pin_marker_is_not_pinned():
    r = oa.parse_list(_row(1, "示例新通知", "2026-10-30", extra="<font color=red>NEW</font>") + _row(2, "示例置顶", "2026-10-01", True))
    assert [(i["id"], i["top"]) for i in r["items"]] == [("1", False), ("2", True)]
    assert r["items"][1]["title"] == "示例置顶"


def test_unpinned_old_notice_does_not_stay_on_top(tmp_path):
    """#161：安装时置顶的旧通知取消置顶后，不能永远排在新通知上面。"""
    from jlu_toolkit import ui
    old = oa.parse_list(_row(900, "示例奖学金评选", "2026-10-10", True) + _row(899, "示例旧通知", "2026-10-09"))
    oa.save(tmp_path, {"channel": "179577", "fetched_at": "t1", "items": old["items"], "channels": {}, "page1": True})
    new = oa.parse_list(_row(950, "示例新置顶", "2026-11-01", True) + _row(949, "示例新通知", "2026-10-31"))
    oa.save(tmp_path, {"channel": "179577", "fetched_at": "t2", "items": new["items"], "channels": {}, "page1": True})
    ids = [i["id"] for i in ui.oa_notices_api(ui.Store(tmp_path), {})["items"]]
    assert ids == ["950", "949", "900", "899"]


def test_keyword_result_does_not_clear_pins(tmp_path):
    a = oa.parse_list(_row(5, "示例置顶", "2026-10-10", True))
    oa.save(tmp_path, {"channel": "179577", "fetched_at": "t1", "items": a["items"], "channels": {}, "page1": True})
    oa.save(tmp_path, {"channel": "179577", "fetched_at": "t2", "items": [], "channels": {}})
    d = json.loads((tmp_path / "oa_notices.json").read_text(encoding="utf-8"))
    assert d["channels_items"]["179577"][0]["top"] is True


def test_numeric_id_tiebreak():
    items = [{"id": "999999", "time": "2026-10-01"}, {"id": "1000000", "time": "2026-10-01"}]
    assert sorted(items, key=oa.sort_key, reverse=True)[0]["id"] == "1000000"


# ── 真实 OA 第 1 页节选（2026-11-03）：近两天的通知显示「今天/昨天 HH:MM」 ──
import datetime as _dt
from pathlib import Path as _P

LIVE = (_P(__file__).parent / "fixtures" / "oa_live_p1.html").read_text(encoding="utf-8")
NOW = _dt.datetime(2026, 11, 3, 10, 0, tzinfo=_dt.timezone(_dt.timedelta(hours=8)))


def test_parse_time_relative_and_no_year():
    assert oa.parse_time("今天\xa0\xa0 09:09", NOW) == "2026-11-03 09:09"
    assert oa.parse_time("昨天  15:52", NOW) == "2026-11-02 15:52"
    assert oa.parse_time("前天 08:00", NOW) == "2026-11-01 08:00"
    assert oa.parse_time("10-30", NOW) == "2026-10-30"
    assert oa.parse_time("12-30", NOW) == "2025-12-30"  # 不会跑到未来
    assert oa.parse_time("2026-10-30", NOW) == "2026-10-30"
    nyd = _dt.datetime(2027, 1, 1, 8, 0)
    assert oa.parse_time("昨天 23:00", nyd) == "2026-12-31 23:00"


def test_live_page1_fixture():
    r = oa.parse_list(LIVE, NOW)
    items = r["items"]
    assert len(items) == 11 and sum(i["top"] for i in items) == 7 and r["total_pages"] == 2515
    assert all(oa.is_dated(i["time"]) for i in items)
    assert items[0]["time"] == "2026-11-02 09:18" and items[7]["time"] == "2026-11-03 09:09"
    assert all(i["dept"] and not i["title"].startswith("[置顶]") for i in items)


def test_relative_times_never_outrank_new_dates_after_days(tmp_path):
    """#161 主因复现：旧缓存原样存了「今天 09:09」，字符串排序时永远压在真实日期上面。"""
    from jlu_toolkit import ui
    old_cache = {"updated": "2026-10-10T12:00:00", "channels_updated": {"179577": "2026-10-10T12:00:00"},
                 "channels": {}, "channels_items": {"179577": [
                     {"id": "100", "title": "示例奖学金", "dept": "示例处", "time": "今天 09:00", "top": False, "url": ""},
                     {"id": "99", "title": "示例旧", "dept": "示例处", "time": "昨天 10:00", "top": False, "url": ""},
                     {"id": "98", "title": "示例无日期", "dept": "示例处", "time": "未知", "top": False, "url": ""}]}}
    (tmp_path / "oa_notices.json").write_text(json.dumps(old_cache, ensure_ascii=False), encoding="utf-8")
    # 读取时就迁移：旧版本留下的相对时间无法可靠还原，当作未知
    j = ui.oa_notices_api(ui.Store(tmp_path), {})
    assert [(i["id"], i["time"]) for i in j["items"]] == [("100", ""), ("99", ""), ("98", "")]
    # 刷新后新通知排在最上面，无法识别日期的排最后
    r = oa.parse_list(LIVE, NOW)
    oa.save(tmp_path, {"channel": "179577", "fetched_at": NOW.replace(tzinfo=None).isoformat(),
                       "items": r["items"], "channels": {}, "page1": True})
    ids = [i["id"] for i in ui.oa_notices_api(ui.Store(tmp_path), {})["items"] if not i["top"]]
    assert ids[0] == "71736581" and ids[-1] == "98" and ids.index("100") > ids.index("71645669")
    cached = json.loads((tmp_path / "oa_notices.json").read_text(encoding="utf-8"))["channels_items"]["179577"]
    assert {i["id"]: i["time"] for i in cached}["100"] == ""
    assert all(oa.is_dated(i["time"]) for i in cached if i["id"].startswith("71"))


def test_undated_item_without_reference_sorts_last():
    items = [{"id": "1", "time": "今天 09:00"}, {"id": "2", "time": "2026-01-01"}]
    assert oa.normalize_cached(items, None)[0]["time"] == ""
    assert sorted(items, key=oa.sort_key, reverse=True)[0]["id"] == "2"


def test_legacy_relative_time_not_dated_by_later_refresh():
    """旧缓存：10 月 10 日存下「今天 09:00」，11 月 2 日的刷新不能把它算成 11 月 2 日。"""
    items = [{"id": "1", "time": "今天 09:00"}, {"id": "2", "time": "10-30"}, {"id": "3", "time": "2026-11-01"}]
    out = oa.normalize_cached(items, "2026-11-02T18:00:00")
    assert [i["time"] for i in out] == ["", "2026-10-30", "2026-11-01"]
    assert [i["id"] for i in sorted(out, key=oa.sort_key, reverse=True)] == ["3", "2", "1"]


def test_midnight_and_keyword_paths():
    late = _dt.datetime(2026, 11, 3, 0, 5, tzinfo=_dt.timezone(_dt.timedelta(hours=8)))
    assert oa.parse_time("昨天 23:59", late) == "2026-11-02 23:59"
    utc = _dt.datetime(2026, 11, 2, 16, 30, tzinfo=_dt.timezone.utc)  # = 北京时间 11-03 00:30
    assert oa.parse_time("今天 00:10", utc) == "2026-11-03 00:10"
    oa._search_pref = ()
    try:
        assert oa.fetch_notices(Fake(1), keyword="教务")["page1"] is False
    finally:
        oa._search_pref = None
    assert oa.fetch_notices(Fake(1))["page1"] is True
