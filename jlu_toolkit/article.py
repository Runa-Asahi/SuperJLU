"""通知正文提取与清洗（OA 与学院官网共用）。

学校/学院页面多是 Word 粘贴来的 HTML：满屏内联样式、字体、&nbsp; 缩进、空段落。
这里只保留阅读需要的结构（段落、换行、加粗、列表、表格、链接、图片），其余标签去掉、保留文字；
链接/图片只允许 http(s) 并补全为绝对地址；图片和附件仅限吉大域名或原文所在站点。输出可直接放进页面。
"""
from __future__ import annotations

import html as _html
import re
import urllib.parse
from html.parser import HTMLParser
from typing import Callable, Optional

_KEEP = {"p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li", "table", "thead", "tbody",
         "tr", "td", "th", "a", "img", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "sub", "sup"}
_DROP = {"script", "style", "noscript", "iframe", "object", "embed", "form", "input", "button",
         "select", "textarea", "svg", "video", "audio", "head", "title", "meta", "link"}
_VOID = {"br", "img", "hr", "input", "meta", "link", "col", "area", "source", "wbr"}
_BLOCK = {"div", "section", "article", "center", "dl", "dt", "dd", "hr"}
_HEAD_MAP = {"h1": "h3", "h2": "h3", "h3": "h4", "h4": "h4", "h5": "h4", "h6": "h4"}


def _abs(url: str, base: str) -> str:
    u = urllib.parse.urljoin(base or "", _html.unescape((url or "").strip()))
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https") or not p.hostname or p.username:
        return ""
    return u


def _trusted(u: str, base: str = "") -> bool:
    """吉大域名，或与原文同一站点（附属医院官网不在 jlu.edu.cn 下）。"""
    h = (urllib.parse.urlparse(u).hostname or "").lower()
    own = (urllib.parse.urlparse(base or "").hostname or "").lower()
    return h == "jlu.edu.cn" or h.endswith(".jlu.edu.cn") or (bool(own) and h == own)


class _Clean(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base, self.out, self.stack, self.drop = base, [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in _DROP:
            if tag not in _VOID:
                self.drop += 1
            return
        if self.drop:
            return
        a = dict(attrs)
        if tag in _BLOCK:
            self.out.append("\n<br>")
            return
        if tag not in _KEEP:
            return
        tag = _HEAD_MAP.get(tag, tag)
        if tag == "b":
            tag = "strong"
        if tag == "i":
            tag = "em"
        if tag == "br":
            self.out.append("<br>")
            return
        if tag == "img":
            src = _abs(a.get("src") or "", self.base)
            if src and _trusted(src, self.base):
                alt = _html.escape(a.get("alt") or "", quote=True)
                self.out.append(f'<img src="{_html.escape(src, quote=True)}" alt="{alt}" loading="lazy">')
            return
        if tag == "a":
            href = _abs(a.get("href") or "", self.base)
            self.out.append(f'<a href="{_html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">'
                            if href else "<a>")
        elif tag in ("td", "th"):
            extra = "".join(f' {k}="{int(a[k])}"' for k in ("colspan", "rowspan")
                            if str(a.get(k) or "").isdigit() and 1 < int(a[k]) <= 50)
            self.out.append(f"<{tag}{extra}>")
        else:
            self.out.append(f"<{tag}>")
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in _DROP and tag not in _VOID:
            self.drop -= 1

    def handle_endtag(self, tag):
        if tag in _DROP:
            if tag not in _VOID and self.drop:
                self.drop -= 1
            return
        if self.drop:
            return
        if tag in _BLOCK:
            self.out.append("<br>\n")
            return
        tag = _HEAD_MAP.get(tag, {"b": "strong", "i": "em"}.get(tag, tag))
        if tag in self.stack:
            while self.stack:
                t = self.stack.pop()
                self.out.append(f"</{t}>")
                if t == tag:
                    break

    def handle_data(self, data):
        if not self.drop:
            self.out.append(_html.escape(data, quote=False))

    def result(self) -> str:
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")
        return "".join(self.out)


_EMPTY = re.compile(r"<(p|strong|em|u|li|h3|h4|blockquote|sub|sup|a)>(?:\s|&nbsp;|<br>)*</\1>")


def clean_html(fragment: str, base: str = "") -> str:
    """把正文 HTML 清洗成只含基础排版的安全片段。"""
    p = _Clean(base)
    p.feed((fragment or "").replace("\r", ""))
    p.close()
    s = p.result().replace("\xa0", " ").replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    for _ in range(3):
        s = _EMPTY.sub("", s)
    s = re.sub(r"(?:\s*<br>\s*){3,}", "<br><br>", s)
    s = re.sub(r"<p>\s*(?:<br>\s*)+", "<p>", s)
    s = re.sub(r"(?:<br>\s*)+</p>", "</p>", s)
    blocks = r"(?:p|ul|ol|li|table|tr|h3|h4|blockquote)"
    s = re.sub(rf"(<{blocks}>)\s+", r"\1", s)
    s = re.sub(rf"\s+(</{blocks}>)", r"\1", s)
    # 段落、表格之间不需要额外换行
    s = re.sub(rf"(</{blocks}>)\s*(?:<br>\s*)+", r"\1\n", s)
    s = re.sub(rf"(?:<br>\s*)+(<{blocks}>)", r"\n\1", s)
    s = re.sub(r"^(?:\s*<br>)+|(?:<br>\s*)+$", "", s.strip())
    return s.strip()


def html_to_text(fragment: str) -> str:
    s = re.sub(r"<br\s*/?>|</p>|</li>|</tr>|</h\d>", "\n", fragment or "", flags=re.I)
    s = re.sub(r"</t[dh]>", " ", s, flags=re.I)
    s = _html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ").replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", "\n".join(x.strip() for x in s.split("\n"))).strip()


class _Grab(HTMLParser):
    """取出第一个满足 match(tag, attrs) 的元素的内部 HTML（按嵌套深度配对）。"""

    def __init__(self, match: Callable[[str, dict], bool]):
        super().__init__(convert_charrefs=False)
        self.match, self.depth, self.buf, self.done, self.tag = match, 0, [], False, ""

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if self.depth:
            self.buf.append(self.get_starttag_text() or "")
            if tag == self.tag and tag not in _VOID:
                self.depth += 1
        elif self.match(tag, dict(attrs)):
            self.tag, self.depth = tag, 1

    def handle_startendtag(self, tag, attrs):
        if self.depth and not self.done:
            self.buf.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag):
        if not self.depth or self.done:
            return
        if tag == self.tag:
            self.depth -= 1
            if not self.depth:
                self.done = True
                return
        self.buf.append(f"</{tag}>")

    def handle_data(self, d):
        if self.depth and not self.done:
            self.buf.append(d)

    def handle_entityref(self, name):
        if self.depth and not self.done:
            self.buf.append(f"&{name};")

    def handle_charref(self, name):
        if self.depth and not self.done:
            self.buf.append(f"&#{name};")


