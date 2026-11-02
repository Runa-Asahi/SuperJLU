import shutil
import subprocess
from pathlib import Path

import pytest


def test_academic_ui_actions():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node unavailable")
    result = subprocess.run([node, "tests/js_academic_test.js"],
                            cwd=Path(__file__).resolve().parents[1],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
