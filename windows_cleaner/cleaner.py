"""
cleaner.py
----------
Core cleaning, repair, and optimisation routines for the Windows Cleaner
Utility.

This module contains the high-level operations that correspond to the menu
options in the original batch script:

1. :func:`clean_temporary_files` – Delete temp files, caches, and crash dumps.
2. :func:`repair_windows_image`  – Run SFC and DISM to scan/repair Windows.
3. :func:`flush_dns_cache`       – Release/renew IP and flush DNS.
4. :func:`enable_ultimate_performance` – Enable the Ultimate Performance power
   plan via ``powercfg``.

Each function is designed to be called independently and contains its own
error handling and logging.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

from windows_cleaner.utils import delete_files, expand_env, run_command

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Temporary file glob patterns
# (mirrors the ``del`` commands in the original .bat :clear section)
# ---------------------------------------------------------------------------
TEMP_FILE_PATTERNS: List[str] = [
    # Recycle Bin
    "%SYSTEMDRIVE%\\$Recycle.bin\\*",
    # PowerShell ReadLine history
    "%APPDATA%\\Microsoft\\Windows\\PowerShell\\PSReadLine\\*.*",
    # Thumbnail caches
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\*.db",
    # Windows Update download cache
    "C:\\Windows\\SoftwareDistribution\\Download\\*",
    # General temp folders
    "%TEMP%\\*.*",
    "%WINDIR%\\Temp\\*.*",
    # Memory / crash dumps
    "%SYSTEMROOT%\\memory.dmp",
    "%SYSTEMROOT%\\Minidump\\*.*",
    # Application crash dumps
    "%LOCALAPPDATA%\\CrashDumps\\*.*",
    # Prefetch
    "%WINDIR%\\Prefetch\\*.*",
    # Windows Caches
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Caches\\*.*",
    # Windows Error Reporting temp
    "%PROGRAMDATA%\\Microsoft\\Windows\\WER\\Temp\\*.*",
    # LocalLow temp
    "%HOMEPATH%\\AppData\\LocalLow\\Temp\\*.*",
    # Miscellaneous
    "%SYSTEMDRIVE%\\*.tmp",
    "%USERPROFILE%\\cookies\\*.*",
]

LOG_FILE_PATTERNS: List[str] = [
    "%SYSTEMDRIVE%\\*.log",
    "%SYSTEMDRIVE%\\*.old",
    "%SYSTEMDRIVE%\\*.trace",
    "%WINDIR%\\*.bak",
    "%WINDIR%\\Logs\\CBS\\CbsPersist\\*.log",
    "%WINDIR%\\Logs\\MoSetup\\*.log",
    "%WINDIR%\\Panther\\*.log",
    "%WINDIR%\\Logs\\*.log",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache\\*.log",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\INetCache\\*.log",
]

DRIVER_FILE_PATTERNS: List[str] = [
    "%SYSTEMDRIVE%\\AMD\\*.*",
    "%SYSTEMDRIVE%\\NVIDIA\\*.*",
    "%SYSTEMDRIVE%\\INTEL\\*.*",
]

DEFENDER_PATTERNS: List[str] = [
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Network Inspection System\\Support\\*.log",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\CacheManager",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\ReportLatency\\Latency",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\Service\\*.log",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\MetaStore",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Support",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\Results\\Quick",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\Results\\Resource",
]

# ---------------------------------------------------------------------------
# Ultimate Performance power-plan GUIDs
# ---------------------------------------------------------------------------
_UP_SOURCE_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"
_UP_TARGET_GUID = "95533644-e700-4a79-a56c-a89e8cb109d9"


def _stop_service(service_name: str) -> None:
    """Stop a Windows service, suppressing errors.

    Parameters
    ----------
    service_name : str
        The short service name (e.g. ``"wuauserv"``).
    """
    logger.info("Stopping service: %s", service_name)
    run_command(["net", "stop", service_name], capture_output=True)


def _start_service(service_name: str) -> None:
    """Start a Windows service, suppressing errors.

    Parameters
    ----------
    service_name : str
        The short service name (e.g. ``"wuauserv"``).
    """
    logger.info("Starting service: %s", service_name)
    run_command(["net", "start", service_name], capture_output=True)


def _restart_explorer() -> None:
    """Kill and restart ``explorer.exe``."""
    logger.info("Restarting explorer.exe …")
    run_command(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
    print("You will need to restart the PC to finish rebuilding your icon cache.")
    run_command(["start", "explorer.exe"], shell=True, capture_output=True)


def _clear_event_logs() -> None:
    """Clear all Windows Event Log channels.

    Enumerates log names via ``wevtutil el`` and then calls
    ``wevtutil cl <name>`` for each one.  Errors are suppressed so that
    protected logs (e.g. Security) do not abort the operation.
    """
    logger.info("Clearing Windows Event Logs …")
    try:
        result = run_command(
            ["wevtutil", "el"], capture_output=True, check=True
        )
        log_names = result.stdout.strip().splitlines()
        for log_name in log_names:
            log_name = log_name.strip()
            if log_name:
                try:
                    run_command(
                        ["wevtutil", "cl", log_name],
                        capture_output=True,
                    )
                    logger.debug("Cleared event log: %s", log_name)
                except (subprocess.CalledProcessError, PermissionError, OSError) as exc:
                    logger.debug("Could not clear event log %s: %s", log_name, exc)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        logger.warning("Could not enumerate event logs: %s", exc)


def check_temp_files_exist() -> bool:
    """Check whether any temporary files exist in ``%TEMP%``.

    Returns
    -------
    bool
        ``True`` if at least one file or directory is present in the temp
        directory, ``False`` otherwise.

    Examples
    --------
    >>> from windows_cleaner.cleaner import check_temp_files_exist
    >>> isinstance(check_temp_files_exist(), bool)
    True
    """
    temp_dir = Path(expand_env("%TEMP%"))
    if not temp_dir.exists():
        return False
    try:
        return any(True for _ in temp_dir.iterdir())
    except PermissionError:
        logger.warning("Permission denied reading %TEMP%; assuming files exist.")
        return True


def clean_temporary_files() -> Dict[str, int]:
    """Delete temporary files, caches, logs, and driver remnants.

    Performs the following operations in order:

    1. Stop ``cleanmgr`` / autoclean.
    2. Delete temp files (see :data:`TEMP_FILE_PATTERNS`).
    3. Restart Explorer to rebuild icon / thumbnail caches.
    4. Stop Windows Update service, clear its download cache, restart it.
    5. Delete log files (see :data:`LOG_FILE_PATTERNS`).
    6. Clear Windows Event Logs.
    7. Delete remnant driver files (AMD/NVIDIA/Intel).
    8. Delete Windows Defender logs/caches.

    Returns
    -------
    dict
        A mapping of category name → number of files deleted.  Keys are:
        ``"temp"``, ``"logs"``, ``"drivers"``, ``"defender"``.

    Raises
    ------
    RuntimeError
        If a critical sub-operation fails and cannot be recovered.

    Examples
    --------
    >>> # Smoke-test: function returns a dict (files deleted may be 0 on Linux)
    >>> from windows_cleaner.cleaner import clean_temporary_files
    >>> result = clean_temporary_files()
    >>> isinstance(result, dict)
    True
    >>> all(k in result for k in ("temp", "logs", "drivers", "defender"))
    True
    """
    stats: Dict[str, int] = {
        "temp": 0,
        "logs": 0,
        "drivers": 0,
        "defender": 0,
    }

    print("[Cleaning] Temporary Files …")
    logger.info("Starting temporary file cleanup …")

    # --- Disk Cleanup ---
    if sys.platform == "win32":
        run_command(["cleanmgr", "/autoclean"], capture_output=True)
        run_command(
            ["dism", "/online", "/cleanup-image", "/analyzecomponentstore"],
            capture_output=True,
        )
        run_command(
            ["dism", "/online", "/cleanup-image", "/startcomponentcleanup"],
            capture_output=True,
        )

    # --- Temp files ---
    stats["temp"] = delete_files(TEMP_FILE_PATTERNS)
    logger.info("Deleted %d temporary files.", stats["temp"])

    # --- Restart Explorer (icon/thumbnail cache rebuild) ---
    if sys.platform == "win32":
        _restart_explorer()

    # --- Windows Update cache ---
    if sys.platform == "win32":
        _stop_service("wuauserv")
        delete_files(["C:\\Windows\\SoftwareDistribution\\Download\\*"])
        _start_service("wuauserv")

    # --- Log files ---
    print("[Cleaning] Log Files …")
    logger.info("Cleaning log files …")
    stats["logs"] = delete_files(LOG_FILE_PATTERNS)
    logger.info("Deleted %d log files.", stats["logs"])

    # --- Event logs ---
    print("[Cleaning] Event Logs …")
    if sys.platform == "win32":
        _clear_event_logs()

    # --- Remnant driver files ---
    print("[Cleaning] Remnant Driver Files …")
    logger.info("Cleaning remnant driver files …")
    stats["drivers"] = delete_files(DRIVER_FILE_PATTERNS)
    logger.info("Deleted %d driver files.", stats["drivers"])

    # --- Windows Defender caches ---
    print("[Cleaning] Windows Defender Cache/Logs …")
    logger.info("Cleaning Windows Defender caches …")
    stats["defender"] = delete_files(DEFENDER_PATTERNS)
    logger.info("Deleted %d Defender files.", stats["defender"])

    total = sum(stats.values())
    logger.info("Cleanup complete. Total files deleted: %d", total)
    return stats


def repair_windows_image() -> bool:
    """Run SFC and DISM to scan and repair the Windows system image.

    Executes the following commands in sequence:

    1. ``sfc /scannow``
    2. ``DISM /Online /Cleanup-Image /CheckHealth``
    3. ``DISM /Online /Cleanup-Image /ScanHealth``
    4. ``DISM /Online /Cleanup-Image /RestoreHealth``

    Returns
    -------
    bool
        ``True`` if all commands completed without a non-zero exit code,
        ``False`` if any command reported a failure.

    Notes
    -----
    On non-Windows platforms the function logs a warning and returns ``False``
    immediately because these tools are not available.

    Examples
    --------
    >>> from windows_cleaner.cleaner import repair_windows_image
    >>> isinstance(repair_windows_image(), bool)
    True
    """
    if sys.platform != "win32":
        logger.warning("repair_windows_image() is only supported on Windows.")
        return False

    commands = [
        ["sfc", "/scannow"],
        ["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"],
        ["DISM", "/Online", "/Cleanup-Image", "/ScanHealth"],
        ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
    ]

    success = True
    for cmd in commands:
        logger.info("Running: %s", " ".join(cmd))
        result = run_command(cmd, capture_output=False)
        if result.returncode != 0:
            logger.error(
                "Command %s exited with code %d", " ".join(cmd), result.returncode
            )
            success = False

    if success:
        print("\nWindows Repaired Successfully!")
        logger.info("Windows image repair completed successfully.")
    else:
        logger.warning("One or more repair commands reported errors.")

    return success


def flush_dns_cache() -> bool:
    """Release/renew the IP address and flush the DNS resolver cache.

    Executes the following ``netsh`` / ``ipconfig`` commands:

    - ``ipconfig /release``
    - ``ipconfig /renew``
    - ``ipconfig /flushdns``
    - ``netsh int ip reset``
    - ``netsh winsock reset``
    - ``netsh interface ipv4 reset``
    - ``netsh interface ipv6 reset``

    Returns
    -------
    bool
        ``True`` if all commands completed without error, ``False`` otherwise.

    Notes
    -----
    A system restart may be required for all changes to take effect.
    On non-Windows platforms this function logs a warning and returns ``False``.

    Examples
    --------
    >>> from windows_cleaner.cleaner import flush_dns_cache
    >>> isinstance(flush_dns_cache(), bool)
    True
    """
    if sys.platform != "win32":
        logger.warning("flush_dns_cache() is only supported on Windows.")
        return False

    commands = [
        ["ipconfig", "/release"],
        ["ipconfig", "/renew"],
        ["ipconfig", "/flushdns"],
        ["netsh", "int", "ip", "reset"],
        ["netsh", "winsock", "reset"],
        ["netsh", "interface", "ipv4", "reset"],
        ["netsh", "interface", "ipv6", "reset"],
    ]

    success = True
    print("[Cleaning] DNS Resolver Cache …")
    for cmd in commands:
        logger.info("Running: %s", " ".join(cmd))
        result = run_command(cmd, capture_output=True)
        if result.returncode != 0:
            logger.warning(
                "Command %s exited with code %d (may be normal)",
                " ".join(cmd),
                result.returncode,
            )
            success = False

    if success:
        logger.info("DNS cache flushed successfully.")
    return success


def enable_ultimate_performance() -> bool:
    """Enable the Ultimate Performance power plan via ``powercfg``.

    Duplicates the built-in Ultimate Performance scheme to a custom GUID and
    then sets it as the active power plan.  This matches the ``powercfg``
    commands in the original batch script.

    Returns
    -------
    bool
        ``True`` if both ``powercfg`` commands succeeded, ``False`` otherwise.

    Notes
    -----
    On non-Windows platforms the function logs a warning and returns ``False``.

    Examples
    --------
    >>> from windows_cleaner.cleaner import enable_ultimate_performance
    >>> isinstance(enable_ultimate_performance(), bool)
    True
    """
    if sys.platform != "win32":
        logger.warning("enable_ultimate_performance() is only supported on Windows.")
        return False

    print("[Enabling] Ultimate Performance Mode …")
    logger.info("Enabling Ultimate Performance power plan …")

    result1 = run_command(
        [
            "powercfg",
            "-duplicatescheme",
            _UP_SOURCE_GUID,
            _UP_TARGET_GUID,
        ],
        capture_output=True,
    )
    result2 = run_command(
        ["powercfg", "-setactive", _UP_TARGET_GUID],
        capture_output=True,
    )

    success = result1.returncode == 0 and result2.returncode == 0
    if success:
        print("Successfully Enabled Ultimate Performance Mode!")
        logger.info("Ultimate Performance Mode enabled.")
    else:
        logger.warning("Could not enable Ultimate Performance Mode.")
    return success
