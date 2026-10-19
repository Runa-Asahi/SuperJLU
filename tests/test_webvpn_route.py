"""Application-owned VPN sessions and fixed HTTPS diagnostics; synthetic only."""
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import campus, connectivity, jwxt, network, sessions, ui, webvpn


def test_current_public_cas_redirect_vector_and_original_ports():
    # Public, unauthenticated school's login redirect; no account/ticket data.
    original = "https://cas.jlu.edu.cn/tpass/login"
    assert campus.vpn_url(original) == (
        "https://vpn.jlu.edu.cn/https/48714f71342f7a336d582f7e285737375ccd605402c6dbebb4864756174f/tpass/login")
    for url in (jwxt.IEDU_PORTAL, "https://iedu.jlu.edu.cn:8443/jwapp/?x=1", "http://iedu.jlu.edu.cn:8080/path"):
        assert webvpn.canonical_url(campus.vpn_url(url)) == url


def test_route_proxies_iedu_and_oa_but_preserves_cas_service_and_colleges():
    assert webvpn.request_url(jwxt.IEDU_PORTAL) == campus.vpn_url(jwxt.IEDU_PORTAL)
    oa = "https://oa.jlu.edu.cn/defaultroot/"
    assert webvpn.request_url(oa) == campus.vpn_url(oa)
    url = jwxt.CAS_LOGIN + "?service=" + urllib.parse.quote(jwxt.IEDU_PORTAL, safe="")
    proxied = urllib.parse.urlsplit(webvpn.request_url(url))
    assert proxied.hostname == "cas.jlu.edu.cn"
    assert urllib.parse.parse_qs(proxied.query)["service"] == [jwxt.IEDU_PORTAL]
    for url in ("https://csw.jlu.edu.cn/", "https://ccst.jlu.edu.cn/",
                "https://iedu.jlu.edu.cn.evil.invalid/", webvpn.SERVICE):
        assert webvpn.request_url(url) == url


def test_callback_and_proxied_cas_redirects_each_use_correct_route():
    from email.message import Message
    class Client: route = "webvpn"
    handler = webvpn.RedirectHandler(Client())
    source = urllib.request.Request(jwxt.CAS_LOGIN)
    callback = jwxt.REF_SCHEDULE + "?ticket=ST-synthetic"
    redirected = handler.redirect_request(source, None, 302, "Found", Message(), callback)
    assert redirected.full_url == campus.vpn_url(callback)
    cas = jwxt.CAS_LOGIN + "?service=" + urllib.parse.quote(jwxt.REF_SCHEDULE, safe="")
    redirected = handler.redirect_request(source, None, 302, "Found", Message(), campus.vpn_url(cas))
    assert redirected.full_url == cas  # Original CAS domain and service, not proxy service.


def test_new_cas_login_replaces_stale_jwxt_cas_cookie_only_once(monkeypatch):
    fresh = [{"name":"CASTGC", "value":"fresh", "domain":"cas.jlu.edu.cn", "path":"/tpass"}]
    monkeypatch.setattr(sessions, "load_cookies", lambda sid: fresh if sid == "cas" else [])
    c = jwxt.JwxtClient(route="webvpn")
    old = [{**fresh[0], "value":"stale"}]
    c.jar = jwxt.jar_from_list(old)
    c._restore_vpn_cookies()
    assert next(iter(c.jar)).value == "fresh"
    for cookie in jwxt.jar_from_list([{**fresh[0], "value":"renewed-by-server"}]): c.jar.set_cookie(cookie)
    c._restore_vpn_cookies()
    assert next(iter(c.jar)).value == "renewed-by-server"


def test_connect_uses_owned_cas_session_and_only_enables_route_after_validation(monkeypatch):
    monkeypatch.setenv("JLU_TOOLKIT_NO_KEYRING", "1")
    sessions.save_cookies("cas", [{"name": "CASTGC", "value": "synthetic", "domain": "cas.jlu.edu.cn"}])
    calls = []
    def reply(c, url, **kw):
        calls.append(url)
        assert c.has_cas_cookie()
        if urllib.parse.urlsplit(url).hostname == jwxt.IEDU_HOST:
            assert c.route == "webvpn"
            return 200, "business entry", url, b""
        assert c.route == "direct"
        cookie = jwxt.jar_from_list([{"name": "VPN", "value": "synthetic", "domain": "vpn.jlu.edu.cn"}])
        for item in cookie: c.jar.set_cookie(item)
        return 200, "resource portal", "https://vpn.jlu.edu.cn/", b""
    monkeypatch.setattr(jwxt.JwxtClient, "_request", reply)
    monkeypatch.setattr(campus, "check_vpn", lambda c: {"logged_in": True})
    assert webvpn.mode() == "direct"
    result = webvpn.connect()
    assert result["mode"] == "webvpn" and result["vpn"]["state"] == "ok"
    assert result["jwxt_ready"] is True
    assert urllib.parse.parse_qs(urllib.parse.urlsplit(calls[0]).query)["service"] == [webvpn.SERVICE]
    assert "synthetic" not in json.dumps(result)
    assert sessions.load_cookies("vpn")
    webvpn.set_mode("direct")
    assert jwxt.JwxtClient().route == "direct"


