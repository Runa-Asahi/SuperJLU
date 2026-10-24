"""SuperJLU 桌面启动器（Windows 单文件 exe 的入口，也可在其它系统运行）。

- 在 127.0.0.1 的空闲端口后台启动 Web UI，自动打开浏览器
- 系统托盘图标（pystray + Pillow）：「打开 SuperJLU」「退出」；缺少 pystray 时无托盘，直接前台运行
- 单实例：config_dir()/desktop.json 记录端口；再次启动时若旧实例仍在响应，只打开浏览器后退出
- 窗口模式（无控制台）下 stdout 可能为 None，所有输出写到 config_dir()/desktop.log
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable, Optional

from . import jwxt

APP_NAME = "SuperJLU"
SERVER_HEADERS = ("SuperJLU-UI", "JLUToolkitUI")  # ui.make_handler 的 server_version（新/旧名）


def state_path() -> Path:
    return jwxt.config_dir() / "desktop.json"


def log_path() -> Path:
    return jwxt.config_dir() / "desktop.log"


def _setup_logging() -> logging.Logger:
    log = logging.getLogger("superjlu.desktop")
    if getattr(log, "_superjlu_path", None) != str(log_path()):
        for h0 in list(log.handlers):
            log.removeHandler(h0)
            h0.close()
        log._superjlu_path = str(log_path())  # type: ignore[attr-defined]
        try:
            log_path().parent.mkdir(parents=True, exist_ok=True)
            h: logging.Handler = logging.FileHandler(log_path(), encoding="utf-8")
        except OSError:
            h = logging.NullHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log


def free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def url_for(port: int) -> str:
    return f"http://127.0.0.1:{port}/"


def read_state() -> Optional[dict]:
    try:
        d = json.loads(state_path().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) and isinstance(d.get("port"), int) else None
    except (OSError, ValueError):
        return None


def write_state(port: int) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"port": port, "pid": os.getpid()}), encoding="utf-8")


def clear_state(port: int) -> None:
    st = read_state()
    if st and st.get("port") == port:
        try:
            state_path().unlink()
        except OSError:
            pass


def is_running(port: int, timeout: float = 1.5) -> bool:
    """端口上是否是 SuperJLU 的 UI 服务（看 Server 头，避免把别的程序当成旧实例）。

    不带令牌探测：端口上可能是别的程序，令牌不能发给它；SuperJLU 的 401 同样带 Server 头。
    """
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 本机地址不走代理
        with op.open(url_for(port) + "api/session", timeout=timeout) as r:
            srv = r.headers.get("Server") or ""
    except urllib.error.HTTPError as e:
        srv = e.headers.get("Server") or ""
    except Exception:  # noqa: BLE001
        return False
    return any(h in srv for h in SERVER_HEADERS)


def existing_instance() -> Optional[int]:
    st = read_state()
    if st and is_running(st["port"]):
        return st["port"]
    if (not st or st["port"] != DEFAULT_PORT) and is_running(DEFAULT_PORT, timeout=0.8):
        return DEFAULT_PORT  # 状态文件丢了，但 8765 上已是 SuperJLU
    return None


DEFAULT_PORT = 8765  # 文档里写的端口；被占用时才换空闲端口


def _bind(port: int, handler):
    from http.server import ThreadingHTTPServer

    class _Server(ThreadingHTTPServer):
        # Windows 上 SO_REUSEADDR 会允许两个进程绑同一端口，必须关掉才能检测「被占用」
        allow_reuse_address = os.name != "nt"
    return _Server(("127.0.0.1", port), handler)


def start_server(root: Optional[Path] = None, port: Optional[int] = None):
    """后台线程启动 UI 服务，返回 (httpd, url)。

    port=None：优先 127.0.0.1:8765，被占用则用空闲端口；port=0：直接用空闲端口。
    """
    from . import ui
    store = ui.Store(root or ui.data_dir())
    handler = ui.make_handler(store)
    if port is None:
        try:
            httpd = _bind(DEFAULT_PORT, handler)
        except OSError:
            _setup_logging().info("端口 %s 被占用，改用空闲端口", DEFAULT_PORT)
            httpd = _bind(0, handler)
    else:
        httpd = _bind(port, handler)
    t = threading.Thread(target=httpd.serve_forever, name="superjlu-ui", daemon=True)
    t.start()
    return httpd, url_for(httpd.server_address[1])


ICON_REL = Path("assets") / "brand" / "superjlu.ico"  # 官方品牌图标（PR #27）


def resource_path(rel) -> Path:
    """PyInstaller 打包后为 sys._MEIPASS/<rel>，开发时为仓库根目录/<rel>。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / rel


