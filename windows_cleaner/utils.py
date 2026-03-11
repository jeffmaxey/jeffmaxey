"""
utils.py
--------
Utility helpers shared across the Windows Cleaner Utility package.

Provides:
- Coloured/styled console output (ANSI escape codes).
- Banner / ASCII-art rendering.
- Safe subprocess execution with logging.
- Path expansion helpers.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ANSI colour constants (Windows 10+ with VT processing enabled)
# ---------------------------------------------------------------------------
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BOLD = "\033[1m"

# Banner text (matches the original .bat ASCII-art colour scheme)
BANNER = rf"""
{RED}╔╗╔╗╔╗╔══╗╔═╗ ╔╗╔═══╗╔═══╗╔╗╔╗╔╗╔═══╗{RESET}  {BLUE}╔═══╗╔╗   ╔═══╗╔═══╗╔═╗ ╔╗╔═══╗╔═══╗{RESET}
{RED}║║║║║║╚╣╠╝║║╚╗║║╚╗╔╗║║╔═╗║║║║║║║║╔═╗║{RESET}  {BLUE}║╔═╗║║║   ║╔══╝║╔═╗║║║╚╗║║║╔══╝║╔═╗║{RESET}
{RED}║║║║║║ ║║ ║╔╗╚╝║ ║║║║║║ ║║║║║║║║║╚══╗{RESET}  {BLUE}║║ ╚╝║║   ║╚══╗║║ ║║║╔╗╚╝║║╚══╗║╚═╝║{RESET}
{RED}║╚╝╚╝║ ║║ ║║╚╗║║ ║║║║║║ ║║║╚╝╚╝║╚══╗║{RESET}  {BLUE}║║ ╔╗║║ ╔╗║╔══╝║╚═╝║║║╚╗║║║╔══╝║╔╗╔╝{RESET}
{RED}╚╗╔╗╔╝╔╣╠╗║║ ║║║╔╝╚╝║║╚═╝║╚╗╔╗╔╝║╚═╝║{RESET}  {BLUE}║╚═╝║║╚═╝║║╚══╗║╔═╗║║║ ║║║║╚══╗║║║╚╗{RESET}
{RED} ╚╝╚╝ ╚══╝╚╝ ╚═╝╚═══╝╚═══╝ ╚╝╚╝ ╚═══╝{RESET}  {BLUE}╚═══╝╚═══╝╚═══╝╚╝ ╚╝╚╝ ╚═╝╚═══╝╚╝╚═╝{RESET}
"""

MENU_BOX = rf"""
{YELLOW}   ╔═════════════════════════════════╗
   ║     Windows Cleaner Utility     ║
   ║                                 ║
   ╚═════════════════════════════════╝{RESET}
"""


def enable_ansi_on_windows() -> None:
    """Enable ANSI escape-code processing on Windows 10+.

    On Windows the virtual-terminal (VT) processing mode must be explicitly
    enabled for the console handle.  This function is silently ignored on
    other platforms or older Windows versions that do not support VT sequences.

    Examples
    --------
    >>> from windows_cleaner.utils import enable_ansi_on_windows
    >>> enable_ansi_on_windows()  # no-op / no error on any OS
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import ctypes.wintypes

        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.wintypes.DWORD()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError) as exc:
        logger.debug("Could not enable ANSI on Windows: %s", exc)


def print_banner() -> None:
    """Print the Windows Cleaner Utility ASCII-art banner to stdout.

    Examples
    --------
    >>> from windows_cleaner.utils import print_banner
    >>> print_banner()  # outputs to stdout – no assertion needed
    """
    print(BANNER)
    print(MENU_BOX)


def clear_screen() -> None:
    """Clear the terminal screen.

    Uses ``cls`` on Windows and ``clear`` on POSIX systems.

    Examples
    --------
    >>> from windows_cleaner.utils import clear_screen
    >>> clear_screen()  # no error
    """
    os.system("cls" if sys.platform == "win32" else "clear")


