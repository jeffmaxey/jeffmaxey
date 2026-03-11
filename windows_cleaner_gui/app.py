"""
app.py
------
QApplication bootstrap for the Windows Cleaner GUI.

This module owns the single QApplication instance, configures global Qt
settings (application name, organisation, high-DPI, stylesheet), sets up
application-level logging (file + Qt log viewer handler), and launches the
main window.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Gracefully handle PySide6 being absent so that non-GUI tests can still
# import the rest of the package without crashing.
# ---------------------------------------------------------------------------
try:
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False

from windows_cleaner_gui import __version__

logger = logging.getLogger(__name__)

APP_NAME = "Windows Cleaner"
APP_ORG = "Chainski"
APP_VERSION = __version__

# ---------------------------------------------------------------------------
# QT logging bridge
# ---------------------------------------------------------------------------

class _QtLogHandler(logging.Handler):
    """Forwards Python log records to any registered Qt log-viewer callbacks."""

    _listeners: list = []

    @classmethod
    def add_listener(cls, callback) -> None:
        cls._listeners.append(callback)

    @classmethod
    def remove_listener(cls, callback) -> None:
        try:
            cls._listeners.remove(callback)
        except ValueError:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        for cb in list(self._listeners):
            try:
                cb(record.levelno, msg)
            except Exception:  # noqa: BLE001
                pass


def _configure_logging(log_dir: Path) -> _QtLogHandler:
    """Set up root logger with file + console + Qt handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "windows_cleaner_gui.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler (INFO+)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Qt bridge handler
    qh = _QtLogHandler()
    qh.setLevel(logging.DEBUG)
    qh.setFormatter(fmt)
    root.addHandler(qh)

    return qh


def _load_stylesheet(app: "QApplication") -> None:
    """Load QSS dark theme from the bundled resource file."""
    styles_path = Path(__file__).parent / "resources" / "styles" / "dark.qss"
    if styles_path.exists():
        app.setStyleSheet(styles_path.read_text(encoding="utf-8"))
    else:
        logger.warning("Stylesheet not found at %s; using default theme.", styles_path)


def _app_data_dir() -> Path:
    """Return a platform-appropriate directory for application data."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    return base / APP_ORG / APP_NAME


def main() -> int:
    """Bootstrap the QApplication and show the main window.

    Returns
    -------
    int
        Exit code suitable for ``sys.exit()``.
    """
    if not _PYSIDE6_AVAILABLE:
        print(
            "PySide6 is not installed.  Install the GUI extras with:\n"
            "    pip install 'windows-cleaner-utility[gui]'\n",
            file=sys.stderr,
        )
        return 1

    # Enable high-DPI scaling before creating the QApplication
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion(APP_VERSION)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Icon
    icon_path = Path(__file__).parent / "resources" / "icons" / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Stylesheet
    _load_stylesheet(app)

    # Logging
    log_dir = _app_data_dir() / "logs"
    _configure_logging(log_dir)

    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

    # Import the main window here (after QApplication is alive)
    from windows_cleaner_gui.views.main_window import MainWindow  # noqa: PLC0415

    window = MainWindow()
    window.show()

    return app.exec()
