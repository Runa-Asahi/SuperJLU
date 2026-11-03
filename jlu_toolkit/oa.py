"""吉大 OA（oa.jlu.edu.cn，万户 ezOFFICE）校内通知 —— 只读。

已知（公开资料 + 开源项目 Reachee / JLU.OA.AnnounceBot / OAWebScraping）：
  列表  GET /defaultroot/PortalInformation!jldxList.action?channelId=179577&startPage=N
        条目 <a class="font14" href="PortalInformation!getInformation.action?id=..&channelId=..">标题</a>
        同行 <a> 第二个为发布单位，<span> 为时间（「2026年10月15日 09:30」）；置顶带 <font>
  详情  GET /defaultroot/PortalInformation!getInformation.action?id=<id>&channelId=<ch>
        .content_t 标题 / .content_time 时间+单位 / .content_font 正文
  搜索  &searchnr=<文本>&searchlx=<类型>（旧客户端用 searchlx=3 按日期 yyyyMMdd）
  访问  OA 原站可经校园网或学校 VPN 访问；应用内选「校外 WebVPN」时同步走 WebVPN 路由，浏览器会话不会传入程序。

本模块绝不提交任何表单（审批/办理等），只发 GET。--probe 只输出计数与字段名。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from . import jwxt

HOST = "https://oa.jlu.edu.cn"
BASE = HOST + "/defaultroot"
LOGIN = BASE + "/login.jsp?access=oa"
LIST = BASE + "/PortalInformation!jldxList.action"
DETAIL = BASE + "/PortalInformation!getInformation.action"
DEFAULT_CHANNEL = "179577"  # 校内通知
KNOWN_CHANNELS = {"179577": "校内通知"}
# UI / 全局刷新：多翻几页，避免置顶占满首页时普通通知长期不更新。每页大约十余条，5 页约 75 条，上限 100。
REFRESH_LIMIT = 100
REFRESH_MAX_PAGES = 5
_WRITE = re.compile(r"(save|submit|update|delete|del|approve|audit|deal|send|add|modify)", re.I)


def _assert_read_only(url: str) -> None:
    path = urllib.parse.urlparse(url).path
    if _WRITE.search(path.rsplit("/", 1)[-1]) and "getInformation" not in path and "List" not in path:
        raise ValueError(f"refused non read-only OA url: {path}")


def _decode(raw: bytes, text: str) -> str:
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:2048] or b"", re.I)
    cs = (m.group(1).decode("ascii", "ignore").lower() if m else "") or "utf-8"
    if cs in ("utf-8", "utf8"):
        return text
    try:
        return raw.decode("gb18030" if cs in ("gbk", "gb2312", "gb18030") else cs, errors="replace")
    except LookupError:
        return text


def get(client, url: str) -> tuple[int, str, str]:
    """只读 GET → (status, html, final_url)。"""
    _assert_read_only(url)
    code, text, final, raw = client._request(url, headers={"Referer": BASE + "/"})
    return code, _decode(raw or b"", text or ""), final or url


def needs_login(final_url: str, html: str) -> bool:
    u = urllib.parse.urlparse(final_url)
    low = (html or "")[:20000].lower()
    if jwxt.looks_like_login_redirect(final_url, html):
        return True
    if "login.jsp" in (u.path or "") or "authserver" in (u.hostname or "") + (u.path or ""):
        return True
    return 'type="password"' in low and "font14" not in low


# ───────────────────────── HTML 解析（标准库） ─────────────────────────

class _ListParser(HTMLParser):
    """收集列表行：每个 a.font14 为一条；随后的 a（单位）与 span（时间）归属同一条。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[dict] = []
        self.channels: dict[str, str] = {}
        self.pages: set[int] = set()
        self._cur: Optional[dict] = None
        self._in: Optional[str] = None
        self._chan: Optional[str] = None
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get("href") or ""
        if tag == "a":
            m = re.search(r"channelId=(\d+)", href)
            if "jldxList" in href and m:
                self._chan, self._buf = m.group(1), ""
            pm = re.search(r"startPage=(\d+)", href)
            if pm:
                self.pages.add(int(pm.group(1)))
            if "font14" in (a.get("class") or "") and "getInformation" in href:
                idm = re.search(r"[?&]id=(\d+)", href)
                self._cur = {"id": idm.group(1) if idm else "", "href": href, "title": "", "dept": "",
                             "time": "", "top": False, "channel": m.group(1) if m else ""}
                self.items.append(self._cur)
                self._in = "title"
            elif self._cur is not None and self._in is None and not self._cur["dept"]:
                self._in = "dept"
        elif tag == "span" and self._cur is not None and not self._cur["time"]:
            self._in = "time"

    def handle_endtag(self, tag):
        if tag == "a" and self._chan:
            name = re.sub(r"\s+", "", self._buf)
            if name and len(name) <= 20:
                self.channels.setdefault(self._chan, name)
            self._chan = None
        if tag in ("a", "span") and self._in:
            self._in = None

    def handle_data(self, data):
        if self._chan:
            self._buf += data
        if self._in and self._cur is not None:
            k = self._in
            self._cur[k] = (self._cur[k] + data) if k != "top" else self._cur[k]


