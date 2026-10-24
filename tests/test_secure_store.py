import json
import os
import sys

import pytest

from jlu_toolkit import jwxt, secure_store

keyring = pytest.importorskip("keyring")
pytest.importorskip("cryptography")
from keyring.backend import KeyringBackend  # noqa: E402


class MemKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.d = {}

    def get_password(self, s, u):
        return self.d.get((s, u))

    def set_password(self, s, u, p):
        self.d[(s, u)] = p

    def delete_password(self, s, u):
        self.d.pop((s, u), None)


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("JLU_TOOLKIT_NO_KEYRING", raising=False)
    return tmp_path / "jlu-toolkit"


@pytest.fixture
def mem(monkeypatch):
    kr = MemKeyring()
    old = keyring.get_keyring()
    keyring.set_keyring(kr)
    yield kr
    keyring.set_keyring(old)


def test_encrypted_roundtrip_no_plaintext(cfg, mem):
    path = jwxt.save_credentials("prefix", "s3cret-pw")
    assert path.suffix == ".enc"
    raw = path.read_bytes()
    assert b"s3cret-pw" not in raw and b"prefix" not in raw
    assert jwxt.load_credentials() == ("prefix", "s3cret-pw")
    assert secure_store.KEY_ENTRY in {u for (_, u) in mem.d}
    if os.name == "posix":
        assert (path.stat().st_mode & 0o777) == 0o600


def test_migrates_legacy_plaintext(cfg, mem):
    cfg.mkdir(parents=True)
    legacy = cfg / "session.json"
    legacy.write_text(json.dumps({"cookies": []}), encoding="utf-8")
    c = jwxt.JwxtClient()
    assert c.load_session()
    assert not legacy.exists()
    assert (cfg / "session.enc").exists()
    assert jwxt.JwxtClient().load_session()


def test_no_password_saved_when_no_keyring(cfg, monkeypatch, capsys):
    monkeypatch.setenv("JLU_TOOLKIT_NO_KEYRING", "1")
    cfg.mkdir(parents=True, exist_ok=True)
    legacy = cfg / "credentials.json"
    legacy.write_text(json.dumps({"username": "u", "password": "old"}), encoding="utf-8")
    assert jwxt.save_credentials("u", "p") is None
    assert "警告" in capsys.readouterr().err
    assert not legacy.exists()
    assert jwxt.load_credentials() is None
    # 会话仍可明文保存
    jwxt.JwxtClient().save_session()
    assert jwxt.JwxtClient().load_session()


def test_wrong_key_raises_clear_error(cfg, mem):
    jwxt.save_credentials("u", "p")
    mem.d.clear()
    with pytest.raises(secure_store.SecureStoreError):
        jwxt.load_credentials()
    jwxt.JwxtClient().save_session()
    mem.d.clear()
    assert jwxt.JwxtClient().load_session() is False


def test_session_status_lifecycle(cfg, mem):
    assert jwxt.session_status()["state"] == "missing"
    assert jwxt.session_status()["needs_login"] is True
    jwxt.JwxtClient().save_session()
    st = jwxt.session_status()
    assert st["state"] == "ok" and st["logged_in"] and st["storage"].startswith("keyring")
    jwxt.mark_session_expired("test")
    st = jwxt.session_status()
    assert st["state"] == "expired" and st["needs_login"] and st["session_expired"] is True and "更多 → 登录" in st["message"] and "force-login" not in st["message"]


def test_post_form_redirect_to_login_raises_typed_error(cfg, mem, monkeypatch):
    c = jwxt.JwxtClient()
    c.save_session()
    html = '<form id="loginForm" action="/tpass/login">password</form>'
    monkeypatch.setattr(c, "_request", lambda *a, **k: (200, html, "https://cas.jlu.edu.cn/tpass/login?service=x", b""))
    with pytest.raises(jwxt.SessionExpiredError) as ei:
        c._post_form("/jwapp/x.do", {}, "ref")
    assert "更多 → 登录" in str(ei.value) and "force-login" not in str(ei.value)
    assert isinstance(ei.value, jwxt.LoginError)  # 旧的 except LoginError 依然能接住
    assert jwxt.session_status()["state"] == "expired"


def test_looks_like_login_redirect():
    assert jwxt.looks_like_login_redirect("https://cas.jlu.edu.cn/tpass/login?service=a")
    assert not jwxt.looks_like_login_redirect("https://iedu.jlu.edu.cn/jwapp/x.do", '{"datas":{}}')


def test_cli_status_exit_code(cfg, mem, monkeypatch, capsys):
    from jlu_toolkit import cli
    monkeypatch.setattr(sys, "argv", ["jlu-toolkit", "status", "--json"])
    with pytest.raises(SystemExit) as ei:
        cli.main()
    assert ei.value.code == 3
    assert json.loads(capsys.readouterr().out)["state"] == "missing"


def test_ui_session_endpoint(cfg, mem):
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from jlu_toolkit import ui
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(cfg)))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{srv.server_address[1]}/api/session"
        req = urllib.request.Request(url, headers={"Host": f"127.0.0.1:{srv.server_address[1]}"})
        d = json.loads(urllib.request.urlopen(req, timeout=5).read())
        assert d["state"] == "missing" and d["needs_login"] is True
    finally:
        srv.shutdown()


def test_multi_accounts(tmp_path):
    from jlu_toolkit import jwxt as J
    p = tmp_path / "credentials.json"
    J.save_credentials("a", "pa", p)
    J.save_credentials("b", "pb", p)
    assert J.list_accounts(p) == ["b", "a"]
    assert J.load_credentials(p) == ("b", "pb")
    assert J.account_password("a", p) == "pa"
    J.save_credentials("a", "pa2", p)
    assert J.list_accounts(p) == ["a", "b"] and J.account_password("a", p) == "pa2"
    assert J.delete_account("a", p) and not J.delete_account("zz", p)
    assert J.list_accounts(p) == ["b"] and J.account_password("a", p) is None
    assert J.load_credentials(p) == ("b", "pb")
