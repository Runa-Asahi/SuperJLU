import argparse
import getpass
import json
import sys

from . import core
from . import exams as exmod
from . import jwxt


def _utf8_stdio() -> None:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None):
    try:
        _main(argv)
    except jwxt.SessionExpiredError as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(3)


def _cmd_status(x):
    if x.check:
        client = jwxt.JwxtClient()
        if client.load_session():
            try:
                client.session_alive()
            except jwxt.JwxtError:
                pass
    st = jwxt.session_status()
    if x.json:
        print(json.dumps(st, ensure_ascii=False))
    else:
        print(f"会话：{st['message']}（state={st['state']}，存储={st['storage']}）")
    if st["needs_login"]:
        sys.exit(3)


def _main(argv=None):
    _utf8_stdio()
    from . import __version__
    p = argparse.ArgumentParser(prog="jlu-toolkit", description="SuperJLU —— 吉大人的一站式服务（课表/成绩/教务/OA/校园服务）。命令 jlu-toolkit 与 superjlu 等价。")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    ss = sub.add_parser("sessions", help="各校园站点会话状态（不联网）；clear <site> 清除某站会话")
    ss.add_argument("action", nargs="?", default="list", choices=["list", "clear", "check", "keepalive"])
    ss.add_argument("site", nargs="?", default="")
    ss.add_argument("--json", action="store_true")
    camp = sub.add_parser("campus", help="校园站点探测（只读 GET；pay/xsxk/ilearn/vpn/lib）")
    camp.add_argument("--probe", action="store_true", help="匿名探测登录类型/重定向/候选只读接口（无个人数值）")
    camp.add_argument("--json", action="store_true", help="输出完整 JSON 报告")
    st = sub.add_parser("status", help="查看登录会话状态（默认不联网；--check 访问教务一次验证）")
    st.add_argument("--check", action="store_true", help="访问教务一次确认会话是否仍有效")
    st.add_argument("--json", action="store_true")

    a = sub.add_parser("ics", help="课表导出 iCal（与 App 同一份：教务 + 调停课 + 个人修改）")
    a.add_argument("csv", nargs="?", help="schedule.csv 路径；省略则读数据目录")
    a.add_argument("--first-monday", help="第一周周一 YYYY-MM-DD；省略则用校历/设置")
    a.add_argument("-o", default="schedule.ics")

    b = sub.add_parser("gpa", help="计算绩点；或 --probe 扫描教务官方绩点接口")
    b.add_argument("csv", nargs="?", help="成绩 CSV（本地计算时必填）")
    b.add_argument("--term")
    b.add_argument("--probe", action="store_true", help="扫描 cjcx 应用的绩点/统计接口，只打印结构")
    b.add_argument("-o", "--out", help="--probe 报告路径")
    b.add_argument("--debug", action="store_true")

    c = sub.add_parser("today", help="查看某周某天的课（与 App 同一份课表）")
    c.add_argument("csv", nargs="?", help="schedule.csv 路径；省略则读数据目录")
    c.add_argument("--week", type=int, required=True)
    c.add_argument("--weekday", type=int, required=True)

    f = sub.add_parser(
        "fetch",
        help="从教务系统拉取课表/成绩并导出 CSV（需校园网或 VPN；支持二次认证）",
    )
    f.add_argument(
        "--user",
        help="统一身份认证账号（邮箱前缀，不是学号）；省略则尝试本地已保存凭据或已保存会话",
    )
    f.add_argument(
        "--password",
        help="密码；强烈不建议在命令行传入（会出现在 shell 历史）。省略则交互输入",
    )
    f.add_argument(
        "--save-credentials",
        action="store_true",
        help="可选：保存账号密码（优先加密存入系统钥匙串；不可用时为 ~/.config/jlu-toolkit/credentials.json，chmod 600）",
    )
    f.add_argument(
        "--force-login",
        action="store_true",
        help="忽略已保存会话，强制重新登录（含二次认证）",
    )
    f.add_argument(
        "--schedule-out",
        default="schedule.csv",
        help="课表 CSV 输出路径（默认 schedule.csv）",
    )
    f.add_argument(
        "--grades-out",
        default="grades.csv",
        help="成绩 CSV 输出路径（默认 grades.csv）",
    )
    f.add_argument("--term", help="学期代码，如 2025-2026-2；默认当前学期")
    f.add_argument(
        "--exams-out",
        default="exams.csv",
        help="考试安排 CSV 输出路径（默认 exams.csv）",
    )
    f.add_argument(
        "--what",
        choices=("all", "schedule", "grades", "exams"),
        default="all",
        help="拉取内容（默认 all）",
    )
    f.add_argument(
        "--probe",
        action="store_true",
        help="只探测 CAS/验证码/教务是否可达，不登录",
    )
    f.add_argument(
        "--debug",
        action="store_true",
        help="打印登录诊断信息（字段名/长度、HTTP 状态、最终 URL、重定向链、服务器错误文案；不打印密码）",
    )
    f.add_argument(
        "--show-captcha",
        action="store_true",
        help="在终端用 ASCII 显示图形验证码（默认关闭；自动识别失败时仍会提示手动输入）",
    )
    f.add_argument(
        "--no-auto-captcha",
        action="store_true",
        help="禁用图形验证码自动识别，始终手动输入",
    )

    e = sub.add_parser("exams", help="查看考试倒计时（读取 exams.csv）")
    e.add_argument("csv", nargs="?", default="exams.csv")
    e.add_argument("--all", action="store_true", help="包含已结束的考试")

    ex_p = sub.add_parser(
        "explore",
        help="只读探测教务各应用接口，生成脱敏报告（需已保存会话；不做任何写操作）",
    )
    ex_p.add_argument("--term", help="学期代码；默认自动取当前学期")
    ex_p.add_argument("-o", "--out", help="报告路径（默认 Termux 下载目录或当前目录 jlu_explore_report.json）")
    ex_p.add_argument("--debug", action="store_true")

    sy = sub.add_parser(
        "sync",
        help="用已保存会话同步全部数据到本地数据目录（课表/成绩/考试/校历/节次/官方绩点/学业完成）；非交互",
    )
    sy.add_argument("--term", help="学期代码；默认当前学期")
    sy.add_argument("--data-dir", help="数据目录（默认 ~/.config/jlu-toolkit/data）")
    sy.add_argument("--debug", action="store_true")

    rm = sub.add_parser("rooms", help="查询空教室（需已保存会话；必须指定校区/日期/节次）")
    rm.add_argument("--campus", help="校区代码（先用 --list-campuses 查看）")
    rm.add_argument("--date", help="空闲日期 YYYY-MM-DD（默认今天）")
    rm.add_argument("--periods", default="1-2", help="空闲节次，如 3 或 3-4（默认 1-2）")
    rm.add_argument("--building", default="", help="教学楼代码（可选，--list-buildings 查看）")
    rm.add_argument("--type", dest="kind", default="", help="教室类型代码（--list-types 查看）")
    rm.add_argument("--seats", default="", help="上课座位数范围，如 100- / 50-120 / -80")
    rm.add_argument("--exam-seats", default="", help="考试座位数范围，同上")
    rm.add_argument("--weeks", default="", help="按周次查询：周次，如 6 / 6-8 / 6,8（与 --weekday 配合，忽略 --date）")
    rm.add_argument("--weekday", type=int, default=0, help="按周次查询：星期 1-7")
    rm.add_argument("--field", action="append", default=[], metavar="名=值",
                    help="其它检索字段（--list-fields 查看），可重复")
    rm.add_argument("--list-types", action="store_true", help="列出教室类型代码")
    rm.add_argument("--list-fields", action="store_true", help="列出元数据中的其它检索字段")
    rm.add_argument("--sort", default="", help="排序：name/building/seats/exam_seats，前缀 - 为降序")
    rm.add_argument("--list-campuses", action="store_true", help="列出校区代码")
    rm.add_argument("--list-buildings", action="store_true", help="列出教学楼代码（可配合 --campus）")
    rm.add_argument("--probe", action="store_true", help="只读探测接口/参数组合，只打印结构，不打印数据")
    rm.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    rm.add_argument("-o", "--out", help="--probe 报告路径（默认临时目录 jlu_rooms_probe.json）")
    rm.add_argument("--debug", action="store_true")

    pp = sub.add_parser("plan", help="培养方案课程明细（课程号/学分/学期/课组/修读状态）")
    pp.add_argument("--probe", action="store_true", help="只读探测：应用/模块/动作名、字段名+标题、行数（无数值）")
    pp.add_argument("--debug-known", action="store_true",
                    help="只读：打印各已知接口的参数名与响应行数/total（ASCII，无数值）")
    pp.add_argument("--refresh", action="store_true", help="从教务重新拉取（默认读本地 plan_courses.json）")
    pp.add_argument("--status", default="", help="只看某状态：已修/在修/未修/未通过")
    pp.add_argument("--term", default="", help="按建议修读学期筛选（包含匹配）")
    pp.add_argument("--nature", default="", help="按课程性质/类别筛选（包含匹配）")
    pp.add_argument("--json", action="store_true", help="ASCII JSON 输出")
    pp.add_argument("-o", "--out", help="--probe 报告路径")
    pp.add_argument("--debug", action="store_true")

    oa = sub.add_parser("oa", help="吉大 OA 校内通知（只读；需校园网/VPN）")
    oa.add_argument("action", nargs="?", default="notices", choices=["notices", "subscribe", "watch"],
                    help="notices：列出通知；subscribe：管理关键词订阅；watch：增量同步并提醒")
    oa.add_argument("sub_action", nargs="?", default="list", choices=["add", "list", "remove"],
                    help="subscribe 的子命令：add/list/remove")
    oa.add_argument("rule_id", nargs="?", default="", help="remove 时的规则 id")
    oa.add_argument("--keywords", "-k", default="", help="subscribe add：关键词，逗号分隔")
    oa.add_argument("--dept", default="", help="subscribe add：发文单位过滤，逗号分隔（可选）")
    oa.add_argument("--interval", type=int, default=30, help="watch 间隔分钟（默认 30，最小 10）")
    oa.add_argument("--once", action="store_true", help="watch 只运行一次")
    oa.add_argument("--probe", action="store_true", help="只读探测认证方式/列表/分页/详情（ASCII 计数，无标题）")
    oa.add_argument("--category", default="", help="栏目 channelId 或名称（默认 179577 校内通知）")
    oa.add_argument("--keyword", default="", help="标题/单位关键字（本地过滤）")
    oa.add_argument("--limit", type=int, default=30)
    oa.add_argument("--pages", type=int, default=5, help="最多翻页数")
    oa.add_argument("--json", action="store_true", help="ASCII JSON 输出")
    oa.add_argument("--debug", action="store_true")

    u = sub.add_parser("ui", help="启动本地网页界面（127.0.0.1，手机浏览器打开）")
    u.add_argument("--port", type=int, default=8765)
    u.add_argument("--demo", action="store_true", help="使用示例数据（不读写真实数据目录）")
    u.add_argument("--data-dir", help="自定义数据目录")
    u.add_argument("--open", action="store_true", help="启动后尝试打开浏览器")

    x = p.parse_args(argv)
    if x.cmd == "ics":
        from . import timetable, ui
        root = timetable.root_for_csv(x.csv) if x.csv else ui.data_dir()
        st = ui.Store(root)
        fm = x.first_monday or st.first_monday()
        if not fm:
            print("缺少开学日期：请加 --first-monday YYYY-MM-DD，或先同步校历", file=sys.stderr); sys.exit(2)
        cs = timetable.courses_from_csv(x.csv) if x.csv else timetable.courses(root)
        open(x.o, "w", encoding="utf-8").write(core.to_ics(cs, fm, st.periods() or None))
        print(f"已导出 {x.o}")
    elif x.cmd == "gpa":
        if x.probe:
            _cmd_gpa_probe(x)
        else:
            if not x.csv:
                from . import ui
                f = ui.data_dir() / "official_gpa.json"
                from . import secure_store
                d = secure_store.load_json(f)
                if d is None:
                    print("尚无官方绩点；先运行 jlu-toolkit sync，或提供成绩 CSV", file=sys.stderr); sys.exit(2)
                print(f"来源：{d.get('source')}  {d.get('endpoint') or ''}")
                for i in d.get("items", []):
                    print(f"  {i['label']}：{i['value']}")
                return
            print(json.dumps(core.gpa(core.load_grades(x.csv), x.term), ensure_ascii=False))
    elif x.cmd == "today":
        from . import timetable, ui
        cs = timetable.courses_from_csv(x.csv) if x.csv else timetable.courses(ui.data_dir())
        for k in core.courses_on(cs, x.week, x.weekday):
            print(f"第{k.start}-{k.end}节 {k.name} @ {k.location}")
    elif x.cmd == "sessions":
        _cmd_sessions(x)
    elif x.cmd == "campus":
        _cmd_campus(x)
    elif x.cmd == "status":
        _cmd_status(x)
    elif x.cmd == "fetch":
        _cmd_fetch(x)
    elif x.cmd == "exams":
        _cmd_exams(x)
    elif x.cmd == "explore":
        _cmd_explore(x)
    elif x.cmd == "ui":
        _cmd_ui(x)
    elif x.cmd == "plan":
        _cmd_plan(x)
    elif x.cmd == "sync":
        _cmd_sync(x)
    elif x.cmd == "oa":
        _cmd_oa(x)
    elif x.cmd == "rooms":
        _cmd_rooms(x)


