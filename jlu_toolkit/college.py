"""学院新闻/通知（只读、免登录、只取列表第 1 页）。

多数学院官网是博达站群：列表页每条是 <li> 里的日期 + 指向 info/<栏目>/<id>.htm 的链接。
白求恩第三临床医学院是 div.li 列表；第二临床医学院是 content_<id>.html；
第一临床医学院是 eyoucms 的 View&aid=。这三种都走栏目列表，用法与软件学院、计算机学院相同。
学院站点直接访问；连接失败不推断为校园网限制，保留缓存并显示网络错误。

学院目录见 data/college_catalog.json。scrape=true 的栏目可抓取；没有栏目的学院仅作入口
（channel id = <college_id>-site），选中后提示打开官网。
用户偏好（已选信息源顺序）保存在本地 oa_source_prefs.json。
"""
from __future__ import annotations

import datetime as dt
import html as _html
import json
import re
import urllib.parse
from pathlib import Path
from typing import Optional

CACHE = "college_news.json"
PREFS = "oa_source_prefs.json"
TIMEOUT = 10
UA = "Mozilla/5.0 (SuperJLU read-only)"
CATALOG_PATH = Path(__file__).parent / "data" / "college_catalog.json"
OA_CAMPUS_ID = "179577"

# 内置兜底：catalog 读失败时仍能解析 csw/ccst（测试 fixture 依赖这些 id）
_FALLBACK_SOURCES = {
    "csw": {"name": "软件学院", "host": "csw.jlu.edu.cn", "cols": {
        "xytz": ("学院通知", "index/xytz_.htm"),
        "jbtz": ("教办通知", "index/jbtz.htm"),
        "xbtz": ("学办通知", "index/xbtz.htm"),
        "xsdt": ("学术动态", "index/xsdt.htm"),
    }},
    "ccst": {"name": "计算机学院", "host": "ccst.jlu.edu.cn", "cols": {
        "xytz": ("学院通知", "xwzx/xytz.htm"),
        "xyxw": ("学院新闻", "xwzx/xyxw.htm"),
        "jxtz": ("教学通知", "rcpy/bksjy/jxtz.htm"),
        "yjs": ("研究生通知", "rcpy/yjsjy/gltz.htm"),
    }},
}


def _load_catalog() -> dict:
    try:
        d = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _build_sources(catalog: Optional[dict] = None) -> dict:
    """从 catalog 生成 SOURCES 形态：{id: {name, host, cols:{cid:(name,path)}}}。"""
    cat = catalog if catalog is not None else _load_catalog()
    out = {}
    for group in cat.get("categories") or []:
        for col in group.get("colleges") or []:
            if not col.get("scrape") or not col.get("cols"):
                continue
            cid = str(col.get("id") or "")
            if not cid:
                continue
            cols = {}
            for k, v in (col.get("cols") or {}).items():
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    cols[str(k)] = (str(v[0]), str(v[1]))
            if cols:
                out[cid] = {
                    "name": str(col.get("name") or cid),
                    "host": str(col.get("host") or ""),
                    "cols": cols,
                    "parser": str(col.get("parser") or "boda"),
                }
    return out or dict(_FALLBACK_SOURCES)


SOURCES = _build_sources()


def reload_sources() -> dict:
    """测试或热更新：重新读 catalog。"""
    global SOURCES
    SOURCES = _build_sources()
    return SOURCES


def catalog() -> dict:
    """完整学院目录（含分类），供 UI 选学院。"""
    cat = _load_catalog()
    if not cat.get("categories"):
        # 兜底：至少给出可抓取的两所学院
        return {
            "version": 0,
            "oa_defaults": [{"id": OA_CAMPUS_ID, "name": "校内通知", "kind": "oa"}],
            "categories": [{
                "id": "cs",
                "name": "计算机、软件与信息科学",
                "colleges": [
                    {"id": k, "name": v["name"], "host": v["host"],
                     "home": f"https://{v['host']}/", "scrape": True,
                     "cols": {ck: list(cv) for ck, cv in v["cols"].items()}}
                    for k, v in SOURCES.items()
                ],
            }],
        }
    return cat


def colleges_flat() -> list:
    """扁平学院列表。"""
    out = []
    for g in catalog().get("categories") or []:
        for c in g.get("colleges") or []:
            if isinstance(c, dict) and c.get("id"):
                out.append({**c, "category": g.get("id"), "category_name": g.get("name")})
    return out


def college_by_id(cid: str) -> Optional[dict]:
    for c in colleges_flat():
        if c.get("id") == cid:
            return c
    return None


