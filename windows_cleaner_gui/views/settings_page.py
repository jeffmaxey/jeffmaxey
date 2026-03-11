"""
settings_page.py
----------------
Application settings page backed by ``SettingsService`` / ``QSettings``.
"""

from __future__ import annotations

import logging

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QGroupBox,
        QFormLayout,
        QCheckBox,
        QComboBox,
        QFrame,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]

from windows_cleaner_gui.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


class SettingsPage(QWidget):  # type: ignore[misc]
    """Settings editor page."""

    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._settings = settings
        self._build_ui()
        self._load()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # --- General group ---
        general_group = QGroupBox("General")
        general_form = QFormLayout(general_group)

        self._confirm_cb = QCheckBox("Ask for confirmation before cleaning")
        general_form.addRow("Confirm before clean:", self._confirm_cb)

        self._auto_scan_cb = QCheckBox("Automatically scan on startup")
        general_form.addRow("Auto-scan on start:", self._auto_scan_cb)

        self._admin_warn_cb = QCheckBox("Show warning when not running as Administrator")
        general_form.addRow("Admin warning:", self._admin_warn_cb)

        layout.addWidget(general_group)

        # --- Logging group ---
        log_group = QGroupBox("Logging")
        log_form = QFormLayout(log_group)

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(_LOG_LEVELS)
        log_form.addRow("Log level:", self._log_level_combo)

        layout.addWidget(log_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(reset_btn)

        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self) -> None:
        self._confirm_cb.setChecked(self._settings.confirm_before_clean)
        self._auto_scan_cb.setChecked(self._settings.auto_scan_on_start)
        self._admin_warn_cb.setChecked(self._settings.show_admin_warning)
        idx = self._log_level_combo.findText(self._settings.log_level)
        if idx >= 0:
            self._log_level_combo.setCurrentIndex(idx)

    def _save(self) -> None:
        self._settings.confirm_before_clean = self._confirm_cb.isChecked()
        self._settings.auto_scan_on_start = self._auto_scan_cb.isChecked()
        self._settings.show_admin_warning = self._admin_warn_cb.isChecked()
        self._settings.log_level = self._log_level_combo.currentText()
        logger.info("Settings saved.")

    def _reset(self) -> None:
        from windows_cleaner_gui.services.settings_service import DEFAULTS  # noqa: PLC0415
        self._settings.confirm_before_clean = bool(DEFAULTS["confirm_before_clean"])
        self._settings.auto_scan_on_start = bool(DEFAULTS["auto_scan_on_start"])
        self._settings.show_admin_warning = bool(DEFAULTS["show_admin_warning"])
        self._settings.log_level = str(DEFAULTS["log_level"])
        self._load()
        logger.info("Settings reset to defaults.")
