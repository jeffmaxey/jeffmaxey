"""
test_menu.py
------------
Unit tests for :mod:`windows_cleaner.menu`.

All interactive I/O and sub-operations are mocked so that tests run without
user interaction or system-level side effects.
"""

import sys
import unittest
from unittest.mock import MagicMock, call, patch


class TestGetChoice(unittest.TestCase):
    """Tests for :func:`windows_cleaner.menu._get_choice`."""

    @patch("builtins.input", return_value="1")
    def test_accepts_valid_choice(self, _):
        from windows_cleaner.menu import _get_choice, VALID_OPTIONS

        choice = _get_choice("Select: ", VALID_OPTIONS)
        self.assertEqual(choice, "1")

    @patch("builtins.input", side_effect=["9", "abc", "2"])
    def test_retries_on_invalid_input(self, _):
        from windows_cleaner.menu import _get_choice, VALID_OPTIONS

        choice = _get_choice("Select: ", VALID_OPTIONS)
        self.assertEqual(choice, "2")

    @patch("builtins.input", side_effect=EOFError)
    def test_returns_exit_on_eof(self, _):
        from windows_cleaner.menu import _get_choice, OPT_EXIT, VALID_OPTIONS

        choice = _get_choice("Select: ", VALID_OPTIONS)
        self.assertEqual(choice, OPT_EXIT)

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_returns_exit_on_keyboard_interrupt(self, _):
        from windows_cleaner.menu import _get_choice, OPT_EXIT, VALID_OPTIONS

        choice = _get_choice("Select: ", VALID_OPTIONS)
        self.assertEqual(choice, OPT_EXIT)


class TestShowMainMenu(unittest.TestCase):
    """Tests for :func:`windows_cleaner.menu.show_main_menu`."""

    @patch("windows_cleaner.menu.print_banner")
    @patch("windows_cleaner.menu.clear_screen")
    def test_shows_menu_without_error(self, mock_clear, mock_banner):
        from windows_cleaner.menu import show_main_menu

        with patch("builtins.print"):  # suppress output
            show_main_menu()

        mock_clear.assert_called_once()
        mock_banner.assert_called_once()


class TestHandleInfo(unittest.TestCase):
    @patch("builtins.input", return_value="")
    @patch("windows_cleaner.menu.clear_screen")
    def test_info_prints_version(self, _, __):
        from windows_cleaner.menu import _handle_info

        with patch("builtins.print") as mock_print:
            _handle_info()

        printed = " ".join(str(c) for call_ in mock_print.call_args_list for c in call_[0])
        self.assertIn("Windows Cleaner Utility", printed)


class TestHandleGithub(unittest.TestCase):
    @patch("windows_cleaner.menu.open_url")
    @patch("windows_cleaner.menu.clear_screen")
    def test_opens_github_url(self, _, mock_open):
        from windows_cleaner import __github__
        from windows_cleaner.menu import _handle_github

        _handle_github()
        mock_open.assert_called_once_with(__github__)


class TestHandleExit(unittest.TestCase):
    def test_calls_sys_exit(self):
        from windows_cleaner.menu import _handle_exit

        with self.assertRaises(SystemExit):
            _handle_exit()


class TestHandleRepair(unittest.TestCase):
    @patch("builtins.input", return_value="")
    @patch("windows_cleaner.menu.repair_windows_image", return_value=True)
    @patch("windows_cleaner.menu.clear_screen")
    def test_repair_success_message(self, _, mock_repair, __):
        from windows_cleaner.menu import _handle_repair

        with patch("builtins.print") as mock_print:
            _handle_repair()

        mock_repair.assert_called_once()

    @patch("builtins.input", return_value="")
    @patch("windows_cleaner.menu.repair_windows_image", return_value=False)
    @patch("windows_cleaner.menu.clear_screen")
    def test_repair_failure_message(self, _, mock_repair, __):
        from windows_cleaner.menu import _handle_repair

        with patch("builtins.print"):
            _handle_repair()

        mock_repair.assert_called_once()


class TestHandleClean(unittest.TestCase):
    @patch("windows_cleaner.menu.check_temp_files_exist", return_value=False)
    @patch("windows_cleaner.menu.clear_screen")
    @patch("builtins.input", return_value="")
    def test_no_cleaning_needed(self, _, __, mock_check):
        """When no temp files exist the user should be told their PC is clean."""
        from windows_cleaner.menu import _handle_clean

        with patch("builtins.print"):
            _handle_clean()

    @patch("windows_cleaner.menu.enable_ultimate_performance", return_value=True)
    @patch("windows_cleaner.menu.flush_dns_cache", return_value=True)
    @patch(
        "windows_cleaner.menu.clean_temporary_files",
        return_value={"temp": 10, "logs": 2, "drivers": 0, "defender": 1},
    )
    @patch("windows_cleaner.menu.check_temp_files_exist", side_effect=[True, False])
    @patch("windows_cleaner.menu.clear_screen")
    @patch("builtins.input", return_value="")
    @patch("windows_cleaner.menu._get_choice", return_value="1")
    def test_clean_and_complete(
        self,
        mock_choice,
        mock_input,
        mock_clear,
        mock_check,
        mock_clean,
        mock_dns,
        mock_perf,
    ):
        """Full clean flow: temp files found → clean → complete message."""
        from windows_cleaner.menu import _handle_clean

        with patch("builtins.print"):
            _handle_clean()

        mock_clean.assert_called_once()
        mock_dns.assert_called_once()
        mock_perf.assert_called_once()


class TestRunMenuLoop(unittest.TestCase):
    @patch("windows_cleaner.menu.show_main_menu")
    @patch("windows_cleaner.menu._get_choice", return_value="5")
    def test_dispatches_exit(self, mock_choice, mock_menu):
        from windows_cleaner.menu import run_menu_loop

        with self.assertRaises(SystemExit):
            run_menu_loop()

        mock_menu.assert_called_once()


if __name__ == "__main__":
    unittest.main()
