"""Android 设备当前默认网络（只读），用于解释「校园网直连」失败的常见原因。

只报告系统默认网络是 Wi-Fi 还是移动数据、是否通过系统联网验证；不切换路由、
不绑定 socket、不弹窗。桌面端及任何读取失败一律返回 unknown，不产生提示。
"""
from __future__ import annotations

import os

CELLULAR_HINT = ("当前手机走的是移动数据，没有走校园 Wi-Fi，教务直连会失败。"
                 "请确认已连上校园 Wi-Fi 并在网关认证页登录（可暂时关掉移动数据），"
                 "或改用「校外 WebVPN」。")
WIFI_UNVALIDATED_HINT = ("已连接 Wi-Fi，但系统判定它还不能上网，可能还没在校园网网关登录；"
                         "此时手机可能改走移动数据，教务直连会失败。请先在网关认证页登录，"
                         "或改用「校外 WebVPN」。")

_UNKNOWN = {"platform": "other", "transport": "unknown", "validated": False, "captive_portal": False}


def _read_android():
    from java import jclass
    return str(jclass("cn.superjlu.app.NetworkStatus").current())


def parse(raw):
    parts = str(raw or "").split("|")
    if len(parts) != 3 or parts[0] not in ("wifi", "cellular", "ethernet", "vpn", "other", "none", "unknown"):
        return dict(_UNKNOWN, platform="android")
    return {"platform": "android", "transport": parts[0],
            "validated": parts[1] == "1", "captive_portal": parts[2] == "1"}


def status(reader=None):
    """{"platform","transport","validated","captive_portal"}；非 Android 为 unknown。"""
    if reader is None:
        if "ANDROID_ROOT" not in os.environ:
            return dict(_UNKNOWN)
        reader = _read_android
    try:
        return parse(reader())
    except Exception:
        return dict(_UNKNOWN, platform="android")


def direct_hint(info):
    """直连模式下针对当前设备网络的提示；无需提示时返回空串。"""
    info = info or {}
    if info.get("platform") != "android":
        return ""
    transport = info.get("transport")
    if transport == "cellular":
        return CELLULAR_HINT
    if transport == "wifi" and (info.get("captive_portal") or not info.get("validated")):
        return WIFI_UNVALIDATED_HINT
    return ""


def current_direct_hint():
    try:
        return direct_hint(status())
    except Exception:
        return ""


def with_direct_hint(message):
    """把设备网络提示附在直连失败信息后；没有提示或已附过时原样返回。"""
    hint = current_direct_hint()
    message = str(message or "")
    if not hint or hint in message:
        return message
    return message + ("" if not message or message.endswith(("。", "；")) else "。") + hint