def _prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except EOFError:
        print("\n已取消。", file=sys.stderr)
        sys.exit(130)


def _interactive_second_factor(client: jwxt.JwxtClient, show_captcha: bool = False, auto_captcha: bool = True) -> None:
    """图形验证码（默认自动识别）+ 微信验证码交互。"""
    from . import captcha_util
    from . import captcha_solver

    print(
        "需要二次认证：图形验证码默认自动识别；微信验证码请到「智慧吉大」查看。",
        file=sys.stderr,
    )
    if auto_captcha:
        try:
            captcha_solver.load_templates()
        except Exception as e:
            print(f"自动识别不可用（{e}），改为手动输入。", file=sys.stderr)
            auto_captcha = False

    max_auto_tries = 5
    auto_try = 0
    while True:
        path = client.download_captcha()
        raw = client.last_captcha_bytes or path.read_bytes()
        if show_captcha:
            print(captcha_util.render_ascii(raw), file=sys.stderr)
            for p in client.last_captcha_paths or [path]:
                try:
                    print(f"  已保存 {p} ({p.stat().st_size} bytes)", file=sys.stderr)
                except OSError:
                    pass

        captcha = None
        if auto_captcha and auto_try < max_auto_tries:
            auto_try += 1
            try:
                captcha = captcha_solver.solve_captcha(raw)
            except RuntimeError as e:
                print(f"自动识别需要 Pillow：{e}", file=sys.stderr)
                auto_captcha = False
                captcha = None
            if captcha:
                print(f"图形验证码自动识别：{captcha}（第 {auto_try}/{max_auto_tries} 次）", file=sys.stderr)
            else:
                print(f"自动识别失败（第 {auto_try}/{max_auto_tries} 次），刷新重试…", file=sys.stderr)
                continue

        if not captcha:
            captcha = _prompt("请输入图形验证码（直接回车刷新图片）：")
            if not captcha:
                continue

        result = client.request_wechat_code(captcha)
        if result == jwxt.WechatCodeResult.CAPTCHA_ERROR:
            print("图形验证码错误。", file=sys.stderr)
            if auto_captcha and auto_try < max_auto_tries:
                print("自动刷新并重试…", file=sys.stderr)
                continue
            print("请手动输入。", file=sys.stderr)
            auto_captcha = False
            continue
        if result == jwxt.WechatCodeResult.TOO_FREQUENT:
            print("发送太频繁，请稍后再试。", file=sys.stderr)
            sys.exit(1)
        if result == jwxt.WechatCodeResult.SESSION_EXPIRED:
            print("二次认证会话已失效，请重新运行并完成密码登录。", file=sys.stderr)
            sys.exit(1)
        if result != jwxt.WechatCodeResult.SUCCESS:
            print(f"发送微信验证码失败（{result.value}）。", file=sys.stderr)
            sys.exit(1)
        print(
            "微信验证码已发送，请到「智慧吉大」查看「统一身份认证」消息。",
            file=sys.stderr,
        )
        wx = _prompt("请输入微信验证码：")
        if not wx:
            print("未输入微信验证码。", file=sys.stderr)
            sys.exit(2)
        step = client.login_second_factor(captcha, wx)
        if step == jwxt.LoginStep.SUCCESS:
            print("二次认证成功。", file=sys.stderr)
            return
        print("验证码不正确或已过期，请重试。", file=sys.stderr)
        again = _prompt("再试一次？[Y/n] ").lower()
        if again in ("n", "no", "q"):
            sys.exit(1)
        auto_try = 0  # allow auto again on full retry