def parse_list(html: str, now: Optional[dt.datetime] = None) -> dict:
    p = _ListParser()
    p.feed(html or "")
    items = []
    for it in p.items:
        t = re.sub(r"\s+", " ", it["title"]).strip()
        # 置顶只认标题里的「[置顶]」字样；OA 也会用 <font> 标红「新」等，不能据此当置顶。
        it["top"] = bool(re.match(r"^\[?置顶\]?", t))
        t = re.sub(r"^\[?置顶\]?\s*", "", t)
        items.append({"id": it["id"], "title": t, "dept": it["dept"].strip(), "time": parse_time(it["time"], now),
                      "top": it["top"], "channel": it["channel"],
                      "url": urllib.parse.urljoin(BASE + "/", it["href"])})
    total_pages = None
    m = re.search(r"共\s*(\d+)\s*页", html or "")
    if m:
        total_pages = int(m.group(1))
    elif p.pages:
        total_pages = max(p.pages)
    return {"items": items, "channels": p.channels, "total_pages": total_pages}


_CN = dt.timezone(dt.timedelta(hours=8))  # 学校 OA 显示的是北京时间
_REL_DAYS = {"今天": 0, "昨天": 1, "前天": 2}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _now_cn(now: Optional[dt.datetime] = None) -> dt.datetime:
    if now is None:
        return dt.datetime.now(_CN)
    return now.astimezone(_CN) if now.tzinfo else now


def parse_time(s: str, now: Optional[dt.datetime] = None) -> str:
    """统一成「YYYY-MM-DD[ HH:MM]」。OA 对近两天的通知显示「今天 09:09」「昨天 15:52」，
    按 now（取列表的时间，北京时间）换算；无年份的「10-30」按 now 补年份（不晚于 now）。
    无法识别时原样返回（is_dated() 为 False，排序时排在有日期的条目后面）。"""
    s = re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()
    m = re.search(r"(\d{4})\D(\d{1,2})\D(\d{1,2})\D*(?:(\d{1,2}):(\d{2}))?", s)
    if m:
        y, mo, d, h, mi = m.groups()
        out = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        return out + (f" {int(h):02d}:{mi}" if h else "")
    base = _now_cn(now)
    m = re.match(r"^(今天|昨天|前天)\s*(?:(\d{1,2}):(\d{2}))?", s)
    if m:
        day = base.date() - dt.timedelta(days=_REL_DAYS[m.group(1)])
        out = day.isoformat()
        return out + (f" {int(m.group(2)):02d}:{m.group(3)}" if m.group(2) else "")
    m = re.match(r"^(\d{1,2})[-/月](\d{1,2})日?\s*(?:(\d{1,2}):(\d{2}))?$", s)
    if m:
        mo, d, h, mi = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        try:
            day = dt.date(base.year, mo, d)
            if day > base.date():
                day = dt.date(base.year - 1, mo, d)
        except ValueError:
            return s
        return day.isoformat() + (f" {int(h):02d}:{mi}" if h else "")
    return s


