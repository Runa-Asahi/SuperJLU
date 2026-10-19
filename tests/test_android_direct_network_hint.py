"""Android 直连：手机实际走移动数据 / Wi-Fi 未过网关时，给出清楚的原因提示。"""
from pathlib import Path

import pytest

from jlu_toolkit import connectivity, netstatus

PAGE = Path("jlu_toolkit/ui_page.py").read_text(encoding="utf-8")
JAVA = Path("android/app/src/main/java/cn/superjlu/app/NetworkStatus.java").read_text(encoding="utf-8")
MAIN = Path("android/app/src/main/java/cn/superjlu/app/MainActivity.java").read_text(encoding="utf-8")
MANIFEST = Path("android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")


def test_desktop_is_unknown_and_silent(monkeypatch):
    monkeypatch.delenv("ANDROID_ROOT", raising=False)
    info = netstatus.status()
    assert info["platform"] == "other" and info["transport"] == "unknown"
    assert netstatus.direct_hint(info) == ""
    assert netstatus.current_direct_hint() == ""
    assert netstatus.with_direct_hint("原始错误。") == "原始错误。"


@pytest.mark.parametrize("raw,expected", [
    ("cellular|1|0", netstatus.CELLULAR_HINT),
    ("wifi|0|1", netstatus.WIFI_UNVALIDATED_HINT),
    ("wifi|0|0", netstatus.WIFI_UNVALIDATED_HINT),
    ("wifi|1|0", ""),
    ("vpn|1|0", ""),
    ("ethernet|1|0", ""),
    ("none|0|0", ""),
    ("unknown|0|0", ""),
    ("garbage", ""),
])
def test_android_transport_hints(raw, expected):
    assert netstatus.direct_hint(netstatus.status(reader=lambda: raw)) == expected


def test_reader_failure_never_raises():
    def boom():
        raise RuntimeError("jni")
    info = netstatus.status(reader=boom)
    assert info["transport"] == "unknown" and netstatus.direct_hint(info) == ""


def test_copy_is_actionable():
    assert "移动数据" in netstatus.CELLULAR_HINT and "网关认证页" in netstatus.CELLULAR_HINT
    assert "校外 WebVPN" in netstatus.CELLULAR_HINT
    assert "还不能上网" in netstatus.WIFI_UNVALIDATED_HINT and "网关" in netstatus.WIFI_UNVALIDATED_HINT


def test_with_direct_hint_appends_once(monkeypatch):
    monkeypatch.setattr(netstatus, "current_direct_hint", lambda: netstatus.CELLULAR_HINT)
    msg = netstatus.with_direct_hint("访问教务时，网络连接中断：iedu.jlu.edu.cn:443。已保留本地数据。")
    assert msg.endswith(netstatus.CELLULAR_HINT)
    assert netstatus.with_direct_hint(msg) == msg


def test_check_all_adds_device_hint(monkeypatch):
    monkeypatch.setattr(connectivity, "check_one", lambda t, timeout=6: {"id": t[0], "reachable": True})
    monkeypatch.setattr(netstatus, "current_direct_hint", lambda: netstatus.CELLULAR_HINT)
    assert connectivity.check_all()["device_hint"] == netstatus.CELLULAR_HINT
    monkeypatch.setattr(netstatus, "current_direct_hint", lambda: "")
    assert "device_hint" not in connectivity.check_all()


def test_iedu_bounce_failure_explains_cellular(monkeypatch):
    from jlu_toolkit import jwxt, sessions
    monkeypatch.setattr(netstatus, "current_direct_hint", lambda: netstatus.CELLULAR_HINT)
    c = jwxt.JwxtClient(route="direct")
    c.pending = jwxt.PendingSecondFactor(lt="LT", execution="e1s1")
    monkeypatch.setattr(sessions, "save_cas_from_jar", lambda jar: True)
    monkeypatch.setattr(c, "_request", lambda *a, **k: (
        302, "", "https://iedu.jlu.edu.cn/sso?ticket=ST-1", {}))

    def fail(*a, **k):
        raise jwxt.NetworkError("访问教务或完成认证回跳时，网络连接中断：iedu.jlu.edu.cn:443。")
    monkeypatch.setattr(c, "_follow_redirects", fail)
    with pytest.raises(jwxt.NetworkError) as e:
        c.login_second_factor("", "123456")
    assert "二次认证已返回跳转" in str(e.value) and netstatus.CELLULAR_HINT in str(e.value)


def test_page_wires_hint_non_intrusively():
    assert 'id="device-net-hint"' in PAGE and 'id="lg-device-net"' in PAGE
    assert 'fetch("/api/network/device")' in PAGE
    assert "function renderDeviceNet()" in PAGE and "renderDeviceNet();loadDeviceNet()}" in PAGE
    assert "network-device-hint" in PAGE and "data.device_hint" in PAGE
    # 只在直连模式下显示，不弹窗
    assert 'sel!=="webvpn"' in PAGE and 'lgTarget==="jwxt"' in PAGE
    seg = PAGE[PAGE.index("function renderDeviceNet()"):PAGE.index("async function loadNetworkState()")]
    assert "alert(" not in seg and "confirm(" not in seg and "showModal" not in seg


def test_android_native_side_is_read_only():
    assert "ACCESS_NETWORK_STATE" in MANIFEST
    assert "NetworkStatus.init(getApplicationContext())" in MAIN
    for needle in ("getActiveNetwork", "TRANSPORT_CELLULAR", "TRANSPORT_WIFI",
                   "NET_CAPABILITY_VALIDATED", "NET_CAPABILITY_CAPTIVE_PORTAL"):
        assert needle in JAVA
    for forbidden in ("bindProcessToNetwork", "requestNetwork", "setProcessDefaultNetwork"):
        assert forbidden not in JAVA
