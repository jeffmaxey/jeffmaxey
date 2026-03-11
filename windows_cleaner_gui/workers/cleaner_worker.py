"""
cleaner_worker.py
-----------------
QThread-based worker that executes ``CleanerService`` operations off the
UI thread and reports progress / results / errors back via Qt signals.

Usage::

    worker = CleanerWorker(operation="clean_temp", service=svc)
    worker.progress.connect(my_slot)
    worker.result.connect(on_result)
    worker.error.connect(on_error)
    worker.start()
    # later:
    worker.cancel()
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from PySide6.QtCore import QThread, Signal

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover – tested without Qt
    QThread = object  # type: ignore[assignment,misc]

    class Signal:  # type: ignore[no-redef]
        def __init__(self, *args: Any) -> None:
            pass

        def connect(self, *args: Any) -> None:
            pass

        def emit(self, *args: Any) -> None:
            pass

    _PYSIDE6_AVAILABLE = False

from windows_cleaner_gui.services.cleaner_service import CleanerService

logger = logging.getLogger(__name__)

# Supported operation identifiers
OPERATIONS = {
    "scan",
    "clean_temp",
    "repair",
    "flush_dns",
    "ultimate_perf",
}


class CleanerWorker(QThread):  # type: ignore[misc]
    """Background worker for a single cleaner operation.

    Signals
    -------
    progress(step: int, total: int, message: str)
        Emitted at each major processing step.
    result(operation: str, data: object)
        Emitted once with the operation result when it completes successfully.
    error(operation: str, message: str)
        Emitted when the operation raises an exception.
    finished_with_status(operation: str, success: bool)
        Emitted on completion (success or failure) after result/error.
    """

    progress: Signal = Signal(int, int, str)
    result: Signal = Signal(str, object)
    error: Signal = Signal(str, str)
    finished_with_status: Signal = Signal(str, bool)

    def __init__(self, operation: str, parent: Any = None) -> None:
        if operation not in OPERATIONS:
            raise ValueError(f"Unknown operation: {operation!r}.  Must be one of {OPERATIONS}.")
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._operation = operation
        self._cancelled = False
        self._service: CleanerService | None = None

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Request cancellation; the worker stops between steps."""
        self._cancelled = True
        logger.info("Cancellation requested for operation: %s", self._operation)

    def _is_cancelled(self) -> bool:
        return self._cancelled

    # ------------------------------------------------------------------
    # Thread body
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: PLR0912
        """Execute the requested operation on the worker thread."""
        self._service = CleanerService(
            progress_callback=self._on_progress,
            cancelled_check=self._is_cancelled,
        )
        success = False
        try:
            data = self._dispatch()
            self.result.emit(self._operation, data)
            success = True
        except CleanerService.OperationCancelledError:
            logger.info("Operation %s was cancelled.", self._operation)
            self.error.emit(self._operation, "Operation cancelled by user.")
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Operation %s failed: %s", self._operation, exc, exc_info=True
            )
            self.error.emit(self._operation, str(exc))
        finally:
            self.finished_with_status.emit(self._operation, success)

    def _on_progress(self, step: int, total: int, message: str) -> None:
        self.progress.emit(step, total, message)

    def _dispatch(self) -> Any:
        """Call the appropriate service method for the current operation."""
        svc = self._service
        assert svc is not None
        if self._operation == "scan":
            return svc.scan()
        if self._operation == "clean_temp":
            return svc.clean_temporary_files()
        if self._operation == "repair":
            return svc.repair_windows_image()
        if self._operation == "flush_dns":
            return svc.flush_dns_cache()
        if self._operation == "ultimate_perf":
            return svc.enable_ultimate_performance()
        raise ValueError(f"Unhandled operation: {self._operation!r}")  # pragma: no cover