def is_dated(s) -> bool:
    return bool(_DATE_RE.match(str(s or "")))


def _parse_iso(s) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(str(s)) if s else None
    except ValueError:
        return None


def normalize_cached(items: list, fetched_at=None) -> list:
    """修正旧缓存里原样存下的时间（#161）。
    新代码在取列表时就换算「今天/昨天」，缓存里残留的相对时间只可能来自旧版本；旧版本每次刷新都会改写
    更新时间，而早已翻出第 1 页的条目保留着当初的「今天 09:00」，用栏目更新时间去换算会把它算成最近一天，
    又排回最上面。所以相对时间一律当作未知（清空，排在有日期的条目之后）；只有不依赖「今天」的
    无年份「MM-DD」才按 fetched_at 补年份。"""
    ref = _parse_iso(fetched_at)
    out = []
    for i in items or []:
        if isinstance(i, dict) and i.get("time") and not is_dated(i["time"]):
            raw = re.sub(r"\s+", " ", str(i["time"]).replace("\xa0", " ")).strip()
            if raw[:2] in _REL_DAYS:
                i = {**i, "time": ""}
            elif ref is not None:
                fixed = parse_time(raw, ref)
                i = {**i, "time": fixed if is_dated(fixed) else ""}
            else:
                i = {**i, "time": ""}
        out.append(i)
    return out


def parse_detail(html: str) -> dict:
    """详情页：标题、时间单位、清洗后的正文 HTML/纯文本、附件。"""
    from . import article

    def cls(name):
        m = re.search(rf'class="[^"]*\b{name}\b[^"]*"[^>]*>(.*?)</(?:div|h\d|p|span)>', html or "", re.S)
        return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    a = article.extract(html, BASE + "/", [article.by_class("content_font")] + article.BODY_MATCHERS)
    atts = a["attachments"] + [x for x in article.attachments(html, BASE + "/")
                               if x["url"] not in {y["url"] for y in a["attachments"]}]
    return {"title": cls("content_t"), "time_dept": cls("content_time"),
            "html": a["html"], "text": a["text"], "attachments": atts}


# ───────────────────────── 访问 ─────────────────────────

def list_url(channel: str = DEFAULT_CHANNEL, page: int = 1, keyword: str = "", enc: str = "utf-8",
             field: str = "searchId") -> str:
    q = {"channelId": channel, "startPage": str(page)}
    if keyword:
        q[field] = keyword
    return LIST + "?" + urllib.parse.urlencode(q, encoding=enc)


# 搜索变体：(名称, 方法, 字段, 编码, 是否带 channelId)。门户搜索表单只有 searchId 一个输入。
SEARCH_VARIANTS = [
    ("get_searchId_utf8_ch", "GET", "searchId", "utf-8", True),
    ("get_searchId_gbk_ch", "GET", "searchId", "gbk", True),
    ("get_searchId_utf8", "GET", "searchId", "utf-8", False),
    ("get_searchId_gbk", "GET", "searchId", "gbk", False),
    ("post_searchId_utf8", "POST", "searchId", "utf-8", False),
    ("post_searchId_gbk", "POST", "searchId", "gbk", False),
    ("post_searchId_utf8_ch", "POST", "searchId", "utf-8", True),
    ("get_searchnr_utf8_ch", "GET", "searchnr", "utf-8", True),
]
_search_pref: Optional[tuple] = None


def search_request(client, keyword: str, variant: tuple, page: int = 1) -> tuple[int, str, str]:
    """门户搜索（只读查询；POST 仅用于提交搜索框，与页面表单一致）。"""
    _, method, field, enc, with_ch = variant
    q = {field: keyword}
    if with_ch:
        q["channelId"] = DEFAULT_CHANNEL
    if page > 1:
        q["startPage"] = str(page)
    if method == "GET":
        return get(client, LIST + "?" + urllib.parse.urlencode(q, encoding=enc))
    body = urllib.parse.urlencode(q, encoding=enc).encode("ascii")
    code, text, final, raw = client._request(LIST, data=body, method="POST", headers={
        "Referer": LOGIN, "Content-Type": "application/x-www-form-urlencoded"})
    return code, _decode(raw or b"", text or ""), final or LIST


