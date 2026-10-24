from pathlib import Path
"""jwxt 单元测试：加密向量、二次认证分类、模拟 HTTP。不访问真实教务。"""
from unittest import mock

import pytest

from jlu_toolkit import jwxt
from jlu_toolkit.des_tpass import strEnc, strDec


def test_strenc_matches_login10_js_vectors():
    assert strEnc("a", "1", "2", "3") == "A62B4F77D5F8C6C7"
    assert strEnc("abcd", "1", "2", "3") == "A9CF2704230383D1"
    assert (
        strEnc("abcde", "1", "2", "3")
        == "A9CF2704230383D100DE5835FF643FD8"
    )
    assert (
        strEnc("2021001234WrongPass!LT-TEST-abc", "1", "2", "3")
        == "B6FC8B80C5445D4B3F18F3B7CC8F793AADF1687CA51FC40AEE4D770A7CD23E1F"
        "06A44DF02FBE364323F565D94D86535E620B0E1BD16331DC39644174795FB4D0"
    )
    assert strDec(strEnc("secret", "neusoft", "cas", "pd"), "neusoft", "cas", "pd") == "secret"


def test_encrypt_password_bundle():
    rsa = jwxt.JwxtClient.encrypt_password_bundle("u", "p", "LT-1")
    assert rsa == strEnc("upLT-1", "1", "2", "3")


def test_parse_weeks_and_teacher():
    assert jwxt.parse_weeks_skzc("0101") == [2, 4]
    assert jwxt.clean_teacher("张三/1001,李四/1002") == "张三,李四"


def test_row_to_course_and_grade():
    c = jwxt.row_to_course(
        {
            "KCM": "高等数学",
            "SKJS": "王五/2001",
            "JASMC": "经信A101",
            "SKXQ": "1",
            "KSJC": "1",
            "JSJC": "2",
            "SKZC": "1111000000000000",
        }
    )
    assert c is not None and c.weeks == [1, 2, 3, 4]
    g = jwxt.row_to_grade(
        {"KCM": "线代", "XF": "3.0", "ZCJ": "88", "XNXQDM": "2025-2026-1"}
    )
    assert g is not None and g.score == "88"


def test_emap_str_coerces_numeric():
    assert jwxt._emap_str(None) == ""
    assert jwxt._emap_str(92.0) == "92"
    assert jwxt._emap_str(3.5) == "3.5"
    assert jwxt._emap_str(88) == "88"
    assert jwxt._emap_str(" 优秀 ") == "优秀"
    assert jwxt._emap_str("92.0") == "92"


def test_row_to_grade_numeric_fields():
    """EMAP 常把 ZCJ/XF 序列化为 JSON number（float）。"""
    g = jwxt.row_to_grade(
        {"KCM": "操作系统", "XF": 3.0, "ZCJ": 92.0, "XNXQDM": "2025-2026-1"}
    )
    assert g is not None
    assert g.score == "92"
    assert g.credit == 3.0
    assert g.name == "操作系统"

    g2 = jwxt.row_to_grade(
        {"KCM": "体育", "XF": 1, "ZCJ": None, "DJCJMC": "优秀", "XNXQDM": 202520261}
    )
    assert g2 is not None and g2.score == "优秀"
    assert g2.term == "202520261"

    g3 = jwxt.row_to_grade(
        {"KCM": "选修", "XF": 2.0, "ZCJ": "", "XSZCJMC": "及格", "XNXQDM": "2024-2025-2"}
    )
    assert g3 is not None and g3.score == "及格"


def test_row_to_course_numeric_fields():
    c = jwxt.row_to_course(
        {
            "KCM": "数据结构",
            "SKJS": "赵六/9",
            "JASMC": None,
            "SKXQ": 3.0,
            "KSJC": 5.0,
            "JSJC": 6,
            "SKZC": 1111111111111111,  # 偶发 number
        }
    )
    assert c is not None
    assert c.weekday == 3 and c.start == 5 and c.end == 6
    assert c.location == "待定"
    assert c.teacher == "赵六"


def test_classify_need_second_factor():
    html = """
    <html><body><h1>二次认证</h1>
    <form class="recheck">
      <input name="lt" value="LT-2FA" />
      <input name="execution" value="e1s2" />
      <input name="WxCode" />
      <img id="codeImage" src="code?1"/>
      <a href="recheckcode">获取微信验证码</a>
    </form></body></html>
    """
    assert jwxt.classify_login_html(html) == jwxt.LoginStep.NEED_SECOND_FACTOR


def test_classify_wrong_password():
    html = '<div>用户名或密码有误，请重新输入。</div><footer>微信扫码</footer>'
    assert jwxt.classify_login_html(html) == jwxt.LoginStep.WRONG_PASSWORD


def test_classify_username_password_error_no_huo():
    html = '<span id="errormsghide" class="login_box_title_notice script_red">用户名密码错误<br/></span><form id="loginForm"></form>'
    assert jwxt.classify_login_html(html) == jwxt.LoginStep.WRONG_PASSWORD
    assert jwxt.extract_cas_error(html) == "用户名密码错误"


