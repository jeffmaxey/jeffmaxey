"""
settings_service.py
-------------------
Thin wrapper around ``QSettings`` that provides typed access to all
persisted application preferences.

All settings use the ``Chainski / Windows Cleaner`` scope so they are
stored in the Windows registry (``HKCU\\\\Software\\\\Chainski\\\\Windows Cleaner``)
on Windows and in ``~/.config/Chainski/Windows Cleaner.ini`` elsewhere.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import QSettings

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "log_level": "INFO",
    "confirm_before_clean": True,
    "auto_scan_on_start": False,
    "show_admin_warning": True,
    "window_geometry": None,
    "window_state": None,
}


class SettingsService:
    """Typed façade over ``QSettings``.

    Instantiate once and share via dependency injection.
    When PySide6 is unavailable (e.g., in unit tests) the service falls
    back to a plain ``dict``.
    """

    def __init__(self) -> None:
        if _PYSIDE6_AVAILABLE:
            self._q = QSettings("Chainski", "Windows Cleaner")
        else:
            self._q = None  # type: ignore[assignment]
        self._cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Generic get / set
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the stored value for *key*, falling back to *default*."""
        if self._q is not None:
            val = self._q.value(key, DEFAULTS.get(key, default))
            # QSettings stores booleans as strings on some platforms
            if isinstance(DEFAULTS.get(key), bool) and isinstance(val, str):
                return val.lower() in ("true", "1", "yes")
            return val
        return self._cache.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        """Persist *value* for *key*."""
        if self._q is not None:
            self._q.setValue(key, value)
            self._q.sync()
        else:
            self._cache[key] = value

    # ------------------------------------------------------------------
    # Typed convenience accessors
    # ------------------------------------------------------------------

    @property
    def theme(self) -> str:
        return str(self.get("theme", "dark"))

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def log_level(self) -> str:
        return str(self.get("log_level", "INFO"))

    @log_level.setter
    def log_level(self, value: str) -> None:
        self.set("log_level", value)

    @property
    def confirm_before_clean(self) -> bool:
        return bool(self.get("confirm_before_clean", True))

    @confirm_before_clean.setter
    def confirm_before_clean(self, value: bool) -> None:
        self.set("confirm_before_clean", value)

    @property
    def auto_scan_on_start(self) -> bool:
        return bool(self.get("auto_scan_on_start", False))

    @auto_scan_on_start.setter
    def auto_scan_on_start(self, value: bool) -> None:
        self.set("auto_scan_on_start", value)

    @property
    def show_admin_warning(self) -> bool:
        return bool(self.get("show_admin_warning", True))

    @show_admin_warning.setter
    def show_admin_warning(self, value: bool) -> None:
        self.set("show_admin_warning", value)

    def save_geometry(self, geometry: bytes, state: bytes) -> None:
        """Persist the main-window geometry and dock/toolbar state."""
        self.set("window_geometry", geometry)
        self.set("window_state", state)

    def load_geometry(self) -> tuple[bytes | None, bytes | None]:
        """Return saved ``(geometry, state)`` bytes, or ``(None, None)``."""
        geo = self.get("window_geometry")
        state = self.get("window_state")
        return (
            bytes(geo) if geo is not None else None,
            bytes(state) if state is not None else None,
        )
