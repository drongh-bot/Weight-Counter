# -*- mode: python ; coding: utf-8 -*-

# ============================================================
# 1. 禁用 PyInstaller 默认 Qt hook（避免自动引入大量 DLL）
# ============================================================
import PyInstaller.hooks
PyInstaller.hooks.is_hook_enabled = lambda name: False

import os
import sys
import PySide6
from PyInstaller.utils.hooks import collect_submodules

project_path = os.path.abspath(".")
pyside6_path = os.path.dirname(PySide6.__file__)

# ============================================================
# 2. 指定 PySide6 最小模块（Widgets + SerialPort）
# ============================================================
qt_modules = ["QtCore", "QtGui", "QtWidgets", "QtSerialPort"]

hiddenimports = []
for module in qt_modules:
    hiddenimports += collect_submodules(f"PySide6.{module}")

# ============================================================
# 3. 添加资源文件 + 必要插件（平台 + 全部 imageformats）
# ============================================================
datas = [
    ("app/resources/icons", "app/resources/icons"),
    ("app/resources/sounds", "app/resources/sounds"),

    # 平台插件目录（后面过滤，只保留 qwindows.dll）
    (os.path.join(pyside6_path, "plugins", "platforms"), "PySide6/plugins/platforms"),

    # ⭐ 包含整个 imageformats（最省心）
    (os.path.join(pyside6_path, "plugins", "imageformats"), "PySide6/plugins/imageformats"),
]

# ============================================================
# 4. Analysis 阶段（排除不需要的 Qt 模块）
# ============================================================
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
    pathex=[project_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)

# ============================================================
# 5. 过滤平台插件（只保留 qwindows.dll）
# ============================================================
a.datas = [
    item for item in a.datas
    if ("plugins\\platforms" not in item[0] or "qwindows.dll" in item[0])
]

# ============================================================
# 6. 删除无用 DLL（OpenGL / Svg / Qml / Quick / Pdf 等）
# ============================================================
remove_prefixes = [
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
]

filtered_binaries = []
for (dest, src, kind) in a.binaries:
    if not any(p in dest.lower() for p in remove_prefixes):
        filtered_binaries.append((dest, src, kind))
a.binaries = filtered_binaries

# ============================================================
# 7. 删除无用插件目录（generic / tls / iconengines 等）
# ============================================================
remove_dirs = [
    "translations",
    "tls",
    "networkinformation",
    "platforminputcontexts",
    "generic",
]

filtered_datas = []
for (dest, src, kind) in a.datas:
    d = dest.lower()

    if not any(dname in d for dname in remove_dirs) and \
       not any(p in d for p in remove_prefixes):
        filtered_datas.append((dest, src, kind))
a.datas = filtered_datas

# ============================================================
# 8. 构建 EXE（不使用 UPX，不 strip）
# ============================================================
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    name="WeightCounter",
    debug=False,
    strip=False,     # Windows 不支持 strip
    upx=False,       # 不使用 UPX
    console=False,
    icon="app/resources/icons/app.ico",
)

# ============================================================
# 9. 收集最终文件到 dist 目录
# ============================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="WeightCounter",
)
