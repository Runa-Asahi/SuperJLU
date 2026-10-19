"""Android 入口：在后台线程启动 JLU Toolkit Web UI，只监听 127.0.0.1 的随机端口。

不修改桌面端代码：通过 XDG_CONFIG_HOME 把配置/数据目录指到应用私有目录，
会话、账号密码和缓存由 secure_store 的 Android Keystore 后端加密
（密钥别名 jlu-toolkit-storage，见 #14），不再设置 JLU_TOOLKIT_NO_KEYRING。
"""
from __future__ import annotations

import os
import threading
from http.server import ThreadingHTTPServer
from typing import Optional

PREFERRED_PORT = 18765
_httpd: Optional[ThreadingHTTPServer] = None


def start(files_dir: str) -> str:
    """启动服务并返回 URL；重复调用返回同一个地址。"""
    global _httpd
    if _httpd is not None:
        return f"http://127.0.0.1:{_httpd.server_address[1]}/"
    os.environ["XDG_CONFIG_HOME"] = os.path.join(files_dir, "config")
    os.environ.setdefault("HOME", files_dir)
    from jlu_toolkit import ui

    store = ui.Store(ui.data_dir())
    # 优先固定端口，让 WebView 来源（localStorage）跨启动保持一致；被占用时退回随机端口，
    # 界面偏好另外落盘在 ui_prefs.json，不依赖端口。
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", PREFERRED_PORT), ui.make_handler(store))
    except OSError:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler(store))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, name="jlu-ui", daemon=True).start()
    _httpd = httpd
    return f"http://127.0.0.1:{httpd.server_address[1]}/"


def stop() -> None:
    global _httpd
    if _httpd is not None:
        _httpd.shutdown()
        _httpd.server_close()
        _httpd = None


def campus_reachable(timeout: float = 3.0) -> bool:
    """兼容旧入口：实际 HTTPS 检查，不再把旧站点 TCP:80 当校园网判据。"""
    from jlu_toolkit.connectivity import TARGETS, check_one
    # Only a warning about JWXT: OA has its own campus-network requirement.
    return check_one(TARGETS[1], timeout)["reachable"]