def _ensure_login(x) -> jwxt.JwxtClient:
    debug = bool(getattr(x, "debug", False))
    client = jwxt.JwxtClient(debug=debug)

    if not x.force_login and client.load_session():
        print("发现本地会话，正在检测是否有效…", file=sys.stderr)
        if client.session_alive():
            print("会话有效，跳过登录。", file=sys.stderr)
            try:
                client.bootstrap_emap_apps()
                client.save_session()
            except (jwxt.LoginError, jwxt.JwxtError, jwxt.NetworkError) as e:
                print(f"会话探测通过但进入应用失败：{e}；将尝试继续。", file=sys.stderr)
            if getattr(x, "debug", False):
                print(f"[debug] {client.session_cookie_summary()}", file=sys.stderr)
            return client
        print("会话已失效，需要重新登录。", file=sys.stderr)
        client.clear_session_file()
        client = jwxt.JwxtClient(debug=debug)

    username = x.user
    password = x.password
    if not username or not password:
        saved = jwxt.load_credentials()
        if saved:
            if not username:
                username = saved[0]
            if not password:
                password = saved[1]
                print(f"使用本地已保存账号：{username}", file=sys.stderr)
    if not username:
        print(
            "请用 --user 指定邮箱前缀（统一身份认证账号，不是学号），"
            "或先 --save-credentials 保存一次。",
            file=sys.stderr,
        )
        sys.exit(2)
    if not password:
        try:
            password = getpass.getpass(f"请输入 {username} 的统一身份认证密码：")
        except Exception:
            # 部分 Termux 环境 getpass 异常时回退到可见输入
            password = _prompt(f"请输入 {username} 的统一身份认证密码（可见输入）：")

    try:
        print("正在提交账号密码…", file=sys.stderr)
        step = client.login_password(username, password)
    except jwxt.NetworkError as e:
        print(f"网络错误：{e}", file=sys.stderr)
        print(
            "提示：CAS（cas.jlu.edu.cn）公网可访问；教务（iedu.jlu.edu.cn）"
            "通常需要校园网或学校 VPN。",
            file=sys.stderr,
        )
        sys.exit(1)

    if step == jwxt.LoginStep.WRONG_PASSWORD:
        err = client.last_error_text
        if err:
            print(f"统一登录失败：服务器返回「{err}」。", file=sys.stderr)
        else:
            print("统一登录失败：用户名或密码错误。", file=sys.stderr)
        print(
            "账号请使用邮箱前缀（不要用学号；完整邮箱也可，会自动剥掉后缀）。"
            "可加 --debug 查看字段长度与响应详情。",
            file=sys.stderr,
        )
        sys.exit(1)
    if step == jwxt.LoginStep.NEED_SECOND_FACTOR:
        try:
            _interactive_second_factor(
                client,
                show_captcha=bool(getattr(x, "show_captcha", False)),
                auto_captcha=not bool(getattr(x, "no_auto_captcha", False)),
            )
        except jwxt.NetworkError as e:
            print(f"网络错误：{e}", file=sys.stderr)
            sys.exit(1)
        except jwxt.SecondFactorError as e:
            print(f"二次认证失败：{e}", file=sys.stderr)
            sys.exit(1)
    elif step != jwxt.LoginStep.SUCCESS:
        print(f"登录未完成（{step.value}）。", file=sys.stderr)
        sys.exit(1)
    else:
        print("密码登录成功（无需二次认证）。", file=sys.stderr)

    if x.save_credentials:
        path = jwxt.save_credentials(username, password)
        print(f"已保存凭据到 {path}（权限 600）", file=sys.stderr)
    password = None  # noqa: F841

    # 预进入课表/成绩应用，写入 _WEU 等，再落盘会话
    try:
        print("正在进入教务应用（课表/成绩）…", file=sys.stderr)
        client.bootstrap_emap_apps()
    except jwxt.LoginError as e:
        print(f"进入教务应用失败：{e}", file=sys.stderr)
        sys.exit(1)
    except jwxt.NetworkError as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)

    sess = client.save_session()
    summary = client.session_cookie_summary()
    print(f"已保存会话到 {sess}（权限 600）。", file=sys.stderr)
    if summary.get("has_CASTGC"):
        print(
            "会话含 CASTGC：下次若教务 Cookie 过期，仍可能靠它静默换票（通常无需再过微信验证）。",
            file=sys.stderr,
        )
    else:
        print(
            "注意：会话里没有 CASTGC（CAS 长期票据）。"
            "下次主要依赖教务站 Cookie；失效后需要 --force-login 再走一遍认证。",
            file=sys.stderr,
        )
    if getattr(x, "debug", False):
        print(f"[debug] cookies={summary.get('cookie_names')}", file=sys.stderr)
    return client


