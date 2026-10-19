"""吉大本科教务（iedu.jlu.edu.cn 金智 jwapp）HTTP 客户端。

登录走统一身份认证 cas.jlu.edu.cn/tpass（Neusoft TPASS / login10.js）：
  1) GET 登录页 → 解析 form#loginForm 的 action/lt/execution
     → 按浏览器字段提交 rsa=strEnc(trim(账号)+trim(密码)+lt,'1','2','3'),
       ul/pl/sl=0/lt/execution/_eventId=submit（缺 sl 会 HTTP 500）
  2) 若返回「二次认证」页：下载图形验证码 /tpass/code → 调 /tpass/recheckcode 发微信验证码
     → 再 POST lt/execution/code/WxCode 完成登录 → 跟随 ticket 回跳教务

课表/成绩接口（对照 JFyuhong/JLU_schedule ScheduleRemoteSource）：
  - 先 GET 应用入口 *default/index.do 激活 _WEU 等业务 Cookie（可顺带用 CASTGC 换票）
  - 当前学期 POST /jwapp/sys/wdkb/modules/jshkcb/dqxnxq.do
  - 课表     POST /jwapp/sys/wdkb/modules/xskcb/cxxszhxqkb.do
  - 成绩     POST /jwapp/sys/cjcx/modules/cjcx/xscjcx.do
  - 请求头需带 X-Requested-With / Referer=对应应用入口

仅标准库。密码与验证码不会写入日志。
"""
from __future__ import annotations

import csv
import http.client
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from http.cookiejar import Cookie, CookieJar
from pathlib import Path
from typing import Iterable, Optional

from . import secure_store
from . import core
from .des_tpass import strEnc
from . import captcha_util
from . import network

CAS_BASE = "https://cas.jlu.edu.cn/tpass"
CAS_LOGIN = f"{CAS_BASE}/login"
CAS_CODE = f"{CAS_BASE}/code"
CAS_RECHECKCODE = f"{CAS_BASE}/recheckcode"
IEDU_HOST = "iedu.jlu.edu.cn"
# 与当前登录页 form#loginForm action 默认 service 一致（浏览器从教务入口跳转时也是这个）
CAS_SERVICE = "https://iedu.jlu.edu.cn/"
IEDU_PORTAL = "https://iedu.jlu.edu.cn/jwapp/sys/emaphome/portal/index.do"
IEDU_BASE = "https://iedu.jlu.edu.cn"

from . import endpoints as _EP  # noqa: E402

EP_CURRENT_SEM = _EP.KNOWN["current_term"].path
EP_COURSES = _EP.KNOWN["schedule"].path
EP_GRADES = _EP.KNOWN["grades"].path
REF_SCHEDULE = "https://iedu.jlu.edu.cn/jwapp/sys/wdkb/*default/index.do"
REF_GRADES = "https://iedu.jlu.edu.cn/jwapp/sys/cjcx/*default/index.do"
# 考试安排（金智通用 studentWdksapApp；参考 XJTU/BIT 公开脚本）
REF_EXAMS = "https://iedu.jlu.edu.cn/jwapp/sys/studentWdksapApp/*default/index.do"
EP_EXAMS = _EP.KNOWN["exams_alt"].path
EP_EXAMS_ALT = _EP.KNOWN["exams"].path

# 与 wzyyyyyyy/iLearn 一致的桌面 Chrome UA（login10.js 无移动端特殊分支）
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_LT_RE = re.compile(r'(?:id|name)="lt"[^>]*value="([^"]*)"', re.I)
_LT_RE2 = re.compile(r'value="([^"]*)"[^>]*(?:id|name)="lt"', re.I)
_EXEC_RE = re.compile(r'name="execution"[^>]*value="([^"]*)"', re.I)
_EVENT_RE = re.compile(r'name="_eventId"[^>]*value="([^"]*)"', re.I)
_ERR_RE = re.compile(r'id="errormsg"[^>]*>([^<]*)', re.I)
_ERR_HIDE_RE = re.compile(
    r'id="errormsghide"[^>]*class="[^"]*script_red[^"]*"[^>]*>(.*?)</span>',
    re.I | re.S,
)
_ERR_HIDE_RE2 = re.compile(
    r'id="errormsghide"[^>]*>(.*?)</span>',
    re.I | re.S,
)
_FORM_ACTION_RE = re.compile(
    r'<form[^>]*\bid=["\']loginForm["\'][^>]*\baction=["\']([^"\']+)["\']',
    re.I,
)
_WXCODE_RE = re.compile(r'name=["\']WxCode["\']', re.I)
_JLU_EMAIL_SUFFIXES = (
    "@mails.jlu.edu.cn",
    "@jlu.edu.cn",
    "@mail.jlu.edu.cn",
)


class JwxtError(Exception):
    """教务/认证相关错误。"""


class LoginError(JwxtError):
    """用户名或密码错误，或登录被拒绝。"""


class NetworkError(JwxtError):
    """网络不可达（常见于校外访问不到 iedu）。"""

    def __init__(self, message, kind="connection", can_connect_vpn=False):
        super().__init__(message)
        self.kind = kind
        self.can_connect_vpn = can_connect_vpn


class SessionExpiredError(LoginError):
    """已保存的会话失效（教务把请求重定向到了 CAS 登录页）。需要重新走微信验证码登录。"""

    def __init__(self, msg: str = "登录会话已过期，请在「更多 → 登录」中重新登录"):
        super().__init__(msg)


class SecondFactorError(JwxtError):
    """二次认证（图形/微信验证码）失败。"""


class LoginStep(Enum):
    SUCCESS = "success"
    NEED_SECOND_FACTOR = "need_second_factor"
    WRONG_PASSWORD = "wrong_password"
    FAILED = "failed"


class WechatCodeResult(Enum):
    SUCCESS = "success"
    CAPTCHA_ERROR = "img_code_error"
    TOO_FREQUENT = "get_times_more"
    SESSION_EXPIRED = "get_session_error"
    FAILED = "failed"


@dataclass
class PendingSecondFactor:
    lt: str
    execution: str
    event_id: str = "submit"
    service: str = CAS_SERVICE


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "jlu-toolkit"


def default_cred_path() -> Path:
    return config_dir() / "credentials.json"


def default_session_path() -> Path:
    return config_dir() / "session.json"


def captcha_save_path(filename: str = "jlu_cas_captcha.jpg") -> Path:
    """优先 Termux ~/storage/downloads，其次 Pictures/dcim、当前目录、系统临时目录。

    只返回真正可写的目录：Android App 里 cwd 是只读的 "/"，
    直接写会 OSError [Errno 30]。
    """
    for p in captcha_util.captcha_candidate_paths(filename):
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if os.access(p.parent, os.W_OK):
                return p
        except OSError:
            continue
    import tempfile
    return Path(tempfile.mkdtemp(prefix="superjlu-")) / filename


