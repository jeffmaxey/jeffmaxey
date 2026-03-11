"""
results_page.py
---------------
Results view – displays the outcome of the most recent scan or cleaning
operation in a structured, human-readable form.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QFrame,
        QHeaderView,
        QSizePolicy,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class ResultsPage(QWidget):  # type: ignore[misc]
    """Displays results from the most recent operation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Results")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self._summary_label = QLabel("No results yet.  Run a Scan or a Clean operation first.")
        self._summary_label.setWordWrap(True)
        self._summary_label.setObjectName("pageSubtitle")
        layout.addWidget(self._summary_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # Results table
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Category", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_scan_results(self, data: dict[str, Any]) -> None:
        """Populate the table with scan result data."""
        self._summary_label.setText("Scan results:")
        rows = [
            ("Temporary files found", "Yes" if data.get("temp_files_exist") else "No"),
            ("Administrator privileges", "Yes" if data.get("is_admin") else "No"),
            ("Platform", str(data.get("platform", ""))),
        ]
        self._populate_table(rows)

    def show_operation_results(self, operation: str, data: Any) -> None:
        """Populate the table with operation result data."""
        label_map = {
            "clean_temp": "Clean Temporary Files",
            "repair": "Repair Windows Image",
            "flush_dns": "Flush DNS Cache",
            "ultimate_perf": "Enable Ultimate Performance",
            "scan": "System Scan",
        }
        op_label = label_map.get(operation, operation)

        if isinstance(data, dict):
            self._summary_label.setText(f"Results of: {op_label}")
            rows = [(k.replace("_", " ").title(), str(v)) for k, v in data.items()]
        elif isinstance(data, bool):
            self._summary_label.setText(f"Results of: {op_label}")
            rows = [("Success", "✅  Yes" if data else "❌  No")]
        else:
            self._summary_label.setText(f"Results of: {op_label}")
            rows = [("Result", str(data))]

        self._populate_table(rows)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _populate_table(self, rows: list[tuple[str, str]]) -> None:
        self._table.setRowCount(len(rows))
        for i, (cat, val) in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(cat))
            self._table.setItem(i, 1, QTableWidgetItem(val))
