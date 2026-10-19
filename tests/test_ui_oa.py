"""Web UI 的 OA 通知接口：只读本地 data/oa_notices.json；刷新只取第 1 页。"""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import jwxt, oa, ui

SAMPLE = {"updated": "2026-10-15T09:00:00", "channels": {"179577": "校内通知"},
          "channels_items": {"179577": [
              {"id": "1", "title": "示例：运动会停课安排", "dept": "示例教务处", "time": "2026-10-14 08:00",
               "top": False, "url": "https://oa.jlu.edu.cn/defaultroot/PortalInformation!getInformation.action?id=1&channelId=179577"},
              {"id": "2", "title": "示例：奖学金评审通知", "dept": "示例学生处", "time": "2026-10-10 09:00", "top": True,
               "url": "https://oa.jlu.edu.cn/defaultroot/x?id=2", "text": "正文示例",
               "attachments": [{"name": "附件.docx", "url": "rd/download/attachdownload.jsp?res=abc"},
                               {"name": "恶意", "url": "https://evil.example/x"}]},
              {"id": "3", "title": "示例：讲座预告", "dept": "示例研究院", "time": "2026-10-12 10:00",
               "top": False, "url": "javascript:alert(1)"}]}}


@pytest.fixture
def srv(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", tmp_path
    httpd.shutdown()


def _get(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_notices_empty(srv):
    base, _ = srv
    code, j = _get(base + "/api/oa/notices")
    assert code == 200 and j["ok"] and j["count"] == 0 and j["items"] == [] and j["channel"] == "179577"


def test_notices_shape_filter_and_sanitize(srv):
    base, root = srv
    (root / "oa_notices.json").write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
    _, j = _get(base + "/api/oa/notices")
    assert set(j) >= {"ok", "channel", "channel_name", "count", "fetched_at", "items"}
    assert j["channel_name"] == "校内通知" and j["count"] == 3
    assert [i["id"] for i in j["items"]] == ["2", "1", "3"]  # 置顶优先，再按时间
    assert set(j["items"][0]) == {"id", "title", "time", "dept", "top", "url"}
    assert j["items"][2]["url"] == ""  # 非 OA 链接被丢弃
    _, j = _get(base + "/api/oa/notices?keyword=" + urllib.request.quote("学生处") + "&limit=5")
    assert [i["id"] for i in j["items"]] == ["2"]
    _, j = _get(base + "/api/oa/notices?limit=1")
    assert j["count"] == 1
    code, j = _get(base + "/api/oa/notices?limit=x")
    assert code == 400 and j["ok"] is False
    _, j = _get(base + "/api/oa/channels")
    oa_only = [c for c in j["channels"] if "-" not in c["id"]]
    assert oa_only and oa_only[0]["id"] == "179577" and oa_only[0]["name"] == "校内通知"


def test_notice_detail(srv):
    base, root = srv
    (root / "oa_notices.json").write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
    _, j = _get(base + "/api/oa/notice?id=2")
    it = j["item"]
    assert it["text"] == "正文示例"
    assert it["attachments"] == [{"name": "附件.docx",
                                  "url": "https://oa.jlu.edu.cn/defaultroot/rd/download/attachdownload.jsp?res=abc"}]
    code, j = _get(base + "/api/oa/notice?id=999")
    assert code == 404 and j["ok"] is False


def test_refresh_fetches_page_one_only(srv, monkeypatch):
    base, root = srv
    seen = {}

    def fake_fetch(client, channel="179577", keyword="", limit=30, max_pages=5):
        seen.update(channel=channel, max_pages=max_pages)
        return {"channel": channel, "channel_name": "校内通知", "fetched_at": "2026-10-15T10:00:00", "count": 1,
                "items": [{"id": "9", "title": "示例新通知", "dept": "示例处", "time": "2026-10-15 09:00",
                           "top": False, "channel": channel, "url": oa.BASE + "/x?id=9"}], "channels": {}}
    monkeypatch.setattr(jwxt.JwxtClient, "load_session", lambda self: False)
    monkeypatch.setattr(oa, "fetch_notices", fake_fetch)
    code, j = _post(base + "/api/oa/refresh", {})
    assert code == 200 and j["ok"] and seen == {"channel": "179577", "max_pages": 1}
    assert j["items"][0]["id"] == "9" and (root / "oa_notices.json").exists()


def test_refresh_errors(srv, monkeypatch):
    base, _ = srv
    monkeypatch.setattr(jwxt.JwxtClient, "load_session", lambda self: False)

    def boom(*a, **k):
        raise jwxt.NetworkError("timeout")
    monkeypatch.setattr(oa, "fetch_notices", boom)
    code, j = _post(base + "/api/oa/refresh", {})
    assert code == 502 and j["offline"] and not j["campus_required"]
    assert j["browser_vpn_supported"] and not j["app_vpn_supported"]
    assert "学校 WebVPN" in j["error"] and "OA 同步仍走直连" in j["error"]
    assert "学院通知" in j["error"] and "先连 vpn" not in j["error"]

    def need(*a, **k):
        raise jwxt.LoginError("OA 需要登录")
    monkeypatch.setattr(oa, "fetch_notices", need)
    code, j = _post(base + "/api/oa/refresh", {})
    assert code == 400 and j["login_needed"] is True


def test_page_has_oa_tab():
    from jlu_toolkit.ui_page import PAGE
    assert 'data-t="oa"' in PAGE and 'id="t-oa"' in PAGE and "/api/oa/notices" in PAGE
    assert "学校 OA 可经校园网或学校 VPN 访问" in PAGE
    assert 'href="/api/oa/webvpn"' in PAGE and "OA 通知同步仍走直连" in PAGE
    assert "需校园网直连" not in PAGE
    assert "/api/oa/subscriptions" in PAGE
    # CLI watch/notices wording may appear in empty-state copy; do not require it.


def test_oa_tab_always_loads_subscriptions():
    """Keyword subscription UI must load even when OA was already filled by refresh."""
    from jlu_toolkit.ui_page import PAGE
    # Tab click must call loadSubs whether or not OA is already loaded.
    assert '(OA?Promise.resolve():loadOA()).then(loadSubs)' in PAGE
    assert 'if(!OA){loadOA().then(loadSubs)}' not in PAGE
    # fullRefresh should also warm subscriptions after loadOA.
    assert 'loadOA().then(loadSubs).catch(()=>{})' in PAGE
    # Avoid TDZ / isolated-extract ReferenceError: loadSubs before fullRefresh.
    assert PAGE.index('async function loadSubs(') < PAGE.index('async function fullRefresh(')


def test_oa_webvpn_link_only_redirects_to_official_portal(srv):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs): return None
    opener = urllib.request.build_opener(NoRedirect())
    base, _ = srv
    with pytest.raises(urllib.error.HTTPError) as error:
        opener.open(base + "/api/oa/webvpn?target=https://evil.example/")
    assert error.value.code == 302
    assert error.value.headers["Location"] == "https://vpn.jlu.edu.cn/"
    assert error.value.headers.get("Set-Cookie") is None


def test_channels_from_file_and_category(srv):
    base, root = srv
    _, j = _get(base + "/api/oa/channels")
    oa_only = [c for c in j["channels"] if "-" not in c["id"]]
    assert oa_only and oa_only[0]["id"] == "179577" and oa_only[0]["name"] == "校内通知"  # 无文件时回退
    (root / "oa_channels.json").write_text(json.dumps({"179578": "学术讲座", "179579": "示例公告"}, ensure_ascii=False),
                                           encoding="utf-8")
    d = json.loads(json.dumps(SAMPLE))
    d["channels_items"]["179578"] = [{"id": "50", "title": "示例讲座", "dept": "示例学院", "time": "2026-10-15 08:00",
                                      "top": False, "url": ""}]
    (root / "oa_notices.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    _, j = _get(base + "/api/oa/channels")
    assert [c["id"] for c in j["channels"] if "-" not in c["id"]] == ["179577", "179578", "179579"]
    _, j = _get(base + "/api/oa/notices?category=179578")
    assert j["channel_name"] == "学术讲座" and [i["id"] for i in j["items"]] == ["50"]
    _, j = _get(base + "/api/oa/notices?category=" + urllib.request.quote("讲座"))
    assert j["channel"] == "179578"
    _, j = _get(base + "/api/oa/notices?category=179579")
    assert j["count"] == 0
