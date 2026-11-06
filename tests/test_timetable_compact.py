"""课表紧凑显示：固定行高 + clamp + 偏好开关。"""
from jlu_toolkit.ui_page import PAGE


def test_compact_grid_uses_fixed_rows_and_clamp():
    assert "grid-auto-rows:34px" in PAGE
    assert "-webkit-line-clamp:2" in PAGE
    assert "line-clamp:2" in PAGE
    assert "-webkit-line-clamp:1" in PAGE
    assert "min-height:46px" not in PAGE  # 旧硬下限会撑高整行
    assert "word-break:break-word" in PAGE
    assert "word-break:break-all;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12)}" not in PAGE
    assert "justify-content:center" in PAGE
    assert ".grid.kb-comfy" in PAGE


def test_compact_toggle_persists_via_jlu_prefs():
    assert 'id="kb-compact"' in PAGE
    assert 'id="kb-compact-sz"' in PAGE
    assert "jlu-kb-compact" in PAGE
    assert "function kbCompactOn()" in PAGE
    assert "function applyKbCompact()" in PAGE
    assert "function setKbCompact(on)" in PAGE
    assert 'localStorage.getItem("jlu-kb-compact")!=="false"' in PAGE


def test_render_grid_keeps_span_and_badges_and_cell_coords():
    # 跨节 grid-row 写法不能丢；角标伪元素保留；空白格带坐标供双击添加
    assert "grid-row:${c.start+1}/${c.end+2}" in PAGE
    assert '.cls.edited::after{content:"改"}' in PAGE
    assert '.cls.custom::after{content:"自"}' in PAGE
    assert '.cls.adjusted::after{content:"调"' in PAGE
    assert '.cls.cancelled::after{content:"停"' in PAGE
    assert 'data-d="${d}" data-p="${p}"' in PAGE
    assert 'font-size:11px' in PAGE  # 课程名可读下限


def test_course_name_stays_readable_in_compact():
    # 紧凑默认下课程名仍约 11px
    assert ".cls b{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden;font-size:11px" in PAGE
