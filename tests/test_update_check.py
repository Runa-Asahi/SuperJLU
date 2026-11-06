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
    m = out["mirrors"]
    assert m["quark"]["url"] == "https://pan.quark.cn/s/216d5fbd8095"
    assert m["baidu"]["url"] == "https://pan.baidu.com/s/50ch5v2DmkgXIirwbN-1Brw"
    assert "同步文件夹" in m["note"]


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
    assert 'id="upd-quark"' in PAGE and 'id="upd-baidu"' in PAGE and 'id="upd-dl"' in PAGE
    assert "夸克网盘" in PAGE and "百度网盘" in PAGE
    assert 'target="_blank"' in PAGE and 'rel="noopener noreferrer"' in PAGE
    assert "updHttps" in PAGE and "不更新也能照常使用" in PAGE
    assert "127.0.0.1" not in block


def test_mirrors_reject_foreign_urls(monkeypatch):
    monkeypatch.setitem(uc.MIRRORS, "quark", {"label": "夸克网盘", "url": "https://evil.example/x", "note": "同步文件夹"})
    monkeypatch.setitem(uc.MIRRORS, "baidu", {"label": "百度网盘", "url": "http://pan.baidu.com/s/x", "note": "同步文件夹"})
    m = uc.mirrors_payload()
    assert m["quark"]["url"] == "" and m["baidu"]["url"] == ""
    assert uc.local()["mirrors"]["note"]


def test_card_id_is_unique():
    assert PAGE.count('id="upd"') == 1  # 顶部「更新于」那行
    assert PAGE.count('id="ver-card"') == 1


def test_current_version_prefers_android_injection(monkeypatch):
    monkeypatch.setenv("SUPERJLU_APP_VERSION", "v1.2.0")
    assert uc.current_version() == "1.2.0"
    assert uc.summarize({"tag_name": "v1.2.0"})["current"] == "1.2.0"


def test_current_version_falls_back_when_missing_or_empty(monkeypatch):
    for bad in ("", "   ", "garbage"):
        monkeypatch.setenv("SUPERJLU_APP_VERSION", bad)
        assert uc.current_version() == uc.__version__
    monkeypatch.delenv("SUPERJLU_APP_VERSION")
    assert uc.current_version() == uc.__version__
    monkeypatch.setattr(uc, "__version__", "")
    assert uc.current_version() == "未知"
    out = uc.check(fetch=lambda _t: (_ for _ in ()).throw(OSError("x")), now=1.0)
    assert out["current"] == "未知" and out["unavailable"]


def test_android_start_injects_version(monkeypatch, tmp_path):
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location("jlu_android", "android/app/src/main/python/jlu_android.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.delenv("SUPERJLU_APP_VERSION", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    try:
        mod.start(str(tmp_path), "1.2.0")
        assert os.environ["SUPERJLU_APP_VERSION"] == "1.2.0"
        assert uc.current_version() == "1.2.0"
    finally:
        mod.stop()
        os.environ.pop("SUPERJLU_APP_VERSION", None)  # stop() 不会清掉注入的版本
    java = Path("android/app/src/main/java/cn/superjlu/app/MainActivity.java").read_text(encoding="utf-8")
    assert '"start", getFilesDir().getAbsolutePath(), appVersion(this)' in java
    assert "getPackageInfo(ctx.getPackageName(), 0).versionName" in java


def test_up_to_date_and_failure_states_are_distinct():
    ok = uc.check(fetch=lambda _t: {"tag_name": "v" + uc.current_version()}, now=1.0)
    assert ok["has_update"] is False and not ok.get("unavailable")
    bad = uc.check(fetch=lambda _t: (_ for _ in ()).throw(OSError("blocked")), now=2.0, force=True)
    assert bad["unavailable"] and "OSError" in bad["reason"]
    assert "当前已是最新版本哦！" in PAGE and 'id="upd-why"' in PAGE


def test_deadline_bounds_hanging_fetch():
    import time as _t
    t0 = _t.time()
    out = uc.check(fetch=lambda _x: _t.sleep(5), now=1.0, deadline=0.2)
    assert out["unavailable"] and "timeout" in out["reason"] and _t.time() - t0 < 2


class _Resp:
    def __init__(self, code, headers=None, body=b""):
        self.code, self.headers, self._b = code, headers or {}, body

    def read(self, _n=-1):
        return self._b


def test_page_fallback_parses_latest_redirect():
    r = uc._page(lambda req, t: _Resp(302, {"Location": "https://github.com/Runa-Asahi/SuperJLU/releases/tag/v1.2.0"}), 5)
    assert r["tag_name"] == "v1.2.0" and uc.summarize(r, current="1.1.1")["has_update"]
    assert uc._page(lambda req, t: _Resp(302, {"Location": "https://github.com/Runa-Asahi/SuperJLU/releases"}), 5) == {}


def test_fetch_falls_back_from_api_to_page(monkeypatch):
    seen = []

    def opener(req, t):
        seen.append(req.full_url)
        assert req.get_header("User-agent", "").startswith("SuperJLU/")
        if "api.github.com" in req.full_url:
            assert req.get_header("Accept") == "application/vnd.github+json"
            return _Resp(403)  # 限流 / 校园网拦截
        return _Resp(302, {"Location": "https://github.com/Runa-Asahi/SuperJLU/releases/tag/v1.2.0"})
    monkeypatch.setattr(uc, "_native_ok", lambda: True)
    monkeypatch.setattr(uc, "_open_native", opener)
    assert uc._fetch(5)["tag_name"] == "v1.2.0"
    assert seen == [uc.API, uc.RELEASES_PAGE]


def test_index_page_embeds_current_version():
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from jlu_toolkit import ui
    import tempfile
    store = ui.Store(Path(tempfile.mkdtemp()))
    h = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(store))
    threading.Thread(target=h.serve_forever, daemon=True).start()
    try:
        port = h.server_address[1]
        html = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10).read().decode()
        assert f'<span id="upd-v">{uc.current_version()}</span>' in html
        import json
        j = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/update?local=1", timeout=10).read())
        assert j["current"] == uc.current_version()
    finally:
        h.shutdown()
