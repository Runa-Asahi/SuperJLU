"""登录对话框的多账号：GET/DELETE /api/login/accounts，绝不返回密码。"""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from jlu_toolkit import jwxt, ui


@pytest.fixture
def srv(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(ui.Store(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _req(url, method="GET"):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method)) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_accounts_list_and_delete(srv, monkeypatch):
    monkeypatch.setattr(jwxt.secure_store, "can_encrypt", lambda: True)
    jwxt.save_credentials("alice", "SECRET-A")
    jwxt.save_credentials("bob", "SECRET-B")
    code, body = _req(srv + "/api/login/accounts")
    assert code == 200 and json.loads(body)["accounts"] == ["bob", "alice"]
    assert "SECRET" not in body
    code, body = _req(srv + "/api/login")
    j = json.loads(body)
    assert j["saved_username"] == "bob" and j["accounts"] == ["bob", "alice"] and "SECRET" not in body
    code, body = _req(srv + "/api/login/accounts/bob", "DELETE")
    assert code == 200 and json.loads(body)["accounts"] == ["alice"]
    assert jwxt.account_password("bob") is None and jwxt.load_credentials() == ("alice", "SECRET-A")
    code, _ = _req(srv + "/api/login/accounts/nobody", "DELETE")
    assert code == 404