def run_command(
    args: Union[str, Sequence[str]],
    *,
    shell: bool = False,
    capture_output: bool = False,
    check: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Run a system command and log the result.

    A thin wrapper around :func:`subprocess.run` that adds structured
    logging at DEBUG level so that all sub-process invocations are recorded in
    the application log.

    Parameters
    ----------
    args : str or list of str
        The command and its arguments.  Passed directly to
        :func:`subprocess.run`.
    shell : bool, optional
        If ``True`` the command is executed through the shell.  Defaults to
        ``False``.
    capture_output : bool, optional
        If ``True`` stdout and stderr are captured and returned in the result
        object instead of being printed to the terminal.  Defaults to
        ``False``.
    check : bool, optional
        If ``True`` a :class:`subprocess.CalledProcessError` is raised when
        the command exits with a non-zero return code.  Defaults to ``False``.
    timeout : int, optional
        Maximum number of seconds to wait for the command to finish.  Raises
        :class:`subprocess.TimeoutExpired` if exceeded.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process result, including *returncode*, *stdout*, and
        *stderr* when *capture_output* is ``True``.

    Raises
    ------
    subprocess.CalledProcessError
        If *check* is ``True`` and the process exits with a non-zero code.
    subprocess.TimeoutExpired
        If *timeout* is set and the command does not finish in time.
    FileNotFoundError
        If the executable cannot be found.

    Examples
    --------
    >>> from windows_cleaner.utils import run_command
    >>> result = run_command(["echo", "hello"], capture_output=True)
    >>> result.returncode
    0
    """
    cmd_str = args if isinstance(args, str) else " ".join(str(a) for a in args)
    logger.debug("Running command: %s", cmd_str)
    try:
        result = subprocess.run(
            args,
            shell=shell,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=check,
        )
        logger.debug(
            "Command finished with return code %d: %s", result.returncode, cmd_str
        )
        return result
    except subprocess.CalledProcessError as exc:
        logger.error("Command failed (rc=%d): %s", exc.returncode, cmd_str)
        raise
    except FileNotFoundError as exc:
        logger.error("Executable not found for command: %s – %s", cmd_str, exc)
        raise
    except subprocess.TimeoutExpired as exc:
        logger.error("Command timed out: %s", cmd_str)
        raise


def expand_env(path: str) -> str:
    """Expand environment variables and user home in *path*.

    Combines :func:`os.path.expandvars` and :func:`os.path.expanduser` so
    that paths like ``%TEMP%\\*.log`` or ``~/logs`` are resolved correctly.

    Parameters
    ----------
    path : str
        The path string to expand.

    Returns
    -------
    str
        The expanded absolute path.

    Examples
    --------
    >>> import os
    >>> from windows_cleaner.utils import expand_env
    >>> result = expand_env("%TEMP%")  # expands on Windows, no-op vars on Linux
    >>> isinstance(result, str)
    True
    """
    return os.path.expandvars(os.path.expanduser(path))


def delete_files(pattern_paths: Sequence[str], *, ignore_errors: bool = True) -> int:
    """Delete files matching glob patterns, returning the count of removed files.

    Each entry in *pattern_paths* is first expanded via :func:`expand_env` and
    then matched with :meth:`Path.glob`.  Deletion errors are logged at WARNING
    level and, when *ignore_errors* is ``True``, do not propagate.

    Parameters
    ----------
    pattern_paths : sequence of str
        Glob-style paths whose matching files should be deleted.  Supports
        ``**`` for recursive matching.
    ignore_errors : bool, optional
        When ``True`` (default) individual deletion failures are logged as
        warnings rather than raised.

    Returns
    -------
    int
        The total number of files successfully deleted.

    Examples
    --------
    >>> import tempfile, os
    >>> from pathlib import Path
    >>> from windows_cleaner.utils import delete_files
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     p = Path(tmpdir) / "test.tmp"
    ...     _ = p.write_text("x")
    ...     count = delete_files([str(p)])
    ...     count == 1
    True
    """
    deleted = 0
    for raw_pattern in pattern_paths:
        expanded = expand_env(raw_pattern)
        path = Path(expanded)

        # Determine parent and glob pattern
        if path.is_absolute() and not any(c in path.name for c in ("*", "?")):
            # Exact path – try to delete directly
            targets = [path]
        else:
            parent = path.parent
            name_pattern = path.name
            if not parent.exists():
                logger.debug("Skipping non-existent directory: %s", parent)
                continue
            targets = list(parent.glob(name_pattern))

        for target in targets:
            if target.is_file():
                try:
                    target.unlink()
                    deleted += 1
                    logger.debug("Deleted: %s", target)
                except PermissionError as exc:
                    if not ignore_errors:
                        raise
                    logger.warning("Permission denied deleting %s: %s", target, exc)
                except OSError as exc:
                    if not ignore_errors:
                        raise
                    logger.warning("Could not delete %s: %s", target, exc)
    return deleted


def open_url(url: str) -> None:
    """Open *url* in the default web browser.

    Uses :func:`webbrowser.open` so it works on Windows, macOS, and Linux.

    Parameters
    ----------
    url : str
        The URL to open.

    Examples
    --------
    >>> from windows_cleaner.utils import open_url
    >>> # Just verify the function is importable; don't open a real browser here
    """
    import webbrowser

    logger.info("Opening URL: %s", url)
    webbrowser.open(url)