RARE_KEYWORD = "zzqx9"


def search_variants(client, keywords=("2025", "通知")) -> dict:
    """每个变体：行数、与未过滤第 1 页的 id 重叠数、标题含关键字数；rare 关键字应为 0 行。
    filters=true 表示服务端确实按关键字过滤。只输出计数。"""
    try:
        c0, h0, f0 = get(client, list_url())
        base = {i["id"] for i in parse_list(h0)["items"]}
    except jwxt.NetworkError:
        base = set()
    out = {}
    for v in SEARCH_VARIANTS:
        row = {}
        for k, kw in zip(("ascii", "cjk", "rare"), (*keywords, RARE_KEYWORD)):
            try:
                c, h, f = search_request(client, kw, v)
                if c != 200 or needs_login(f, h):
                    row[k] = {"rows": -c}
                    continue
                items = parse_list(h)["items"]
                row[k] = {"rows": len(items), "overlap": sum(1 for i in items if i["id"] in base),
                          "hits": sum(1 for i in items if kw in i["title"] or kw in i["dept"])}
            except jwxt.NetworkError:
                row[k] = {"rows": -1}
        asc, rare = row["ascii"], row["rare"]
        n = asc.get("rows", 0)
        row["filters"] = bool(rare.get("rows") == 0 and n > 0 and asc.get("hits", 0) >= 0.8 * n
                              and (asc.get("overlap", 0) < n or not base))
        out[v[0]] = row
    out["base_rows"] = len(base)
    return out


# PC 实测（2026-10）：GET/POST searchId UTF-8 且不带 channelId 时服务端按关键字检索（跨全部栏目，
# 可能命中正文）；带 channelId 时忽略关键字；GBK 中文返回 0。
DEFAULT_SEARCH = ("get_searchId_utf8", "GET", "searchId", "utf-8", False)


def pick_search(client) -> Optional[tuple]:
    """默认使用 DEFAULT_SEARCH；_search_pref 可被设为 () 以强制本地过滤。"""
    return DEFAULT_SEARCH if _search_pref is None else (_search_pref or None)


# ───────────────────────── 栏目发现 ─────────────────────────

_CH_LINK = re.compile(r"channelId=(\d+)[^<>]{0,300}?>\s*(?:<[^>]+>\s*)*([^<>\s][^<>]{0,30}?)\s*<", re.S)
_CH_JS = re.compile(r"channelId=(\d+)[\s\S]{0,200}?['\">]([\u4e00-\u9fff][\u4e00-\u9fff\w/（）()·]{1,20})")


def discover_channels(client) -> dict:
    """从登录页链接与 jldx_left.js / main.js 中提取 channelId→名称。"""
    found: dict = {}
    src_counts: dict = {}
    try:
        code, html, final, raw = client._request(LOGIN)
        html = _decode(raw or b"", html or "")
    except jwxt.NetworkError:
        return {"channels": {}, "sources": {"login": -1}}
    pages = [("login", html)]
    for s in re.findall(r'<script[^>]*src="([^"]+)"', html or "", re.I):
        name = s.rsplit("/", 1)[-1].split("?")[0]
        if name in ("jldx_left.js", "main.js") or "jldx" in name:
            try:
                c, t, f, r = client._request(urllib.parse.urljoin(final or LOGIN, s))
                pages.append((name, _decode(r or b"", t or "")))
            except jwxt.NetworkError:
                src_counts[name] = -1
    for name, text in pages:
        n0 = len(found)
        for rx in (_CH_LINK, _CH_JS):
            for cid, label in rx.findall(text or ""):
                label = label.strip()
                if label and not label.startswith(("http", "javascript")):
                    found.setdefault(cid, label)
        for cid in re.findall(r"channelId=(\d+)", text or ""):
            found.setdefault(cid, "")
        src_counts[name] = len(found) - n0
    return {"channels": found, "sources": src_counts}