def test_no_cas_or_failed_vpn_does_not_enable_route(monkeypatch):
    monkeypatch.setattr(sessions, "migrate_cas_from_jwxt", lambda: 0)
    monkeypatch.setattr(sessions, "load_cookies", lambda *args: None)
    with pytest.raises(jwxt.LoginError): webvpn.connect()
    assert webvpn.mode() == "direct"
    monkeypatch.setattr(sessions, "load_cookies", lambda sid: [{"name":"CASTGC", "value":"test", "domain":"cas.jlu.edu.cn"}])
    monkeypatch.setattr(jwxt.JwxtClient, "_request", lambda *args, **kw: (200, '<form id="loginForm">', jwxt.CAS_LOGIN, b""))
    with pytest.raises(jwxt.LoginError): webvpn.connect()
    assert webvpn.mode() == "direct"


def test_separate_vpn_password_and_otp_flow_uses_vpn_service_not_jwxt():
    from jlu_toolkit.web_login import LoginFlow
    calls = []
    class Client:
        last_error_text = ""
        def login_password(self, username, password, service):
            calls.append(("password", service))
            return jwxt.LoginStep.NEED_SECOND_FACTOR
        def login_second_factor(self, image, otp):
            calls.append(("otp",))
            return jwxt.LoginStep.SUCCESS
        def bootstrap_emap_apps(self):
            pytest.fail("VPN must validate its own service first")
        def save_session(self):
            pytest.fail("VPN must not pretend the JWXT session was verified")
    client = Client()
    flow = LoginFlow(lambda: client, service=webvpn.SERVICE,
                     on_success=lambda c: {"jwxt_ready":False, "warning":"synthetic business failure"})
    assert flow.start("synthetic-user", "synthetic-password", remember=False)["step"] == "need_second_factor"
    result = flow.verify(wechat_code="synthetic-otp")
    assert result["step"] == "success" and result["jwxt_ready"] is False
    assert calls == [("password", webvpn.SERVICE), ("otp",)]


def test_direct_login_cancellation_and_failed_authentication_keep_active_vpn(monkeypatch):
    webvpn.set_mode("webvpn")
    calls = []
    class Client:
        def __init__(self, route):
            assert route == "direct"  # Campus login must use the explicit direct route.
        def login_password(self, username, password):
            return jwxt.LoginStep.NEED_SECOND_FACTOR
        def login_second_factor(self, image, otp):
            return jwxt.LoginStep.SUCCESS
        def bootstrap_emap_apps(self):
            calls.append("bootstrap")
        def save_session(self):
            assert webvpn.mode() == "webvpn"
            calls.append("save")
    monkeypatch.setattr(jwxt, "JwxtClient", Client)
    flow = webvpn.direct_login_flow()
    flow.start("synthetic", "synthetic", remember=False)
    assert webvpn.mode() == "webvpn"
    flow.cancel()
    assert webvpn.mode() == "webvpn" and calls == []
    flow.start("synthetic", "synthetic", remember=False)
    result = flow.verify(wechat_code="synthetic")
    assert result["jwxt_ready"] is True and webvpn.mode() == "direct"
    assert calls == ["bootstrap", "save"]


def test_failed_direct_login_save_does_not_switch_route(monkeypatch):
    webvpn.set_mode("webvpn")
    class Client:
        def __init__(self, route): pass
        def login_password(self, username, password): return jwxt.LoginStep.SUCCESS
        def bootstrap_emap_apps(self): pass
        def save_session(self): raise OSError("synthetic save failure")
    monkeypatch.setattr(jwxt, "JwxtClient", Client)
    with pytest.raises(OSError, match="synthetic save failure"):
        webvpn.direct_login_flow().start("synthetic", "synthetic", remember=False)
    assert webvpn.mode() == "webvpn"


