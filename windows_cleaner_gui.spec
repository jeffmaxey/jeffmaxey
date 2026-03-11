# windows_cleaner_gui.spec
# ------------------------
# PyInstaller spec file for building the Windows Cleaner GUI executable.
#
# Usage (from repo root on Windows):
#   pip install pyinstaller
#   pyinstaller windows_cleaner_gui.spec
#
# Output:
#   dist\WindowsCleaner\WindowsCleaner.exe   (onedir)
#   dist\WindowsCleaner.exe                  (onefile, uncomment ONEFILE below)

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(SPECPATH)  # noqa: F821 – injected by PyInstaller
GUI_PKG = ROOT / "windows_cleaner_gui"
BACKEND_PKG = ROOT / "windows_cleaner"

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
APP_NAME = "WindowsCleaner"
APP_VERSION = "1.0.0"
APP_ICON = str(GUI_PKG / "resources" / "icons" / "app.ico")

# Change to True to build a single-file executable (slower to start)
ONEFILE = False

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------
datas = [
    # Stylesheet
    (str(GUI_PKG / "resources" / "styles" / "dark.qss"),
     "windows_cleaner_gui/resources/styles"),
    # App icon
    (str(GUI_PKG / "resources" / "icons" / "app.ico"),
     "windows_cleaner_gui/resources/icons"),
]

# ---------------------------------------------------------------------------
# Hidden imports that PyInstaller may miss
# ---------------------------------------------------------------------------
hiddenimports = [
    "windows_cleaner",
    "windows_cleaner.cleaner",
    "windows_cleaner.admin",
    "windows_cleaner.utils",
    "windows_cleaner.menu",
    "windows_cleaner_gui",
    "windows_cleaner_gui.app",
    "windows_cleaner_gui.services.cleaner_service",
    "windows_cleaner_gui.services.settings_service",
    "windows_cleaner_gui.workers.cleaner_worker",
    "windows_cleaner_gui.views.main_window",
    "windows_cleaner_gui.views.scan_page",
    "windows_cleaner_gui.views.clean_page",
    "windows_cleaner_gui.views.results_page",
    "windows_cleaner_gui.views.settings_page",
    "windows_cleaner_gui.views.logs_page",
    "windows_cleaner_gui.views.about_page",
    # PySide6 modules
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

# ---------------------------------------------------------------------------
# Exclusions (reduce binary size)
# ---------------------------------------------------------------------------
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PIL",
    "test",
    "unittest",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(  # noqa: F821
    [str(ROOT / "windows_cleaner_gui" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

# ---------------------------------------------------------------------------
# EXE
# ---------------------------------------------------------------------------
if ONEFILE:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=APP_ICON,
        version_file=None,
    )
else:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=APP_ICON,
        version_file=None,
    )

    coll = COLLECT(  # noqa: F821
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