def reach(client) -> dict:
    """尝试用已保存的 CAS 会话进入 OA：直接访问列表；被拦则走 CAS service 跳转一次。"""
    code, html, final = get(client, list_url())
    info = {"direct_status": code, "direct_login_needed": needs_login(final, html)}
    if info["direct_login_needed"]:
        cas = f"{jwxt.CAS_LOGIN}?service={urllib.parse.quote(LIST + '?channelId=' + DEFAULT_CHANNEL, safe='')}"
        try:
            c2, h2, f2, _ = client._request(cas)
            info.update({"cas_status": c2, "cas_final_host": urllib.parse.urlparse(f2 or "").hostname,
                         "cas_login_needed": needs_login(f2 or "", h2 or "")})
            code, html, final = get(client, list_url())
            info["after_cas_login_needed"] = needs_login(final, html)
        except jwxt.NetworkError as e:
            info["cas_error"] = type(e).__name__
    info["ok"] = not needs_login(final, html) and code == 200
    return info


def _select(items, keyword, variant, channel, channel_filter):
    if keyword and not variant:
        items = [i for i in items if keyword in i["title"] or keyword in i["dept"]]
    if channel_filter and variant:
        items = [i for i in items if not i["channel"] or i["channel"] == channel]
    return items


def fetch_notices(client, channel: str = DEFAULT_CHANNEL, keyword: str = "", limit: int = 30,
                  max_pages: int = 5, channel_filter: bool = False) -> dict:
    """keyword 走服务端搜索（跨栏目，可能匹配正文，不再按标题二次过滤）；
    channel_filter=True 时按条目链接中的 channelId 本地筛到指定栏目。"""
    items: list = []
    channels: dict = {}
    variant = pick_search(client) if keyword else None
    for page in range(1, max_pages + 1):
        if variant:
            code, html, final = search_request(client, keyword, variant, page)
        else:
            code, html, final = get(client, list_url(channel, page))
        if code != 200 or needs_login(final, html):
            if page == 1:
                raise jwxt.LoginError("OA 需要登录（会话无法复用）；运行 jlu-toolkit oa --probe 查看")
            break
        got = parse_list(html)
        channels.update(got["channels"])
        new = [i for i in got["items"] if i["id"] not in {x["id"] for x in items}]
        if not new:
            break
        items += new
        if len(_select(items, keyword, variant, channel, channel_filter)) >= limit:
            break
    items = _select(items, keyword, variant, channel, channel_filter)
    return {"search": "server" if variant else ("local" if keyword else "none"),
            "page1": not keyword and bool(items),
            "pages_scanned": page, "channel_filtered": bool(channel_filter and variant), "channel": channel, "channel_name": channels.get(channel) or KNOWN_CHANNELS.get(channel, ""),
            "fetched_at": dt.datetime.now().isoformat(timespec="seconds"), "count": min(len(items), limit),
            "items": items[:limit], "channels": channels}


def resolve_category(cat: str, known: dict) -> str:
    if not cat:
        return DEFAULT_CHANNEL
    if cat.isdigit():
        return cat
    for cid, name in {**KNOWN_CHANNELS, **known}.items():
        if cat in name:
            return cid
    raise ValueError(f"未知分类：{cat}（先运行 jlu-toolkit oa --probe 发现栏目）")


def sort_key(i: dict) -> tuple:
    """先有日期的（按日期），再无法识别日期的；同时间按数字 id（字符串比较会让 1000000 排在 999999 后面）。"""
    sid = str(i.get("id") or "")
    t = str(i.get("time") or "")
    dated = is_dated(t)
    return (dated, t if dated else "", int(sid) if sid.isdigit() else -1, sid)


