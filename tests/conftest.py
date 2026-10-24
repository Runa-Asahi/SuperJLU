import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "real_ui_auth: 不跳过本地接口令牌校验（见 test_ui_token.py）")


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    """所有测试使用临时配置目录，绝不读写真实 ~/.config/jlu-toolkit。"""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


@pytest.fixture(autouse=True)
def _ui_token_bypass(request, monkeypatch):
    """多数 UI 测试直接用 urllib 调接口、只关心接口本身；令牌校验在标记 real_ui_auth 的测试里单独验证。"""
    if request.node.get_closest_marker("real_ui_auth"):
        return
    from jlu_toolkit import ui
    monkeypatch.setattr(ui, "_token_ok", lambda headers, token: True)
