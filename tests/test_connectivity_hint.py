"""Connection-check advice for the common off-campus direct-gap pattern."""
from jlu_toolkit import connectivity


def _svc(sid, reachable, error=None):
    row = {"id": sid, "name": sid, "host": "example", "port": 443,
           "reachable": reachable, "authentication_checked": False}
    if error:
        row["error"] = error
        row["error_kind"] = "tls"
    else:
        row["http_status"] = 200
    return row


def test_offcampus_pattern_when_cas_vpn_up_iedu_oa_down():
    services = [
        _svc("cas", True),
        _svc("jwxt", False, "TLS/SSL 异常中断"),
        _svc("oa", False, "连接/响应超时"),
        _svc("vpn", True),
    ]
    hint = connectivity.advice_from_services(services)
    assert hint
    assert "教务直连未通" in hint
    assert "学校 OA 直连未通" in hint
    assert "校外 WebVPN" in hint
    assert "更多 → 登录" in hint
    # Must not claim device-proven OA-via-VPN (negation language only).
    assert "不代表" in hint and "验收" in hint
    assert "OA 已可用" not in hint and "VPN 已验收" not in hint


def test_no_hint_when_all_direct_reachable():
    services = [_svc(s, True) for s in ("cas", "jwxt", "oa", "vpn")]
    assert connectivity.advice_from_services(services) is None


def test_no_hint_when_vpn_portal_also_down():
    services = [
        _svc("cas", True),
        _svc("jwxt", False, "TLS"),
        _svc("oa", False, "timeout"),
        _svc("vpn", False, "timeout"),
    ]
    assert connectivity.advice_from_services(services) is None


def test_check_all_includes_hint_for_offcampus_gap(monkeypatch):
    canned = [
        _svc("cas", True),
        _svc("jwxt", False, "TLS/SSL 异常中断"),
        _svc("oa", False, "连接/响应超时"),
        _svc("vpn", True),
    ]

    def fake_one(target, timeout=6):
        sid = target[0]
        return next(s for s in canned if s["id"] == sid)

    monkeypatch.setattr(connectivity, "check_one", fake_one)
    result = connectivity.check_all()
    assert result["pattern"] == "offcampus_direct_gap"
    assert "校外 WebVPN" in result["hint"]
    assert len(result["services"]) == 4


def test_jwxt_only_failure_still_hints_webvpn_login():
    services = [
        _svc("cas", True),
        _svc("jwxt", False, "TLS"),
        _svc("oa", True),
        _svc("vpn", True),
    ]
    hint = connectivity.advice_from_services(services)
    assert hint and "教务直连未通" in hint and "校外 WebVPN" in hint
    assert "学校 OA 直连未通" not in hint
