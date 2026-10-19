"""`jlu-toolkit explore`：只读探测吉大金智 EMAP 各应用接口，输出**脱敏**报告。

报告只含：HTTP 状态、最终路径、JSON 顶层键、datas 子块名、行数、字段名。
不含任何字段值（姓名、学号、成绩等一律不写）。

只发起查询类请求（GET 应用入口 / POST *cx*.do 查询）；
**绝不**调用选课、退课、重算、报名、评教提交等写接口。

候选端点来源：JFyuhong/JLU_schedule（wdkb）、Youwenqwq/ysu-sdk（金智 EMAP 通用 API 表）、
XJTU/BIT 公开脚本（studentWdksapApp）。吉大实际部署可能不同，这正是探测的目的。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import jwxt

APP = "https://iedu.jlu.edu.cn/jwapp/sys/{}/*default/index.do"

# 写接口关键字黑名单：探测前硬性检查，防止误加
FORBIDDEN = (
    "xk/", "xsxkapp/sys/xsxkapp/elective", "tk.do", "bysc.do", "xgksrwxs",
    "commit", "calculate", "save", "delete", "submit", "add", "update",
)


@dataclass
class Probe:
    label: str
    app: str  # 应用名（拼 *default/index.do）
    path: Optional[str] = None  # 为空则只 GET 入口
    form: Callable[..., dict] = field(default=lambda term, ctx=None: {})
    needs: tuple = ()  # 需要的上下文键（如 XH），缺失则跳过


def _term_parts(term: str) -> tuple[str, str]:
    # "2025-2026-1" → XN="2025-2026", XQ="1"
    if term and term.count("-") == 2:
        a, b, c = term.split("-")
        return f"{a}-{b}", c
    return "", ""


PROBES: list[Probe] = [
    # 学期 / 校历
    Probe("当前学期(wdkb)", "wdkb", "/jwapp/sys/wdkb/modules/jshkcb/dqxnxq.do"),
    Probe("当前学期(考试应用)", "studentWdksapApp", "/jwapp/sys/studentWdksapApp/modules/wdksap/dqxnxq.do"),
    Probe("学期校历", "wdkb", "/jwapp/sys/wdkb/modules/xskcb/cxxljc.do",
          lambda t, c=None: dict(zip(("XN", "XQ"), _term_parts(t)))),
    Probe("当前周次", "wdkb", "/jwapp/sys/wdkb/modules/jshkcb/dqzc.do",
          lambda t, c=None: dict(zip(("XN", "XQ"), _term_parts(t)), RQ=dt.date.today().isoformat())),
    Probe("节次时间", "wdkb", "/jwapp/sys/wdkb/modules/jshkcb/jc.do", lambda t, c=None: {"XNXQDM": t}),
    Probe("学期列表(jwpubapp)", "wdkb", "/jwapp/sys/jwpubapp/modules/bb/cxjwggbbdqxnxq.do"),
    # 考试
    Probe("考试安排 cxxsksap", "studentWdksapApp",
          "/jwapp/sys/studentWdksapApp/WdksapController/cxxsksap.do",
          lambda t, c=None: {"requestParamStr": json.dumps({"XNXQDM": t, "*order": "-KSRQ,-KSSJMS"})}),
    Probe("考试安排 wdksap", "studentWdksapApp",
          "/jwapp/sys/studentWdksapApp/modules/wdksap/wdksap.do",
          lambda t, c=None: {"XNXQDM": t, "*order": "-KSRQ,-KSSJMS"}),
    # 成绩扩展
    Probe("学分绩点统计(无学号)", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/cxzxfaxfjd.do"),
    # 空教室 / 教室
    Probe("教室列表(kcbcx)", "kcbcx", "/jwapp/sys/kcbcx/modules/jskcb/jscx.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("教室列表(kcbcxby)", "kcbcxby", "/jwapp/sys/kcbcxby/modules/jskcb/jscx.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("空教室入口(kxjas)", "kxjas"),
    Probe("空教室入口(kxjscx)", "kxjscx"),
    # 培养方案 / 学业
    Probe("个人培养方案", "xsfacx", "/jwapp/sys/xsfacx/modules/pyfacxepg/grpyfacx.do"),
    Probe("学业完成情况", "xywccx", "/jwapp/sys/xywccx/modules/xywccx/cxxsscfa.do",
          lambda t, c=None: {"SCLBDM": "04", "*order": "-CZSJ"}),
    Probe("学业预警", "xyyj", "/jwapp/sys/xyyj/modules/xsxyyjjg/cxxsyjpcjg.do"),
    # v2：需要学号/方案代码的接口（值只在内存中使用，不写入报告）
    Probe("学分绩点统计(XH1..6)", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/cxzxfaxfjd.do",
          lambda t, c=None: {f"XH{i}": c["XH"] for i in range(1, 7)}, needs=("XH",)),
    Probe("学业完成课组明细", "xywccx", "/jwapp/sys/xywccx/modules/xywccx/cxscfakz.do",
          lambda t, c=None: {"XH": c["XH"], "PYFADM": c["PYFADM"], "BYNJDM": c.get("BYNJDM") or "-",
                             "SCLBDM": c.get("SCLBDM") or "04"}, needs=("XH", "PYFADM")),
    Probe("培养方案课程列表", "xsfacx", "/jwapp/sys/jwpubapp/modules/pyfa/kzkccx.do",
          lambda t, c=None: {"PYFADM": c["PYFADM"], "pageSize": "5", "pageNumber": "1"}, needs=("PYFADM",)),
    # v2：空教室候选（只读查询；真实路径以 discover 结果为准）
    Probe("空教室 kxjscx/cxkxjs", "kxjscx", "/jwapp/sys/kxjscx/modules/kxjscx/cxkxjs.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("空教室 kxjscx/kxjscx", "kxjscx", "/jwapp/sys/kxjscx/modules/kxjscx/kxjscx.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("空教室 kxjscx/jscx", "kxjscx", "/jwapp/sys/kxjscx/modules/kxjscx/jscx.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("空教室 kxjas/kxjascx", "kxjas", "/jwapp/sys/kxjas/modules/kxjas/kxjascx.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("空教室 kxjas/cxkxjas", "kxjas", "/jwapp/sys/kxjas/modules/kxjas/cxkxjas.do",
          lambda t, c=None: {"XNXQDM": t, "pageSize": "5", "pageNumber": "1"}),
    Probe("代码表 校区", "kxjscx", "/jwapp/code/83a986fc-e677-400e-99a4-c7bb39c2ca35.do"),
    Probe("代码表 教学楼", "kxjscx", "/jwapp/code/82101c45-a7d3-414d-988b-24744db9f5ea.do"),
    # v3：成绩行字段（找教务单科绩点字段名）与绩点候选
    Probe("成绩行字段(1行)", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/xscjcx.do",
          lambda t, c=None: {"pageSize": "1", "pageNumber": "1"}),
    Probe("绩点候选 cxzxfaxfjd(XH)", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/cxzxfaxfjd.do",
          lambda t, c=None: {"XH": c["XH"]}, needs=("XH",)),
    Probe("绩点候选 cxxsjdtj", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/cxxsjdtj.do",
          lambda t, c=None: {"XH": c["XH"]}, needs=("XH",)),
    Probe("绩点候选 cxpjxfjd", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/cxpjxfjd.do",
          lambda t, c=None: {"XH": c["XH"]}, needs=("XH",)),
    Probe("绩点候选 xspjxfjd", "cjcx", "/jwapp/sys/cjcx/modules/cjcx/xspjxfjd.do",
          lambda t, c=None: {"XH": c["XH"]}, needs=("XH",)),
    # 个人信息
    Probe("学生基本信息", "xsjbxxgl", "/jwapp/sys/xsjbxxgl/modules/xsjbxx/cxxsjbxxlb.do"),
    # 选课结果（只看入口，不碰选课接口）
    Probe("选课应用入口(xsxkapp)", "xsxkapp"),
    Probe("选课结果入口(xkjgcx)", "xkjgcx"),
    # 课表变动（只读）
    Probe("个人调课课程 xsdkkc", "wdkb", "/jwapp/sys/wdkb/modules/xskcb/xsdkkc.do",
          lambda t, c=None: {"XNXQDM": t, "*order": "-SQSJ"}),
    Probe("调课记录", "wdkb", "/jwapp/sys/wdkb/modules/jshkcb/cxztdkjl.do", lambda t, c=None: {"XNXQDM": t}),
    Probe("未排课程", "wdkb", "/jwapp/sys/wdkb/modules/xskcb/xswpkc.do", lambda t, c=None: {"XNXQDM": t}),
]


def _assert_read_only(path: str) -> None:
    low = path.lower()
    for bad in FORBIDDEN:
        if bad in low:
            raise ValueError(f"拒绝探测疑似写接口：{path}")


def summarize_json(obj) -> dict:
    """只保留结构信息，不保留任何值。"""
    out: dict = {"type": type(obj).__name__}
    if not isinstance(obj, dict):
        if isinstance(obj, list):
            out["len"] = len(obj)
        return out
    out["keys"] = sorted(obj.keys())
    if "code" in obj and isinstance(obj["code"], (str, int)) and len(str(obj["code"])) <= 6:
        out["code"] = str(obj["code"])
    if isinstance(obj.get("msg"), str) and "datas" not in obj:
        # 服务端错误文案（非个人数据）；截断并抹去长数字串以防回显学号
        out["msg"] = re.sub(r"\d{5,}", "#", obj["msg"])[:60]
    datas = obj.get("datas")
    if isinstance(datas, dict):
        blocks = {}
        for name, blk in datas.items():
            b: dict = {"type": type(blk).__name__}
            if isinstance(blk, dict):
                rows = blk.get("rows")
                if isinstance(rows, list):
                    b["rows"] = len(rows)
                    fields = set()
                    for r in rows[:20]:
                        if isinstance(r, dict):
                            fields.update(r.keys())
                    b["fields"] = sorted(fields)
                if isinstance(blk.get("totalSize"), int):
                    b["totalSize"] = blk["totalSize"]
                ext = blk.get("extParams")
                if isinstance(ext, dict) and "code" in ext:
                    b["extCode"] = str(ext["code"])[:6]
                b["keys"] = sorted(k for k in blk.keys() if k != "rows")
            elif isinstance(blk, list):
                b["len"] = len(blk)
            blocks[name] = b
        out["datas"] = blocks
    return out


def _path_only(url: str) -> str:
    u = urllib.parse.urlparse(url or "")
    return f"{u.hostname or ''}{u.path}"


def run_explore(client: "jwxt.JwxtClient", term: Optional[str] = None,
                log: Callable[[str], None] = print) -> dict:
    report: dict = {
        "tool": "jlu-toolkit explore",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "note": "脱敏：仅状态码/路径/键名/行数/字段名，不含任何值",
        "term_detected": None,
        "apps": {},
        "probes": [],
    }
    if not term:
        try:
            term = client.current_semester()
        except Exception as e:  # noqa: BLE001
            log(f"无法取得当前学期：{type(e).__name__}")
    # 学期代码不是个人信息，可报告格式
    report["term_detected"] = term
    term = term or ""

    ctx: dict = {}  # 学号/方案代码等：只在内存中，绝不写入报告
    entered: set[str] = set()
    for pr in PROBES:
        entry = APP.format(pr.app)
        if pr.app not in entered:
            entered.add(pr.app)
            try:
                code, html, final, _ = client._request(
                    entry, headers={"Referer": jwxt.IEDU_PORTAL})
                report["apps"][pr.app] = {
                    "status": code,
                    "final": _path_only(final),
                    "bytes": len(html or ""),
                    "bounced_to_cas": "cas.jlu.edu.cn" in (final or ""),
                }
            except Exception as e:  # noqa: BLE001
                report["apps"][pr.app] = {"error": type(e).__name__}
            log(f"[入口] {pr.app}: {report['apps'][pr.app]}")
        if not pr.path:
            continue
        _assert_read_only(pr.path)
        item: dict = {"label": pr.label, "path": pr.path}
        missing = [k for k in pr.needs if not ctx.get(k)]
        if missing:
            item["skipped"] = "缺少上下文：" + ",".join(missing)
            report["probes"].append(item)
            log(f"[跳过] {pr.label}: {item['skipped']}")
            continue
        try:
            code, text, final = client.post_raw(pr.path, pr.form(term, ctx), entry)
            item["status"] = code
            item["final"] = _path_only(final)
            try:
                parsed = json.loads(text)
                _capture_ctx(parsed, ctx)
                item["json"] = summarize_json(parsed)
            except (json.JSONDecodeError, ValueError):
                item["non_json_bytes"] = len(text or "")
                item["looks_like_login"] = "loginForm" in (text or "")
        except Exception as e:  # noqa: BLE001
            item["error"] = type(e).__name__
        report["probes"].append(item)
        rows = ""
        for name, b in (item.get("json", {}).get("datas") or {}).items():
            if "rows" in b:
                rows += f" {name}={b['rows']}行"
        log(f"[查询] {pr.label}: HTTP {item.get('status', item.get('error'))}{rows}")
    report["context_found"] = sorted(ctx.keys())  # 只列键名
    try:
        from . import rooms, ui as _ui
        rp = rooms.probe(client, _ui.Store(_ui.data_dir()).first_monday(), term, None, None, (1, 2), log=log)
        report["rooms_probe"] = {k: rp.get(k) for k in ("entered", "week", "weekday", "meta", "campus_count",
                                                         "campus_source", "hit")}
        report["rooms_probe"]["tries"] = [{k: t.get(k) for k in ("endpoint", "scheme", "param_names", "status",
                                                                 "code", "msg", "rows", "fields")}
                                          for t in rp["tries"]]
    except Exception as e:  # noqa: BLE001
        report["rooms_probe"] = {"error": type(e).__name__}
    report["discover"] = {app: discover_app(client, app) for app in DISCOVER_APPS}
    for app, d in report["discover"].items():
        log(f"[发现] {app}: {len(d.get('do_paths', []))} 个 .do 路径")
    return report


CTX_KEYS = ("XH", "PYFADM", "BYNJDM", "SCLBDM")


def _capture_ctx(parsed, ctx: dict) -> None:
    for blk in ((parsed or {}).get("datas") or {}).values() if isinstance(parsed, dict) else ():
        rows = blk.get("rows") if isinstance(blk, dict) else None
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            for k in CTX_KEYS:
                v = rows[0].get(k)
                if v not in (None, "") and k not in ctx:
                    ctx[k] = str(v)


DISCOVER_APPS = ("kxjscx", "kxjas", "cjcx", "wdkb")
_DO_RE = re.compile(r"""["'(]([\w./*-]*?\.do)\b""")
_SRC_RE = re.compile(r"""(?:src|href)\s*=\s*["']([^"'#?]+\.(?:js|json))""", re.I)


