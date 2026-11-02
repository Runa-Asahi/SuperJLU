"""学业完成刷新：校园网直连与校外 WebVPN 两种通道走同一条取数链路；单步意外错误不拖垮整次刷新。"""
import email.message
import io
import json
import urllib.parse

import pytest

from jlu_toolkit import jwxt, meta, sync, ui, webvpn
from jlu_toolkit.ui_page import PAGE

R = {
    "/jwapp/sys/xsfacx/modules/pyfacxepg/grpyfacx.do": {"code": "0", "datas": {"grpyfacx": {"rows": [
        {"XH": "T", "PYFADM": "FA", "PYFAMC": "示例方案", "ZSYQXF": "160", "YWCXF": "50"}]}}},
    "/jwapp/sys/xywccx/modules/xywccx/cxxsscfa.do": {"code": "0", "datas": {"cxxsscfa": {"rows": [
        {"XH": "T", "PYFADM": "FA", "YQXF": "160", "WCXF": "50", "CZSJ": "2026-10-30"}]}}},
    "/jwapp/sys/xywccx/modules/xywccx/cxscfakz.do": {"code": "0", "datas": {"cxscfakz": {"rows": [
        {"KZM": "必修", "KZH": "1", "YQXF": "100", "WCXF": "40"}]}}},
}


class _Resp(io.BytesIO):
    def __init__(self, body, url, ctype="application/json;charset=UTF-8", status=200):
        super().__init__(body.encode())
        self._url = url
        self._status = status
        self.headers = email.message.Message()
        self.headers["Content-Type"] = ctype

    def geturl(self):
        return self._url

    def getcode(self):
        return self._status


class _Opener:
    """按「逻辑地址」回放；WebVPN 通道下断言请求确实发往 vpn.jlu.edu.cn。"""

    def __init__(self, route, routes):
        self.route, self.routes, self.seen = route, routes, []

    def open(self, req, timeout=None):
        url = req.full_url
        logical = webvpn.canonical_url(url) if self.route == "webvpn" else url
        parts = urllib.parse.urlsplit(logical)
        assert parts.hostname == "iedu.jlu.edu.cn"
        assert urllib.parse.urlsplit(url).hostname == ("vpn.jlu.edu.cn" if self.route == "webvpn" else "iedu.jlu.edu.cn")
        self.seen.append(parts.path)
        body = self.routes.get(parts.path)
        if isinstance(body, tuple):
            status, text = body
            return _Resp(text, url, "text/html", status=status)
        if body is None:
            return _Resp("<html></html>", url, "text/html")
        return _Resp(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False), url)


def _client(route, routes=R):
    c = jwxt.JwxtClient(route=route)
    c.opener = _Opener(route, routes)
    c._restore_vpn_cookies = lambda: None
    c.current_semester = lambda: "2026-2027-1"
    return c


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_fetch_completion_both_routes(route):
    c = _client(route)
    comp = meta.fetch_completion(c)
    assert comp["plan"] == "示例方案" and comp["required"] == 160 and comp["earned"] == 50
    assert "/jwapp/sys/xywccx/modules/xywccx/cxxsscfa.do" in c.opener.seen


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_completion_survives_plan_forbidden(route):
    routes = dict(R)
    routes[meta.EP_PLAN] = (403, "Forbidden")
    c = _client(route, routes)
    comp = meta.fetch_completion(c)
    assert comp["required"] == 160 and comp["earned"] == 50
    assert comp["groups"][0]["earned"] == 40
    assert meta.EP_COMPLETION in c.opener.seen
    assert meta.EP_COMPLETION_GROUPS in c.opener.seen


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_completion_empty_and_plan_forbidden_is_still_failure(route):
    routes = dict(R)
    routes[meta.EP_PLAN] = (403, "Forbidden")
    routes[meta.EP_COMPLETION] = {"datas": {"cxxsscfa": {"rows": []}}}
    with pytest.raises(jwxt.JwxtError, match="培养方案补充查询失败.*403"):
        meta.fetch_completion(_client(route, routes))


@pytest.mark.parametrize("route", ["direct", "webvpn"])
@pytest.mark.parametrize("path", [meta.EP_PLAN, meta.EP_COMPLETION, meta.EP_COMPLETION_GROUPS])
def test_completion_does_not_swallow_expired_login(route, path):
    routes = dict(R)
    routes[path] = '<html><form id="loginForm"></form></html>'
    with pytest.raises(jwxt.LoginError):
        meta.fetch_completion(_client(route, routes))


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_sync_all_writes_completion_both_routes(route, tmp_path):
    s = sync.sync_all(_client(route), tmp_path)
    assert s["completion"]["ok"] is True
    assert ui.Store(tmp_path).snapshot()["completion"]["earned"] == 50


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_sync_writes_completion_despite_plan_forbidden(route, tmp_path, monkeypatch):
    from jlu_toolkit import plan

    routes = dict(R)
    routes[meta.EP_PLAN] = (403, "Forbidden")
    # The later curriculum sync is independent; its failure must preserve completion.
    def unavailable(*args, **kwargs):
        raise jwxt.JwxtError("synthetic curriculum unavailable")
    monkeypatch.setattr(plan, "fetch_plan", unavailable)
    result = sync.sync_all(_client(route, routes), tmp_path)
    assert result["completion"]["ok"] is True
    assert result["plan_courses"]["ok"] is False
    assert ui.Store(tmp_path).snapshot()["completion"]["earned"] == 50


@pytest.mark.parametrize("route", ["direct", "webvpn"])
def test_non_dict_json_is_reported_not_crash(route, tmp_path):
    routes = dict(R)
    routes["/jwapp/sys/xywccx/modules/xywccx/cxxsscfa.do"] = "[]"
    routes["/jwapp/sys/xsfacx/modules/pyfacxepg/grpyfacx.do"] = "\"oops\""
    s = sync.sync_all(_client(route, routes), tmp_path)
    assert s["completion"]["ok"] is False and "格式异常" in s["completion"]["error"]


def test_unexpected_step_error_does_not_abort_refresh(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise TypeError("bad row")
    monkeypatch.setattr(meta, "fetch_completion", boom)
    s = sync.sync_all(_client("direct"), tmp_path)
    assert s["completion"] == {"ok": False, "error": "读取出错（TypeError）"}
    assert "plan_courses" in s  # 后续步骤仍会执行


def test_progress_page_shows_refresh_error():
    assert "function progRefreshError(r)" in PAGE
    assert "学业完成没有刷新成功" in PAGE
    assert "PROG_ERR=progRefreshError(j.result)" in PAGE


@pytest.mark.parametrize("value", [0, "0", "0.0"])
def test_completion_zero_is_not_replaced_by_plan(value):
    comp = meta.parse_completion({"YQXF": value, "WCXF": value},
                                 {"ZSYQXF": "160", "YWCXF": "50"}, [])
    assert comp["required"] == 0
    assert comp["earned"] == 0


@pytest.mark.parametrize("value", [None, "", "not-a-number"])
def test_completion_missing_numbers_still_fall_back_to_plan(value):
    comp = meta.parse_completion({"YQXF": value, "WCXF": value},
                                 {"ZSYQXF": "160", "YWCXF": "50"}, [])
    assert comp["required"] == 160
    assert comp["earned"] == 50
