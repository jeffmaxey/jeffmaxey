"""
clean_page.py
-------------
Clean page – lets the user select which operations to run and monitors
progress with a live progress bar and log output.  Operations run
off the UI thread via ``CleanerWorker``.
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
        QCheckBox,
        QTextEdit,
        QFrame,
        QSizePolicy,
        QMessageBox,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]
    Signal = object  # type: ignore[assignment]

from windows_cleaner_gui.services.settings_service import SettingsService
from windows_cleaner_gui.workers.cleaner_worker import CleanerWorker

logger = logging.getLogger(__name__)

# (label, worker operation key, tooltip)
_OPERATIONS = [
    ("Clean Temporary Files", "clean_temp", "Removes %TEMP%, caches, crash dumps, Defender logs…"),
    ("Repair Windows Image (SFC/DISM)", "repair", "Runs sfc /scannow and DISM restore health (Windows only)"),
    ("Flush DNS Cache", "flush_dns", "Releases/renews IP and resets Winsock stacks (Windows only)"),
    ("Enable Ultimate Performance", "ultimate_perf", "Activates the Ultimate Performance power plan (Windows only)"),
]


class CleanPage(QWidget):  # type: ignore[misc]
    """Page for running individual or all cleaning operations."""

    operation_completed = Signal(str, object)

    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._settings = settings
        self._worker: CleanerWorker | None = None
        self._queue: list[str] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Clean System")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("Select the operations you want to run, then click Start Cleaning.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # Operation checkboxes
        ops_group = QGroupBox("Operations")
        ops_layout = QVBoxLayout(ops_group)
        self._checkboxes: dict[str, QCheckBox] = {}
        for label, key, tip in _OPERATIONS:
            cb = QCheckBox(label)
            cb.setToolTip(tip)
            cb.setChecked(key == "clean_temp")  # default: only temp files
            self._checkboxes[key] = cb
            ops_layout.addWidget(cb)
        layout.addWidget(ops_group)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready.")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # Live log output
        self._log_output = QTextEdit()
        self._log_output.setReadOnly(True)
        self._log_output.setObjectName("logOutput")
        self._log_output.setMaximumHeight(160)
        layout.addWidget(self._log_output)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("✖  Cancel")
        self._cancel_btn.setObjectName("dangerButton")
        self._cancel_btn.setFixedHeight(40)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)
        btn_layout.addWidget(self._cancel_btn)

        self._start_btn = QPushButton("🚀  Start Cleaning")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.setFixedHeight(40)
        self._start_btn.clicked.connect(self._start)
        btn_layout.addWidget(self._start_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def _start(self) -> None:
        selected = [k for k, cb in self._checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, "No Operations Selected", "Please select at least one operation to run.")
            return

        if self._settings.confirm_before_clean:
            key_to_label = {key: label for label, key, _ in _OPERATIONS}
            labels = "\n".join(f"  • {key_to_label.get(op, op)}" for op in selected)
            reply = QMessageBox.question(
                self,
                "Confirm Cleaning",
                f"The following operations will be performed:\n\n{labels}\n\nProceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._queue = list(selected)
        self._log_output.clear()
        self._progress_bar.setValue(0)
        self._run_next()

    def _run_next(self) -> None:
        if not self._queue:
            self._start_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._status_label.setText("All operations complete.")
            return

        operation = self._queue.pop(0)
        self._log(f"Starting: {operation}")
        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)

        self._worker = CleanerWorker(operation)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.finished_with_status.connect(self._on_finished)
        self._worker.start()

    def _cancel(self) -> None:
        self._queue.clear()
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("Cancellation requested…")

    # ------------------------------------------------------------------
    # Worker slots
    # ------------------------------------------------------------------

    def _on_progress(self, step: int, total: int, message: str) -> None:
        if total > 0:
            pct = int((step / total) * 100)
            self._progress_bar.setValue(pct)
        self._status_label.setText(message)
        self._log(message)

    def _on_result(self, operation: str, data: Any) -> None:
        self._log(f"✅ {operation} completed successfully.")
        self.operation_completed.emit(operation, data)

    def _on_error(self, operation: str, message: str) -> None:
        self._log(f"❌ Error in {operation}: {message}")
        self._status_label.setText(f"Error: {message}")

    def _on_finished(self, operation: str, success: bool) -> None:
        self._progress_bar.setValue(100 if success else self._progress_bar.value())
        self._run_next()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        self._log_output.append(message)
        logger.debug("[CleanPage] %s", message)
