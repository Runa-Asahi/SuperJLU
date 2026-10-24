# -*- mode: python ; coding: utf-8 -*-
# 用法（Windows）：python packaging/build_windows.py   → dist/SuperJLU.exe
# 图标：仓库 assets/brand/superjlu.ico（PR #27），同时打包进 exe 供托盘使用。
import importlib.util
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ICON = os.path.join(ROOT, "assets", "brand", "superjlu.ico")
if not os.path.isfile(ICON):
    raise SystemExit(f"缺少品牌图标 {ICON}（见 PR #27）")

hidden = (collect_submodules("jlu_toolkit") + collect_submodules("keyring.backends")
          + collect_submodules("PIL")  # 验证码识别（captcha / captcha_solver）与托盘图标
          + ["keyring.backends.Windows", "win32ctypes.core", "win32ctypes.pywin32.win32cred",
             "pystray._win32", "cryptography.hazmat.primitives.ciphers.aead",
             "openpyxl", "xlrd"])  # 成绩单导入（函数内延迟 import）
datas = collect_data_files("jlu_toolkit")  # 含 data/digit_templates.json（验证码模板）、demo、campus_links
datas += [(ICON, os.path.join("assets", "brand"))]
binaries = []
# 可选：装了 ddddocr（.[ocr]）就连同 onnxruntime 与模型一起打包
for pkg in ("ddddocr", "onnxruntime"):
    if importlib.util.find_spec(pkg):
        d, b, h = collect_all(pkg)
        datas += d; binaries += b; hidden += h

a = Analysis([os.path.join(SPECPATH, "superjlu_exe.py")], pathex=[ROOT], datas=datas, binaries=binaries,
             hiddenimports=hidden, excludes=["tkinter"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="SuperJLU", console=False,
          icon=ICON, upx=False, runtime_tmpdir=None)
