"""
scan_page.py
------------
Scan / Analyse page – checks the system for files that can be cleaned and
presents a summary before the user starts a full clean.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QProgressBar,
        QGroupBox,
        QFormLayout,
        QFrame,
        QSizePolicy,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]
    Signal = object  # type: ignore[assignment]

from windows_cleaner_gui.services.settings_service import SettingsService
from windows_cleaner_gui.workers.cleaner_worker import CleanerWorker

logger = logging.getLogger(__name__)


class ScanPage(QWidget):  # type: ignore[misc]
    """Page that runs a background scan and summarises findings."""

    scan_completed = Signal(dict)

    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._settings = settings
        self._worker: CleanerWorker | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Page title
        title = QLabel("System Scan")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Analyse your system to discover temporary files, caches, and "
            "other junk that can be safely removed."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # Results group
        results_group = QGroupBox("Scan Results")
        results_layout = QFormLayout(results_group)
        results_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._temp_label = QLabel("–")
        self._admin_label = QLabel("–")
        self._platform_label = QLabel("–")
        results_layout.addRow("Temporary files found:", self._temp_label)
        results_layout.addRow("Administrator privileges:", self._admin_label)
        results_layout.addRow("Platform:", self._platform_label)
        layout.addWidget(results_group)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # indeterminate
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._scan_btn = QPushButton("🔍  Start Scan")
        self._scan_btn.setObjectName("primaryButton")
        self._scan_btn.setFixedHeight(40)
        self._scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self._scan_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Scan logic
    # ------------------------------------------------------------------

    def start_scan(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self._scan_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._status_label.setText("Scanning…")

        self._worker = CleanerWorker("scan")
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.finished_with_status.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, step: int, total: int, message: str) -> None:
        self._status_label.setText(message)

    def _on_result(self, operation: str, data: Any) -> None:
        if not isinstance(data, dict):
            return
        temp_found = data.get("temp_files_exist", False)
        is_admin = data.get("is_admin", False)
        platform = data.get("platform", "unknown")

        self._temp_label.setText("✅  Yes – cleaning recommended" if temp_found else "✔  None found")
        self._admin_label.setText("✅  Yes" if is_admin else "⚠️  No – some operations may fail")
        self._platform_label.setText(platform)

        self.scan_completed.emit(data)
        logger.info("Scan complete: %s", data)

    def _on_error(self, operation: str, message: str) -> None:
        self._status_label.setText(f"Error: {message}")
        logger.error("Scan error: %s", message)

    def _on_finished(self, operation: str, success: bool) -> None:
        self._progress_bar.setVisible(False)
        self._scan_btn.setEnabled(True)
        if success:
            self._status_label.setText("Scan complete.")
