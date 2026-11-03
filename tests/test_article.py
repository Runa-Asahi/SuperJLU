"""通知正文清洗（OA / 学院官网）。"""
import json
from pathlib import Path

from jlu_toolkit import article, college, oa, ui

FIX = Path(__file__).parent / "fixtures" / "college"
BASE = "https://csw.jlu.edu.cn/info/1009/8158.htm"

WORD = """<div class="v_news_content"><p style="margin:0;font-size:24px" class="MsoNormal"><span style="font-family:等线">
标题&nbsp;&nbsp;&nbsp;一</span></p><p>&nbsp;</p><p><o:p></o:p></p><p><br></p><br><br><br>
<p onclick="x()">正文<script>alert(1)</script><style>p{color:red}</style><font size=7>大字</font></p>
<table border=1 style="width:900px"><tr><td colspan="2" style="x">合并</td></tr><tr><td>a</td><td>b</td></tr></table>
<img src="/__local/a.png" onerror="x()"><img src="https://evil.example/t.png">
<a href="javascript:alert(1)">坏链接</a><a href="../x.pdf">附件</a></div>"""


def test_clean_html_strips_junk_and_keeps_structure():
    h = article.extract(WORD, BASE)["html"]
    for bad in ("style=", "class=", "onclick", "onerror", "<script", "alert", "<span", "<font", "o:p",
                "evil.example", "javascript:", "&nbsp;", "<p></p>"):
        assert bad not in h, bad
    assert "<p>标题 一</p>" in h and "大字" in h
    assert '<td colspan="2">合并</td>' in h
    assert '<img src="https://csw.jlu.edu.cn/__local/a.png"' in h
    assert '<a href="https://csw.jlu.edu.cn/info/x.pdf"' in h and "<a>坏链接</a>" in h
    assert "<br>" not in h


def test_csw_live_detail():
    r = article.extract((FIX / "csw_detail.html").read_text(encoding="utf-8"), BASE)
    assert r["html"].startswith("<p><strong>关于申报 2025 年")
    assert "font-family" not in r["html"] and "报名对象" in r["text"]
    assert [a["name"][:3] for a in r["attachments"]] == ["附件2", "附件1"]
    assert all(a["url"].startswith("https://csw.jlu.edu.cn/system/_content/download.jsp") for a in r["attachments"])


def test_oa_parse_detail_html():
    d = oa.parse_detail('<div class="content_t">T</div><div class="content_font"><p style="x">一&nbsp;二</p>'
                        '<p>&nbsp;</p></div><a href="rd/download/attachdownload.jsp?res=1">附件.docx</a>')
    assert d["html"] == "<p>一 二</p>" and d["text"] == "一 二"
    assert d["attachments"][0]["url"].startswith("https://oa.jlu.edu.cn/defaultroot/rd/download/")


def _college_cache(root, item):
    (root / college.CACHE).write_text(json.dumps({"channels_items": {"csw-xytz": [item]}}, ensure_ascii=False),
                                      encoding="utf-8")


ITEM = {"id": "csw-xytz:1009-8158", "title": "示例", "time": "2025-12-01", "dept": "软件学院",
        "top": False, "url": BASE, "channel": "csw-xytz"}


def test_college_detail_fetched_inline_and_cached(tmp_path, monkeypatch):
    _college_cache(tmp_path, ITEM)
    page = (FIX / "csw_detail.html").read_text(encoding="utf-8")
    calls = []
    monkeypatch.setattr(college, "_get", lambda url, timeout=10: calls.append(url) or page)
    st = ui.Store(tmp_path)
    it = ui.oa_notice_api(st, ITEM["id"])["item"]
    assert it["source"] == "college" and it["html"].startswith("<p><strong>") and len(it["attachments"]) == 2
    assert it["url"] == BASE and "detail_error" not in it
    assert ui.oa_notice_api(st, ITEM["id"])["item"]["html"] and calls == [BASE]  # 第二次读缓存


def test_college_detail_failure_keeps_original_link(tmp_path, monkeypatch):
    _college_cache(tmp_path, ITEM)

    def boom(url, timeout=10):
        raise OSError("down")
    monkeypatch.setattr(college, "_get", boom)
    it = ui.oa_notice_api(ui.Store(tmp_path), ITEM["id"])["item"]
    assert it["html"] == "" and it["url"] == BASE and "打开原文" in it["detail_error"]
    assert "OSError" not in json.dumps(it, ensure_ascii=False)


def test_cached_html_is_resanitized(tmp_path):
    _college_cache(tmp_path, {**ITEM, "html": '<p onclick="x">ok</p><script>alert(1)</script>'})
    it = ui.oa_notice_api(ui.Store(tmp_path), ITEM["id"], fetch_body=False)["item"]
    assert it["html"] == "<p>ok</p>"


def test_page_renders_rich_body():
    from jlu_toolkit.ui_page import PAGE
    assert 'class="body rich">${i.html}' in PAGE and ".oad .rich img{max-width:100%" in PAGE
    assert "学院新闻只保存标题" not in PAGE


