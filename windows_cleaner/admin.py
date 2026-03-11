"""
admin.py
--------
Handles administrator/UAC privilege checking and elevation on Windows.

This module provides functions to:
- Detect whether the current process has administrator privileges.
- Re-launch the current script with elevated (admin) privileges via UAC if needed.
"""

import ctypes
import logging
import os
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """Check whether the current process is running with administrator privileges.

    Uses the Windows API ``IsUserAnAdmin`` via ``ctypes`` to detect privilege
    level.  On non-Windows platforms the function always returns ``False`` so
    that unit tests can run without modification.

    Returns
    -------
    bool
        ``True`` if the process has administrator rights, ``False`` otherwise.

    Examples
    --------
    >>> from windows_cleaner.admin import is_admin
    >>> isinstance(is_admin(), bool)
    True
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except AttributeError:
        # Not on Windows (e.g. running unit tests on Linux/macOS)
        logger.debug("ctypes.windll not available – assuming non-admin environment.")
        return False


def request_elevation(script_path: Optional[str] = None) -> None:
    """Re-launch the current script with elevated privileges via UAC.

    This function uses the ``ShellExecuteW`` API to ask Windows to re-launch
    the Python interpreter (or the given *script_path*) as an administrator.
    After the elevated process is spawned the current (non-elevated) process
    exits immediately.

    Parameters
    ----------
    script_path : str, optional
        Absolute path of the Python script to run elevated.  When omitted,
        ``sys.argv[0]`` is used.

    Raises
    ------
    OSError
        If the ``ShellExecuteW`` call fails (e.g. the user clicked *No* in the
        UAC prompt).

    Notes
    -----
    The function is a no-op on non-Windows platforms; a warning is logged
    instead so that tests do not fail.

    Examples
    --------
    >>> # Dry-run: only verify the function is importable on non-Windows
    >>> from windows_cleaner.admin import request_elevation
    """
    if script_path is None:
        script_path = os.path.abspath(sys.argv[0])

    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    python_exe = sys.executable

    logger.info("Requesting administrative privileges for: %s", script_path)
    print("Requesting administrative privileges...")

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", python_exe, f'"{script_path}" {params}', None, 1
        )
        if result <= 32:  # ShellExecuteW returns <=32 on error
            raise OSError(f"ShellExecuteW failed with return code {result}")
    except AttributeError:
        logger.warning(
            "request_elevation() is only supported on Windows. "
            "Cannot re-launch with elevated privileges on this platform."
        )
        return

    sys.exit(0)


def ensure_admin() -> None:
    """Ensure the current process runs with administrator privileges.

    If the process already has admin rights, this function is a no-op.
    Otherwise it calls :func:`request_elevation` to spawn an elevated copy of
    the script and then exits the current (non-elevated) process.

    Examples
    --------
    >>> # Should not raise on any platform
    >>> # (will be a no-op because tests don't run as admin)
    """
    if not is_admin():
        logger.info("Not running as administrator. Requesting elevation...")
        request_elevation()
