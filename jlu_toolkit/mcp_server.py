"""MCP 接口：让 Claude、Cursor 等 AI 助手直接查询你的课表和绩点。数据只从本地文件读取。
环境变量 JLU_SCHEDULE_CSV / JLU_GRADES_CSV 指定文件路径；课表省略时读数据目录（与 App 同一份）。"""
import os
from typing import Optional
from . import core

def main():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("SuperJLU")

    @mcp.tool()
    def courses_on_day(week: int, weekday: int) -> list:
        """查询第 week 周星期 weekday（1-7）的课程（与 App 同一份：教务 + 调停课 + 个人修改）。"""
        from . import timetable, ui
        csv_path = os.environ.get("JLU_SCHEDULE_CSV")
        cs = timetable.courses_from_csv(csv_path) if csv_path else timetable.courses(ui.data_dir())
        return [c.__dict__ for c in core.courses_on(cs, week, weekday)]

    @mcp.tool()
    def compute_gpa(term: str = "") -> dict:
        """计算绩点，term 为空表示全部学期。"""
        return core.gpa(core.load_grades(os.environ["JLU_GRADES_CSV"]), term or None)

    @mcp.tool()
    def list_grades(term: str = "") -> list:
        """列出成绩。"""
        return [g.__dict__ for g in core.load_grades(os.environ["JLU_GRADES_CSV"]) if not term or g.term == term]

    @mcp.tool()
    def free_rooms(campus: str, date: str = "", periods: str = "1-2", building: str = "", room_type: str = "",
                   seat_min: int = 0, seat_max: int = 0, exam_seat_min: int = 0, exam_seat_max: int = 0,
                   weeks: str = "", weekday: int = 0, extra: Optional[dict] = None) -> dict:
        """查询空教室（需已用 jlu-toolkit fetch 保存会话）。campus 校区代码（list_campuses），
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
            return {"error": "尚无 plan_courses.json，请先运行 jlu-toolkit sync"}
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