def _chmod600(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _secret(path: Path) -> "secure_store.SecretFile":
    return secure_store.SecretFile(path.parent, path.stem)


def _cred_accounts(data) -> list:
    """凭据文件里的账号列表（最近使用在前）；兼容旧的单账号格式。"""
    out, seen = [], set()
    if not isinstance(data, dict):
        return out
    items = list(data.get("accounts") or [])
    if data.get("username") and data.get("password"):
        items.insert(0, {"username": data["username"], "password": data["password"]})
    for a in items:
        if not isinstance(a, dict):
            continue
        u, pw = a.get("username"), a.get("password")
        if u and pw and str(u) not in seen:
            seen.add(str(u))
            out.append({"username": str(u), "password": str(pw)})
    return out


def _save_accounts(accounts: list, path: Path) -> Path:
    top = accounts[0] if accounts else {"username": "", "password": ""}
    return _secret(path).save({"username": top["username"], "password": top["password"], "accounts": accounts})


def save_credentials(username: str, password: str, path: Optional[Path] = None) -> Path:
    """保存账号密码（可多账号，最近使用的排第一）：优先系统钥匙串加密（见 secure_store），否则 0600 明文文件。"""
    path = path or default_cred_path()
    accts = [a for a in _cred_accounts(_secret(path).load()) if a["username"] != username]
    return _save_accounts([{"username": username, "password": password}] + accts, path)


def load_credentials(path: Optional[Path] = None) -> Optional[tuple[str, str]]:
    """最近使用的账号 (username, password)。"""
    path = path or default_cred_path()
    accts = _cred_accounts(_secret(path).load())
    return (accts[0]["username"], accts[0]["password"]) if accts else None


def account_password(username: str, path: Optional[Path] = None) -> Optional[str]:
    path = path or default_cred_path()
    for a in _cred_accounts(_secret(path).load()):
        if a["username"] == username:
            return a["password"]
    return None


def list_accounts(path: Optional[Path] = None) -> list:
    """已保存的账号名（不含密码），最近使用在前。"""
    path = path or default_cred_path()
    return [a["username"] for a in _cred_accounts(_secret(path).load())]


def delete_account(username: str, path: Optional[Path] = None) -> bool:
    """删除一个已保存账号及其密码；返回是否删到了。"""
    path = path or default_cred_path()
    accts = _cred_accounts(_secret(path).load())
    rest = [a for a in accts if a["username"] != username]
    if len(rest) == len(accts):
        return False
    _save_accounts(rest, path)
    return True


# ---- 会话状态（给 Web UI / MCP 用；不含任何秘密） ----
SESSION_OK = "ok"
SESSION_EXPIRED = "expired"
SESSION_MISSING = "missing"
SESSION_UNKNOWN = "unknown"


def session_status_path() -> Path:
    return config_dir() / "session_status.json"


def _write_session_status(state: str, reason: str = "") -> None:
    try:
        p = session_status_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        prev = {}
        if p.is_file():
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                prev = {}
        now = int(time.time())
        obj = {"state": state, "checked_at": now, "reason": reason,
               "saved_at": now if state == SESSION_OK else prev.get("saved_at")}
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def mark_session_expired(reason: str = "") -> None:
    _write_session_status(SESSION_EXPIRED, reason)


def session_status() -> dict:
    """返回 {state, logged_in, needs_login, message, checked_at, saved_at, storage}。

    只读本地文件，不访问网络。state: ok / expired / missing / unknown。
    """
    has = _secret(default_session_path()).exists()
    info: dict = {}
    p = session_status_path()
    if p.is_file():
        try:
            info = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            info = {}
    if not has:
        state = SESSION_MISSING
    else:
        state = info.get("state") or SESSION_UNKNOWN
    msg = {
        SESSION_OK: "已登录",
        SESSION_EXPIRED: "登录已过期，请在「更多 → 登录」中重新登录",
        SESSION_MISSING: "尚未登录，请在「更多 → 登录」中登录",
        SESSION_UNKNOWN: "已保存会话，尚未验证是否有效",
    }[state]
    return {
        "state": state,
        "logged_in": state == SESSION_OK,
        "needs_login": state in (SESSION_EXPIRED, SESSION_MISSING),
        "session_expired": state == SESSION_EXPIRED,  # 与 Web UI（PR #6）约定的顶层字段
        "message": msg,
        "checked_at": info.get("checked_at"),
        "saved_at": info.get("saved_at"),
        "storage": secure_store.backend_name(),
    }


_REMEMBER_RE = re.compile(r"<input\b[^>]*\bname=[\"']((?:remember|rememberMe|rememberme|warn)[\w-]*)[\"'][^>]*>", re.I)


def remember_me_fields(html: str) -> list:
    """登录表单若有「记住我」类字段（remember*/rememberMe），返回 [(name, value)] 以开启它；没有则 []。"""
    out = []
    for m in _REMEMBER_RE.finditer(html or ""):
        name = m.group(1)
        if name.lower() == "warn":
            continue
        vm = re.search(r"\bvalue=[\"']([^\"']*)[\"']", m.group(0), re.I)
        out.append((name, (vm.group(1) if vm and vm.group(1) not in ("", "false", "0") else "true")))
    return out[:2]


def looks_like_login_redirect(final_url: str, text: str = "") -> bool:
    """响应是否落在了 CAS 登录页 / 二次认证页（= 会话失效）。"""
    u = urllib.parse.urlparse(final_url or "")
    if (u.hostname or "").startswith("cas.") and "/tpass/login" in (u.path or ""):
        return True
    head = (text or "")[:8192]
    low = head.lower()
    return 'id="loginform"' in low or "二次认证" in head or ("/tpass/login" in low and "password" in low)


def parse_weeks_skzc(skzc: str) -> list[int]:
    return [i + 1 for i, ch in enumerate(skzc or "") if ch == "1"]


def clean_teacher(raw: str) -> str:
    if not raw:
        return ""
    names = []
    for part in raw.split(","):
        name = part.split("/")[0].strip()
        if name:
            names.append(name)
    return ",".join(names)


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def _extract_lt(html: str) -> Optional[str]:
    m = _LT_RE.search(html) or _LT_RE2.search(html)
    return m.group(1) if m else None


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).replace("&nbsp;", " ").strip()


def extract_cas_error(html: str) -> Optional[str]:
    """从登录页提取服务器错误文案（优先 #errormsghide.script_red）。"""
    m = _ERR_HIDE_RE.search(html) or _ERR_HIDE_RE2.search(html)
    if m:
        msg = _strip_tags(m.group(1))
        if msg:
            return msg
    m = _ERR_RE.search(html)
    if m:
        msg = _strip_tags(m.group(1))
        # 默认隐藏文案「请输入正确信息」在未失败时也会出现，单独不够作失败证据
        if msg and msg not in ("请输入正确信息",):
            return msg
    return None


def normalize_username(username: str) -> str:
    """login10.js 会对账号 trim；若粘贴了完整吉大邮箱则剥成前缀。"""
    u = (username or "").strip()
    low = u.lower()
    for suf in _JLU_EMAIL_SUFFIXES:
        if low.endswith(suf):
            return u[: len(u) - len(suf)]
    return u


