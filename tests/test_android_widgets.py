import shutil, subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_swipe_and_widget_export_js():
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    r = subprocess.run([node, str(ROOT / "tests" / "js_swipe_widget_test.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_page_has_android_extras_card():
    from jlu_toolkit.ui_page import PAGE
    assert 'id="android-extras"' in PAGE and "<!--ANDROID_EXTRAS_CARD-->" not in PAGE


def test_manifest_declares_widgets_and_boot():
    m = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    for s in ("TodayWidget", "WeekWidget", "BOOT_COMPLETED", "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS", "POST_NOTIFICATIONS"):
        assert s in m
