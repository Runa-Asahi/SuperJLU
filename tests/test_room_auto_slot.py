"""空教室：打开时按当前时间自动选好接下来两节。"""
import json
import re
import shutil
import subprocess

import pytest

from jlu_toolkit.ui_page import PAGE

DEF = {1: ["08:00", "08:45"], 2: ["08:55", "09:40"], 3: ["10:00", "10:45"], 4: ["10:55", "11:40"],
       5: ["13:30", "14:15"], 6: ["14:25", "15:10"], 7: ["15:30", "16:15"], 8: ["16:25", "17:10"],
       9: ["18:30", "19:15"], 10: ["19:25", "20:10"], 11: ["20:20", "21:05"]}


def _fn():
    m = re.search(r"function roomNextSlot\(map,now\)\{.*?\n", PAGE)
    assert m, "roomNextSlot missing"
    return m.group(0)


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
@pytest.mark.parametrize("hm,day,a,b", [
    ("07:10", 0, 1, 2),    # 早上没课前：第 1-2 节
    ("08:30", 0, 1, 2),    # 第 1 节进行中：从第 1 节开始
    ("09:50", 0, 3, 4),    # 课间：下一节第 3 节
    ("12:30", 0, 5, 6),    # 午休：下午第 5-6 节
    ("17:05", 0, 8, 9),    # 第 8 节进行中
    ("20:30", 0, 11, 11),  # 最后一节进行中：只剩第 11 节
    ("21:30", 1, 1, 2),    # 当天结束：明天第 1-2 节
])
def test_next_slot(tmp_path, hm, day, a, b):
    h, mi = map(int, hm.split(":"))
    js = _fn() + f"""
const r=roomNextSlot({json.dumps(DEF)},new Date(2026,9,19,{h},{mi}));
console.log(JSON.stringify({{a:r.a,b:r.b,day:r.date.getDate()-19}}));
"""
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    out = json.loads(subprocess.run(["node", str(f)], capture_output=True, text=True, check=True).stdout)
    assert out == {"a": a, "b": b, "day": day}


def test_auto_slot_respects_manual_edits_and_has_hint():
    assert 'id="rauto"' in PAGE
    assert "_rTouched=true" in PAGE
    assert "roomAutoSlot();" in PAGE
    # 默认值不再写死为当天 0 点的第 1-2 节
    assert 'toISOString().slice(0,10);rdToWeek();periodsToStudy()})();' not in PAGE