def _form_action_url(html: str, service: str) -> str:
    """优先用页面 form#loginForm 的 action（与浏览器提交目标一致）。"""
    m = _FORM_ACTION_RE.search(html)
    if m:
        return urllib.parse.urljoin("https://cas.jlu.edu.cn", m.group(1))
    return f"{CAS_LOGIN}?service={urllib.parse.quote(service, safe='')}"


def classify_login_html(html: str) -> LoginStep:
    """根据密码提交后的 HTML 判断下一步（对照 wzyyyyyyy/iLearn LoginResponseClassifier）。"""
    # 先查明确的错密文案（含「用户名密码错误」，无「或」）
    wrong_markers = (
        "用户名密码错误",
        "用户名或密码错误",
        "账号或密码错误",
        "用户名或密码有误",
        "账号或密码有误",
        "密码错误",
        "密码有误",
    )
    if any(m in html for m in wrong_markers):
        return LoginStep.WRONG_PASSWORD
    err = extract_cas_error(html)
    if err and any(m in err for m in ("错误", "有误", "失败")):
        # errormsghide 标红时几乎总是认证失败
        if "二次认证" not in html and not _WXCODE_RE.search(html):
            return LoginStep.WRONG_PASSWORD
    if (
        _WXCODE_RE.search(html)
        or "recheckcode" in html.lower()
        or "二次认证" in html
        or 'name="WxCode"' in html
        or "获取微信验证码" in html
    ):
        return LoginStep.NEED_SECOND_FACTOR
    if 'id="loginForm"' in html or "id='loginForm'" in html:
        return LoginStep.WRONG_PASSWORD
    return LoginStep.SUCCESS


def jar_to_list(jar: CookieJar) -> list[dict]:
    out = []
    for c in jar:
        out.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path or "/",
                "secure": bool(c.secure),
                "expires": c.expires,
                "rest": dict(c._rest) if getattr(c, "_rest", None) else {},
            }
        )
    return out


def jar_from_list(items: list[dict]) -> CookieJar:
    jar = CookieJar()
    for d in items:
        c = Cookie(
            version=0,
            name=d["name"],
            value=d["value"],
            port=None,
            port_specified=False,
            domain=d.get("domain") or "",
            domain_specified=bool(d.get("domain")),
            domain_initial_dot=str(d.get("domain") or "").startswith("."),
            path=d.get("path") or "/",
            path_specified=True,
            secure=bool(d.get("secure")),
            expires=d.get("expires"),
            discard=d.get("expires") is None,
            comment=None,
            comment_url=None,
            rest=d.get("rest") or {},
            rfc2109=False,
        )
        jar.set_cookie(c)
    return jar


def _redact_url(url: str) -> str:
    """日志用：保留 host/path，抹掉 ticket/jsessionid 等敏感 query。"""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    redacted = []
    for k, v in q:
        lk = k.lower()
        if lk in ("ticket", "jsessionid", "tpasssessionid") or "token" in lk:
            redacted.append((k, "<redacted>"))
        else:
            redacted.append((k, v))
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(redacted), "")
    )