def save(root: Path, res: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    f = root / "oa_notices.json"
    old = {}
    if f.exists():
        try:
            old = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            old = {}
    store = old.get("channels_items") or {}
    ch_ref = (old.get("channels_updated") or {}).get(str(res["channel"])) or old.get("updated")
    prev = {i["id"]: i for i in normalize_cached(store.get(res["channel"], []), ch_ref)}
    if res.get("page1"):
        # 置顶条目都在第 1 页；本次没出现在置顶里的旧条目说明已取消置顶，不能一直挂在最上面。
        pinned = {i["id"] for i in res["items"] if i.get("top")}
        for k, v in prev.items():
            if v.get("top") and k not in pinned:
                prev[k] = {**v, "top": False}
    for i in res["items"]:
        prev[i["id"]] = {**prev.get(i["id"], {}), **i}
    store[res["channel"]] = sorted(prev.values(), key=sort_key, reverse=True)[:500]
    verified = dict(old.get("pins_verified") or {})
    if res.get("page1"):
        verified[str(res["channel"])] = True
    ch_updated = dict(old.get("channels_updated") or {})
    if res.get("fetched_at"):
        ch_updated[str(res["channel"])] = res["fetched_at"]
    out = {"updated": res.get("fetched_at") or old.get("updated"),
           "channels_updated": ch_updated,
           "pins_verified": verified,
           "channels": {**old.get("channels", {}), **res.get("channels", {})},
           "channels_items": store}
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def pins_verified(data: dict, channel: str) -> bool:
    """置顶标记是否由新版本读第 1 页时写入；旧版本缓存里的置顶可能早已取消，不可信。"""
    v = (data or {}).get("pins_verified") if isinstance(data, dict) else None
    return isinstance(v, dict) and bool(v.get(str(channel)))


def cached_items(data: dict, channel: str) -> list:
    """读缓存给界面/MCP 用：修正旧时间、未确认的置顶不当置顶，按置顶→日期排序。"""
    data = data if isinstance(data, dict) else {}
    raw = [i for i in normalize_cached((data.get("channels_items") or {}).get(str(channel)) or [],
                                       channel_fetched_at(data, channel)) if isinstance(i, dict)]
    if not pins_verified(data, channel):
        raw = [{**i, "top": False} for i in raw]
    return sorted(raw, key=lambda i: (bool(i.get("top")), *sort_key(i)), reverse=True)


def channel_fetched_at(data: dict, channel: str) -> Optional[str]:
    """当前栏目自己的刷新时间；旧缓存没有分栏目字段时回退到顶层 updated。"""
    data = data if isinstance(data, dict) else {}
    ch_updated = data.get("channels_updated") or {}
    if isinstance(ch_updated, dict):
        v = ch_updated.get(str(channel))
        if v:
            return str(v)
    v = data.get("updated")
    return str(v) if v else None


def fetch_detail(client, item: dict) -> dict:
    """按列表项的详情链接拉取正文与附件（只读 GET）。"""
    url = str((item or {}).get("url") or "")
    if not url:
        cid = str((item or {}).get("id") or "")
        ch = str((item or {}).get("channel") or DEFAULT_CHANNEL)
        if not cid:
            raise ValueError("缺少通知链接")
        url = f"{DETAIL}?id={urllib.parse.quote(cid)}&channelId={urllib.parse.quote(ch)}"
    code, html, final = get(client, url)
    if code != 200 or needs_login(final, html):
        raise jwxt.LoginError("OA 需要登录后才能查看通知正文")
    d = parse_detail(html)
    return {"title": d["title"], "time_dept": d["time_dept"], "text": d["text"], "html": d["html"],
            "attachments": d["attachments"]}


def merge_detail(root: Path, notice_id: str, detail: dict) -> Optional[dict]:
    """把正文/附件写回本地缓存中对应通知，返回更新后的条目。"""
    root = Path(root)
    f = root / "oa_notices.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None
    store = data.get("channels_items") or {}
    nid = str(notice_id)
    for ch, items in store.items():
        if not isinstance(items, list):
            continue
        for idx, it in enumerate(items):
            if not isinstance(it, dict) or str(it.get("id")) != nid:
                continue
            updated = dict(it)
            if detail.get("text"):
                updated["text"] = detail["text"]
            if detail.get("html"):
                updated["html"] = detail["html"]
            atts = detail.get("attachments")
            if isinstance(atts, list):
                updated["attachments"] = atts
            if detail.get("title") and not updated.get("title"):
                updated["title"] = detail["title"]
            items[idx] = updated
            store[ch] = items
            data["channels_items"] = store
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return updated
    return None


# ───────────────────────── 探测（只输出计数/字段名） ─────────────────────────

def _login_page_info(client) -> dict:
    try:
        code, html, final, _ = client._request(LOGIN)
    except jwxt.NetworkError as e:
        return {"error": type(e).__name__}
    low = (html or "").lower()
    forms = re.findall(r"<form[^>]*>", html or "", re.I)
    actions = [urllib.parse.urlparse(urllib.parse.urljoin(final, a)).path
               for a in re.findall(r'<form[^>]*action="([^"]*)"', html or "", re.I)]
    inputs = sorted(set(re.findall(r'<input[^>]*name="([\w.\-]+)"', html or "", re.I)))
    scripts = re.findall(r'<script[^>]*src="([^"]+)"', html or "", re.I)
    return {"status": code, "final_host": urllib.parse.urlparse(final or "").hostname,
            "final_path": urllib.parse.urlparse(final or "").path, "forms": len(forms), "form_actions": actions[:5],
            "input_names": inputs[:30], "scripts": len(scripts),
            "script_names": [s.rsplit("/", 1)[-1].split("?")[0] for s in scripts][:20],
            "mentions": {k: k in low for k in ("cas.jlu.edu.cn", "tpass", "authserver", "vpns", "sso",
                                                  "ids", "captcha", "verifycode", "encrypt", "des", "rsa")}}


def probe(client, anon_client=None) -> dict:
    rep: dict = {"login_page": _login_page_info(anon_client or client)}
    if anon_client is not None:
        try:
            code, html, final = get(anon_client, list_url())
            got = parse_list(html)
            rep["anonymous_list"] = {"status": code, "login_needed": needs_login(final, html),
                                     "rows": len(got["items"]), "final_path": urllib.parse.urlparse(final).path}
        except jwxt.NetworkError as e:
            rep["anonymous_list"] = {"error": type(e).__name__}
    try:
        rep["session_reuse"] = reach(client)
    except jwxt.NetworkError as e:
        rep["session_reuse"] = {"error": type(e).__name__}
        return rep
    code, html, final = get(client, list_url())
    got = parse_list(html)
    items = got["items"]
    rep["list"] = {"endpoint": "PortalInformation!jldxList.action", "status": code,
                   "login_needed": needs_login(final, html), "rows": len(items),
                   "fields_filled": {k: sum(1 for i in items if i[k]) for k in ("id", "title", "dept", "time", "url")},
                   "top_rows": sum(1 for i in items if i["top"]), "total_pages": got["total_pages"],
                   "categories": len(got["channels"]),
                   "category_ids": sorted(got["channels"])[:30]}
    if items:
        code2, html2, final2 = get(client, list_url(DEFAULT_CHANNEL, 2))
        rep["paging"] = {"param": "startPage", "page2_status": code2, "page2_rows": len(parse_list(html2)["items"]),
                         "page2_distinct": len({i["id"] for i in parse_list(html2)["items"]} - {i["id"] for i in items})}
        code3, html3, _ = get(client, items[0]["url"])
        d = parse_detail(html3)
        rep["detail"] = {"endpoint": "PortalInformation!getInformation.action", "pattern": "id=<id>&channelId=<ch>",
                         "status": code3, "has_title": bool(d["title"]), "has_time_dept": bool(d["time_dept"]),
                         "text_chars": len(d["text"]), "attachments": len(d["attachments"])}
        rep["search_variants"] = search_variants(client)
    disc = discover_channels(anon_client or client)
    allch = {**disc["channels"], **got["channels"]}
    rep["channel_discovery"] = {"sources": disc["sources"], "total": len(allch), "ids": sorted(allch)[:40],
                                "named": sum(1 for v in allch.values() if v)}
    got["channels"] = allch
    if got["channels"]:
        cnt = {}
        for cid in sorted(got["channels"])[:12]:
            c5, h5, f5 = get(client, list_url(cid))
            cnt[cid] = {"status": c5, "rows": len(parse_list(h5)["items"]), "login_needed": needs_login(f5, h5)}
        rep["category_lists"] = cnt
    return rep
