"""Login modal: in-app WebVPN continue must stay visible after direct ST callback failure."""
from pathlib import Path

PAGE = Path("jlu_toolkit/ui_page.py").read_text(encoding="utf-8")


def test_vpn_continue_button_sits_with_error_not_header():
    header = PAGE.split("<dialog id=\"login\"")[1].split("</dialog>")[0]
    err_at = header.index('id="lge"')
    cont_at = header.index('id="lg-vpn-continue"')
    assert cont_at > err_at, "continue CTA must sit below the error so mobile users see it"
    assert 'id="lg-vpn-continue"' not in header.split('id="lge"')[0]


def test_vpn_hint_prefers_in_app_when_cas_ticket_saved():
    assert "function lgVpnHint(j,opts)" in PAGE
    assert "请点下方「通过应用内 WebVPN 继续」" in PAGE
    assert "lgVpnHint(p,{canConnectVpn:!!e.canConnectVpn})" in PAGE
