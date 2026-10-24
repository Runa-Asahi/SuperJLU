import json
import threading

import pytest

from jlu_toolkit import desktop, ui


@pytest.fixture(autouse=True)
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(desktop, "DEFAULT_PORT", desktop.free_port())  # 测试不碰真实 8765
    monkeypatch.setattr(desktop, "start_server",
                        lambda root=None, port=None: desktop.__dict__["_real_start"](tmp_path / "data", port))
    return tmp_path / "jlu-toolkit"


desktop._real_start = desktop.start_server


def test_free_port_and_state(cfg):
    p = desktop.free_port()
    assert 0 < p < 65536
    assert desktop.read_state() is None
    desktop.write_state(p)
    assert desktop.read_state()["port"] == p
    desktop.clear_state(p + 1)  # 别人的端口不清
    assert desktop.read_state()
    desktop.clear_state(p)
    assert desktop.read_state() is None
    (cfg / "desktop.json").write_text("garbage", encoding="utf-8")
    assert desktop.read_state() is None


def test_is_running_detects_only_superjlu(cfg):
    httpd, url = desktop._real_start(cfg / "data")
    port = httpd.server_address[1]
    try:
        assert desktop.is_running(port)
        assert not desktop.is_running(desktop.free_port(), timeout=0.3)
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_main_starts_opens_and_quits(cfg):
    opened, seen = [], {}

    def fake_tray(url, on_quit, opener):
        seen["url"] = url
        seen["running"] = desktop.existing_instance()
        on_quit()
        return True
    assert desktop.main(opener=opened.append, tray=fake_tray) == 0
    assert opened == [ui.launch_url(seen["url"])] and "?t=" not in seen["url"]  # 托盘提示不含令牌
    assert seen["running"] == int(seen["url"].rsplit(":", 1)[1].strip("/"))
    assert desktop.read_state() is None  # 退出后清理


def test_second_launch_opens_existing(cfg):
    httpd, url = desktop._real_start(cfg / "data")
    port = httpd.server_address[1]
    desktop.write_state(port)
    opened = []
    try:
        called = []
        assert desktop.main(opener=opened.append, tray=lambda *a: called.append(1)) == 0
        assert opened == [ui.launch_url(url)] and called == []
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_stale_state_starts_new(cfg):
    desktop.write_state(desktop.free_port())  # 旧实例已退出
    opened = []
    assert desktop.main(opener=opened.append, tray=lambda u, q, o: (q(), True)[1]) == 0
    assert len(opened) == 1


def test_no_tray_falls_back(cfg):
    opened = []
    ev = threading.Event()
    assert desktop.main(opener=opened.append, tray=lambda *a: False, wait=ev.set) == 0
    assert ev.is_set() and len(opened) == 1 and desktop.read_state() is None


def test_browser_failure_does_not_crash(cfg):
    def boom(u):
        raise OSError("no browser")
    assert desktop.main(opener=boom, tray=lambda u, q, o: (q(), True)[1]) == 0
    assert "打开浏览器失败" in (cfg / "desktop.log").read_text(encoding="utf-8")


def test_icon_uses_brand_ico_only(tmp_path, monkeypatch):
    PIL = pytest.importorskip("PIL")
    from PIL import Image
    monkeypatch.setattr(desktop.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert desktop.icon_path() is None and desktop.make_icon(64) is None  # 缺失时不画替代图标
    assert desktop.run_tray("u", lambda: None, lambda u: None) is False
    ico = tmp_path / "assets" / "brand" / "superjlu.ico"
    ico.parent.mkdir(parents=True)
    Image.new("RGBA", (256, 256), (255, 0, 0, 255)).save(ico, sizes=[(16, 16), (64, 64), (256, 256)])
    img = desktop.make_icon(64)
    assert img.size == (64, 64) and img.mode == "RGBA" and img.getpixel((32, 32))[0] == 255


def test_prefers_default_port(cfg):
    httpd, url = desktop._real_start(cfg / "data")
    try:
        assert httpd.server_address[1] == desktop.DEFAULT_PORT and url == desktop.url_for(desktop.DEFAULT_PORT)
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_falls_back_when_default_busy(cfg):
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", desktop.DEFAULT_PORT))
    s.listen(1)
    try:
        httpd, url = desktop._real_start(cfg / "data")
        try:
            assert httpd.server_address[1] != desktop.DEFAULT_PORT
        finally:
            httpd.shutdown()
            httpd.server_close()
    finally:
        s.close()


def test_running_on_default_port_without_state(cfg):
    httpd, url = desktop._real_start(cfg / "data")  # 占 DEFAULT_PORT，但不写 desktop.json
    opened = []
    try:
        assert desktop.read_state() is None
        assert desktop.main(opener=opened.append, tray=lambda *a: pytest.fail("不应再启动")) == 0
        assert opened == [ui.launch_url(desktop.url_for(desktop.DEFAULT_PORT))]
    finally:
        httpd.shutdown()
        httpd.server_close()