def test_proxied_request_keeps_body_normalizes_result_and_proxies_oa(monkeypatch):
    monkeypatch.setattr(sessions, "load_cookies", lambda *_: [])
    c = jwxt.JwxtClient(route="webvpn")
    seen = []
    def response(req, timeout):
        seen.append(req)
        return network._response(req, 200, "Content-Type: text/plain; charset=utf-8\r\n", b"synthetic")
    monkeypatch.setattr(c.opener, "open", response)
    result = c._request(jwxt.IEDU_PORTAL, data=b"readonly=query", headers={"Origin":jwxt.IEDU_BASE,"Referer":jwxt.IEDU_PORTAL})
    assert seen[0].full_url == campus.vpn_url(jwxt.IEDU_PORTAL)
    assert seen[0].data == b"readonly=query" and seen[0].get_header("Origin") == campus.VPN_BASE
    assert result[2] == jwxt.IEDU_PORTAL
    oa = "https://oa.jlu.edu.cn/defaultroot/"
    result = c._request(oa, headers={"Referer": oa})
    assert seen[1].full_url == campus.vpn_url(oa)
    assert seen[1].get_header("Referer") == campus.vpn_url(oa)
    assert result[2] == oa


def test_diagnostics_are_anonymous_and_do_not_load_sessions(monkeypatch):
    monkeypatch.setattr(jwxt.JwxtClient, "load_session", lambda *_: pytest.fail("diagnostic loaded account"))
    def reply(c, url):
        assert c.route == "direct" and not list(c.jar)
        return 200, "login", jwxt.CAS_LOGIN, b""
    monkeypatch.setattr(jwxt.JwxtClient, "_request", reply)
    result = connectivity.check_all()
    assert len(result["services"]) == 4
    assert all(s["reachable"] and s["authentication_checked"] is False and s["port"] == 443 for s in result["services"])


def test_xsxk_old_override_cannot_restore_vpn_button(tmp_path):
    override = tmp_path / "links.json"
    override.write_text(json.dumps({"links":[{"id":"xsxk", "campus_only":True,"vpn_url":"https://vpn.jlu.edu.cn/old"}]}))
    link = next(x for x in ui.campus_links_api(override)["links"] if x["id"] == "xsxk")
    assert link["campus_only"] is False and "vpn_url" not in link


def test_network_failure_api_is_502_with_cache_not_401_and_never_changes_login(tmp_path, monkeypatch):
    def fail(*args): raise jwxt.NetworkError("TLS interrupted", "tls")
    monkeypatch.setattr(ui, "refresh_from_jwxt", fail)
    server = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(tmp_path)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/refresh", data=b"{}", headers={"Content-Type":"application/json"})
        with pytest.raises(urllib.error.HTTPError) as error: urllib.request.urlopen(req)
        result = json.loads(error.value.read())
        assert error.value.code == 502 and result["network_error"] and result["error_kind"] == "tls"
        assert not result.get("session_expired")
    finally:
        server.shutdown(); server.server_close()

def test_oa_vpn_login_redirect_raises_session_dead(monkeypatch):
    import io
    from email.parser import Parser
    monkeypatch.setattr(sessions, "load_cookies", lambda *_: [])
    c = jwxt.JwxtClient(route="webvpn")
    def response(req, timeout):
        # Final URL is the VPN login portal (not a proxied OA path).
        headers = Parser().parsestr("Content-Type: text/html\r\n")
        resp = urllib.response.addinfourl(io.BytesIO(b"login"), headers, "https://vpn.jlu.edu.cn/login", 200)
        resp.msg = "OK"
        return resp
    monkeypatch.setattr(c.opener, "open", response)
    with pytest.raises(jwxt.NetworkError, match="WebVPN 会话不可用") as err:
        c._request("https://oa.jlu.edu.cn/defaultroot/")
    assert err.value.kind == "webvpn"


def test_oa_callback_redirect_is_proxied():
    from email.message import Message
    class Client: route = "webvpn"
    handler = webvpn.RedirectHandler(Client())
    source = urllib.request.Request("https://oa.jlu.edu.cn/defaultroot/")
    callback = "https://oa.jlu.edu.cn/defaultroot/PortalInformation!jldxList.action?channelId=179577"
    redirected = handler.redirect_request(source, None, 302, "Found", Message(), callback)
    assert redirected.full_url == campus.vpn_url(callback)