def test_normalize_username():
    assert jwxt.normalize_username("  foo@mails.jlu.edu.cn ") == "foo"
    assert jwxt.normalize_username("bar@jlu.edu.cn") == "bar"
    assert jwxt.normalize_username("baz") == "baz"


LOGIN_HTML = '''
<form id="loginForm" action="/tpass/login?service=https%3A%2F%2Fiedu.jlu.edu.cn%2F" method="post">
<input type="hidden" id="lt" name="lt" value="LT-UNIT-TEST" />
<input type="hidden" name="execution" value="e1s1" />
<input type="hidden" name="_eventId" value="submit" />
</form>
'''

RECHECK_HTML = '''
<html><body><h1>二次认证</h1>
<form>
<input type="hidden" id="lt" name="lt" value="LT-RECHECK" />
<input type="hidden" name="execution" value="e1s2" />
<input type="hidden" name="_eventId" value="submit" />
<input name="code" />
<input name="WxCode" />
<script>fetch("recheckcode?code=")</script>
</form></body></html>
'''


def test_login_password_need_2fa_mocked():
    client = jwxt.JwxtClient()

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        if data is None:
            return 200, LOGIN_HTML, url, LOGIN_HTML.encode()
        return 200, RECHECK_HTML, url, RECHECK_HTML.encode()

    with mock.patch.object(client, "_request", side_effect=fake_request):
        step = client.login_password("mailprefix", "secret")
    assert step == jwxt.LoginStep.NEED_SECOND_FACTOR
    assert client.pending is not None
    assert client.pending.lt == "LT-RECHECK"
    assert client.pending.execution == "e1s2"


def test_login_password_success_mocked():
    client = jwxt.JwxtClient()
    calls = {"n": 0}

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        calls["n"] += 1
        if data is None and "login" in url and allow_redirects is not False:
            # GET login page (allow_redirects default True in fetch)
            return 200, LOGIN_HTML, url, LOGIN_HTML.encode()
        if data is None and allow_redirects is False:
            # following ticket redirect or portal hit
            return 200, "<html>portal</html>", jwxt.CAS_SERVICE, b"<html>portal</html>"
        if data is not None:
            # password POST: 302 to service with ticket
            assert b"sl=0" in data
            assert b"ul=10" in data  # mailprefix
            loc = jwxt.CAS_SERVICE + "?ticket=ST-TEST"
            return 302, "", loc, b""
        return 200, LOGIN_HTML, url, LOGIN_HTML.encode()

    with mock.patch.object(client, "_request", side_effect=fake_request):
        step = client.login_password("mailprefix", "secret")
    assert step == jwxt.LoginStep.SUCCESS
    assert client._logged_in


def test_login_password_trims_and_strips_email():
    client = jwxt.JwxtClient()
    seen = {}

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        if data is None:
            return 200, LOGIN_HTML, url, LOGIN_HTML.encode()
        seen["data"] = data
        return 200, RECHECK_HTML, url, RECHECK_HTML.encode()

    with mock.patch.object(client, "_request", side_effect=fake_request):
        step = client.login_password("  prefix@mails.jlu.edu.cn  ", "  secret  ")
    assert step == jwxt.LoginStep.NEED_SECOND_FACTOR
    # ul=len("prefix")==6, pl=len("secret")==6
    assert b"ul=6" in seen["data"]
    assert b"pl=6" in seen["data"]


def test_request_wechat_code_reads_cookie():
    client = jwxt.JwxtClient()

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        from http.cookiejar import Cookie

        client.jar.set_cookie(
            Cookie(
                0, "recheck_mobile_error_info", "success", None, False,
                "cas.jlu.edu.cn", True, False, "/", True, False, None, True,
                None, None, {}, False,
            )
        )
        return 200, "", url, b""

    with mock.patch.object(client, "_request", side_effect=fake_request):
        assert client.request_wechat_code("3908") == jwxt.WechatCodeResult.SUCCESS


def test_login_second_factor_mocked():
    client = jwxt.JwxtClient()
    client.pending = jwxt.PendingSecondFactor(lt="LT-X", execution="e1s2")

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        assert b"WxCode=123456" in data
        assert b"code=3908" in data
        return 200, "<html>ok</html>", jwxt.IEDU_PORTAL, b"<html>ok</html>"

    with mock.patch.object(client, "_request", side_effect=fake_request):
        step = client.login_second_factor("3908", "123456")
    assert step == jwxt.LoginStep.SUCCESS
    assert client.pending is None


def test_download_captcha_mocked(tmp_path):
    client = jwxt.JwxtClient()
    jpeg = (Path(__file__).parent / "fixtures" / "sample_captcha.jpg").read_bytes()

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        assert "/code" in url
        assert headers and "Referer" in headers
        client.last_content_type = "image/jpeg"
        return 200, "", url, jpeg

    path = tmp_path / "c.jpg"
    with mock.patch.object(client, "_request", side_effect=fake_request):
        saved = client.download_captcha(path)
    assert saved.read_bytes() == jpeg
    assert client.last_captcha_bytes == jpeg


