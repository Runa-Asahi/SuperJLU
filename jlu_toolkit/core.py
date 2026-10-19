"""核心逻辑：读取课表/成绩 CSV，计算绩点，导出 iCal。全部在本地完成。"""
import csv, datetime as dt, uuid
from dataclasses import dataclass

PERIODS = {1:("08:00","08:45"),2:("08:55","09:40"),3:("10:00","10:45"),4:("10:55","11:40"),
           5:("13:30","14:15"),6:("14:25","15:10"),7:("15:30","16:15"),8:("16:25","17:10"),
           9:("18:30","19:15"),10:("19:25","20:10"),11:("20:20","21:05")}

@dataclass
class Course:
    name: str; teacher: str; location: str; weekday: int; start: int; end: int; weeks: list
    jxbid: str = ""   # 教学班 ID（教务 JXBID）；旧 7 列 CSV 没有，为空
    kch: str = ""     # 课程号（KCH）
    adj: str = ""     # 由教务调课生成的这节课的说明（只在读取时合并产生，不写入 CSV）
    istk: bool = False  # 教务课表 ISTK=1：教务标记这门课有调/停课（只作提示，详情以调课接口为准）

@dataclass
class Grade:
    name: str; credit: float; score: str; term: str
    jw_point: "float | None" = None  # 教务返回的单科绩点（若有）
    nature: str = ""

def parse_weeks(s):
    out = []
    for part in s.replace("，", ",").split(","):
        part = part.strip()
        odd = part.endswith("单"); even = part.endswith("双"); part = part.rstrip("单双周")
        if "-" in part:
            a, b = map(int, part.split("-"))
            out += [w for w in range(a, b+1) if not (odd and w%2==0) and not (even and w%2)]
        elif part:
            out.append(int(part))
    return out

def load_courses(path):
    with open(path, encoding="utf-8-sig") as f:
        return [Course(r["课程"], r.get("教师",""), r.get("地点",""), int(r["星期"]),
                       int(r["开始节"]), int(r["结束节"]), parse_weeks(r["周次"]),
                       (r.get("教学班") or "").strip(), (r.get("课程号") or "").strip(), "",
                       (r.get("教务调课标记") or "").strip() == "是")
                for r in csv.DictReader(f)]

def load_grades(path):
    with open(path, encoding="utf-8-sig") as f:
        out = []
        for r in csv.DictReader(f):
            jp = (r.get("教务绩点") or "").strip()
            out.append(Grade(r["课程"], float(r["学分"]), r["成绩"].strip(), r.get("学期",""),
                             float(jp) if jp else None, r.get("课程性质", "")))
        return out

LEVEL = {"优秀":95,"良好":85,"中等":75,"及格":65,"不及格":55,"通过":None,"不通过":0}

def score_to_point(score):
    """百分制：60 分记 1.0，每多 1 分加 0.1，90 分及以上记 4.0；等级制先换算成分数。具体规则请以学校规定为准。"""
    v = LEVEL.get(score, None) if not score.replace(".","",1).isdigit() else float(score)
    if v is None: return None
    if v < 60: return 0.0
    return min(4.0, round(1.0 + (v-60)*0.1, 2))

def gpa(grades, term=None):
    tot = pts = 0.0
    for g in grades:
        if term and g.term != term: continue
        p = score_to_point(g.score)
        if p is None: continue
        tot += g.credit; pts += p*g.credit
    return {"gpa": round(pts/tot, 3) if tot else 0.0, "credits": tot}

def courses_on(courses, week, weekday):
    return sorted([c for c in courses if week in c.weeks and c.weekday == weekday], key=lambda c: c.start)

def to_ics(courses, first_monday, periods=None):
    """periods: {节次: ("HH:MM","HH:MM")}；缺省用内置 PERIODS（教务节次时间可覆盖）。"""
    P = dict(PERIODS)
    if periods:
        P.update({int(k): tuple(v) for k, v in periods.items()})
    d0 = dt.date.fromisoformat(first_monday)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//SuperJLU//CN","X-WR-CALNAME:吉大课表",
             "X-WR-TIMEZONE:Asia/Shanghai"]
    for c in courses:
        for w in c.weeks:
            day = d0 + dt.timedelta(weeks=w-1, days=c.weekday-1)
            if c.start not in P or c.end not in P: continue
            s = P[c.start][0].replace(":",""); e = P[c.end][1].replace(":","")
            lines += ["BEGIN:VEVENT", f"UID:{uuid.uuid4()}@jlu-toolkit", f"DTSTAMP:{stamp}",
                      f"DTSTART;TZID=Asia/Shanghai:{day:%Y%m%d}T{s}00",
                      f"DTEND;TZID=Asia/Shanghai:{day:%Y%m%d}T{e}00",
                      f"SUMMARY:{c.name}", f"LOCATION:{c.location}",
                      f"DESCRIPTION:教师 {c.teacher}｜第{w}周 第{c.start}-{c.end}节",
                      "BEGIN:VALARM","TRIGGER:-PT15M","ACTION:DISPLAY","DESCRIPTION:上课提醒","END:VALARM",
                      "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
