"""
cleaner_service.py
------------------
Service layer that wraps the ``windows_cleaner`` backend package and exposes
a stable, minimal public API for use by the GUI layer.

All public methods are synchronous and safe to call from a worker thread.
Progress reporting is done via callback hooks so that callers can forward
updates to Qt signals without creating a circular dependency.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-import the backend so that this module can be imported on any platform
# (the heavy Windows-specific logic lives in the backend).
from windows_cleaner import cleaner, admin  # noqa: E402


class CleanerService:
    """Facade over the ``windows_cleaner`` backend.

    Parameters
    ----------
    progress_callback:
        Optional callable ``(step: int, total: int, message: str) -> None``
        invoked at each major step of an operation.
    cancelled_check:
        Optional callable ``() -> bool`` that returns ``True`` when the user
        has requested cancellation.  The service will check this between
        major steps and raise :exc:`OperationCancelledError` if set.
    """

    class OperationCancelledError(Exception):
        """Raised when the user cancels a running operation."""

    def __init__(
        self,
        progress_callback: Callable[[int, int, str], None] | None = None,
        cancelled_check: Callable[[], bool] | None = None,
    ) -> None:
        self._progress = progress_callback or (lambda *_: None)
        self._is_cancelled = cancelled_check or (lambda: False)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_cancel(self) -> None:
        if self._is_cancelled():
            raise self.OperationCancelledError("Operation cancelled by user.")

    def _report(self, step: int, total: int, message: str) -> None:
        self._progress(step, total, message)
        logger.debug("[%d/%d] %s", step, total, message)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def is_admin() -> bool:
        """Return ``True`` if the process has administrator privileges."""
        try:
            return admin.is_admin()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not determine admin status: %s", exc)
            return False

    @staticmethod
    def is_windows() -> bool:
        """Return ``True`` on Windows."""
        return sys.platform == "win32"

    def check_temp_files_exist(self) -> bool:
        """Check whether temporary files are present in ``%TEMP%``.

        Returns
        -------
        bool
            ``True`` when cleaning is likely to recover space.
        """
        try:
            return cleaner.check_temp_files_exist()
        except Exception as exc:  # noqa: BLE001
            logger.warning("check_temp_files_exist failed: %s", exc)
            return False

    def scan(self) -> dict[str, Any]:
        """Scan the system and return a summary of what would be cleaned.

        Returns
        -------
        dict
            ``{"temp_files_exist": bool, "platform": str,
               "is_admin": bool}``
        """
        self._report(0, 1, "Scanning system…")
        self._check_cancel()
        result = {
            "temp_files_exist": self.check_temp_files_exist(),
            "platform": sys.platform,
            "is_admin": self.is_admin(),
        }
        self._report(1, 1, "Scan complete.")
        return result

    def clean_temporary_files(self) -> dict[str, int]:
        """Delete temporary files and return a statistics dict.

        Returns
        -------
        dict
            ``{"temp": int, "logs": int, "drivers": int, "defender": int}``
        """
        self._report(0, 4, "Starting temporary file cleanup…")
        self._check_cancel()

        try:
            stats = cleaner.clean_temporary_files()
        except Exception as exc:  # noqa: BLE001
            logger.error("clean_temporary_files failed: %s", exc, exc_info=True)
            raise

        self._report(4, 4, "Temporary file cleanup complete.")
        return stats

    def repair_windows_image(self) -> bool:
        """Run SFC and DISM to repair the Windows image.

        Returns
        -------
        bool
            ``True`` if all commands succeeded.
        """
        steps = ["Preparing…", "Running SFC…", "Running DISM check…", "Restoring health…"]
        for i, msg in enumerate(steps):
            self._report(i, len(steps), msg)
            self._check_cancel()

        try:
            success = cleaner.repair_windows_image()
        except Exception as exc:  # noqa: BLE001
            logger.error("repair_windows_image failed: %s", exc, exc_info=True)
            raise

        self._report(len(steps), len(steps), "Repair complete.")
        return success

    def flush_dns_cache(self) -> bool:
        """Flush the DNS resolver cache and reset network stacks.

        Returns
        -------
        bool
            ``True`` if all commands succeeded.
        """
        self._report(0, 3, "Releasing IP address…")
        self._check_cancel()
        self._report(1, 3, "Flushing DNS cache…")
        self._check_cancel()

        try:
            success = cleaner.flush_dns_cache()
        except Exception as exc:  # noqa: BLE001
            logger.error("flush_dns_cache failed: %s", exc, exc_info=True)
            raise

        self._report(3, 3, "DNS flush complete.")
        return success

    def enable_ultimate_performance(self) -> bool:
        """Enable the Ultimate Performance power plan.

        Returns
        -------
        bool
            ``True`` if the power plan was activated successfully.
        """
        self._report(0, 2, "Activating Ultimate Performance power plan…")
        self._check_cancel()

        try:
            success = cleaner.enable_ultimate_performance()
        except Exception as exc:  # noqa: BLE001
            logger.error("enable_ultimate_performance failed: %s", exc, exc_info=True)
            raise

        self._report(2, 2, "Power plan change complete.")
        return success
