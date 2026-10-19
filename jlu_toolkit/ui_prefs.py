"""界面偏好（主题等 jlu-* 键）落盘，避免端口变化导致 WebView localStorage 丢失。"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict

PREFIX = "jlu-"
MAX_KEY = 64
MAX_VALUE = 2048
MAX_KEYS = 32
MAX_TOTAL = 16 * 1024
FILE = "ui_prefs.json"
_lock = threading.Lock()


def _valid_key(k) -> bool:
    return (isinstance(k, str) and k.startswith(PREFIX) and len(k) <= MAX_KEY
            and all(c.isalnum() or c in "-_." for c in k))


def _clean(d) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(d, dict):
        return out
    for k, v in d.items():
        if _valid_key(k) and isinstance(v, str) and len(v) <= MAX_VALUE and len(out) < MAX_KEYS:
            out[k] = v
    while out and len(json.dumps(out, ensure_ascii=False)) > MAX_TOTAL:
        out.pop(next(iter(out)))
    return out


def load(root: Path) -> Dict[str, str]:
    try:
        return _clean(json.loads((Path(root) / FILE).read_text("utf-8")))
    except (OSError, ValueError):
        return {}


def update(root: Path, set_: dict = None, remove=None) -> Dict[str, str]:
    """set_ 里 None 值等同删除；不合法的键/值被忽略。"""
    with _lock:
        cur = load(root)
        for k in remove or []:
            if isinstance(k, str):
                cur.pop(k, None)
        for k, v in (set_ or {}).items() if isinstance(set_, dict) else []:
            if v is None:
                cur.pop(k, None)
            elif _valid_key(k) and isinstance(v, str) and len(v) <= MAX_VALUE:
                cur[k] = v
        cur = _clean(cur)
        p = Path(root) / FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(cur, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return cur


def inline_script(root: Path) -> str:
    """首帧前注入的 <script>；转义 < > & 和行分隔符，防止提前闭合 script。"""
    s = json.dumps(load(root), ensure_ascii=True)
    s = s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return "<script>window.__PREFS=" + s + ";</script>"
