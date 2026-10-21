"""「更多」页：Android 浏览器偏好可访问，运行时技术信息仍折叠。"""
from pathlib import Path

from jlu_toolkit import ui_page
from jlu_toolkit.ui_page import PAGE

ROOT = Path(__file__).resolve().parents[1]


def _more_tab(page: str) -> str:
    start = page.index('<section class="tab" id="t-sz">')
    return page[start:page.index("</section>", start)]


def test_browser_preferences_card_is_enabled_but_hidden_until_android_is_detected():
    assert ui_page.SHOW_BROWSER_PREFERENCES is True
    more = _more_tab(PAGE)
    assert 'id="browser-preferences" hidden' in more
    assert 'id="browser-settings-button"' in more
    assert "BROWSER_PREFERENCES_CARD" not in more
    assert 'if(bp)bp.hidden=!/SuperJLU-Android/.test(navigator.userAgent)' in PAGE


def test_browser_preferences_card_opens_native_settings_without_disabled_button():
    card = ui_page.BROWSER_PREFERENCES_CARD
    assert 'href="superjlu://browser-settings"' in card
    assert "设置默认浏览器" in card and "仅影响本应用" in card
    assert "disabled" not in card and "暂不可用" not in card
    assert card in PAGE


def test_user_facing_more_cards_still_present():
    more = _more_tab(PAGE)
    for marker in ('id="links"', 'id="adj-on"', 'data-theme="dark"', 'id="lgbtn"', 'id="network-check"',
                   'id="ics"', 'id="kb-edits-card"', 'id="ver-card"', "数据与隐私"):
        assert marker in more


def test_network_check_summary_hides_runtime_versions():
    line = next(x for x in PAGE.splitlines() if x.startswith('$("#network-check").onclick'))
    assert '" · Python "+data.python' not in line
    assert 'id="network-tech"' in line and "<details" in line


def test_android_browser_settings_interface_is_enabled_and_releases_dialog_on_destroy():
    src = (ROOT / "android/app/src/main/java/cn/superjlu/app/MainActivity.java").read_text(encoding="utf-8")
    assert "static final boolean BROWSER_SETTINGS_ENABLED = true;" in src
    assert "if (BROWSER_SETTINGS_ENABLED) browsers.showSettings();" in src
    assert "if (browsers != null) browsers.close();" in src
