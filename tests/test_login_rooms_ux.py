"""BATCH 2：登录自动发验证码；空教室三档查询与节次换算；结果列去重。"""
from __future__ import annotations

from jlu_toolkit import rooms
from jlu_toolkit.ui_page import PAGE

PERIODS = {
    1: ["08:00", "08:45"],
    2: ["08:55", "09:40"],
    3: ["10:00", "10:45"],
    4: ["10:55", "11:40"],
    5: ["13:30", "14:15"],
    6: ["14:25", "15:10"],
    7: ["15:30", "16:15"],
    8: ["16:25", "17:10"],
    9: ["18:30", "19:15"],
    10: ["19:25", "20:10"],
    11: ["20:20", "21:05"],
}


def test_login_auto_sends_wechat_code_after_password():
    assert "lgSendCode" in PAGE
    assert 'LG.step==="pw"' in PAGE
    assert "await lgSendCode()" in PAGE
    # 密码通过后同一提交里就会发码，cap 步留给「重新发送」
    pw = PAGE.split("if(LG.step===\"pw\")", 1)[1].split("else if(LG.step===\"cap\")", 1)[0]
    assert "lgSendCode" in pw
    assert "点「发送微信验证码」" not in PAGE
    assert "账号密码已通过" in PAGE
    # 密码通过后保留密文圆点，不把真实密码再提交出去
    assert '$("#lgp").value=PW_MASK' in pw
    assert '$("#lgp").value=""' not in pw
    assert '===PW_MASK?"":' in PAGE
    # 「账号密码已通过」醒目展示，不埋在灰色 .sub 里
    assert "lg-pass-ok" in PAGE
    assert 'class="lg-pass-ok"' in PAGE


def test_rooms_single_form_no_mode_tabs_and_slim_result_cols():
    """去掉顶部「按日期/按周次/按自习时间」三个按钮；下面所有条件都保留并直接显示。"""
    assert 'id="rmode"' not in PAGE and "setRoomMode" not in PAGE
    assert "按日期查询" not in PAGE and "按周次查询" not in PAGE and "按自习时间" not in PAGE
    assert 'id="rd"' in PAGE and 'id="rw"' in PAGE and 'id="rwd"' in PAGE
    assert 'id="rp1"' in PAGE and 'id="rp2"' in PAGE
    assert 'id="rst"' in PAGE and 'id="ret"' in PAGE
    assert 'class="m-week" hidden' not in PAGE and 'class="m-study" hidden' not in PAGE
    assert 'id="rst-presets" hidden' not in PAGE
    assert "rdToWeek" in PAGE and "weekToRd" in PAGE
    assert "roomQueryMode" in PAGE and "mode:roomQueryMode()" in PAGE
    assert 'data-sp="1-4"' in PAGE and 'data-sp="5-8"' in PAGE and 'data-sp="9-12"' in PAGE
    # 结果表去掉与筛选重复的校区/日期/节次/时间列
    assert '["campus","学校校区"]' not in PAGE
    assert '["free_date","空闲日期"]' not in PAGE
    assert '["free_periods","空闲节次"]' not in PAGE
    assert '["free_time","空闲时间"]' not in PAGE
    assert '["building","教学楼"]' in PAGE and '["name","教室名称"]' in PAGE


def test_rooms_study_time_and_period_sync_in_page():
    assert 'id="rst"' in PAGE and 'id="ret"' in PAGE
    assert "periodsToStudy" in PAGE and "studyToPeriods" in PAGE


def test_study_time_for_periods():
    assert rooms.study_time_for_periods(PERIODS, 1, 2) == ("08:00", "09:40")
    assert rooms.study_time_for_periods(PERIODS, 5, 8) == ("13:30", "17:10")
    assert rooms.study_time_for_periods(PERIODS, 9, 11) == ("18:30", "21:05")
    assert rooms.study_time_for_periods(PERIODS, 3, 1) is None


def test_periods_for_study_time():
    assert rooms.periods_for_study_time(PERIODS, "08:00", "09:40") == (1, 2)
    assert rooms.periods_for_study_time(PERIODS, "14:00", "17:00") == (5, 8)
    assert rooms.periods_for_study_time(PERIODS, "18:30", "21:05") == (9, 11)
    # 卡在两节课之间的空档 → 无重叠
    assert rooms.periods_for_study_time(PERIODS, "09:41", "09:59") is None
    assert rooms.periods_for_study_time(PERIODS, "10:00", "09:00") is None


def test_roundtrip_presets():
    for a, b in ((1, 4), (5, 8), (9, 11)):
        st, et = rooms.study_time_for_periods(PERIODS, a, b)
        assert rooms.periods_for_study_time(PERIODS, st, et) == (a, b)


def test_def_periods_before_boot_iife():
    """v1.0.9 回归：IIFE 在 const DEF_PERIODS 前调用 periodsToStudy → TDZ → #boot 卡住。"""
    i_def = PAGE.index("const DEF_PERIODS=")
    i_iife = PAGE.index("\nroomAutoSlot();")  # 原 IIFE，现在按当前时间自动选节次
    assert i_def < i_iife
    assert PAGE.index("let _rTouched=") < i_iife