def _fetch_merged_schedule(client, term, out_path):
    """命令行导出与 App 同一份课表：教务 + 调停课（按 App 设置）+ 个人修改（读数据目录，不写）。

    导出目标正好是数据目录的 schedule.csv 时只写教务原样（App 读取时再合并，避免合并两次）。"""
    from pathlib import Path
    from . import adjust, overlay as ov, timetable, ui
    term = term or client.current_semester() or ""
    raw = client.fetch_schedule(term)
    root = ui.data_dir()
    try:
        if Path(out_path).expanduser().resolve() == (root / "schedule.csv").resolve():
            return raw, "（教务原样；App 读取时合并调课和个人修改）"
    except OSError:
        pass
    enabled = timetable.adjustments_enabled(root)
    adjs: list = []
    if enabled:
        try:
            adjs = adjust.fetch_adjustments(client, term)
        except Exception as e:  # noqa: BLE001 —— 调课读不到不影响课表导出
            print(f"（调课信息暂未获取：{type(e).__name__}，按教务原课表导出）", file=sys.stderr)
    ops = ov.term_ops(timetable.load_overlay(root, term), term)
    v = timetable.build(raw, adjs, ops, enabled)
    for i in v["issues"]:
        print(f"（个人修改提示：{i.get('name', '')} {i['message']}）", file=sys.stderr)
    return timetable.to_courses(v["rows"]), f"（调课 {v['applied']} 处，个人修改 {len(ops)} 处）"