def grab(html: str, match: Callable[[str, dict], bool]) -> Optional[str]:
    g = _Grab(match)
    try:
        g.feed(html or "")
    except Exception:  # noqa: BLE001 — 残缺页面
        pass
    return "".join(g.buf) if g.tag else None


def by_class(*names: str) -> Callable[[str, dict], bool]:
    return lambda tag, a: bool(set((a.get("class") or "").split()) & set(names))


def by_id(*ids: str) -> Callable[[str, dict], bool]:
    return lambda tag, a: (a.get("id") or "") in ids


# 常见站群/CMS 的正文容器（博达 v_news_content、OA content_font、eyoucms 等）
BODY_MATCHERS = [by_class("v_news_content"), by_id("vsb_content"), by_class("content_font"),
                 by_class("wp_articlecontent"), by_class("TRS_Editor"), by_class("article-content"),
                 by_class("article_content"), by_class("news_content"), by_class("newscontent"),
                 by_class("art-body"), by_class("content-con"), by_class("detail-content"),
                 by_class("contentText"), by_class("con"), by_class("article")]

_ATT = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I)
_FILE_EXT = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|txt|wps|et|jpg|png)(?:$|[?#])", re.I)


def attachments(html: str, base: str) -> list:
    out, seen = [], set()
    for href, inner in _ATT.findall(html or ""):
        h = _html.unescape(href)
        if not (re.search(r"download|attach|DownloadAttachUrl", h, re.I) or _FILE_EXT.search(h)):
            continue
        u = _abs(h, base)
        if not u or u in seen or not _trusted(u, base):
            continue
        seen.add(u)
        name = _html.unescape(re.sub(r"<[^>]+>", "", inner)).strip() or "附件"
        name = re.sub(r"^附件[【\[]|[】\]]$", "", name).strip() or "附件"
        out.append({"name": name, "url": u})
    return out


def extract(html: str, base: str, matchers=None) -> dict:
    """返回 {"html", "text", "attachments"}；没找到正文时 html/text 为空。"""
    frag = None
    for m in matchers or BODY_MATCHERS:
        frag = grab(html, m)
        if frag and (html_to_text(frag) or re.search(r"<img\b", frag, re.I)):  # 海报类通知只有图片
            break
        frag = None
    body = clean_html(frag, base) if frag else ""
    atts = attachments(frag or "", base)
    # 博达：附件列表在正文容器之后
    tail = (html or "")
    i = tail.find("div_vote_id")
    if i >= 0:
        atts += [a for a in attachments(tail[i:i + 20000], base) if a["url"] not in {x["url"] for x in atts}]
    return {"html": body, "text": html_to_text(body), "attachments": atts}