def channels() -> dict:
    """可抓取栏目：{"csw-xytz": "软件学院·学院通知", ...}。不含仅链接入口。"""
    return {f"{s}-{c}": f"{v['name']}·{n}" for s, v in SOURCES.items() for c, (n, _) in v["cols"].items()}


def link_channels() -> dict:
    """不可抓取学院的官网入口：{"sai-site": "人工智能学院（官网）", ...}。"""
    out = {}
    for c in colleges_flat():
        if c.get("scrape"):
            continue
        cid = str(c["id"])
        out[f"{cid}-site"] = f"{c.get('name') or cid}（官网）"
    return out


def all_source_channels() -> dict:
    """校内 OA 默认 + 可抓取学院栏目 + 仅链接学院入口。"""
    oa = {OA_CAMPUS_ID: "校内通知"}
    for x in (catalog().get("oa_defaults") or []):
        if isinstance(x, dict) and x.get("id"):
            oa[str(x["id"])] = str(x.get("name") or x["id"])
    return {**oa, **channels(), **link_channels()}


def is_channel(ch: str) -> bool:
    return str(ch or "") in channels()


def is_link_channel(ch: str) -> bool:
    return str(ch or "") in link_channels()


def is_source_id(ch: str) -> bool:
    return str(ch or "") in all_source_channels()


def _split(ch: str):
    s, c = ch.split("-", 1)
    return SOURCES[s], c


def list_url(ch: str) -> str:
    src, c = _split(ch)
    return f"https://{src['host']}/{str(src['cols'][c][1]).lstrip('/')}"


def link_home(ch: str) -> str:
    """仅链接频道 → 学院官网。"""
    if not is_link_channel(ch):
        return ""
    cid = ch.rsplit("-", 1)[0]
    col = college_by_id(cid)
    if not col:
        return ""
    home = str(col.get("home") or "")
    host = str(col.get("host") or "")
    if home.startswith("https://"):
        return home
    if host:
        return f"https://{host}/"
    return ""


def default_channels_for_college(college_id: str) -> list:
    """选中某学院时默认启用的频道 id 列表。"""
    if college_id in SOURCES:
        cols = SOURCES[college_id]["cols"]
        # 优先学院通知
        prefer = ["xytz", "tzgg", "tztg", "xxgg", "xwgg", "xyxw", "jxtz", "xwzx", "kx"]
        ordered = [f"{college_id}-{c}" for c in prefer if c in cols]
        ordered += [f"{college_id}-{c}" for c in cols if f"{college_id}-{c}" not in ordered]
        return ordered[:2]  # 默认只开两个，避免芯片栏过长
    if college_by_id(college_id):
        return [f"{college_id}-site"]
    return []


def safe_url(u, host: str, base: str = "") -> str:
    """补全为绝对地址，且只保留 https?://<host>/ 下的链接。"""
    u = str(u or "").strip()
    if not u:
        return ""
    full = urllib.parse.urljoin(base or f"https://{host}/", u)
    p = urllib.parse.urlparse(full)
    return full if p.scheme in ("http", "https") and p.hostname == host and not p.username else ""


_LI = re.compile(r"<li\b[^>]*>(.*?)</li>", re.S | re.I)
_DATE = re.compile(r"(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})")
_A = re.compile(r"<a\b([^>]*?)href=\"([^\"]*info/\d+/\d+\.htm)\"([^>]*)>(.*?)</a>", re.S | re.I)
_TITLE = re.compile(r"title=\"([^\"]*)\"", re.I)


_SKIP_TITLE = {"查看详情", "查看详情+", "更多", "更多+", "查看更多", "查看更多+", "more"}
_DIVLI = re.compile(
    r'<div class="li">\s*<a\b[^>]*href="([^"]+)"[^>]*>\s*<div class="p">(.*?)</div>\s*<div class="y">(.*?)</div>',
    re.S | re.I)
_CONTENT = re.compile(
    r'<a\b[^>]*href="([^"]*content_(\d+)\.html)"[^>]*>(.*?)</a>(?:\s*<span[^>]*>(.*?)</span>)?',
    re.S | re.I)
_EYOU = re.compile(
    r'<a\b[^>]*href="([^"]*?c=View[^"]*?aid=(\d+)[^"]*)"[^>]*>(.*?)</a>(?:\s*<span[^>]*>(.*?)</span>)?',
    re.S | re.I)


_NAMED_TITLE = re.compile(
    r"<(?:span|p|div|h3)\b[^>]*\bclass=\"[^\"]*\b(?:tit|title)\b[^\"]*\"[^>]*>(.*?)</(?:span|p|div|h3)>",
    re.S | re.I)