def _cmd_fetch(x):
    if x.probe:
        print(json.dumps(jwxt.probe_reachability(), ensure_ascii=False, indent=2))
        return

    try:
        client = _ensure_login(x)
    except jwxt.LoginError as e:
        print(f"登录失败：{e}", file=sys.stderr)
        sys.exit(1)

    try:
        if x.what in ("all", "schedule"):
            courses, extra = _fetch_merged_schedule(client, x.term, x.schedule_out)
            jwxt.export_courses_csv(courses, x.schedule_out)
            print(f"课表 {len(courses)} 门{extra} → {x.schedule_out}")
        if x.what in ("all", "grades"):
            grades = client.fetch_grades()
            jwxt.export_grades_csv(grades, x.grades_out)
            print(f"成绩 {len(grades)} 条 → {x.grades_out}")
            print(json.dumps(core.gpa(grades), ensure_ascii=False))
            print("（注：此为全部课程的简单学分加权；保研/综测口径请在 jlu-toolkit ui 里勾选课程）", file=sys.stderr)
        if x.what in ("all", "exams"):
            try:
                exs = client.fetch_exams(x.term)
                exmod.export_exams_csv(exs, x.exams_out)
                print(f"考试 {len(exs)} 场 → {x.exams_out}")
                _print_countdown(exs)
            except jwxt.JwxtError as e:
                if x.what == "exams":
                    raise
                print(f"（考试安排暂未获取：{e}）", file=sys.stderr)
    except jwxt.LoginError as e:
        print(f"{e}；可加 --force-login 重登。", file=sys.stderr)
        sys.exit(1)
    except jwxt.NetworkError as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)
    except jwxt.JwxtError as e:
        print(f"教务错误：{e}", file=sys.stderr)
        sys.exit(1)


def _print_countdown(exs, show_all: bool = False) -> None:
    items = exs if show_all else exmod.upcoming(exs)
    if not items:
        print("暂无未结束的考试。")
        return
    for e in items:
        when = e.start.replace("T", " ") if e.start else "时间待定"
        cd = exmod.format_countdown(exmod.countdown(e))
        print(f"⏱ {cd:<14} {e.name}  {when}  {e.location}" + (f"  座位{e.seat}" if e.seat else ""))


def _cmd_exams(x):
    try:
        exs = exmod.load_exams(x.csv)
    except FileNotFoundError:
        print(f"找不到 {x.csv}；先运行 jlu-toolkit fetch --what exams", file=sys.stderr)
        sys.exit(1)
    _print_countdown(exs, show_all=x.all)


def _cmd_explore(x):
    from . import explore

    client = jwxt.JwxtClient(debug=bool(x.debug))
    if not client.load_session():
        print("没有已保存的会话。请先运行 jlu-toolkit fetch --user 你的邮箱前缀 登录一次。", file=sys.stderr)
        sys.exit(1)
    print("开始只读探测（不会进行任何选课/退课/提交操作）…", file=sys.stderr)
    try:
        report = explore.run_explore(client, x.term, log=lambda m: print(m, file=sys.stderr))
    except jwxt.NetworkError as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)
    client.save_session()
    from pathlib import Path

    path = explore.write_report(report, Path(x.out) if x.out else None)
    print(f"脱敏报告已写入：{path}\n（只含状态码/键名/行数/字段名，可以直接粘贴给开发者）")


def _cmd_sync(x):
    from pathlib import Path

    from . import sync, ui

    client = jwxt.JwxtClient(debug=bool(x.debug))
    if not client.load_session():
        print("没有已保存的会话。请先运行 jlu-toolkit fetch --user 你的邮箱前缀 登录一次。", file=sys.stderr)
        sys.exit(1)
    root = Path(x.data_dir).expanduser() if x.data_dir else ui.data_dir()
    try:
        summary = sync.sync_all(client, root, x.term)
    except jwxt.LoginError as e:
        print(f"会话失效：{e}；请运行 jlu-toolkit fetch --force-login", file=sys.stderr)
        sys.exit(1)
    except jwxt.NetworkError as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)
    # 摘要不含个人数值（绩点/学分/成绩只写本地文件）
    print(json.dumps({"data_dir": str(root), **summary}, ensure_ascii=False, indent=1))
    bad = [k for k, v in summary.items() if isinstance(v, dict) and not v.get("ok")]
    sys.exit(2 if bad else 0)


def _cmd_gpa_probe(x):
    import tempfile
    from pathlib import Path
    from . import meta

    client = jwxt.JwxtClient(debug=bool(x.debug))
    if not client.load_session():
        print("没有已保存的会话。请先运行 jlu-toolkit fetch --user 你的邮箱前缀 登录一次。", file=sys.stderr)
        sys.exit(1)
    print("扫描成绩应用（cjcx）中的绩点/统计接口…", file=sys.stderr)
    try:
        report = meta.probe_gpa(client, log=lambda m: print(m, file=sys.stderr))
    except jwxt.JwxtError as e:
        print(f"失败：{e}", file=sys.stderr); sys.exit(1)
    client.save_session()
    path = Path(x.out) if x.out else Path(tempfile.gettempdir()) / "jlu_gpa_probe.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"报告：{path}", file=sys.stderr)
    # 终端默认只打印试调用摘要；完整模块清单在报告文件里
    print(json.dumps({
        "hit": report.get("hit"),
        "has_xh": report.get("has_xh"),
        "modules_seen": (report.get("discover") or {}).get("modules_seen"),
        "gpaish_actions": [{"name": a["name"], "url": a["url"], "fields": a["fields"]}
                           for a in report.get("actions", []) if a.get("gpaish")],
        "captions": report.get("captions"),
        "tries": [{k: t.get(k) for k in ("name", "variant", "status", "code", "msg",
                                         "matched_labels", "payload_fields", "field_captions", "shape")}
                  for t in report.get("tries", [])],
    }, ensure_ascii=False, indent=1))