def test_download_captcha_rejects_html(tmp_path):
    client = jwxt.JwxtClient()
    html = b"<!DOCTYPE html><html><body>error</body></html>" + b" " * 200

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        client.last_content_type = "text/html"
        return 200, html.decode(), url, html

    with mock.patch.object(client, "_request", side_effect=fake_request):
        with pytest.raises(jwxt.SecondFactorError, match="不是有效图片"):
            client.download_captcha(tmp_path / "bad.jpg")


def test_session_save_load(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    client = jwxt.JwxtClient()
    from http.cookiejar import Cookie

    client.jar.set_cookie(
        Cookie(
            0, "tpasssessionid", "ABC", None, False,
            "cas.jlu.edu.cn", True, False, "/tpass", True, False, None, True,
            None, None, {}, False,
        )
    )
    path = client.save_session()
    assert path.exists()
    other = jwxt.JwxtClient()
    assert other.load_session()
    names = {c.name: c.value for c in other.jar}
    assert names["tpasssessionid"] == "ABC"



def test_captcha_save_path_prefers_termux_downloads(tmp_path, monkeypatch):
    home = tmp_path / "home"
    downloads = home / "storage" / "downloads"
    downloads.mkdir(parents=True)
    monkeypatch.setattr(jwxt.Path, "home", classmethod(lambda cls: home))
    p = jwxt.captcha_save_path("x.jpg")
    assert p == downloads / "x.jpg"


def test_save_load_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(jwxt.secure_store, "can_encrypt", lambda: True)
    path = tmp_path / "credentials.json"
    jwxt.save_credentials("prefix", "p1", path)
    assert jwxt.load_credentials(path) == ("prefix", "p1")


def test_fetch_schedule_mocked():
    client = jwxt.JwxtClient()

    def fake_post(path, fields, referer):
        if path.endswith("dqxnxq.do"):
            return {"datas": {"dqxnxq": {"rows": [{"DM": "2025-2026-2"}]}}}
        return {
            "datas": {
                "cxxszhxqkb": {
                    "rows": [
                        {
                            "KCM": "操作系统",
                            "SKJS": "赵六/9",
                            "JASMC": "A201",
                            "SKXQ": 3,
                            "KSJC": 5,
                            "JSJC": 6,
                            "SKZC": "1111111111111111",
                        }
                    ]
                }
            }
        }

    with mock.patch.object(client, "enter_emap_app") as enter, mock.patch.object(
        client, "_post_form", side_effect=fake_post
    ):
        courses = client.fetch_schedule()
    assert courses[0].name == "操作系统"
    enter.assert_called_with(jwxt.REF_SCHEDULE)


def test_enter_emap_app_sets_context():
    client = jwxt.JwxtClient(debug=False)
    calls = []

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        calls.append(url)
        if "wdkb" in url or "emaphome" in url:
            return 200, "<html>ok</html>", url, b"<html>ok</html>"
        return 200, "", url, b""

    with mock.patch.object(client, "_request", side_effect=fake_request):
        client.enter_emap_app(jwxt.REF_SCHEDULE)
    assert any("wdkb" in u for u in calls)
    assert client.last_debug.get("step") == "emap_enter_done"


def test_enter_emap_app_requires_castgc_when_bounced_to_cas():
    client = jwxt.JwxtClient()

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        return (
            200,
            '<form id="loginForm"></form>',
            "https://cas.jlu.edu.cn/tpass/login",
            b"<form id=\"loginForm\"></form>",
        )

    with mock.patch.object(client, "_request", side_effect=fake_request):
        with pytest.raises(jwxt.LoginError, match="重新登录"):
            client.enter_emap_app(jwxt.REF_SCHEDULE)


def test_post_form_403_message():
    client = jwxt.JwxtClient()

    def fake_request(url, data=None, headers=None, method=None, allow_redirects=True):
        return 403, "forbidden", url, b"forbidden"

    with mock.patch.object(client, "_request", side_effect=fake_request):
        with pytest.raises(jwxt.JwxtError, match="403"):
            client._post_form("/jwapp/sys/wdkb/modules/jshkcb/dqxnxq.do", {}, jwxt.REF_SCHEDULE)


def test_session_cookie_summary_flags():
    client = jwxt.JwxtClient()
    from http.cookiejar import Cookie

    client.jar.set_cookie(
        Cookie(
            0, "CASTGC", "TGT-1", None, False,
            "cas.jlu.edu.cn", True, False, "/", True, False, None, True,
            None, None, {}, False,
        )
    )
    client.jar.set_cookie(
        Cookie(
            0, "_WEU", "abc", None, False,
            "iedu.jlu.edu.cn", True, False, "/jwapp", True, False, None, True,
            None, None, {}, False,
        )
    )
    s = client.session_cookie_summary()
    assert s["has_CASTGC"] and s["has__WEU"]
    assert client.has_cas_tgc()