_H3 = re.compile(r"<h3\b[^>]*>(.*?)</h3>", re.S | re.I)
_LEAD_INDEX = re.compile(r"^\s*<strong>\s*\d{1,3}\s*</strong>", re.I)
_WIDGET_STRONG = re.compile(
    r"<strong>\s*(\d{1,2})\s*</strong>\s*(\d{4})[-/.](\d{1,2})", re.I)
_WIDGET_B = re.compile(
    r"<b>\s*(\d{1,2})\s*</b>\s*(?:<[^>]+>\s*)?\s*/?\s*(\d{4})[-/.](\d{1,2})", re.I)
_WIDGET_P = re.compile(
    r"<p>\s*(\d{1,2})\s*</p>\s*<p>\s*(\d{4})[-/.](\d{1,2})", re.I)


def _plain(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", _html.unescape(s or ""))).strip()


def _date_of(text: str) -> str:
    d = _DATE.search(text or "")
    return f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}" if d else ""


def _date_parts(day: str, year: str, month: str) -> str:
    d, y, m = int(day), int(year), int(month)
    if 1 <= d <= 31 and 1990 <= y <= 2100 and 1 <= m <= 12:
        return f"{y}-{m:02d}-{d:02d}"
    return ""


def _widget_date(html: str) -> str:
    """列表卡片把「日」和「年-月」拆开时，不从正文里猜日期。"""
    for rx in (_WIDGET_STRONG, _WIDGET_B, _WIDGET_P):
        m = rx.search(html or "")
        if not m:
            continue
        got = _date_parts(m.group(1), m.group(2), m.group(3))
        if got:
            return got
    return ""


def _inner_title(inner: str) -> str:
    """优先栏目标题节点；否则去掉行首序号。摘要留在标题外。"""
    named = _NAMED_TITLE.search(inner or "")
    if named:
        title = _plain(named.group(1))
        if title:
            return title
    h3 = _H3.search(inner or "")
    if h3:
        title = _plain(h3.group(1))
        if title:
            return title
    return _plain(_LEAD_INDEX.sub("", inner or "", count=1))


def _row(ch: str, dept: str, nid: str, title: str, date: str, url: str) -> dict:
    return {"id": f"{ch}:{nid}", "title": title, "time": date, "dept": dept,
            "top": False, "url": url, "channel": ch}


def _parse_boda(html: str, ch: str, src: dict, base: str, dept: str) -> list:
    out, seen = [], set()
    for blk in _LI.findall(html or ""):
        a = _A.search(blk)
        if not a:
            continue
        url = safe_url(a.group(2), src["host"], base)
        if not url or url in seen:
            continue
        t = _TITLE.search(a.group(1) + a.group(3))
        title = _html.unescape(t.group(1)).strip() if t else _inner_title(a.group(4))
        if not title or title in _SKIP_TITLE:
            continue
        outside = re.sub(r"<a\b.*?</a>", "", blk, flags=re.S)
        date = _date_of(outside) or _widget_date(a.group(4)) or _date_of(_plain(blk))
        m = re.search(r"info/(\d+)/(\d+)\.htm", url)
        seen.add(url)
        out.append(_row(ch, dept, f"{m.group(1)}-{m.group(2)}", title, date, url))
    return out


def _parse_divli(html: str, ch: str, src: dict, base: str, dept: str) -> list:
    """白求恩第三临床医学院：<div class="li"><a><div class="p">标题</div><div class="y">日期</div>."""
    out, seen = [], set()
    for href, title_html, date_html in _DIVLI.findall(html or ""):
        url = safe_url(href, src["host"], base)
        title = _plain(title_html)
        if not url or not title or url in seen:
            continue
        m = re.search(r"/(\d+)\.html", url)
        seen.add(url)
        out.append(_row(ch, dept, m.group(1) if m else str(len(out) + 1), title, _date_of(_plain(date_html)), url))
    return out


def _parse_content(html: str, ch: str, src: dict, col: str, base: str, dept: str) -> list:
    """白求恩第二临床医学院：只收当前栏目路径下的 content_<id>.html。"""
    prefix = "/" + str(src["cols"][col][1]).strip("/") + "/"
    out, seen = [], set()
    for href, cid, inner, date_html in _CONTENT.findall(html or ""):
        url = safe_url(_html.unescape(href), src["host"], base)
        if not url or url in seen:
            continue
        path = urllib.parse.urlparse(url).path
        if not path.startswith(prefix):
            continue
        title = _inner_title(inner)
        if len(title) < 4 or title in _SKIP_TITLE:
            continue
        seen.add(url)
        date = _date_of(_plain(date_html or "")) or _widget_date(inner) or _date_of(title)
        out.append(_row(ch, dept, cid, title, date, url))
    return out


