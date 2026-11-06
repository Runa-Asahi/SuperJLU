"""android/app/src/main/python/jlu_android.py：本机随机端口启动、数据目录落在私有目录。"""
import importlib.util
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "android" / "app" / "src" / "main" / "python" / "jlu_android.py"


def _load():
    spec = importlib.util.spec_from_file_location("jlu_android", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_start_serves_ui_on_loopback(tmp_path, monkeypatch):
    for k in ("XDG_CONFIG_HOME", "JLU_TOOLKIT_NO_KEYRING"):
        monkeypatch.delenv(k, raising=False)
    m = _load()
    try:
        url = m.start(str(tmp_path))
        assert url.startswith("http://127.0.0.1:") and not url.endswith(":8765/")
        assert m._httpd.server_address[0] == "127.0.0.1"
        assert m.start(str(tmp_path)) == url
        html = urllib.request.urlopen(url, timeout=5).read().decode()
        assert "<html" in html.lower()
        # Android Keystore（#14）负责加密，入口不能再把它关掉
        assert "JLU_TOOLKIT_NO_KEYRING" not in os.environ
        assert (tmp_path / "config" / "jlu-toolkit" / "data").is_dir()
    finally:
        m.stop()


def test_bootstrap_does_not_disable_keystore():
    assert "JLU_TOOLKIT_NO_KEYRING" not in SRC.read_text(encoding="utf-8").split('"""', 2)[2]


ANDROID = ROOT / "android" / "app" / "src" / "main"


def test_app_name_icon_and_insets():
    strings = (ANDROID / "res" / "values" / "strings.xml").read_text(encoding="utf-8")
    assert ">SuperJLU<" in strings and "吉大人的一站式服务" in strings
    man = (ANDROID / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert "@string/app_name" in man and "@mipmap/ic_launcher" in man
    assert (ANDROID / "res" / "mipmap-anydpi-v26" / "ic_launcher.xml").is_file()
    act = next(ANDROID.rglob("MainActivity.java")).read_text(encoding="utf-8")
    assert "setOnApplyWindowInsetsListener" in act and "displayCutout" in act
    assert "setInsetHeight(R.id.status_inset" in act and "setInsetHeight(R.id.nav_inset" in act
    assert "#0B4EA2" not in act and "#f6f7f9" in act and "#ffffff" in act
    assert "shareIcs" in act and "/api/ics" in act
    assert "shareSchedule" in act and "/api/schedule/share" in act
    helper = ANDROID / "java/cn/superjlu/app/ScheduleShareHelper.java"
    assert helper.is_file() and "superjlu.schedule.share" in helper.read_text(encoding="utf-8")
    assert "singleTop" in man and "android.intent.action.SEND" in man
    layout = (ANDROID / "res" / "layout" / "activity_main.xml").read_text(encoding="utf-8")
    assert "#0B4EA2" not in layout and "status_inset" in layout and "nav_inset" in layout
    assert "ExportProvider" in (ANDROID / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert "api/session/keepalive" in act and "onPause" in act
    gradle = (ROOT / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
    assert 'applicationId "cn.superjlu.app"' in gradle
