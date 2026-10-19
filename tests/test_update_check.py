"""Quiet update notice: parse/compare versions, never raise, never force."""
from pathlib import Path

from jlu_toolkit import update_check as uc

PAGE = Path("jlu_toolkit/ui_page.py").read_text(encoding="utf-8")


def setup_function(_):
    uc._cache.update(at=0.0, ttl=0, result=None)


def test_version_compare():
    assert uc.is_newer("v1.2.0", "1.1.1")
    assert uc.is_newer("v1.1.10", "1.1.9")
    assert not uc.is_newer("v1.1.1", "1.1.1")
    assert not uc.is_newer("v1.0.9", "1.1.1")
    assert not uc.is_newer("nightly", "1.1.1")


def test_summarize_new_release():
    rel = {"tag_name": "v9.0.0", "html_url": "https://github.com/Runa-Asahi/SuperJLU/releases/tag/v9.0.0",
           "published_at": "2026-11-01T00:00:00Z"}
    out = uc.summarize(rel, current="1.1.1")
    assert out["has_update"] and out["latest"] == "9.0.0"
    assert out["url"].endswith("/v9.0.0") and out["published_at"] == "2026-11-01"


def test_summarize_rejects_foreign_url_and_prerelease():
    out = uc.summarize({"tag_name": "v9.0.0", "html_url": "https://evil.example/x"}, current="1.1.1")
    assert out["url"] == uc.RELEASES_PAGE
    assert uc.summarize({"tag_name": "v9.0.0", "prerelease": True}, current="1.1.1")["has_update"] is False


def test_network_failure_is_silent_and_cached():
    calls = []

    def boom(_t):
        calls.append(1)
        raise OSError("offline")

    a = uc.check(fetch=boom, now=1000.0)
    assert a["ok"] and a["has_update"] is False and a["unavailable"]
    b = uc.check(fetch=boom, now=1100.0)
    assert b.get("cached") and len(calls) == 1
    uc.check(fetch=boom, now=1100.0, force=True)
    assert len(calls) == 2


def test_ui_is_non_intrusive():
    block = PAGE.split("新版本提醒")[1].split("\n// ----")[0]
    assert "showModal" not in block and "confirm(" not in block and "alert(" not in block
    assert 'id="upd-auto"' in PAGE and 'id="upd-go"' in PAGE
    assert "不更新也能照常使用" in PAGE
    assert "127.0.0.1" not in block


def test_card_id_is_unique():
    assert PAGE.count('id="upd"') == 1  # 顶部「更新于」那行
    assert PAGE.count('id="ver-card"') == 1
