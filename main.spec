# -*- mode: python ; coding: utf-8 -*-
"""WeightCounter 打包说明（Windows onedir）。

策略：关掉默认 Qt hooks，只收集用到的 PySide6 模块；
平台插件只打入 qwindows.dll；再踢掉无关 DLL / 插件目录以控制体积。
务必：uv run pyinstaller main.spec --clean -y（不要裸跑 pyinstaller main.py）。
"""

# —— 关掉默认 hooks（避免把整套 Qt 拖进来）——
import PyInstaller.hooks

PyInstaller.hooks.is_hook_enabled = lambda name: False

from pathlib import Path

import PySide6
from PyInstaller.utils.hooks import collect_submodules

project_root = Path(".").resolve()
pyside6_root = Path(PySide6.__file__).resolve().parent

# —— 只用到的 PySide6 模块 ——
qt_modules = ["QtCore", "QtGui", "QtWidgets", "QtSerialPort"]
hiddenimports: list[str] = []
for module in qt_modules:
    hiddenimports += collect_submodules(f"PySide6.{module}")

# —— 应用资源 + 必需插件（平台插件只打 qwindows）——
datas = [
    ("app/resources/icons", "app/resources/icons"),
    ("app/resources/sounds", "app/resources/sounds"),
    (
        str(pyside6_root / "plugins" / "platforms" / "qwindows.dll"),
        "PySide6/plugins/platforms",
    ),
    (
        str(pyside6_root / "plugins" / "imageformats"),
        "PySide6/plugins/imageformats",
    ),
]

# —— Analysis：显式排除用不到的 Qt 模块 ——
excludes = [
    "PySide6.QtNetwork",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtSvg",
    "PySide6.QtOpenGL",
    "PySide6.QtTest",
    "PySide6.QtPdf",
    "PySide6.QtVirtualKeyboard",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)

# —— 踢掉多余二进制 / 数据（体积）——
remove_prefixes = (
    "qt6network",
    "qt6opengl",
    "qt6openglwidgets",
    "qt6svg",
    "qt6test",
    "qt6qml",
    "qt6quick",
    "qt6pdf",
    "qt6virtualkeyboard",
    "opengl32sw.dll",
)
remove_dirs = (
    "translations",
    "tls",
    "networkinformation",
    "platforminputcontexts",
    "generic",
)


def _dest_key(dest: str) -> str:
    return dest.replace("\\", "/").lower()


def _keep_binary(dest: str) -> bool:
    key = _dest_key(dest)
    if any(p in key for p in remove_prefixes):
        return False
    # Analysis / hooks 仍可能带上其它平台插件，只留 Windows
    if "/plugins/platforms/" in key and "qwindows.dll" not in key:
        return False
    return True


def _keep_data(dest: str) -> bool:
    key = _dest_key(dest)
    if any(d in key for d in remove_dirs):
        return False
    if any(p in key for p in remove_prefixes):
        return False
    if "/plugins/platforms/" in key and "qwindows.dll" not in key:
        return False
    return True


a.binaries = [
    (dest, src, kind) for dest, src, kind in a.binaries if _keep_binary(dest)
]
a.datas = [(dest, src, kind) for dest, src, kind in a.datas if _keep_data(dest)]

# —— 生成无控制台 EXE，再收集到 dist/weightCounter/ ——
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    name="weightCounter",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon="app/resources/icons/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="weightCounter",
)