def icon_path() -> Optional[Path]:
    p = resource_path(ICON_REL)
    return p if p.is_file() else None


def make_icon(size: int = 64):
    """托盘图标：只用官方 assets/brand/superjlu.ico；缺失时返回 None（不画替代图标）。需要 Pillow。"""
    p = icon_path()
    if p is None:
        return None
    from PIL import Image
    img = Image.open(p)
    try:  # ICO 里挑最接近的尺寸
        img.size = max(img.ico.sizes(), key=lambda wh: (wh[0] <= max(size, 64), wh[0]))  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    return img.convert("RGBA").resize((size, size), Image.LANCZOS)


def run_tray(url: str, on_quit: Callable[[], None], opener: Callable[[str], object]) -> bool:
    """显示托盘图标并阻塞直到「退出」；没有 pystray/Pillow 时返回 False。"""
    try:
        import pystray
        image = make_icon(64)
    except Exception:  # noqa: BLE001
        return False
    if image is None:
        logging.getLogger("superjlu.desktop").warning("缺少 %s，不显示托盘", ICON_REL)
        return False

    def _open(icon=None, item=None):
        opener(url)

    def _quit(icon, item=None):
        on_quit()
        icon.stop()

    icon = pystray.Icon(APP_NAME, image, f"{APP_NAME} · {url}", menu=pystray.Menu(
        pystray.MenuItem("打开 SuperJLU", _open, default=True),
        pystray.MenuItem("退出", _quit)))
    icon.run()
    return True


def main(argv=None, opener: Callable[[str], object] = webbrowser.open,
         tray: Callable = run_tray, wait: Optional[Callable[[], None]] = None) -> int:
    from . import ui
    log = _setup_logging()
    old = existing_instance()
    if old:
        log.info("已有实例在端口 %s，打开浏览器", old)
        opener(ui.launch_url(url_for(old)))  # 同一配置目录，令牌与旧实例相同
        return 0
    httpd, url = start_server()
    port = httpd.server_address[1]
    write_state(port)
    log.info("SuperJLU 已启动：%s", url)  # 日志和托盘提示只写不带令牌的地址
    token = httpd.RequestHandlerClass.auth_token

    def open_ui(u: str):
        return opener(ui.launch_url(u, token))
    stopped = threading.Event()

    def shutdown():
        if not stopped.is_set():
            stopped.set()
            httpd.shutdown()
            httpd.server_close()
            clear_state(port)
            log.info("已退出")

    try:
        try:
            open_ui(url)
        except Exception:  # noqa: BLE001
            log.exception("打开浏览器失败")
        if not tray(url, shutdown, open_ui):
            log.info("无托盘（缺少 pystray/Pillow 或图标），前台运行；Ctrl+C 退出")
            if sys.stdout is not None:
                print(f"{APP_NAME} 已启动：{ui.launch_url(url, token)}  （Ctrl+C 退出）", flush=True)
            (wait or (lambda: stopped.wait()))()
    except KeyboardInterrupt:
        pass
    except Exception:  # noqa: BLE001
        log.exception("启动器异常")
        raise
    finally:
        shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