def _parse_eyou(html: str, ch: str, src: dict, base: str, dept: str) -> list:
    """白求恩第一临床医学院：index.php?m=home&c=View&a=index&aid=。"""
    out, seen = [], set()
    for href, aid, inner, date_html in _EYOU.findall(html or ""):
        if aid in seen:
            continue
        url = safe_url(_html.unescape(href), src["host"], base)
        title = _plain(inner)
        if not url or len(title) < 4 or title in _SKIP_TITLE:
            continue
        seen.add(aid)
        out.append(_row(ch, dept, aid, title, _date_of(_plain(date_html or "")), url))
        if len(out) >= 30:
            break
    return out


def parse_list(html: str, ch: str) -> list:
    src, col = _split(ch)
    base = list_url(ch)
    dept = channels()[ch]
    kind = src.get("parser") or "boda"
    if kind == "divli":
        return _parse_divli(html, ch, src, base, dept)
    if kind == "content":
        return _parse_content(html, ch, src, col, base, dept)
    if kind == "eyou":
        return _parse_eyou(html, ch, src, base, dept)
    return _parse_boda(html, ch, src, base, dept)


def _get(url: str, timeout: int = TIMEOUT) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — 固定 https 主机
        raw = r.read(2_000_000)
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def fetch(ch: str, getter=None) -> dict:
    """只取第 1 页。网络失败返回 status=network_error，不影响学校 OA 或其它学院栏目。
    仅链接频道返回 status=link_only。"""
    now = dt.datetime.now().isoformat(timespec="seconds")
    if is_link_channel(ch):
        home = link_home(ch)
        return {"ok": True, "channel": ch, "status": "link_only", "fetched_at": now, "items": [],
                "hint": "该学院官网暂不支持自动抓取列表，请打开官网查看通知公告。",
                "source_url": home}
    try:
        html = (getter or _get)(list_url(ch))
    except Exception as e:  # noqa: BLE001 — do not erase the last successful list
        return {"ok": False, "channel": ch, "status": "network_error", "fetched_at": now, "items": [],
                "hint": f"暂时无法连接 {_split(ch)[0]['host']}，请检查网络后重试，已保留本地通知（{type(e).__name__}）"}
    items = parse_list(html, ch)
    st = "ok" if items else "empty"
    return {"ok": True, "channel": ch, "status": st, "fetched_at": now, "items": items,
            "hint": "" if items else "页面结构可能变了，没解析到条目"}