def _range(s: str) -> tuple[int, int]:
    import re as _re
    s = (s or "").strip()
    if not s:
        return 0, 0
    m = _re.fullmatch(r"(\d*)\s*(-?)\s*(\d*)", s)
    if not m or not (m.group(1) or m.group(3)):
        raise ValueError("座位数范围格式：100- / 50-120 / -80 / 100")
    lo, hi = int(m.group(1) or 0), int(m.group(3) or 0)
    if not m.group(2):
        hi = lo
    return lo, hi


def sort_rooms(rs, key: str):
    if not key:
        return rs
    desc = key.startswith("-")
    k = key.lstrip("-")
    num = k in ("seats", "exam_seats")
    f = (lambda r: float(getattr(r, k) or 0)) if num else (lambda r: str(getattr(r, k, "")))
    return sorted(rs, key=f, reverse=desc)


def filter_plan(courses: list, status: str = "", term: str = "", nature: str = "") -> list:
    return [c for c in courses if (not status or c.get("status") == status)
            and (not term or term in (c.get("term") or ""))
            and (not nature or nature in (c.get("nature") or "") or nature in (c.get("category") or ""))]


def _cmd_plan(x):
    import tempfile
    from pathlib import Path

    from . import plan as pl, ui
    store = ui.Store(ui.data_dir())
    f = store.p("plan_courses.json")
    err = lambda m: print(m, file=sys.stderr)  # noqa: E731
    try:
        if getattr(x, "debug_known", False):
            client = jwxt.JwxtClient(debug=bool(x.debug))
            if not client.load_session():
                raise jwxt.LoginError("no saved session")
            print(json.dumps(pl.debug_known(client)))
            client.save_session()
            return
        from . import secure_store
        if x.probe or x.refresh or not secure_store.json_exists(f):
            client = jwxt.JwxtClient(debug=bool(x.debug))
            if not client.load_session():
                raise jwxt.LoginError("没有已保存的会话")
            if x.probe:
                rep, found = pl.explore(client, log=err)
                cf = store.p("completion.json")
                comp_groups = (secure_store.load_json(cf) or {}).get("groups")
                try:
                    rep["diagnostics"] = pl.diagnose(client, found, comp_groups)
                except jwxt.JwxtError as e:
                    rep["diagnostics"] = {"error": type(e).__name__}
                path = Path(x.out) if x.out else Path(tempfile.gettempdir()) / "jlu_plan_probe.json"
                path.write_text(json.dumps(rep, indent=1), encoding="ascii")
                client.save_session()
                err(f"probe report: {path}")
                calls = rep["calls_with_rows"]
                print(json.dumps({"best": rep["best"], "tree_candidates": rep["tree_candidates"],
                                  "diagnostics": rep["diagnostics"], "apps": {k: {"entered": v.get("entered"),
                                  "modules": sorted(v.get("modules") or {})} for k, v in rep["apps"].items()},
                                  "calls_total": len(rep["calls"]), "calls_with_rows": calls}))
                return
            grades = core.load_grades(str(store.p("grades.csv"))) if store.p("grades.csv").exists() else []
            courses_now = core.load_courses(str(store.p("schedule.csv"))) if store.p("schedule.csv").exists() else []
            p = pl.fetch_plan(client, grades, courses_now, use_cache=not x.refresh)
            from .endpoints import scrub
            secure_store.save_json(f, scrub(p))
            cf = store.p("completion.json")
            comp = secure_store.load_json(cf)
            if comp is not None:
                secure_store.save_json(cf, pl.attach_to_completion(comp, p))
            client.save_session()
        p = secure_store.load_json(f, {})
    except jwxt.LoginError as e:
        err(f"会话失效：{e}；请运行 jlu-toolkit fetch --force-login"); _json_err(x, e); sys.exit(1)
    except jwxt.JwxtError as e:
        err(f"培养方案获取失败：{e}"); _json_err(x, e); sys.exit(1)
    cs = filter_plan(p.get("courses", []), x.status, x.term, x.nature)
    if x.json:
        print(json.dumps({"source": p.get("source"), "count": len(cs), "courses": cs,
                          "tree_stats": p.get("tree_stats"), "tree_summary": p.get("tree_summary")}))
        return
    groups: dict = {}
    for c in cs:
        groups.setdefault(c.get("group") or c.get("category") or c.get("nature") or "未分组", []).append(c)
    for g, items in groups.items():
        done = sum(pl.credit_of(c) for c in items if pl.is_done(c))
        tot = sum(c["credit"] or 0 for c in items)
        print(f"■ {g}  已修 {done:g}/{tot:g} 学分")
        for c in items:
            print(f"   [{c['status']}] {c['code']} {c['name']} {c['credit'] or ''}学分 "
                  f"{c.get('term') or ''} {c.get('nature') or ''} {c.get('score') or ''}".rstrip())


def _json_err(x, e) -> None:
    """--json 模式下错误也以 JSON 输出到 stdout，方便脚本解析。"""
    if getattr(x, "json", False):
        print(json.dumps({"error": f"{type(e).__name__}: {e}" if isinstance(e, Exception) else str(e)}))


