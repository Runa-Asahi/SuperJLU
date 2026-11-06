"""Shared desktop/WebView notice navigation regression."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_notice_navigation():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is unavailable")
    root = Path(__file__).resolve().parents[1]
    subprocess.run([node, "tests/js_notice_navigation_test.js"], cwd=root, check=True,
                   capture_output=True, text=True, timeout=30)
