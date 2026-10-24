"""本地接口令牌：同机其它程序（Android 上的其它 App）不带令牌时什么都拿不到。"""
import http.client
import importlib.util
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from jlu_toolkit import desktop, jwxt, sessions, ui, ui_check

pytestmark = pytest.mark.real_ui_auth

CK = [{"name": "CASTGC", "value": "TGT-secret", "domain": "cas.jlu.edu.cn", "path": "/"}]
H = {"Host": "127.0.0.1"}


class FakeLogin:
    def __init__(self):
        self.started = []

    def start(self, username, password, remember=True):
        self.started.append(username)
        return {"step": "need_second_factor"}

    def accounts(self):
        return [{"username": "stu"}]

    def delete_account(self, username):
        self.started.append("deleted:" + username)
        return True

    def saved_username(self):
        return "stu"


@pytest.fixture
def srv(tmp_path):
    login = FakeLogin()
    handler = ui.make_handler(ui.Store(tmp_path), login=login)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_address[1], handler.auth_token, login
    httpd.shutdown()
    httpd.server_close()


def _req(port, method, path, headers=None, body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request(method, path, body=body, headers={**H, **(headers or {})})
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


def test_token_persisted_and_well_formed():
    t = ui.load_or_create_token()
    assert t == ui.load_or_create_token() and len(t) >= 32
    assert ui.token_path().read_text(encoding="utf-8").strip() == t
    if os.name != "nt":
        assert (ui.token_path().stat().st_mode & 0o077) == 0
    ui.token_path().write_text("garbage", encoding="utf-8")  # 损坏时重新生成
    assert ui.load_or_create_token() != "garbage"


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/data", None),
    ("GET", "/api/links", None),
    ("GET", "/api/login/accounts", None),
    ("GET", "/api/ics", None),
    ("POST", "/api/login/start", b'{"username":"","password":""}'),
    ("POST", "/api/refresh", b"{}"),
    ("DELETE", "/api/login/accounts/stu", None),
])
def test_api_rejects_without_token(srv, method, path, body):
    port, _, login = srv
    hdrs = {"Content-Type": "application/json"} if body else {}
    st, _, raw = _req(port, method, path, hdrs, body)
    assert st == 401 and json.loads(raw)["auth_required"] is True
    assert login.started == []  # 没有用已保存的账号登录，也没有删账号


def test_wrong_token_rejected(srv):
    port, token, _ = srv
    assert _req(port, "GET", "/api/data", {ui.TOKEN_HEADER: "x" * len(token)})[0] == 401
    assert _req(port, "GET", "/api/data", {"Cookie": ui.TOKEN_COOKIE + "=" + "y" * len(token)})[0] == 401


def test_sso_ticket_not_reachable_without_token(srv, monkeypatch):
    """原攻击链：/api/links 取 nonce → /api/sso/jump 拿到带 CAS ST 的 302。"""
    port, token, _ = srv
    monkeypatch.setattr(sessions, "migrate_cas_from_jwxt", lambda jar=None: 0)
    monkeypatch.setattr(sessions, "load_cookies", lambda s: CK if s == "cas" else None)
    monkeypatch.setattr(sessions, "save_cas_from_jar", lambda jar: 1)
    monkeypatch.setattr(jwxt.JwxtClient, "_request",
                        lambda self, url, **k: (302, "", "https://iedu.jlu.edu.cn/?ticket=ST-1-abc", b""))
    st, hdrs, _ = _req(port, "GET", "/api/sso/jump?id=jwxt&n=" + ui.SSO_NONCE)
    assert st == 401 and "ST-" not in str(hdrs)
    st, hdrs, _ = _req(port, "GET", "/api/sso/jump?id=jwxt&n=" + ui.SSO_NONCE,
                       {"Cookie": f"{ui.TOKEN_COOKIE}={token}"})
    assert st == 302 and hdrs["Location"].endswith("ticket=ST-1-abc")


def test_page_locked_without_token(srv):
    port, _, _ = srv
    st, hdrs, raw = _req(port, "GET", "/")
    assert st == 401 and "请从 SuperJLU 打开界面" in raw.decode() and b"<script" not in raw
    assert _req(port, "GET", "/?t=wrong")[0] == 401


def test_launch_url_sets_cookie_and_redirects(srv):
    port, token, _ = srv
    st, hdrs, _ = _req(port, "GET", "/?t=" + token)
    cookie = hdrs["Set-Cookie"]
    assert st == 302 and hdrs["Location"] == "/"
    assert cookie.startswith(f"{ui.TOKEN_COOKIE}={token};")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie and "Path=/" in cookie
    jar = {"Cookie": "other=1; " + cookie.split(";")[0]}
    st, _, raw = _req(port, "GET", "/", jar)
    assert st == 200 and b"<script>" in raw
    assert _req(port, "GET", "/api/data", jar)[0] == 200
    assert _req(port, "POST", "/api/login/start", {**jar, "Content-Type": "application/json"},
                b'{"username":"stu","password":"pw"}')[0] == 200


def test_header_token_and_public_favicon(srv):
    port, token, _ = srv
    assert _req(port, "GET", "/api/session", {ui.TOKEN_HEADER: token})[0] == 200
    assert _req(port, "GET", "/favicon.svg")[0] == 200


def test_host_check_still_applies_with_token(srv):
    port, token, _ = srv
    assert _req(port, "GET", "/api/data", {"Host": "evil.example", ui.TOKEN_HEADER: token})[0] == 403


def test_desktop_detects_instance_through_401(tmp_path):
    httpd, url = desktop.start_server(tmp_path / "data", port=0)
    try:
        assert desktop.is_running(httpd.server_address[1])
        assert url == desktop.url_for(httpd.server_address[1]) and "?t=" not in url
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ui_check_sends_token(tmp_path):
    out = ui_check.run(rooms=False, root=tmp_path)
    assert out["page"]["status"] == 200 and out["data"]["status"] == 200


def test_android_bootstrap_exposes_token(tmp_path, monkeypatch):
    for k in ("XDG_CONFIG_HOME", "JLU_TOOLKIT_NO_KEYRING"):
        monkeypatch.delenv(k, raising=False)
    src = Path(__file__).resolve().parents[1] / "android" / "app" / "src" / "main" / "python" / "jlu_android.py"
    spec = importlib.util.spec_from_file_location("jlu_android_token", src)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with pytest.raises(RuntimeError):
        m.auth_token()
    try:
        url = m.start(str(tmp_path))
        token = m.auth_token()
        assert (tmp_path / "config" / "jlu-toolkit" / ui.TOKEN_FILE).read_text(encoding="utf-8") == token
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(url + "api/data", timeout=5)
        assert e.value.code == 401
        req = urllib.request.Request(url + "api/data", headers={ui.TOKEN_HEADER: token})
        assert urllib.request.urlopen(req, timeout=5).status == 200
    finally:
        m.stop()


def test_main_activity_sends_token():
    act = next((Path(__file__).resolve().parents[1] / "android").rglob("MainActivity.java")).read_text(encoding="utf-8")
    assert f'TOKEN_COOKIE = "{ui.TOKEN_COOKIE}"' in act and f'TOKEN_HEADER = "{ui.TOKEN_HEADER}"' in act
    assert 'callAttr("auth_token")' in act and "CookieManager" in act and "HttpOnly" in act
    assert act.count("setRequestProperty(TOKEN_HEADER") == 2  # keepalive 和 ics 兜底下载