def _cmd_rooms(x):
    import datetime as _dt
    import tempfile
    from pathlib import Path

    from . import rooms, ui

    client = jwxt.JwxtClient(debug=bool(x.debug))
    if not client.load_session():
        print("没有已保存的会话。请先运行 jlu-toolkit fetch --user 你的邮箱前缀 登录一次。", file=sys.stderr)
        sys.exit(1)
    store = ui.Store(ui.data_dir())
    cal = store.calendar()
    err = lambda m: print(m, file=sys.stderr)  # noqa: E731
    try:
        if x.probe:
            start, end = rooms.parse_periods_arg(x.periods)
            rep = rooms.probe(client, store.first_monday(), cal.get("term") or client.current_semester() or "",
                              [x.campus] if x.campus else None, x.date, (start, end), log=err)
            path = Path(x.out) if x.out else Path(tempfile.gettempdir()) / "jlu_rooms_probe.json"
            path.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            err(f"探测报告：{path}")
            d = rep.get("discover") or {}
            print(json.dumps({"hit": rep["hit"], "meta": rep["meta"], "campus_count": rep["campus_count"],
                              "discover": {k: d.get(k) for k in ("index_status", "index_bytes", "index_final",
                                                                  "script_srcs", "fetched", "do_paths", "modules_seen")},
                              "meta_trace": [m for m in rep.get("meta_trace", []) if m.get("status") == 200][:20],
                              "campus_source": rep.get("campus_source"),
                              "tries": [{k: t.get(k) for k in ("endpoint", "scheme", "status", "code", "msg", "rows")}
                                        for t in rep["tries"][:30]]}, ensure_ascii=False, indent=1))
            client.save_session()
            return
        if x.list_campuses:
            rows = rooms.list_campuses(client)
            print(json.dumps(rows) if x.json else
                  "\n".join(f"{r['code']}\t{r['name']}" for r in rows) or "（未取到校区列表）")
            return
        if x.list_buildings:
            rows = rooms.list_buildings(client, x.campus or "")
            print(json.dumps(rows) if x.json else
                  "\n".join(f"{r['code']}\t{r['name']}" for r in rows) or "（未取到教学楼列表）")
            return
        if x.list_types:
            rows = rooms.list_room_types(client)
            print(json.dumps(rows) if x.json else
                  "\n".join(f"{r['code']}\t{r['name']}" for r in rows) or "（未取到教室类型）")
            return
        if x.list_fields:
            rows = rooms.extra_search_fields(rooms.full_meta(client))
            print(json.dumps(rows) if x.json else
                  "\n".join(f"{r['name']}\t{r['caption']}\t{r['xtype']}" for r in rows) or "（无其它检索字段）")
            return
        if not x.campus:
            err("请用 --campus 指定校区代码（jlu-toolkit rooms --list-campuses 查看）")
            _json_err(x, "missing --campus")
            sys.exit(2)
        lo, hi = _range(x.seats)
        elo, ehi = _range(x.exam_seats)
        extra = {}
        for kv in x.field:
            k, _, v = kv.partition("=")
            if not k or not _:
                raise ValueError("--field 格式为 名=值")
            extra[k.strip()] = v.strip()
        body = {"campus": x.campus, "date": x.date, "periods": x.periods, "building": x.building,
                "kind": x.kind, "seat_min": lo, "seat_max": hi, "exam_min": elo, "exam_max": ehi,
                "mode": "week" if x.weeks else "date", "weeks": x.weeks, "weekday": x.weekday, "extra": extra}
        q = ui.build_room_query(store, body, cal.get("term") or client.current_semester() or "")
        found, prof = rooms.query_rooms_any(client, q, store.p("rooms_profile.json"), store.first_monday())
        found = sort_rooms(found, x.sort)
        client.save_session()
    except ValueError as e:
        err(str(e)); _json_err(x, e); sys.exit(2)
    except jwxt.LoginError as e:
        err(f"会话失效：{e}；请运行 jlu-toolkit fetch --force-login"); _json_err(x, e); sys.exit(1)
    except jwxt.JwxtError as e:
        err(f"空教室查询失败：{e}"); _json_err(x, e); sys.exit(1)
    if x.json:
        print(json.dumps({"query": q.__dict__, "profile": prof, "count": len(found),
                          "rooms": [r.to_dict() for r in found]}))
    else:
        when = (f"第{q.weeks}周 周{q.weekday}" if q.mode == "week" else f"{q.date}（第{q.week}周 周{q.weekday}）")
        print(f"{when} 第{q.start}-{q.end}节 空教室 {len(found)} 间：")
        for r in found:
            print("  " + "\t".join(v for v in (r.campus, r.building, r.kind, r.name, r.free_date, r.free_periods,
                                                r.free_time, r.seats and r.seats + "座",
                                                r.exam_seats and "考" + r.exam_seats) if v))


def _cmd_ui(x):
    from pathlib import Path
    import tempfile

    from . import ui

    root = None
    if x.demo:
        root = Path(tempfile.mkdtemp(prefix="jlu-ui-demo-"))
        ui.seed_demo(root)
    elif x.data_dir:
        root = Path(x.data_dir).expanduser()
        root.mkdir(parents=True, exist_ok=True)
    ui.serve(port=x.port, root=root, open_browser=x.open)




