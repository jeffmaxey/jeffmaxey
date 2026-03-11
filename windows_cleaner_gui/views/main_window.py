"""
main_window.py
--------------
Main application window for the Windows Cleaner GUI.

Layout
~~~~~~
::

    ┌──────────────────────────────────────────────┐
    │  Title bar                                    │
    ├──────────┬───────────────────────────────────┤
    │          │                                   │
    │ Sidebar  │      Page stack (stacked widget)  │
    │ nav      │                                   │
    │          │                                   │
    ├──────────┴───────────────────────────────────┤
    │  Status bar                                  │
    └──────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, QByteArray
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QListWidget,
        QListWidgetItem,
        QStackedWidget,
        QStatusBar,
        QLabel,
        QSizePolicy,
        QMessageBox,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QMainWindow = object  # type: ignore[assignment,misc]

from windows_cleaner_gui import __version__
from windows_cleaner_gui.services.settings_service import SettingsService
from windows_cleaner_gui.services.cleaner_service import CleanerService

logger = logging.getLogger(__name__)

# Nav item labels
_NAV_ITEMS = [
    ("🔍  Scan",      "scan"),
    ("🧹  Clean",     "clean"),
    ("📊  Results",   "results"),
    ("⚙️   Settings",  "settings"),
    ("📋  Logs",      "logs"),
    ("ℹ️   About",     "about"),
]

WINDOW_TITLE = f"Windows Cleaner  v{__version__}"
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 620


class MainWindow(QMainWindow):  # type: ignore[misc]
    """Top-level application window with sidebar navigation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)

        self._settings = SettingsService()
        self._cleaner_svc = CleanerService()

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._build_ui()
        self._build_menu_bar()
        self._restore_geometry()

        # Show admin warning once
        if self._settings.show_admin_warning and not self._cleaner_svc.is_admin():
            self._show_admin_warning()

        # Auto-scan
        if self._settings.auto_scan_on_start:
            self._navigate_to("scan")
            self._scan_page.start_scan()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = self._build_sidebar()
        layout.addWidget(self._sidebar)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._stack)

        # Create pages (lazy-imported to keep startup fast)
        self._pages: dict[str, QWidget] = {}
        self._create_pages()

        # Status bar
        self._status_label = QLabel("Ready")
        status_bar: QStatusBar = self.statusBar()
        status_bar.addPermanentWidget(self._status_label)

        # Select first nav item
        self._nav_list.setCurrentRow(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App name header
        header = QLabel(f"  Windows\n  Cleaner")
        header.setObjectName("sidebarHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        # Navigation list
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        self._nav_list.setFrameShape(QListWidget.Shape.NoFrame)
        for label, key in _NAV_ITEMS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._nav_list.addItem(item)
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self._nav_list)
        layout.addStretch()

        # Version label at the bottom
        ver_label = QLabel(f"  v{__version__}")
        ver_label.setObjectName("sidebarVersion")
        layout.addWidget(ver_label)

        return sidebar

    def _create_pages(self) -> None:
        from windows_cleaner_gui.views.scan_page import ScanPage
        from windows_cleaner_gui.views.clean_page import CleanPage
        from windows_cleaner_gui.views.results_page import ResultsPage
        from windows_cleaner_gui.views.settings_page import SettingsPage
        from windows_cleaner_gui.views.logs_page import LogsPage
        from windows_cleaner_gui.views.about_page import AboutPage

        page_classes = {
            "scan": ScanPage,
            "clean": CleanPage,
            "results": ResultsPage,
            "settings": SettingsPage,
            "logs": LogsPage,
            "about": AboutPage,
        }

        for key, cls in page_classes.items():
            try:
                if key in ("scan", "clean"):
                    page = cls(settings=self._settings)
                elif key == "settings":
                    page = cls(settings=self._settings)
                else:
                    page = cls()
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to create page %r: %s", key, exc, exc_info=True)
                page = QLabel(f"Error loading page:\n{exc}")

            self._pages[key] = page
            self._stack.addWidget(page)

        # Keep typed references for convenience
        self._scan_page = self._pages.get("scan")
        self._results_page = self._pages.get("results")

        # Wire scan results to results page
        if hasattr(self._scan_page, "scan_completed"):
            self._scan_page.scan_completed.connect(self._on_scan_complete)

        # Wire clean results to results page
        clean_page = self._pages.get("clean")
        if clean_page and hasattr(clean_page, "operation_completed"):
            clean_page.operation_completed.connect(self._on_operation_complete)

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(lambda: self._navigate_to("about"))
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_nav_changed(self, row: int) -> None:
        if row < 0 or row >= len(_NAV_ITEMS):
            return
        _, key = _NAV_ITEMS[row]
        self._navigate_to(key)

    def _navigate_to(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            return
        self._stack.setCurrentWidget(page)
        # Update nav selection
        for i, (_, k) in enumerate(_NAV_ITEMS):
            if k == key:
                self._nav_list.setCurrentRow(i)
                break
        logger.debug("Navigated to page: %s", key)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_scan_complete(self, scan_data: dict) -> None:
        if self._results_page and hasattr(self._results_page, "show_scan_results"):
            self._results_page.show_scan_results(scan_data)

    def _on_operation_complete(self, operation: str, data: object) -> None:
        if self._results_page and hasattr(self._results_page, "show_operation_results"):
            self._results_page.show_operation_results(operation, data)
        self._navigate_to("results")
        self.set_status(f"Operation '{operation}' completed.")

    def set_status(self, message: str) -> None:
        """Update the status bar message."""
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        geo, state = self._settings.load_geometry()
        if geo:
            self.restoreGeometry(QByteArray(geo))
        if state:
            self.restoreState(QByteArray(state))

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._settings.save_geometry(
            bytes(self.saveGeometry()),
            bytes(self.saveState()),
        )
        logger.info("Application closing.")
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_admin_warning(self) -> None:
        QMessageBox.warning(
            self,
            "Administrator Privileges Required",
            "Windows Cleaner is not running with administrator privileges.\n\n"
            "Some cleaning and repair operations require elevated rights.  "
            "Please restart the application as Administrator for full functionality.",
        )