def test_poster_only_body_kept():
    h = '<div class="v_news_content"><p><br></p><p><img src="/__local/a.jpg" class="img_vsb_content"></p></div>'
    r = article.extract(h, "https://ciee.jlu.edu.cn/info/1/2.htm")
    assert r["html"] == '<p><img src="https://ciee.jlu.edu.cn/__local/a.jpg" alt="" loading="lazy"></p>'


def test_oa_malformed_body_falls_back_to_loose_cut():
    # Word 粘贴常见：正文里多一个 </div>，按深度配对会提前结束
    h = ('<div class="content_t">T</div><div class="content_font"></div><p>第一段</p><p>第二段</p>'
         '<div class="fujian"><a href="rd/download/attachdownload.jsp?res=1">附件.docx</a></div></body>')
    d = oa.parse_detail(h)
    assert "第一段" in d["text"] and "第二段" in d["html"] and len(d["attachments"]) == 1


def test_college_on_android_falls_back_to_system_tls(monkeypatch):
    import io
    import urllib.response
    from email.message import Message
    from jlu_toolkit import network
    monkeypatch.setenv("ANDROID_ROOT", "/system")
    seen = []

    def fake_native(req, timeout):
        seen.append(req.full_url)
        r = urllib.response.addinfourl(io.BytesIO("<p>ok</p>".encode()), Message(), req.full_url, 200)
        r.msg = "OK"
        return r
    import ssl
    import urllib.request

    def py_fail(self, req):
        raise urllib.error.URLError(ssl.SSLCertVerificationError("unable to get local issuer certificate"))
    monkeypatch.setattr(urllib.request.HTTPSHandler, "https_open", py_fail)
    monkeypatch.setattr(network, "native_open", fake_native)
    monkeypatch.setattr(college, "_NATIVE_HOSTS", set())
    assert college._get(BASE) == "<p>ok</p>" and seen == [BASE]
    assert college._get(BASE) == "<p>ok</p>" and seen == [BASE, BASE]  # 之后直接走系统 HTTPS
    monkeypatch.delenv("ANDROID_ROOT")
    monkeypatch.setattr(college, "_NATIVE_HOSTS", set())
    import pytest
    with pytest.raises(Exception):
        college._get(BASE)  # 电脑端不改走系统通道，仍按原样报错


def test_detail_failure_logged_not_shown(tmp_path, monkeypatch):
    _college_cache(tmp_path, ITEM)

    def boom(url, timeout=10):
        raise ConnectionResetError("reset")
    monkeypatch.setattr(college, "_get", boom)
    st = ui.Store(tmp_path)
    it = ui.oa_notice_api(st, ITEM["id"])["item"]
    assert "reset" not in json.dumps(it, ensure_ascii=False)
    log = st.p("notice_detail.log").read_text(encoding="utf-8")
    assert "college" in log and "ConnectionResetError" in log


def test_college_existing_text_kept_when_fetch_fails(tmp_path, monkeypatch):
    _college_cache(tmp_path, {**ITEM, "text": "旧正文"})
    monkeypatch.setattr(college, "_get", lambda url, timeout=10: (_ for _ in ()).throw(OSError("x")))
    it = ui.oa_notice_api(ui.Store(tmp_path), ITEM["id"])["item"]
    assert it["text"] == "旧正文" and "detail_error" not in it


def test_oa_detail_uses_vpn_cookies_without_session(monkeypatch):
    from jlu_toolkit import jwxt
    monkeypatch.setattr(jwxt.JwxtClient, "load_session", lambda self, path=None: False)
    sentinel = object()
    monkeypatch.setattr(ui, "_client", lambda: sentinel)
    assert ui._oa_detail_client() == (sentinel, False)

    def no_login():
        raise jwxt.LoginError("x")
    monkeypatch.setattr(ui, "_client", no_login)
    c, has = ui._oa_detail_client()
    assert isinstance(c, jwxt.JwxtClient) and has is False


def test_old_parse_version_refetched_once(tmp_path, monkeypatch):
    _college_cache(tmp_path, {**ITEM, "html": "<p>旧</p>", "text": "旧"})  # 旧版本缓存：没有 dv
    page = (FIX / "csw_detail.html").read_text(encoding="utf-8")
    calls = []
    monkeypatch.setattr(college, "_get", lambda url, timeout=10: calls.append(url) or page)
    st = ui.Store(tmp_path)
    assert ui.oa_notice_api(st, ITEM["id"])["item"]["html"].startswith("<p><strong>")
    ui.oa_notice_api(st, ITEM["id"])
    assert calls == [BASE]


def test_old_parse_version_kept_when_offline(tmp_path, monkeypatch):
    _college_cache(tmp_path, {**ITEM, "html": "<p>旧</p>", "text": "旧"})
    monkeypatch.setattr(college, "_get", lambda url, timeout=10: (_ for _ in ()).throw(OSError("x")))
    it = ui.oa_notice_api(ui.Store(tmp_path), ITEM["id"])["item"]
    assert it["html"] == "<p>旧</p>" and "detail_error" not in it
