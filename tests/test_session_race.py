"""登录前开始、登录后结束的请求不能把旧 Cookie 写回去（「登录成功，刷新失败」）。"""
import http.cookiejar

from jlu_toolkit import jwxt


def _ck(name, value, domain="cas.jlu.edu.cn"):
    return http.cookiejar.Cookie(0, name, value, None, False, domain, True, False, "/", True,
                                 True, None, False, None, None, {})


def _names(tmp_path):
    c = jwxt.JwxtClient()
    assert c.load_session()
    return {(k.name, k.value) for k in c.jar}


def test_stale_request_does_not_overwrite_fresh_login(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("JLU_TOOLKIT_NO_KEYRING", "1")
    monkeypatch.setenv("JLU_TOOLKIT_QUIET_STORE", "1")
    old = jwxt.JwxtClient()
    old.jar.set_cookie(_ck("CASTGC", "old"))
    old.save_session()

    stale = jwxt.JwxtClient()          # 例如打开 OA 通知：登录前读到旧会话
    assert stale.load_session()

    fresh = jwxt.JwxtClient()          # 登录流程：全新客户端，登录成功后保存
    fresh.jar.set_cookie(_ck("CASTGC", "new"))
    fresh.save_session()

    stale.save_session()               # 旧请求结束：不能覆盖
    assert ("CASTGC", "new") in _names(tmp_path)

    r = jwxt.JwxtClient()              # 登录后的刷新读到新会话，自己保存不受影响
    assert r.load_session()
    r.jar.set_cookie(_ck("_WEU", "x", "iedu.jlu.edu.cn"))
    r.save_session()
    r.save_session()
    assert ("_WEU", "x") in _names(tmp_path)


def test_logout_not_resurrected(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("JLU_TOOLKIT_NO_KEYRING", "1")
    monkeypatch.setenv("JLU_TOOLKIT_QUIET_STORE", "1")
    a = jwxt.JwxtClient()
    a.jar.set_cookie(_ck("CASTGC", "v"))
    a.save_session()
    b = jwxt.JwxtClient()
    assert b.load_session()
    jwxt.JwxtClient().clear_session_file()
    b.save_session()
    assert not jwxt.JwxtClient().load_session()
