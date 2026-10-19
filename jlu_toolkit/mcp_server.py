"""MCP 接口：让 Claude、Cursor 等 AI 助手直接查询你的课表、成绩、考试、学业进度和通知。

默认读 SuperJLU App 的数据目录（与桌面 App、jlu-toolkit fetch/sync 同一份），无需配置任何路径；
JLU_SCHEDULE_CSV / JLU_GRADES_CSV / JLU_EXAMS_CSV 仅作可选覆盖。MCP 从不自己登录（需要微信验证码），
只复用 App 或命令行保存的会话与数据。查询函数在 mcp_tools.py，便于测试。"""
from typing import Optional
from . import core

def main():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("SuperJLU")

    from . import mcp_tools as T

    @mcp.tool()
    def courses_on_day(week: int, weekday: int) -> list:
        """查询第 week 周星期 weekday（1-7）的课程（与 App 同一份：教务 + 调停课 + 个人修改）。"""
        return T.courses_on_day(week, weekday)

    @mcp.tool()
    def compute_gpa(term: str = "") -> dict:
        """计算绩点（读 App 已同步的成绩），term 为学期代码，空表示全部学期。"""
        return T.compute_gpa(term)

    @mcp.tool()
    def list_grades(term: str = ""):
        """列出成绩（读 App 已同步的成绩），term 为空表示全部学期。"""
        return T.list_grades(term)

    @mcp.tool()
    def gpa_schemes() -> dict:
        """列出绩点方案：内置模板（保研加权、奖学金加权、所有课程）和在 App 里保存的自定义方案。"""
        return T.gpa_schemes()

    @mcp.tool()
    def compute_gpa_with_scheme(scheme: str, term: str = "") -> dict:
        """按指定方案计算加权平均分和加权绩点。scheme 可写「保研加权」「奖学金加权」「所有课程」、
        模板 id（postgraduate/scholarship/comprehensive）或自定义方案名；term 为空表示全部学期。"""
        return T.compute_gpa_with_scheme(scheme, term)

    @mcp.tool()
    def exams(include_past: bool = False):
        """考试安排与倒计时（读 App 已同步的考试）。默认只列未结束的考试，include_past=true 包含已结束的。"""
        return T.exams(include_past)

    @mcp.tool()
    def academic_progress() -> dict:
        """学业进度：总学分及各课组的要求学分、已获学分、还差学分、是否完成（读 App 已同步的学业完成情况）。"""
        return T.academic_progress()

    @mcp.tool()
    def timetable_adjustments() -> dict:
        """本学期的调课/停课/补课/换教室记录：调整前后的星期、节次、周次、新教室，以及是否已自动应用到课表。"""
        return T.adjustments()

    @mcp.tool()
    def college_notices(college: str = "", keyword: str = "", limit: int = 20, refresh: bool = False) -> dict:
        """学院官网通知（只读）。college 为空时列出可用/已关注的学院栏目；传栏目 id 或学院名（如「计算机」）读通知；
        keyword 过滤标题；refresh=true 时联网抓取学院官网公开页面（无需登录），否则读本地缓存。"""
        return T.college_notices(college, keyword, limit, refresh)

    @mcp.tool()
    def free_rooms(campus: str, date: str = "", periods: str = "1-2", building: str = "", room_type: str = "",
                   seat_min: int = 0, seat_max: int = 0, exam_seat_min: int = 0, exam_seat_max: int = 0,
                   weeks: str = "", weekday: int = 0, extra: Optional[dict] = None) -> dict:
        """查询空教室（需已在 App 或 jlu-toolkit fetch 登录保存会话）。campus 校区代码（list_campuses），
        building 教学楼代码（list_buildings），room_type 教室类型代码（list_room_types）；
        按日期：date=YYYY-MM-DD；按周次：weeks="6-8" + weekday=1-7；periods 如 "3-4"；
        座位数范围 0 表示不限；extra 为其它检索字段 {字段名: 值}。自动翻页取全。"""
        from . import ui
        return ui.rooms_api(ui.Store(ui.data_dir()), {
            "campus": campus, "date": date, "periods": periods, "building": building, "kind": room_type,
            "seat_min": seat_min, "seat_max": seat_max, "exam_min": exam_seat_min, "exam_max": exam_seat_max,
            "mode": "week" if weeks else "date", "weeks": weeks, "weekday": weekday, "extra": extra or {}})

    @mcp.tool()
    def list_buildings(campus: str) -> list:
        """列出某校区的教学楼代码。"""
        from . import ui
        return ui.buildings_api(ui.Store(ui.data_dir()), {"campus": campus})["buildings"]

    @mcp.tool()
    def list_room_types() -> list:
        """列出教室类型代码。"""
        from . import ui
        return ui.room_types_api(ui.Store(ui.data_dir()))["types"]

    @mcp.tool()
    def plan_courses(status: str = "", term: str = "", nature: str = "") -> dict:
        """培养方案课程明细（本地 plan_courses.json，先运行 jlu-toolkit sync 或 plan --refresh）。
        status：已修/在修/未修/未通过；term：建议修读学期（包含匹配）；nature：课程性质/类别（包含匹配）。"""
        import json as _j
        from . import ui
        from .cli import filter_plan
        f = ui.Store(ui.data_dir()).p("plan_courses.json")
        from . import secure_store
        p = secure_store.load_json(f)
        if p is None:
            return {"error": "本地还没有培养方案，" + T.LOGIN_HINT + "后再试。"}
        cs = filter_plan(p.get("courses", []), status, term, nature)
        return {"count": len(cs), "courses": cs}

    @mcp.tool()
    def sessions_status() -> dict:
        """各校园站点（教务/缴费/选课/学在吉大/VPN/图书馆）的登录会话状态。只读本地记录，不联网。"""
        from . import sessions
        return sessions.all_status()

    @mcp.tool()
    def session_status() -> dict:
        """教务登录会话状态（只读本地记录，不联网）。needs_login 为 true 时请提示用户在终端重新登录。"""
        from . import jwxt
        return jwxt.session_status()

    @mcp.tool()
    def oa_notices(category: str = "", keyword: str = "", limit: int = 20, refresh: bool = False) -> dict:
        """吉大 OA 校内通知（只读）。category：栏目 channelId 或名称（默认校内通知）；keyword：标题/单位关键字。
        refresh=true 时联网抓取（需校园网/VPN），否则读本地 oa_notices.json。"""
        import json as _j
        from . import jwxt, oa, ui
        root = ui.data_dir()
        f = root / "oa_notices.json"
        try:
            known = _j.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            ch = oa.resolve_category(category, known.get("channels", {}))
            if refresh or not f.exists():
                c = jwxt.JwxtClient()
                c.load_session()
                oa.save(root, oa.fetch_notices(c, ch, keyword, limit, channel_filter=bool(category)))
                known = _j.loads(f.read_text(encoding="utf-8"))
        except (jwxt.JwxtError, ValueError) as e:
            return {"error": str(e)}
        items = known.get("channels_items", {}).get(ch, [])
        if keyword:
            items = [i for i in items if keyword in i.get("title", "") or keyword in i.get("dept", "")]
        return {"channel": ch, "updated": known.get("updated"), "count": len(items[:limit]), "items": items[:limit]}

    @mcp.tool()
    def oa_new_matches(limit: int = 20, since: str = "") -> dict:
        """OA 订阅命中的新通知（只读本地 oa_matches.json，由 jlu-toolkit oa watch 产生）。
        since：ISO 时间，只返回之后命中的；同时返回当前订阅规则。"""
        from . import oa_subscribe as osub
        return {"rules": osub.list_rules(), "matches": osub.recent_matches(limit, since)}

    @mcp.tool()
    def list_campuses() -> list:
        """列出空教室查询可用的校区代码。"""
        from . import ui
        return ui.campuses_api(ui.Store(ui.data_dir()))["campuses"]

    mcp.run()

if __name__ == "__main__": main()