def load(root: Path) -> dict:
    try:
        d = json.loads((root / CACHE).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(root: Path, res: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    d = load(root)
    ch = res["channel"]
    d.setdefault("status", {})[ch] = {"status": res["status"], "hint": res.get("hint", ""), "at": res["fetched_at"]}
    if res.get("source_url"):
        d["status"][ch]["source_url"] = res["source_url"]
    if res["items"]:
        prev = {i["id"]: i for i in (d.get("channels_items") or {}).get(ch, [])}
        for i in res["items"]:
            prev[i["id"]] = i
        d.setdefault("channels_items", {})[ch] = sorted(prev.values(), key=lambda i: (i["time"], i["id"]), reverse=True)[:300]
        d["updated"] = res["fetched_at"]
    f = root / CACHE
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)
    return f


def fetch_detail(item: dict, getter=None) -> dict:
    """学院文章页：清洗后的正文与附件（公开页面，免登录）。没解析到正文时 html 为空。"""
    from . import article
    src, _ = _split(str(item.get("channel") or ""))
    url = safe_url(item.get("url"), src["host"])
    if not url:
        raise ValueError("缺少原文链接")
    return article.extract((getter or _get)(url), url)


def merge_detail(root: Path, nid: str, detail: dict) -> Optional[dict]:
    d = load(root)
    for ch, lst in (d.get("channels_items") or {}).items():
        for k, i in enumerate(lst or []):
            if isinstance(i, dict) and i.get("id") == nid:
                lst[k] = {**i, "html": detail.get("html") or "", "text": detail.get("text") or "",
                          "attachments": detail.get("attachments") or []}
                f = root / CACHE
                tmp = f.with_suffix(".tmp")
                tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                tmp.replace(f)
                return lst[k]
    return None


def find(root: Path, nid: str) -> Optional[dict]:
    for lst in (load(root).get("channels_items") or {}).values():
        for i in lst or []:
            if isinstance(i, dict) and i.get("id") == nid:
                return i
    return None


# ───────── 用户偏好（信息源芯片栏） ─────────

def default_prefs() -> dict:
    return {
        "onboarded": False,
        "home_college": "",
        "enabled": [OA_CAMPUS_ID],
        "order": [OA_CAMPUS_ID],
    }


def load_prefs(root: Path) -> dict:
    base = default_prefs()
    try:
        d = json.loads((root / PREFS).read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return base
    except (OSError, ValueError):
        return base
    known = all_source_channels()
    enabled = [str(x) for x in (d.get("enabled") or []) if str(x) in known]
    order = [str(x) for x in (d.get("order") or []) if str(x) in known]
    if not enabled:
        enabled = list(base["enabled"])
    # order 里补全 enabled，去掉未启用的
    for x in enabled:
        if x not in order:
            order.append(x)
    order = [x for x in order if x in enabled] or list(enabled)
    home = str(d.get("home_college") or "")
    if home and not college_by_id(home):
        home = ""
    return {
        "onboarded": bool(d.get("onboarded")),
        "home_college": home,
        "enabled": enabled,
        "order": order,
    }


def save_prefs(root: Path, upd: dict) -> dict:
    """合并写入偏好。upd 可含 onboarded / home_college / enabled / order。"""
    root.mkdir(parents=True, exist_ok=True)
    cur = load_prefs(root)
    known = all_source_channels()
    if "onboarded" in upd:
        cur["onboarded"] = bool(upd["onboarded"])
    if "home_college" in upd:
        home = str(upd.get("home_college") or "")
        cur["home_college"] = home if (not home or college_by_id(home)) else cur["home_college"]
    if "enabled" in upd and isinstance(upd["enabled"], list):
        cur["enabled"] = [str(x) for x in upd["enabled"] if str(x) in known]
        if OA_CAMPUS_ID not in cur["enabled"]:
            # 校内通知可关掉，但至少留一个源
            if not cur["enabled"]:
                cur["enabled"] = [OA_CAMPUS_ID]
    if "order" in upd and isinstance(upd["order"], list):
        order = [str(x) for x in upd["order"] if str(x) in known and str(x) in cur["enabled"]]
        for x in cur["enabled"]:
            if x not in order:
                order.append(x)
        cur["order"] = order or list(cur["enabled"])
    else:
        # 同步 order 与 enabled
        order = [x for x in cur["order"] if x in cur["enabled"]]
        for x in cur["enabled"]:
            if x not in order:
                order.append(x)
        cur["order"] = order
    out = {k: cur[k] for k in ("onboarded", "home_college", "enabled", "order")}
    f = root / PREFS
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)
    return out


def apply_home_college(root: Path, college_id: str) -> dict:
    """首次选学院：标记已引导，设 home，启用默认栏目。"""
    college_id = str(college_id or "").strip()
    if college_id and not college_by_id(college_id):
        raise ValueError("未知学院")
    prefs = load_prefs(root)
    enabled = [OA_CAMPUS_ID]
    order = [OA_CAMPUS_ID]
    if college_id:
        for ch in default_channels_for_college(college_id):
            if ch not in enabled:
                enabled.append(ch)
                order.append(ch)
    return save_prefs(root, {
        "onboarded": True,
        "home_college": college_id,
        "enabled": enabled,
        "order": order,
    })


def channels_for_prefs(root: Path, include_all_oa: bool = False) -> list:
    """按用户偏好返回 [{id,name,kind,scrape,home}]，供 /api/oa/channels。

    include_all_oa：未引导前仍返回全部可抓取栏目（兼容旧行为）；引导后只返回已启用。
    """
    prefs = load_prefs(root)
    names = all_source_channels()
    if not prefs["onboarded"] and include_all_oa:
        # 兼容：旧测试期望看到全部学院可抓取栏目
        items = []
        for k, v in names.items():
            kind = "oa" if k == OA_CAMPUS_ID or (k.isdigit()) else ("link" if is_link_channel(k) else "college")
            items.append({"id": k, "name": v, "kind": kind})
        return items
    out = []
    for k in prefs["order"]:
        if k not in names:
            continue
        kind = "oa" if k == OA_CAMPUS_ID or str(k).isdigit() else ("link" if is_link_channel(k) else "college")
        item = {"id": k, "name": names[k], "kind": kind}
        if kind == "link":
            item["home"] = link_home(k)
            item["scrape"] = False
        elif kind == "college":
            item["scrape"] = True
        out.append(item)
    return out or [{"id": OA_CAMPUS_ID, "name": "校内通知", "kind": "oa"}]