class JwxtClient:
    def __init__(self, timeout: float = 25.0, debug: bool = False, route=None):
        self.timeout = timeout
        self.debug = debug
        from . import webvpn
        self.route = route or webvpn.mode()
        if self.route not in ("direct", "webvpn"):
            raise ValueError("请选择校园网直连或校外 WebVPN")
        self._restore_saved_cas = True
        self._vpn_cookies_loaded = False
        self.jar = CookieJar()
        self._native_hosts = set()
        self._rebuild_opener()
        self._logged_in = False
        self.pending: Optional[PendingSecondFactor] = None
        self.last_debug: dict = {}
        self.last_error_text: Optional[str] = None
        self.last_content_type: Optional[str] = None
        self.last_status: Optional[int] = None
        self.last_captcha_bytes: Optional[bytes] = None
        self.last_captcha_paths: list = []

    def _restore_vpn_cookies(self):
        if self.route == "webvpn" and not self._vpn_cookies_loaded:
            from . import sessions
            cas = (sessions.load_cookies("cas") or []) if self._restore_saved_cas else []
            if cas:
                for cookie in list(self.jar):
                    if (cookie.domain or "").lstrip(".") == "cas.jlu.edu.cn":
                        self.jar.clear(cookie.domain, cookie.path, cookie.name)
                for cookie in jar_from_list(cas):
                    self.jar.set_cookie(cookie)
            for cookie in jar_from_list(sessions.load_cookies("vpn") or []):
                if (cookie.domain or "").lstrip(".") == "vpn.jlu.edu.cn":
                    self.jar.set_cookie(cookie)
            self._vpn_cookies_loaded = True

    def _dbg(self, **kwargs) -> None:
        self.last_debug.update(kwargs)
        if not self.debug:
            return
        parts = []
        for k, v in kwargs.items():
            parts.append(f"{k}={v}")
        print("[debug] " + " ".join(parts), flush=True)

    def _rebuild_opener(self) -> None:
        from . import webvpn
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar),
            network.SchoolHTTPSHandler(_ssl_context(), self._native_hosts, self._dbg,
                                      ("cas.jlu.edu.cn", IEDU_HOST, "vpn.jlu.edu.cn")),
            webvpn.RedirectHandler(self),
        )

    def _cookie_names(self) -> list[str]:
        return sorted({c.name for c in self.jar})

    def _has_cookie(self, name: str) -> bool:
        return any(c.name == name for c in self.jar)

    def has_cas_tgc(self) -> bool:
        """CAS 长期票据（通常名 CASTGC）。有则可对多个教务应用静默换票。"""
        return self._has_cookie("CASTGC") or self._has_cookie("TGC")

    def has_cas_cookie(self) -> bool:
        """jar 里有任何统一认证（cas.jlu.edu.cn）的 cookie。

        学校 CAS 不一定下发 CASTGC（也可能改名），tpasssessionid 等同样能让 CAS 静默签发 ticket，
        所以只要有 CAS cookie 就值得先试一次换票，失败再要求重新登录。
        """
        return self.has_cas_tgc() or any(
            (c.domain or "").lstrip(".").lower() == "cas.jlu.edu.cn" for c in self.jar)

    def session_cookie_summary(self) -> dict:
        names = self._cookie_names()
        return {
            "cookie_names": names,
            "has_CASTGC": "CASTGC" in names or "TGC" in names,
            "has__WEU": "_WEU" in names,
            "has_MOD_AUTH_CAS": "MOD_AUTH_CAS" in names,
            "has_tpasssessionid": "tpasssessionid" in names,
        }

    def _request(
        self,
        url: str,
        data: Optional[bytes] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = None,
        allow_redirects: bool = True,
    ) -> tuple[int, str, str, bytes]:
        hdrs = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if headers:
            hdrs.update(headers)
        from . import webvpn
        logical_url = url
        if self.route == "webvpn":
            self._restore_vpn_cookies()
            url = webvpn.request_url(url)
            if urllib.parse.urlsplit(url).hostname == "vpn.jlu.edu.cn":
                if "Referer" in hdrs:
                    hdrs["Referer"] = webvpn.request_url(hdrs["Referer"])
                if "Origin" in hdrs:
                    hdrs["Origin"] = "https://vpn.jlu.edu.cn"
        if allow_redirects:
            opener = self.opener
        else:
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.jar),
                network.SchoolHTTPSHandler(_ssl_context(), self._native_hosts, self._dbg,
                                          ("cas.jlu.edu.cn", IEDU_HOST, "vpn.jlu.edu.cn")),
                _NoRedirect(),
            )
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="replace")
                self.last_content_type = resp.headers.get("Content-Type")
                self.last_status = resp.getcode() or 200
                final = resp.geturl()
                if self.route == "webvpn":
                    original = webvpn.canonical_url(final)
                    destination = urllib.parse.urlsplit(original)
                    service = urllib.parse.parse_qs(destination.query).get("service", [""])[0]
                    vpn_login = destination.hostname == "vpn.jlu.edu.cn" or (
                        destination.hostname == "cas.jlu.edu.cn" and urllib.parse.urlsplit(service).hostname == "vpn.jlu.edu.cn")
                    logical_host = urllib.parse.urlsplit(logical_url).hostname
                    if vpn_login and logical_host in (IEDU_HOST, webvpn.OA_HOST):
                        raise NetworkError("应用内 WebVPN 会话不可用，请在「更多 → 登录」选择「校外 WebVPN」重新连接；教务登录和本地数据已保留。", "webvpn")
                    final = original
                if urllib.parse.urlsplit(logical_url).hostname == IEDU_HOST and self.last_status < 400:
                    webvpn.record_connection(self.route)
                return self.last_status, text, final, raw
        except urllib.error.HTTPError as e:
            raw = e.read() if e.fp else b""
            text = raw.decode("utf-8", errors="replace")
            self.last_content_type = e.headers.get("Content-Type") if e.headers else None
            self.last_status = e.code
            # 302 with no-redirect handler lands here
            loc = e.headers.get("Location", "")
            final = urllib.parse.urljoin(url, loc) if loc else url
            if self.route == "webvpn":
                final = webvpn.canonical_url(final)
            return e.code, text, final, raw
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            # Recovery happens per HTTPS hop. Replaying this whole operation
            # could repeat a password/OTP POST followed by a failing redirect.
            kind = network.error_kind(e)
            message = network.error_message(logical_url, e)
            raise NetworkError(message, kind) from e

    def save_session(self, path: Optional[Path] = None) -> Path:
        """保存 cookie（加密存储见 secure_store），并把会话状态记为 ok。"""
        path = path or default_session_path()
        out = _secret(path).save({"cookies": jar_to_list(self.jar)})
        if path == default_session_path():
            _write_session_status(SESSION_OK)
            try:  # CAS 单点登录状态单独加密保存（站点 'cas'），供会话过期时静默换票
                from . import sessions
                sessions.save_cas_from_jar(self.jar)
            except Exception:  # noqa: BLE001
                pass
            if self.route == "webvpn":
                from . import sessions
                cookies = [d for d in jar_to_list(self.jar)
                           if str(d.get("domain") or "").lstrip(".") == "vpn.jlu.edu.cn"]
                if cookies:
                    sessions.save_cookies("vpn", cookies)
        return out

    def try_cas_refresh(self) -> bool:
        """教务会话过期时，用保存的 CAS cookie 换票一次（只试一次）。"""
        if getattr(self, "_cas_tried", False) or getattr(self, "_cas_refreshing", False):
            return False
        self._cas_tried = True
        try:
            from . import sessions
            ok = sessions.refresh_via_cas("jwxt", self)
        except Exception:  # noqa: BLE001
            ok = False
        self._cas_refreshed = ok
        return ok

    def load_session(self, path: Optional[Path] = None) -> bool:
        path = path or default_session_path()
        try:
            data = _secret(path).load()
        except secure_store.SecureStoreError:
            return False
        if not isinstance(data, dict):
            return False
        self.jar = jar_from_list(data.get("cookies") or [])
        self._rebuild_opener()
        try:  # 旧会话可能已含 CAS cookie，但站点 cas 为空（#20 之前登录的）
            from . import sessions
            sessions.migrate_cas_from_jwxt(self.jar)
        except Exception:  # noqa: BLE001
            pass
        return True

    def clear_session_file(self, path: Optional[Path] = None) -> None:
        path = path or default_session_path()
        _secret(path).delete()

    def session_alive(self) -> bool:
        """探测已保存会话是否还能访问教务（不落在 CAS 登录页）。"""
        try:
            code, text, final, _ = self._request(REF_SCHEDULE)
        except NetworkError:
            return False
        host = urllib.parse.urlparse(final).hostname or ""
        if host != IEDU_HOST or code not in (200, 302) or looks_like_login_redirect(final, text):
            if self.try_cas_refresh():
                return self.session_alive()
            mark_session_expired("session_alive")
            return False
        self._logged_in = True
        _write_session_status(SESSION_OK)
        return True

    def fetch_login_page(self, service: str = CAS_SERVICE) -> tuple[str, str, str, str]:
        """返回 (html, lt, execution, post_url)。post_url 取自 form action。"""
        url = f"{CAS_LOGIN}?service={urllib.parse.quote(service, safe='')}"
        code, html, final, _ = self._request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        if code != 200:
            raise NetworkError(f"CAS 登录页 HTTP {code}")
        lt = _extract_lt(html)
        if not lt:
            raise JwxtError("登录页未找到 lt，页面结构可能已变更")
        ex_m = _EXEC_RE.search(html)
        execution = ex_m.group(1) if ex_m else "e1s1"
        post_url = _form_action_url(html, service)
        self._dbg(
            step="get_login",
            status=code,
            final_host=urllib.parse.urlparse(final).hostname,
            lt_len=len(lt),
            lt_prefix=lt[:20] + "...",
            execution=execution,
            form_action=post_url,
            cookies=self._cookie_names(),
        )
        return html, lt, execution, post_url

    @staticmethod
    def encrypt_password_bundle(username: str, password: str, lt: str) -> str:
        return strEnc(username + password + lt, "1", "2", "3")

    def _browser_post_headers(self, referer: str) -> dict:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://cas.jlu.edu.cn",
            "Referer": referer,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    def _follow_redirects(
        self, url: str, html: str, code: int, limit: int = 8
    ) -> tuple[int, str, str, list[str]]:
        """手动跟随 302/303/307，记录链路上的 URL（不含 query 里的 ticket 值）。"""
        chain: list[str] = []
        current = url
        cur_code, cur_html = code, html
        for _ in range(limit):
            if cur_code not in (301, 302, 303, 307, 308):
                break
            chain.append(_redact_url(current))
            cur_code, cur_html, current, _ = self._request(
                current,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1",
                    "Referer": "https://cas.jlu.edu.cn/",
                },
                allow_redirects=False,
            )
        if chain and cur_code not in (301, 302, 303, 307, 308):
            chain.append(_redact_url(current))
        return cur_code, cur_html, current, chain

    def login_password(
        self, username: str, password: str, service: str = CAS_SERVICE
    ) -> LoginStep:
        """第一步：提交邮箱前缀+密码。可能直接成功，或需要二次认证。

        字段与 login10.js / iLearn 对齐：rsa, ul, pl, sl=0, lt, execution, _eventId=submit。
        账号、密码先 trim（与页面 JS 一致）；完整吉大邮箱会剥成前缀。
        """
        username = normalize_username(username)
        password = (password or "").strip()
        if not username or not password:
            self.last_error_text = "账号或密码为空"
            return LoginStep.WRONG_PASSWORD

        _html, lt, execution, post_url = self.fetch_login_page(service)
        remember = remember_me_fields(_html)
        referer = f"{CAS_LOGIN}?service={urllib.parse.quote(service, safe='')}"
        rsa = self.encrypt_password_bundle(username, password, lt)
        # 字段顺序与页面 hidden input 一致；sl 不可省略（省略会 HTTP 500）
        form = urllib.parse.urlencode(
            [
                ("rsa", rsa),
                ("ul", str(len(username))),
                ("pl", str(len(password))),
                ("sl", "0"),
                ("lt", lt),
                ("execution", execution),
                ("_eventId", "submit"),
            ] + remember
        ).encode("utf-8")

        self._dbg(
            step="post_password",
            post_url=post_url,
            ul=len(username),
            pl=len(password),
            sl=0,
            rsa_len=len(rsa),
            username=username,
            cookies_before=self._cookie_names(),
        )

        code, html, final, _ = self._request(
            post_url,
            data=form,
            headers=self._browser_post_headers(referer),
            allow_redirects=False,
        )
        redirect_chain: list[str] = []
        if code in (301, 302, 303, 307, 308):
            code, html, final, redirect_chain = self._follow_redirects(final, html, code)

        step = classify_login_html(html)
        # 若仍停在 CAS 且是重定向目标页，再分类一次
        host = urllib.parse.urlparse(final).hostname or ""
        err = extract_cas_error(html)
        self.last_error_text = err
        self._dbg(
            step="post_password_result",
            status=code,
            final_url=_redact_url(final),
            final_host=host,
            redirect_chain=redirect_chain,
            classify=step.value,
            server_error=err,
            has_loginForm=('id="loginForm"' in html or "id='loginForm'" in html),
            has_二次认证=("二次认证" in html),
            has_WxCode=bool(_WXCODE_RE.search(html)),
            cookies_after=self._cookie_names(),
            body_len=len(html),
        )

        if step == LoginStep.NEED_SECOND_FACTOR:
            new_lt = _extract_lt(html) or lt
            ex_m = _EXEC_RE.search(html)
            ev_m = _EVENT_RE.search(html)
            self.pending = PendingSecondFactor(
                lt=new_lt,
                execution=ex_m.group(1) if ex_m else "e1s2",
                event_id=ev_m.group(1) if ev_m else "submit",
                service=service,
            )
            return LoginStep.NEED_SECOND_FACTOR

        if step == LoginStep.WRONG_PASSWORD:
            return LoginStep.WRONG_PASSWORD

        if host == IEDU_HOST and code in (200, 302):
            self._logged_in = True
            self.pending = None
            # 用短 service 登录成功后再访问一次门户，便于后续 API
            try:
                self._request(IEDU_PORTAL)
            except NetworkError:
                pass
            return LoginStep.SUCCESS

        if "ticket=" in final and IEDU_HOST in final:
            raise NetworkError(
                "CAS 已放行（已签发 ticket），但无法完成到教务站点的回跳。"
                "请确认当前网络能访问 iedu.jlu.edu.cn（校园网或学校 VPN）。"
            )
        if host == IEDU_HOST:
            self._logged_in = True
            self.pending = None
            return LoginStep.SUCCESS
        if host == "cas.jlu.edu.cn":
            return LoginStep.WRONG_PASSWORD
        # 其他业务站回跳也视为 CAS 密码步成功
        if code in (200, 302) and host and host != "cas.jlu.edu.cn":
            self._logged_in = True
            self.pending = None
            return LoginStep.SUCCESS
        return LoginStep.FAILED

    def download_captcha(self, path: Optional[Path] = None, save: bool = True) -> Optional[Path]:
        """GET /tpass/code → 校验为真实图片后多路径保存。

        二次认证页的 codeImage 仍指向 /tpass/code（与登录页相同）。
        必须带上当前会话 cookie；Referer 使用带 service 的登录 URL。
        CAS 返回的图通常只有约 70x36、1.5–2KB，相册常显示为「空白」——
        因此会额外写一份放大的 *_large.jpg，并尽量调用 termux-media-scan。
        """
        svc = self.pending.service if self.pending else CAS_SERVICE
        referer = f"{CAS_LOGIN}?service={urllib.parse.quote(svc, safe='')}"
        url = f"{CAS_CODE}?{int(time.time() * 1000)}"
        code, text, final, raw = self._request(
            url,
            headers={
                "Referer": referer,
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        ct = self.last_content_type
        self._dbg(
            step="download_captcha",
            status=code,
            content_type=ct,
            bytes=len(raw),
            magic=repr(raw[:8]),
            final_url=final,
            cookies=self._cookie_names(),
            referer=referer,
        )
        if code != 200:
            raise SecondFactorError(f"获取图形验证码失败 HTTP {code}")
        try:
            fmt, w, h = captcha_util.validate_captcha_bytes(raw, ct)
        except captcha_util.CaptchaImageError as e:
            snippet = text[:120].replace("\n", " ") if text else ""
            raise SecondFactorError(
                f"验证码不是有效图片：{e}；Content-Type={ct!r}；"
                f"bytes={len(raw)}；正文开头={snippet!r}"
            ) from e

        self.last_captcha_bytes = raw
        if not save:
            # 应用内自动识别只需要内存里的字节，不往工作目录（如桌面）写文件
            self.last_captcha_paths = []
            return None
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            except OSError:
                # 目标不可写（如 Android 只读根目录）：退回多路径写入
                path = None
        if path is not None:
            if path.stat().st_size < 50:
                raise SecondFactorError(f"写入验证码失败（文件过小）：{path}")
            paths = [path]
            # 仍写放大副本到同目录
            try:
                large = captcha_util.scale_for_gallery(raw)
                lp = path.with_name(path.stem + "_large.jpg")
                lp.write_bytes(large)
                paths.append(lp)
            except OSError:
                pass
        else:
            paths = captcha_util.write_captcha_files(raw)
        self.last_captcha_paths = paths
        scan = captcha_util.media_scan(paths)
        self._dbg(
            step="captcha_saved",
            format=fmt,
            width=w,
            height=h,
            paths=[str(p) for p in paths],
            media_scan=scan,
            pillow=captcha_util.has_pillow(),
            ddddocr=captcha_util.has_ddddocr(),
        )
        return paths[0]

    def request_wechat_code(self, image_captcha: str) -> WechatCodeResult:
        """GET /tpass/recheckcode?code=&t= ，结果在 cookie recheck_mobile_error_info。"""
        if not image_captcha.strip():
            raise SecondFactorError("图形验证码不能为空")
        now = int(time.time() * 1000)
        # 与浏览器一致：写入倒计时 cookie
        self.jar.set_cookie(
            Cookie(
                version=0,
                name="recheck_djsendtime",
                value=str(now + 120000),
                port=None,
                port_specified=False,
                domain="cas.jlu.edu.cn",
                domain_specified=True,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
                rfc2109=False,
            )
        )
        url = (
            f"{CAS_RECHECKCODE}?code={urllib.parse.quote(image_captcha.strip())}"
            f"&t={now}"
        )
        svc = self.pending.service if self.pending else CAS_SERVICE
        referer = f"{CAS_LOGIN}?service={urllib.parse.quote(svc, safe='')}"
        code, _, _, _ = self._request(
            url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": referer,
                "Accept": "*/*",
            },
        )
        if code != 200:
            return WechatCodeResult.FAILED
        info = None
        for c in self.jar:
            if c.name == "recheck_mobile_error_info":
                info = c.value
                break
        mapping = {
            "success": WechatCodeResult.SUCCESS,
            "img_code_error": WechatCodeResult.CAPTCHA_ERROR,
            "get_times_more": WechatCodeResult.TOO_FREQUENT,
            "get_session_error": WechatCodeResult.SESSION_EXPIRED,
        }
        return mapping.get(info or "", WechatCodeResult.FAILED)

    def login_second_factor(self, image_captcha: str, wechat_code: str) -> LoginStep:
        """第二步：提交图形验证码 + 微信验证码。"""
        if not self.pending:
            raise SecondFactorError("没有待完成的二次认证（请先完成密码登录）")
        p = self.pending
        form = urllib.parse.urlencode(
            {
                "rsa": "",
                "ul": "",
                "pl": "",
                "sl": "",
                "lt": p.lt,
                "execution": p.execution,
                "_eventId": p.event_id,
                "code": image_captcha.strip(),
                "WxCode": wechat_code.strip(),
                "not_exit_number": "",
                "service_id": "",
            }
        ).encode("utf-8")
        post_url = f"{CAS_LOGIN}?service={urllib.parse.quote(p.service, safe='')}"
        code, html, final, _ = self._request(
            post_url,
            data=form,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": post_url,
                "Origin": "https://cas.jlu.edu.cn",
            },
            allow_redirects=False,
        )
        if code in (301, 302, 303, 307, 308):
            # Separate OTP validation from the follow-up GET. A failure in the
            # latter must not be described as a failed POST to the CAS URL.
            can_connect = False
            target = urllib.parse.urlsplit(final)
            ticket = (urllib.parse.parse_qs(target.query).get("ticket") or [""])[0]
            if self.route == "direct" and target.hostname == IEDU_HOST and ticket.startswith("ST-"):
                from . import sessions
                can_connect = bool(sessions.save_cas_from_jar(self.jar))
            try:
                code, html, final, _ = self._follow_redirects(final, html, code)
            except NetworkError as error:
                hint = "可通过应用内 WebVPN 继续，无需重发验证码。" if can_connect else ""
                raise NetworkError("二次认证已返回跳转，但后续连接失败；尚未完成登录。" + str(error) + hint,
                                   error.kind, can_connect) from error
        host = urllib.parse.urlparse(final).hostname or ""
        if "验证码错误" in html:
            return LoginStep.FAILED
        if classify_login_html(html) == LoginStep.NEED_SECOND_FACTOR:
            new_lt = _extract_lt(html)
            if new_lt:
                self.pending.lt = new_lt
            ex_m = _EXEC_RE.search(html)
            if ex_m:
                self.pending.execution = ex_m.group(1)
            return LoginStep.FAILED
        landed_iedu = host == IEDU_HOST or "iedu.jlu.edu.cn" in final
        has_ticket = "ticket=" in final
        if landed_iedu:
            self._logged_in = True
            self.pending = None
            return LoginStep.SUCCESS
        if has_ticket:
            raise NetworkError(
                "二次认证似乎已通过，但无法完成到教务的回跳，请使用校园网或 VPN。"
            )
        if code in (200, 302) and host not in ("", "cas.jlu.edu.cn"):
            # 其他业务站 service 回跳也算 CAS 成功
            self._logged_in = True
            self.pending = None
            return LoginStep.SUCCESS
        return LoginStep.FAILED

    def bootstrap_emap_apps(self) -> None:
        """登录成功后预进入课表/成绩应用，写入 _WEU 等 Cookie（失败不致命）。"""
        for app in (REF_SCHEDULE, REF_GRADES):
            try:
                self.enter_emap_app(app)
            except (LoginError, JwxtError, NetworkError) as e:
                self._dbg(step="emap_bootstrap_skip", app=app, error=str(e))

    def login(self, username: str, password: str, service: str = CAS_SERVICE) -> None:
        """兼容旧接口：仅密码、无二次认证时可用；需要 2FA 时抛 LoginError。"""
        step = self.login_password(username, password, service)
        if step == LoginStep.SUCCESS:
            self.bootstrap_emap_apps()
            return
        if step == LoginStep.NEED_SECOND_FACTOR:
            raise LoginError(
                "需要二次认证（图形验证码 + 微信验证码）。请使用 CLI 交互流程。"
            )
        if step == LoginStep.WRONG_PASSWORD:
            raise LoginError("用户名或密码错误，或需要额外验证（CAS 仍停留在登录页）")
        raise LoginError("登录未完成")

    def enter_emap_app(self, app_index: str) -> None:
        """进入金智 EMAP 应用页，换发/刷新业务 Cookie（如 _WEU）。

        对照 JLU_schedule：先 GET wdkb|cjcx/*default/index.do（可跟随 CAS 换票），
        再 POST 模块接口。若落到 CAS 登录页且本地无 CASTGC，则无法静默换票。
        """
        code, html, final, _ = self._request(
            app_index,
            headers={
                "Referer": IEDU_PORTAL,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        host = urllib.parse.urlparse(final).hostname or ""
        summary = self.session_cookie_summary()
        self._dbg(
            step="emap_enter",
            app_index=app_index,
            status=code,
            final_url=_redact_url(final),
            final_host=host,
            **summary,
        )

        on_cas = host == "cas.jlu.edu.cn" or 'id="loginForm"' in html or "id='loginForm'" in html
        if on_cas or (host != IEDU_HOST and code in (200, 302)):
            if not self.has_cas_cookie():
                # 教务会话里没有 CAS cookie 时，补上单独加密保存的 CAS 登录状态（站点 cas）再换票
                try:
                    from . import sessions
                    sessions.migrate_cas_from_jwxt(self.jar)
                    for ck in jar_from_list(sessions.load_cookies("cas") or []):
                        self.jar.set_cookie(ck)
                    self._rebuild_opener()
                except Exception:  # noqa: BLE001
                    pass
            if not self.has_cas_cookie():
                mark_session_expired("emap_no_cas_cookie")
                raise SessionExpiredError(
                    "教务登录已过期，请在「更多 → 登录」中重新登录。"
                )
            # 用 CASTGC 对「该应用入口」显式换票
            cas_url = f"{CAS_LOGIN}?service={urllib.parse.quote(app_index, safe='')}"
            code, html, final, _ = self._request(
                cas_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Upgrade-Insecure-Requests": "1",
                },
            )
            host = urllib.parse.urlparse(final).hostname or ""
            summary = self.session_cookie_summary()
            self._dbg(
                step="emap_cas_exchange",
                service=app_index,
                status=code,
                final_url=_redact_url(final),
                final_host=host,
                **summary,
            )
            if host != IEDU_HOST or 'id="loginForm"' in html:
                mark_session_expired("emap_cas_exchange_failed")
                raise SessionExpiredError(
                    "统一认证的登录状态已失效，请在「更多 → 登录」中重新登录。"
                )
            self.save_session()

        if code == 403:
            raise JwxtError(
                f"打开教务应用入口被拒绝 HTTP 403：{app_index}。"
                "可能未完成应用鉴权，请在「更多 → 登录」中重新登录后重试。"
            )
        if host != IEDU_HOST:
            raise NetworkError(
                f"无法打开教务应用入口（最终落在 {host or '未知主机'}）。"
                "请确认校园网/VPN 可访问 iedu.jlu.edu.cn。"
            )
        # 再轻量请求一次门户，部分部署会在此写入通用 Cookie
        try:
            self._request(
                IEDU_PORTAL,
                headers={"Referer": app_index, "Accept": "text/html,*/*"},
            )
        except NetworkError:
            pass
        self._dbg(step="emap_enter_done", app_index=app_index, **self.session_cookie_summary())

    def _post_form(self, path: str, fields: dict, referer: str) -> dict:
        url = IEDU_BASE + path
        data = urllib.parse.urlencode(fields).encode("utf-8") if fields else b""
        code, text, final, _ = self._request(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": referer,
                "Origin": IEDU_BASE,
            },
        )
        self._dbg(
            step="emap_post",
            path=path,
            status=code,
            final_url=_redact_url(final),
            **self.session_cookie_summary(),
        )
        if code == 403:
            raise JwxtError(
                f"{path} HTTP 403：通常是未先进入应用入口（缺少 _WEU 等）。"
                "请在「更多 → 登录」中重新登录后重试。"
            )
        if looks_like_login_redirect(final, text if code != 200 or not text.lstrip().startswith("{") else ""):
            if self.try_cas_refresh():
                return self._post_form(path, fields, referer)
            mark_session_expired(path)
            raise SessionExpiredError()
        if code != 200:
            raise JwxtError(f"{path} HTTP {code}")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            if "loginForm" in text or "/tpass/login" in text or "二次认证" in text:
                if self.try_cas_refresh():
                    return self._post_form(path, fields, referer)
                mark_session_expired(path)
                raise SessionExpiredError() from e
            raise JwxtError(f"{path} 返回非 JSON") from e

    def current_semester(self) -> Optional[str]:
        self.enter_emap_app(REF_SCHEDULE)
        data = self._post_form(EP_CURRENT_SEM, {}, REF_SCHEDULE)
        rows = (data.get("datas", {}).get("dqxnxq", {}) or {}).get("rows") or []
        if not rows:
            return None
        return rows[0].get("DM")

    def fetch_schedule(self, xnxqdm: Optional[str] = None) -> list[core.Course]:
        if not xnxqdm:
            xnxqdm = self.current_semester()
        else:
            self.enter_emap_app(REF_SCHEDULE)
        if not xnxqdm:
            raise JwxtError("无法取得当前学期代码")
        data = self._post_form(EP_COURSES, {"XNXQDM": xnxqdm}, REF_SCHEDULE)
        rows = (data.get("datas", {}).get("cxxszhxqkb", {}) or {}).get("rows") or []
        return [c for c in (row_to_course(r) for r in rows) if c is not None]

    def fetch_grades(self) -> list[core.Grade]:
        self.enter_emap_app(REF_GRADES)
        query = json.dumps(
            [
                {
                    "name": "SFYX",
                    "caption": "是否有效",
                    "linkOpt": "AND",
                    "builderList": "cbl_m_List",
                    "builder": "m_value_equal",
                    "value": "1",
                    "value_display": "是",
                },
                {
                    "name": "SHOWMAXCJ",
                    "caption": "显示最高成绩",
                    "linkOpt": "AND",
                    "builderList": "cbl_m_List",
                    "builder": "m_value_equal",
                    "value": "0",
                    "value_display": "否",
                },
            ],
            ensure_ascii=False,
        )
        data = self._post_form(
            EP_GRADES,
            {
                "querySetting": query,
                "*order": "-XNXQDM,-KCH,-KXH",
                "pageSize": "1000",
                "pageNumber": "1",
            },
            REF_GRADES,
        )
        rows = (data.get("datas", {}).get("xscjcx", {}) or {}).get("rows") or []
        if not rows:
            data = self._post_form(
                EP_GRADES,
                {
                    "querySetting": "[]",
                    "*order": "-XNXQDM,-KCH,-KXH",
                    "pageSize": "1000",
                    "pageNumber": "1",
                },
                REF_GRADES,
            )
            rows = (data.get("datas", {}).get("xscjcx", {}) or {}).get("rows") or []
        return [g for g in (row_to_grade(r) for r in rows) if g is not None]


    def post_raw(self, path: str, fields: dict, referer: str) -> tuple[int, str, str]:
        """只读查询用：不抛 HTTP 状态异常，返回 (status, text, final_url)。"""
        data = urllib.parse.urlencode(fields).encode("utf-8") if fields else b""
        code, text, final, _ = self._request(
            IEDU_BASE + path,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": referer,
                "Origin": IEDU_BASE,
            },
        )
        self._dbg(step="emap_post_raw", path=path, status=code, final_url=_redact_url(final))
        if looks_like_login_redirect(final, "" if text.lstrip().startswith("{") else text):
            mark_session_expired(path)  # 只记状态，不改变本函数「不抛异常」的约定
        return code, text, final

    def fetch_exams(self, xnxqdm: Optional[str] = None) -> list:
        """我的考试安排（只读）。先 cxxsksap.do（ysu-sdk 同款），再试 wdksap.do。"""
        from . import exams as _ex

        if not xnxqdm:
            xnxqdm = self.current_semester()
        self.enter_emap_app(REF_EXAMS)
        attempts = [
            (
                EP_EXAMS_ALT,
                {"requestParamStr": json.dumps({"XNXQDM": xnxqdm or "", "*order": "-KSRQ,-KSSJMS"})},
                "cxxsksap",
            ),
            (EP_EXAMS, {"XNXQDM": xnxqdm or "", "*order": "-KSRQ,-KSSJMS"}, "wdksap"),
        ]
        last_err = "无响应"
        for path, fields, key in attempts:
            code, text, _ = self.post_raw(path, fields, REF_EXAMS)
            if code != 200:
                last_err = f"{path} HTTP {code}"
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                last_err = f"{path} 返回非 JSON"
                continue
            block = (data.get("datas") or {}).get(key) or {}
            rows = block.get("rows") if isinstance(block, dict) else None
            if rows is None:
                last_err = f"{path} 缺少 datas.{key}.rows"
                continue
            return [e for e in (_ex.row_to_exam(r, _emap_str) for r in rows) if e]
        raise JwxtError(f"考试安排获取失败：{last_err}（可运行 jlu-toolkit explore 帮助定位）")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _emap_str(value) -> str:
    """EMAP JSON 字段可能是 str / int / float / None；统一成去空白字符串。

    整数值浮点（如 92.0、3.0）格式化为无小数点形式（'92'、'3'），
    保留真正的小数与等级制文字（'优秀'、'及格'）。
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        if value == int(value):
            return str(int(value))
        # 去掉多余尾零：3.50 -> 3.5
        text = f"{value:.10g}"
        return text
    text = str(value).strip()
    # 偶发 "92.0" 字符串也规整
    if text.endswith(".0") and text[:-2].lstrip("-").isdigit():
        return text[:-2]
    return text


def row_to_course(row: dict) -> Optional[core.Course]:
    name = _emap_str(row.get("KCM"))
    if not name:
        return None
    try:
        weekday = int(row.get("SKXQ"))
        start = int(row.get("KSJC"))
        end = int(row.get("JSJC"))
    except (TypeError, ValueError):
        return None
    weeks = parse_weeks_skzc(_emap_str(row.get("SKZC")))
    if not weeks or weekday < 1:
        return None
    loc = _emap_str(row.get("JASMC")) or "待定"
    return core.Course(
        name=name,
        teacher=clean_teacher(_emap_str(row.get("SKJS"))),
        location=loc,
        weekday=weekday,
        start=start,
        end=end,
        weeks=weeks,
    )


def row_to_grade(row: dict) -> Optional[core.Grade]:
    name = _emap_str(row.get("KCM"))
    if not name:
        return None
    try:
        credit = float(row.get("XF"))
    except (TypeError, ValueError):
        return None
    if credit <= 0:
        return None
    score = (
        _emap_str(row.get("ZCJ"))
        or _emap_str(row.get("XSZCJMC"))
        or _emap_str(row.get("DJCJMC"))
    )
    if not score:
        return None
    return core.Grade(
        name=name,
        credit=credit,
        score=score,
        term=_emap_str(row.get("XNXQDM")),
        jw_point=_first_float(row, GRADE_POINT_FIELDS),
        nature=next((_emap_str(row.get(k)) for k in ("KCXZDM_DISPLAY", "KCXZMC", "KCXZ_DISPLAY", "KCXZ")
                     if _emap_str(row.get(k))), ""),
    )


# 金智 xscjcx 常见的单科绩点字段名（吉大待 explore 确认）
GRADE_POINT_FIELDS = ("XFJD", "JD", "CJJD", "KCJD")


def _first_float(row: dict, keys) -> Optional[float]:
    for k in keys:
        v = _emap_str(row.get(k))
        if v:
            try:
                return float(v)
            except ValueError:
                continue
    return None


def export_courses_csv(courses: Iterable[core.Course], path: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["课程", "教师", "地点", "星期", "开始节", "结束节", "周次"]
        )
        w.writeheader()
        for c in courses:
            w.writerow(
                {
                    "课程": c.name,
                    "教师": c.teacher,
                    "地点": c.location,
                    "星期": c.weekday,
                    "开始节": c.start,
                    "结束节": c.end,
                    "周次": _weeks_to_csv(c.weeks),
                }
            )


def export_grades_csv(grades: Iterable[core.Grade], path: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["课程", "学分", "成绩", "学期", "教务绩点", "课程性质"])
        w.writeheader()
        for g in grades:
            jp = getattr(g, "jw_point", None)
            w.writerow(
                {"课程": g.name, "学分": g.credit, "成绩": g.score, "学期": g.term,
                 "教务绩点": "" if jp is None else jp, "课程性质": g.nature}
            )


def _weeks_to_csv(weeks: list[int]) -> str:
    if not weeks:
        return ""
    weeks = sorted(weeks)
    parts = []
    start = prev = weeks[0]
    for w in weeks[1:]:
        if w == prev + 1:
            prev = w
            continue
        parts.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = w
    parts.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(parts)


def probe_reachability(timeout: float = 12.0) -> dict:
    out = {}
    client = JwxtClient(timeout=timeout)
    try:
        html, lt, execution, post_url = client.fetch_login_page()
        out["cas"] = {
            "ok": True,
            "lt_prefix": lt[:16] + "...",
            "execution": execution,
            "form_action": post_url,
            "has_login_form": 'id="loginForm"' in html,
        }
    except Exception as e:  # noqa: BLE001
        out["cas"] = {"ok": False, "error": type(e).__name__ + ": " + str(e)}
    try:
        path = captcha_save_path("jlu_cas_captcha_probe.jpg")
        saved = client.download_captcha(path)
        info = {}
        if client.last_captcha_bytes:
            try:
                fmt, w, h = captcha_util.validate_captcha_bytes(
                    client.last_captcha_bytes, client.last_content_type
                )
                info = {"format": fmt, "width": w, "height": h}
            except captcha_util.CaptchaImageError as e:
                info = {"validate_error": str(e)}
        out["captcha"] = {
            "ok": True,
            "path": str(saved),
            "paths": [str(p) for p in client.last_captcha_paths],
            "bytes": saved.stat().st_size,
            "content_type": client.last_content_type,
            "url": CAS_CODE,
            **info,
        }
    except Exception as e:  # noqa: BLE001
        out["captcha"] = {"ok": False, "error": type(e).__name__ + ": " + str(e)}
    try:
        # 无密码会话时应返回 get_session_error
        result = client.request_wechat_code("0000")
        out["recheckcode"] = {
            "ok": True,
            "url": CAS_RECHECKCODE,
            "without_session": result.value,
            "note": "无密码会话时预期 get_session_error",
        }
    except Exception as e:  # noqa: BLE001
        out["recheckcode"] = {"ok": False, "error": type(e).__name__ + ": " + str(e)}
    try:
        code, text, final, _ = client._request(IEDU_PORTAL)
        out["iedu"] = {
            "ok": code == 200,
            "http": code,
            "final_host": urllib.parse.urlparse(final).hostname,
            "bytes": len(text),
        }
    except Exception as e:  # noqa: BLE001
        out["iedu"] = {"ok": False, "error": type(e).__name__ + ": " + str(e)}
    return out