def _cmd_oa_sub(x):
    import time
    from . import oa_subscribe as osub
    if x.action == "subscribe":
        try:
            if x.sub_action == "add":
                r = osub.add_rule(x.keywords, x.dept, x.category if x.category.isdigit() else "")
                print(json.dumps(r) if x.json else f"已添加 {r['id']}：{'/'.join(r['keywords'])}"
                      + (f"（单位：{'/'.join(r['depts'])}）" if r["depts"] else ""))
            elif x.sub_action == "remove":
                if not x.rule_id:
                    raise ValueError("用法：jlu-toolkit oa subscribe remove <id>")
                if not osub.remove_rule(x.rule_id):
                    raise ValueError(f"规则不存在：{x.rule_id}")
                print(f"已删除 {x.rule_id}")
            else:
                rules = osub.list_rules()
                if x.json:
                    print(json.dumps({"rules": rules, "matches": osub.recent_matches(x.limit if getattr(x, "limit", 0) else 20)}, ensure_ascii=False))
                for r in [] if x.json else rules:
                    print(f"{r['id']}  {'/'.join(r['keywords'])}" + (f"  单位：{'/'.join(r['depts'])}" if r["depts"] else ""))
                if not x.json:
                    ms = osub.recent_matches(5)
                    if ms:
                        print(f"最近命中 {len(ms)} 条：")
                    for m in ms:
                        print(f"  {m['matched_at']}  {m['notice'].get('title','')}  关键词：{'/'.join(m['keywords_hit'])}")
                if not rules and not x.json:
                    print("暂无订阅；用 jlu-toolkit oa subscribe add -k 讲座,奖学金 添加")
        except ValueError as e:
            print(f"OA: {e}", file=sys.stderr)
            sys.exit(2)
        return
    interval = max(osub.MIN_INTERVAL, x.interval)
    client = jwxt.JwxtClient(debug=bool(x.debug))
    client.load_session()
    while True:
        try:
            res = osub.watch_once(client)
            print(f"[OA] {time.strftime('%H:%M')} 新通知 {res['new']} 条，命中 {res['matches']} 条", file=sys.stderr)
        except (jwxt.JwxtError, ValueError) as e:
            print(f"OA: {e}", file=sys.stderr)
            if x.once:
                sys.exit(2)
        if x.once:
            return
        try:
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            return


def _cmd_oa(x):
    from . import oa, ui
    if x.action in ("subscribe", "watch"):
        return _cmd_oa_sub(x)
    client = jwxt.JwxtClient(debug=bool(x.debug))
    has = bool(client.load_session())
    try:
        if x.probe:
            rep = {"saved_session": has, **oa.probe(client, anon_client=jwxt.JwxtClient())}
            try:
                ch = oa.discover_channels(jwxt.JwxtClient())["channels"]
                if ch:
                    d = ui.data_dir(); d.mkdir(parents=True, exist_ok=True)
                    (d / "oa_channels.json").write_text(json.dumps(ch, ensure_ascii=False, indent=1), encoding="utf-8")
            except jwxt.JwxtError:
                pass
            print(json.dumps(rep, indent=1))
            if has:
                client.save_session()
            return
        store = ui.Store(ui.data_dir())
        known = {}
        try:
            known = json.loads(store.p("oa_notices.json").read_text(encoding="utf-8")).get("channels", {})
        except (OSError, ValueError):
            pass
        try:
            known = {**json.loads(store.p("oa_channels.json").read_text(encoding="utf-8")), **known}
        except (OSError, ValueError):
            pass
        ch = oa.resolve_category(x.category, known)
        res = oa.fetch_notices(client, ch, x.keyword, max(1, x.limit), max(1, x.pages),
                               channel_filter=bool(x.category))
        oa.save(store.root if hasattr(store, "root") else ui.data_dir(), res)
        if has:
            client.save_session()
    except (jwxt.JwxtError, ValueError) as e:
        _json_err(x, e)
        print(f"OA: {e}", file=sys.stderr)
        sys.exit(2)
    if x.json:
        res.pop("channels", None)
        print(json.dumps(res))
        return
    print(f"{res['channel_name'] or res['channel']}  共 {res['count']} 条")
    for i in res["items"]:
        print(f"{'[顶] ' if i['top'] else ''}{i['time']}  {i['title']}  （{i['dept']}）")


def _cmd_campus(x):
    from . import campus, jwxt
    if not x.probe:
        print("用法：jlu-toolkit campus --probe [--json]", file=sys.stderr)
        sys.exit(2)
    try:
        rep = campus.probe(jwxt.JwxtClient())
    except jwxt.NetworkError as e:
        print(f"campus: {e}", file=sys.stderr)
        sys.exit(1)
    if x.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return
    print(campus.probe_table(rep))
    print()
    print(f"vpn_url 格式：{rep.get('vpn_format')}")
    print(f"vpn_key：{rep.get('vpn_key')}")
    for s in rep.get("sites") or []:
        need = s.get("needs_login_to_confirm") or []
        if need:
            print(f"  [{s.get('id')}] 仍需登录确认：{', '.join(need)}")


def _cmd_sessions(x):
    from . import sessions
    try:
        if x.action == "keepalive":
            r = sessions.keepalive()
            print(json.dumps(r, ensure_ascii=False) if x.json else
                  ("会话有效" + ("（已通过统一认证续期）" if r["refreshed_via_cas"] else "")) if r["alive"]
                  else r["session"]["message"])
            if not r["alive"]:
                sys.exit(3)
            return
        if x.action in ("clear", "check"):
            if not x.site:
                raise ValueError(f"用法：jlu-toolkit sessions {x.action} <site>（{', '.join(sessions.SITES)}）")
            if x.action == "clear":
                sessions.clear(x.site)
                print(f"已清除 {x.site} 的会话")
                return
            r = sessions.check(x.site)
            print(json.dumps(r, ensure_ascii=False) if x.json else f"{r['id']}: {r['state']}  {r['message']}")
            return
        res = sessions.all_status()
    except ValueError as e:
        print(f"sessions: {e}", file=sys.stderr)
        sys.exit(2)
    if x.json:
        print(json.dumps(res, ensure_ascii=False))
        return
    for r in res["sites"]:
        print(f"{r['id']:<7}{r['name']:<8}{r['state']:<9}{r['message']}")

if __name__ == "__main__":
    main()
