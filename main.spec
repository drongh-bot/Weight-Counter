# -*- mode: python ; coding: utf-8 -*-

# ============================================================
# 1. Disable default PyInstaller Qt hooks
# ============================================================
import PyInstaller.hooks
PyInstaller.hooks.is_hook_enabled = lambda name: False

import os
import PySide6
from PyInstaller.utils.hooks import collect_submodules

project_path = os.path.abspath(".")
pyside6_path = os.path.dirname(PySide6.__file__)

# ============================================================
# 2. Minimal PySide6 modules (Widgets + SerialPort)
# ============================================================
qt_modules = ["QtCore", "QtGui", "QtWidgets", "QtSerialPort"]

hiddenimports = []
for module in qt_modules:
    hiddenimports += collect_submodules(f"PySide6.{module}")

# ============================================================
# 3. Resource files + required plugins
# ============================================================
datas = [
    ("app/resources/icons", "app/resources/icons"),
    ("app/resources/sounds", "app/resources/sounds"),
    (os.path.join(pyside6_path, "plugins", "platforms"), "PySide6/plugins/platforms"),
    (os.path.join(pyside6_path, "plugins", "imageformats"), "PySide6/plugins/imageformats"),
]

# ============================================================
# 4. Analysis — exclude unused Qt modules
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
# 5. Keep only qwindows.dll platform plugin
# ============================================================
a.datas = [
    item for item in a.datas
    if ("plugins\\platforms" not in item[0] or "qwindows.dll" in item[0])
]

# ============================================================
# 6. Strip unused DLLs
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
# 7. Strip unused plugin directories
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
# 8. Build EXE (no UPX, no strip)
# ============================================================
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    name="WeightCounter",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon="app/resources/icons/app.ico",
)

# ============================================================
# 9. Collect into dist folder
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
