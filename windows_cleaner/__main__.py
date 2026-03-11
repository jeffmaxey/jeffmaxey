"""
__main__.py
-----------
Entry point for ``python -m windows_cleaner``.

Configures logging, checks for administrator privileges, and launches the
interactive menu.

Usage
-----
Run directly (no admin check bypassed)::

    python -m windows_cleaner

Run with verbose debug output::

    python -m windows_cleaner --debug

Run without requesting UAC elevation (useful for testing)::

    python -m windows_cleaner --no-admin-check
"""

import argparse
import logging
import sys

from windows_cleaner import __version__
from windows_cleaner.admin import ensure_admin, is_admin
from windows_cleaner.menu import run_menu_loop
from windows_cleaner.utils import enable_ansi_on_windows


def _configure_logging(debug: bool = False) -> None:
    """Set up the root logger with file and console handlers.

    Parameters
    ----------
    debug : bool
        When ``True`` the console handler emits DEBUG-level messages; otherwise
        only INFO and above are shown.
    """
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s – %(message)s"

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt))
    root.addHandler(console)

    # File handler (always DEBUG)
    try:
        fh = logging.FileHandler("windows_cleaner.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(fmt))
        root.addHandler(fh)
    except OSError as exc:
        logging.warning("Could not open log file: %s", exc)


def main() -> None:
    """Parse arguments, configure logging, check admin rights, then run the menu.

    This is the public entry point called by ``__main__.py`` and by the
    ``windows-cleaner`` console script defined in ``pyproject.toml``.
    """
    parser = argparse.ArgumentParser(
        prog="windows-cleaner",
        description="Windows Cleaner Utility – A Python port of the Chainski Tools batch script.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable verbose debug logging to stderr.",
    )
    parser.add_argument(
        "--no-admin-check",
        dest="no_admin_check",
        action="store_true",
        default=False,
        help="Skip the administrator privilege check (useful for testing).",
    )
    args = parser.parse_args()

    _configure_logging(debug=args.debug)
    logger = logging.getLogger(__name__)

    logger.info("Windows Cleaner Utility v%s starting …", __version__)

    enable_ansi_on_windows()

    if not args.no_admin_check:
        if not is_admin():
            logger.info("Not running as administrator – requesting elevation …")
            ensure_admin()
        else:
            logger.info("Running as administrator.")
    else:
        logger.debug("Admin check skipped (--no-admin-check flag).")

    run_menu_loop()


if __name__ == "__main__":
    main()
