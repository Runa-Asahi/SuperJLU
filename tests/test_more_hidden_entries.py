"""「更多」页暂时下线的入口：外部浏览器卡片与技术信息不应直接展示给同学。"""
from pathlib import Path

from jlu_toolkit import ui_page
from jlu_toolkit.ui_page import PAGE

ROOT = Path(__file__).resolve().parents[1]


def _more_tab(page: str) -> str:
    start = page.index('<section class="tab" id="t-sz">')
    return page[start:page.index("</section>", start)]


def test_browser_preferences_card_hidden_from_more_page():
    assert ui_page.SHOW_BROWSER_PREFERENCES is False
    more = _more_tab(PAGE)
    for marker in ('id="browser-preferences"', 'id="browser-settings-button"', "外部浏览器", "更换浏览器", "BROWSER_PREFERENCES_CARD"):
        assert marker not in more
    # JS 不能因为卡片不存在而在打开「更多」时报错。
    assert 'const bp=$("#browser-preferences");if(bp)bp.hidden=' in PAGE


def test_browser_preferences_card_is_kept_for_restore():
    card = ui_page.BROWSER_PREFERENCES_CARD
    assert 'id="browser-preferences"' in card and "disabled" in card
    restored = ui_page.PAGE  # 当前为隐藏状态；恢复时仅需把开关改回 True
    assert card not in restored


def test_user_facing_more_cards_still_present():
    more = _more_tab(PAGE)
    for marker in ('id="links"', 'id="adj-on"', 'data-theme="dark"', 'id="lgbtn"', 'id="network-check"',
                   'id="ics"', 'id="kb-edits-card"', 'id="ver-card"', "数据与隐私"):
        assert marker in more


def test_network_check_summary_hides_runtime_versions():
    line = next(x for x in PAGE.splitlines() if x.startswith('$("#network-check").onclick'))
    assert '" · Python "+data.python' not in line
    assert 'id="network-tech"' in line and "<details" in line


def test_android_browser_settings_interface_disabled():
    src = (ROOT / "android/app/src/main/java/cn/superjlu/app/MainActivity.java").read_text(encoding="utf-8")
    assert "static final boolean BROWSER_SETTINGS_ENABLED = false;" in src
    assert "if (BROWSER_SETTINGS_ENABLED) browsers.showSettings();" in src