def extract_do_paths(text: str) -> list[str]:
    """从应用前端代码中提取 *.do 路径（代码，不是个人数据）。"""
    found = {m.group(1) for m in _DO_RE.finditer(text or "")}
    return sorted(p for p in found if len(p) < 160)


def discover_app(client, app: str, max_files: int = 12) -> dict:
    """只读：GET 应用入口 HTML 及其同应用 JS/JSON，提取接口路径。"""
    base = f"https://iedu.jlu.edu.cn/jwapp/sys/{app}/"
    out: dict = {"files": 0, "do_paths": []}
    try:
        code, html, final, _ = client._request(APP.format(app), headers={"Referer": jwxt.IEDU_PORTAL})
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}
    paths = set(extract_do_paths(html))
    out["html_bytes"] = len(html or "")
    all_src = [urllib.parse.urlparse(urllib.parse.urljoin(final or base, s)).path
               for s in _SRC_RE.findall(html or "")]
    out["script_srcs"] = all_src[:40]  # 静态资源路径（代码，非个人数据）
    srcs = []
    for s in _SRC_RE.findall(html or ""):
        url = urllib.parse.urljoin(final or base, s)
        if (f"/jwapp/sys/{app}/" in url or f"/{app}" in url) and url not in srcs:
            srcs.append(url)
    # EMAP 页面配置（含模块/动作名）
    for cfg in (f"https://iedu.jlu.edu.cn/jwapp/sys/emappagelog/config/{app}.do",
                f"https://iedu.jlu.edu.cn/jwapp/sys/{app}/config/app.json"):
        try:
            c, txt, _, _ = client._request(cfg, headers={"Referer": APP.format(app)})
            if c == 200 and txt:
                out.setdefault("config_ok", []).append(urllib.parse.urlparse(cfg).path)
                paths.update(extract_do_paths(txt))
                try:
                    cj = json.loads(txt)
                    out.setdefault("config_keys", {})[urllib.parse.urlparse(cfg).path] = (
                        sorted(cj.keys())[:40] if isinstance(cj, dict) else type(cj).__name__)
                except (json.JSONDecodeError, ValueError):
                    pass
        except Exception:  # noqa: BLE001
            pass
    # EMAP 约定的配置/路由文件
    for extra in ("config.json", "public/js/routes.js", "routes.js", "index.js", "pages/index.js"):
        u = base + extra
        if u not in srcs:
            srcs.append(u)
    files_ok = []
    for u in srcs[:max_files]:
        try:
            c, txt, _, _ = client._request(u, headers={"Referer": APP.format(app)})
        except Exception:  # noqa: BLE001
            continue
        if c == 200 and txt:
            files_ok.append(urllib.parse.urlparse(u).path)
            paths.update(extract_do_paths(txt))
            # 次级：同应用 JS 里引用的其他 js（一层）
            for s in re.findall(r"""["']([\w./-]+\.js)["']""", txt)[:20]:
                v = urllib.parse.urljoin(u, s)
                if f"/jwapp/sys/{app}/" in v and v not in srcs and len(srcs) < max_files * 2:
                    srcs.append(v)
    # 尝试 EMAP 模块元数据（*.do 不带动作名），只提取其中的 .do 字符串
    for mp in sorted(p for p in paths if re.search(r"modules/[\w]+\.do$", p))[:6]:
        full = mp if mp.startswith("/") else f"/jwapp/sys/{app}/" + mp.lstrip("./")
        try:
            c, txt, _ = client.post_raw(full, {}, APP.format(app))
            if c == 200:
                paths.update(extract_do_paths(txt))
                out.setdefault("meta_ok", []).append(full)
        except Exception:  # noqa: BLE001
            pass
    out["files"] = len(files_ok)
    out["file_paths"] = files_ok
    out["do_paths"] = sorted(paths)
    return out


def default_report_path() -> Path:
    dl = Path.home() / "storage" / "downloads"
    if dl.is_dir() and os.access(dl, os.W_OK):
        return dl / "jlu_explore_report.json"
    return Path.cwd() / "jlu_explore_report.json"


def write_report(report: dict, path: Optional[Path] = None) -> Path:
    path = path or default_report_path()
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return path
