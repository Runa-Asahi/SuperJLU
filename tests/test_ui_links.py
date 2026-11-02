"""校园服务入口：GET /api/links（内置配置 + 用户覆盖 + 域名白名单）。"""
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import jwxt, ui
from jlu_toolkit.ui_page import PAGE


@pytest.fixture
def srv(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, json.loads(r.read())


def _override(obj):
    p = jwxt.config_dir() / "campus_links.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_builtin_links(srv):
    code, j = _get(srv + "/api/links")
    assert code == 200 and j["ok"] and j["source"] == "builtin"
    ids = [x["id"] for x in j["links"]]
    assert ids == ["jwxt", "pay", "xsxk", "ilearn", "vpn", "lib"]
    for x in j["links"]:
        assert x["url"].startswith("https://") and x["url"].split("/")[2].endswith("jlu.edu.cn")
        assert x["name"] and x["purpose"] and x["login"] and isinstance(x["campus_only"], bool)
    il = next(x for x in j["links"] if x["id"] == "ilearn")
    assert "验证码" in il["login"]
    assert il["campus_only"] is False and "vpn_url" not in il and "vpn_sso_url" not in il


def test_ilearn_old_override_cannot_force_vpn(srv):
    _override({"links": [{"id": "ilearn", "campus_only": True,
                          "vpn_url": "https://vpn.jlu.edu.cn/old"}]})
    _, j = _get(srv + "/api/links")
    il = next(x for x in j["links"] if x["id"] == "ilearn")
    assert il["campus_only"] is False and "vpn_url" not in il and "vpn_sso_url" not in il


def test_override_merge_hide_add_and_allowlist(srv):
    _override({"links": [
        {"id": "lib", "name": "图书馆（改）"},
        {"id": "pay", "hidden": True},
        {"id": "jw", "name": "教务", "url": "https://iedu.jlu.edu.cn/", "purpose": "教务系统", "login": "统一认证",
         "vpn_url": "https://evil.example/x"},
        {"id": "bad", "name": "坏", "url": "https://jlu.edu.cn.evil.example/"},
        {"id": "bad2", "name": "坏2", "url": "javascript:alert(1)"},
        {"id": "bad3", "name": "坏3", "url": "http://lib.jlu.edu.cn/"},
    ]})
    _, j = _get(srv + "/api/links")
    assert j["source"] == "override" and j["dropped"] == 3
    by = {x["id"]: x for x in j["links"]}
    assert "pay" not in by and by["lib"]["name"] == "图书馆（改）" and by["lib"]["url"] == "https://lib.jlu.edu.cn/"
    assert list(by)[-1] == "jw" and "vpn_url" not in by["jw"]


def test_bad_override_ignored(srv):
    _override("{not json")
    _, j = _get(srv + "/api/links")
    assert j["source"] == "builtin" and "warning" in j and len(j["links"]) == 6


def test_page_has_links_tab_without_literal_urls():
    assert 'id="links"' in PAGE and "/api/links" in PAGE
    assert 'rel="noopener' in PAGE and "http://" not in PAGE and "https://" not in PAGE


def test_page_sessions_hook_defensive():
    # /api/sessions（PR #16）缺失时 404 → 不显示状态；401 带 site 时横幅点名站点
    assert "/api/sessions" in PAGE and "if(!r.ok)return null" in PAGE
    assert "session_site" in PAGE and "SITEN(D.session_site)" in PAGE


def test_header_title_never_truncated():
    assert '<span class="ttl">SuperJLU</span>' in PAGE
    assert "header .ttl{white-space:nowrap;flex:none}" in PAGE
    assert "safe-area-inset-top" in PAGE and 'aria-label="强制刷新"' in PAGE
