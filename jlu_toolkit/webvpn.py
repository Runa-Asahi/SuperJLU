"""Explicit direct/WebVPN routes for JWXT and school OA, with application-owned sessions.

Browser cookies are never scraped or imported. CAS issues a service ticket to
the official WebVPN service, using this application's existing CAS cookie jar.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.parse
import urllib.request

SERVICE = "https://vpn.jlu.edu.cn/login?cas_login=true"
OA_HOST = "oa.jlu.edu.cn"
_last_connections = {}
_state_lock = threading.Lock()


def mode():
    from . import jwxt
    try:
        saved = json.loads((jwxt.config_dir() / "network-route.json").read_text(encoding="utf-8"))
        value = saved.get("mode")
        if value in ("direct", "webvpn"):
            return value
        if value == "auto":
            # Retire the experimental auto policy without dropping a saved
            # application VPN session. Future routing is explicitly manual.
            from . import sessions
            return "webvpn" if sessions.load_cookies("vpn") else "direct"
        return "direct"
    except (OSError, ValueError, AttributeError):
        return "direct"


def set_mode(value):
    from . import jwxt
    if value not in ("direct", "webvpn"):
        raise ValueError("请选择校园网直连或校外 WebVPN")
    path = jwxt.config_dir() / "network-route.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"version": 2, "mode": value}), encoding="utf-8")
    temporary.replace(path)


def record_connection(route):
    from . import jwxt
    with _state_lock:
        _last_connections[str(jwxt.config_dir())] = {"route": route, "checked_at": int(time.time())}


def canonical_url(url):
    from .campus import vpn_url_decode
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname == "vpn.jlu.edu.cn" and parsed.path.startswith(("/https/", "/http/", "/https-", "/http-")):
        try:
            return vpn_url_decode(url)
        except ValueError:
            pass
    return url


def request_url(url):
    from .campus import vpn_url
    from . import jwxt
    parsed = urllib.parse.urlsplit(url)
    # Proxy JWXT and school OA when the active route is WebVPN. CAS service
    # tickets must stay on the original service URL (never rewrite CAS /
    # colleges / the VPN login service itself).
    if parsed.hostname in (jwxt.IEDU_HOST, OA_HOST):
        return vpn_url(url)
    return url


class RedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, client):
        self.client = client

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if self.client.route == "webvpn":
            # Apply the route to *every* redirect, including the ST callback,
            # instead of only to the first URL passed into JwxtClient._request.
            newurl = request_url(canonical_url(newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def connect():
    from . import campus, jwxt, sessions
    c = jwxt.JwxtClient(route="direct")
    sessions.migrate_cas_from_jwxt()
    saved = sessions.load_cookies("cas")
    if not saved:
        raise jwxt.LoginError("统一认证会话不可用，请在「更多 → 登录」选择「校外 WebVPN」后登录。")
    for cookie in jwxt.jar_from_list(saved):
        c.jar.set_cookie(cookie)
    for cookie in jwxt.jar_from_list(sessions.load_cookies("vpn") or []):
        c.jar.set_cookie(cookie)
    code, html, final, _ = c._request(jwxt.CAS_LOGIN + "?service=" + urllib.parse.quote(SERVICE, safe=""))
    if jwxt.looks_like_login_redirect(final, html) or urllib.parse.urlsplit(final).hostname != "vpn.jlu.edu.cn":
        raise jwxt.LoginError("未能建立应用内 WebVPN 会话，请重新登录统一身份认证后重试。")
    if code >= 400:
        raise jwxt.LoginError("学校 WebVPN 尚未确认登录，暂未切换同步通道。")
    return finish_connected(c)


def finish_connected(c):
    from . import campus, jwxt, sessions
    if campus.check_vpn(c).get("logged_in") is not True:
        raise jwxt.LoginError("学校 WebVPN 尚未确认登录，暂未切换同步通道。")
    # Include the original CAS cookies for future ticket exchanges, encrypted
    # by the existing SecretFile implementation. Never return them through API.
    sessions.save_cookies("vpn", jwxt.jar_to_list(c.jar))
    sessions.save_cas_from_jar(c.jar)
    set_mode("webvpn")
    c.route = "webvpn"
    c._vpn_cookies_loaded = False
    ready, warning = False, ""
    try:
        c.enter_emap_app(jwxt.REF_SCHEDULE)
        c.save_session()
        ready = True
    except jwxt.JwxtError as error:
        warning = "WebVPN 已登录，但教务入口尚未验证，请重试同步。" + str(error)
    return {**state(), "jwxt_ready": ready, "warning": warning}


def direct_login_flow():
    """Authenticate directly; keep the previous route until login succeeds."""
    from . import jwxt
    from .web_login import LoginFlow

    def finish(c):
        try:
            c.bootstrap_emap_apps()
        except jwxt.JwxtError:
            pass
        c.save_session()
        set_mode("direct")
        return {"mode": "direct", "jwxt_ready": True}

    def client():
        c = jwxt.JwxtClient(route="direct")
        # An explicit password login must not silently authenticate the account
        # from an older CAS cookie. VPN transport cookies may still be reused.
        c._restore_saved_cas = False
        return c

    return LoginFlow(client_factory=client, on_success=finish)


def login_flow():
    from . import jwxt
    from .web_login import LoginFlow
    return LoginFlow(client_factory=lambda: jwxt.JwxtClient(route="direct"),
                     service=SERVICE, on_success=finish_connected)


def state():
    from . import jwxt, sessions
    with _state_lock:
        last = dict(_last_connections.get(str(jwxt.config_dir()), {}))
    return {"ok": True, "mode": mode(), "vpn": sessions.status("vpn"), "last_connection": last,
            "note": "教务与学校 OA 在校园网内选择直连，校外选择应用内 WebVPN，不自动切换通道。学院官网通知仍独立直连。"}
