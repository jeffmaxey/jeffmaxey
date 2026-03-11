"""
logs_page.py
------------
Live log-viewer panel that subscribes to the Qt log bridge in ``app.py``
and renders log entries in a filterable, scrollable text view.
"""

from __future__ import annotations

import logging

try:
    from PySide6.QtCore import Qt, Slot
    from PySide6.QtGui import QColor, QTextCursor
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QComboBox,
        QFrame,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "#8888aa",
    logging.INFO: "#cccccc",
    logging.WARNING: "#ffcc00",
    logging.ERROR: "#ff4444",
    logging.CRITICAL: "#ff0000",
}

_MAX_LINES = 2000


class LogsPage(QWidget):  # type: ignore[misc]
    """Real-time scrollable log viewer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._min_level = logging.DEBUG
        self._build_ui()
        self._register_handler()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Application Logs")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Filter level:"))
        self._level_combo = QComboBox()
        self._level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.setCurrentText("DEBUG")
        self._level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(self._level_combo)
        toolbar.addStretch()

        clear_btn = QPushButton("🗑  Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)
        layout.addLayout(toolbar)

        # Log text area
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setObjectName("logOutput")
        self._log_view.document().setMaximumBlockCount(_MAX_LINES)
        layout.addWidget(self._log_view)

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def _register_handler(self) -> None:
        """Subscribe to the Qt log bridge from app.py."""
        try:
            from windows_cleaner_gui.app import _QtLogHandler  # noqa: PLC0415
            _QtLogHandler.add_listener(self._append_log)
        except Exception:  # noqa: BLE001
            pass

    def _unregister_handler(self) -> None:
        try:
            from windows_cleaner_gui.app import _QtLogHandler  # noqa: PLC0415
            _QtLogHandler.remove_listener(self._append_log)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_level_changed(self, level_name: str) -> None:
        self._min_level = getattr(logging, level_name, logging.DEBUG)

    def _append_log(self, level: int, message: str) -> None:
        if level < self._min_level:
            return
        color = _LEVEL_COLORS.get(level, "#cccccc")
        html = f'<span style="color:{color}; font-family:monospace; font-size:12px;">{self._escape(message)}</span>'
        self._log_view.append(html)
        # Auto-scroll
        cursor = self._log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_view.setTextCursor(cursor)

    def _clear(self) -> None:
        self._log_view.clear()

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def hideEvent(self, event) -> None:  # type: ignore[override]
        super().hideEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._unregister_handler()
        super().closeEvent(event)
