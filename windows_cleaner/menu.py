"""
menu.py
-------
Interactive menu for the Windows Cleaner Utility.

Provides a text-based menu that mirrors the ``choice`` commands in the
original batch script.  The menu loops until the user selects the *Exit*
option.
"""

import logging
import sys
from typing import Callable, Dict, List, NoReturn, Optional, Tuple

from windows_cleaner import __github__, __license__, __version__
from windows_cleaner.cleaner import (
    check_temp_files_exist,
    clean_temporary_files,
    enable_ultimate_performance,
    flush_dns_cache,
    repair_windows_image,
)
from windows_cleaner.utils import (
    BLUE,
    BOLD,
    CYAN,
    GREEN,
    RED,
    RESET,
    YELLOW,
    clear_screen,
    open_url,
    print_banner,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Menu option constants
# ---------------------------------------------------------------------------
OPT_CLEAN = "1"
OPT_REPAIR = "2"
OPT_INFO = "3"
OPT_GITHUB = "4"
OPT_EXIT = "5"

VALID_OPTIONS = (OPT_CLEAN, OPT_REPAIR, OPT_INFO, OPT_GITHUB, OPT_EXIT)


def _get_choice(prompt: str, valid: Tuple[str, ...] = VALID_OPTIONS) -> str:
    """Prompt the user for a single-character menu choice.

    Parameters
    ----------
    prompt : str
        The prompt string displayed to the user.
    valid : tuple of str
        Accepted option characters.

    Returns
    -------
    str
        The validated choice character entered by the user.
    """
    while True:
        try:
            choice = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            logger.info("User interrupted input – treating as Exit.")
            return OPT_EXIT

        if choice in valid:
            return choice
        print(f"{RED}Invalid option. Please press one of: {', '.join(valid)}{RESET}")


def show_main_menu() -> None:
    """Display the main menu banner and option list."""
    clear_screen()
    print_banner()
    print(
        f"{GREEN}Press a button from 1 to 5 – each of these buttons has its own "
        f"function as described below:{RESET}\n"
    )
    print(f"  {BOLD}{OPT_CLEAN}{RESET} - Delete the Temporary Files")
    print()
    print(f"  {BOLD}{OPT_REPAIR}{RESET} - Scan System And Repair Windows Image")
    print()
    print(f"  {BOLD}{OPT_INFO}{RESET} - Program and license information")
    print()
    print(f"  {BOLD}{OPT_GITHUB}{RESET} - Page on GitHub")
    print()
    print(f"  {BOLD}{OPT_EXIT}{RESET} - End session (will close the program)")
    print()


def _handle_clean() -> None:
    """Handle option 1: Delete Temporary Files."""
    clear_screen()

    if not check_temp_files_exist():
        print(
            f"{GREEN}Your PC doesn't need any cleaning – try again later.{RESET}"
        )
        logger.info("No temporary files found; skipping cleanup.")
        input("\nPress ENTER to return to the menu.")
        return

    print()
    print(
        f"{YELLOW}Your PC needs deep cleaning! Select an option below to continue.{RESET}\n"
    )
    print("  1 - Clear data and reclaim disk space.")
    print("      (This process may take several minutes – please be patient)")
    print("  2 - Stop and return to the menu.")
    print()

    choice = _get_choice("Enter choice [1/2]: ", ("1", "2"))
    if choice == "2":
        return

    while True:
        logger.info("Starting full temporary file cleanup …")
        stats = clean_temporary_files()

        # After cleaning, also flush DNS and enable Ultimate Performance
        flush_dns_cache()
        enable_ultimate_performance()

        total = sum(stats.values())

        # Check whether any files remain
        if check_temp_files_exist():
            print()
            print(
                f"{YELLOW}Unfortunately, we were unable to remove all of the "
                f"Temporary files (some are being used by other processes).{RESET}"
            )
            print(
                "You can manually open the Temporary Folders and try to "
                "delete the remaining files.\n"
            )
            print("  1 - Try again.")
            print("  2 - Return to the menu.")
            print()
            retry = _get_choice("Enter choice [1/2]: ", ("1", "2"))
            if retry == "2":
                return
            # else loop again
        else:
            print()
            print(
                f"{GREEN}Ready! Your computer has been cleared of unnecessary "
                f"temporary data! ({total} files removed){RESET}"
            )
            logger.info("Cleanup complete. %d files removed.", total)
            input("\nPress ENTER to return to the menu.")
            return


def _handle_repair() -> None:
    """Handle option 2: Scan System And Repair Windows Image."""
    clear_screen()
    logger.info("Starting Windows image repair …")
    success = repair_windows_image()
    if success:
        print(f"\n{GREEN}Windows Repaired Successfully!{RESET}")
    else:
        print(
            f"\n{YELLOW}Repair may not have completed fully – check logs for "
            f"details.{RESET}"
        )
    print("-" * 50)
    print("Press ENTER to continue.")
    print("-" * 50)
    input()


def _handle_info() -> None:
    """Handle option 3: Program and license information."""
    clear_screen()
    print(f"{BOLD}Windows Cleaner Utility{RESET}")
    print(f"Version {__version__} by Chainski")
    print()
    print(f"Source code available on GitHub: {CYAN}{__github__}{RESET}")
    print(f"Working under license: {__license__}")
    print()
    input("Press ENTER to return to the menu.")


def _handle_github() -> None:
    """Handle option 4: Open the GitHub page."""
    clear_screen()
    logger.info("Opening GitHub page: %s", __github__)
    open_url(__github__)


def _handle_exit() -> NoReturn:
    """Handle option 5: Exit the application."""
    clear_screen()
    print(f"{GREEN}Goodbye!{RESET}")
    logger.info("User exited the application.")
    sys.exit(0)


# Dispatch table: option → handler
_HANDLERS: Dict[str, Callable[[], None]] = {
    OPT_CLEAN: _handle_clean,
    OPT_REPAIR: _handle_repair,
    OPT_INFO: _handle_info,
    OPT_GITHUB: _handle_github,
    OPT_EXIT: _handle_exit,  # type: ignore[assignment]
}


def run_menu_loop() -> NoReturn:
    """Run the interactive main-menu loop until the user exits.

    Displays the menu, reads the user's choice, dispatches to the
    corresponding handler, and repeats.  The loop only terminates when the
    user selects the Exit option (which calls :func:`sys.exit`).

    Examples
    --------
    >>> # This would block – only verify the function is importable
    >>> from windows_cleaner.menu import run_menu_loop
    """
    while True:
        show_main_menu()
        choice = _get_choice(f"Enter choice [{OPT_CLEAN}-{OPT_EXIT}]: ")
        logger.debug("User selected option: %s", choice)
        handler = _HANDLERS.get(choice)
        if handler:
            handler()
