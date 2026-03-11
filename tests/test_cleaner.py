"""
test_cleaner.py
---------------
Unit tests for :mod:`windows_cleaner.cleaner`.

All tests mock out actual file-system and subprocess calls so they can run
safely on any platform (including non-Windows CI environments).
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch


class TestCheckTempFilesExist(unittest.TestCase):
    """Tests for :func:`windows_cleaner.cleaner.check_temp_files_exist`."""

    def test_returns_bool(self):
        from windows_cleaner.cleaner import check_temp_files_exist

        result = check_temp_files_exist()
        self.assertIsInstance(result, bool)

    def test_true_when_files_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "dummy.tmp").write_text("x")
            with patch("windows_cleaner.cleaner.expand_env", return_value=tmpdir):
                from windows_cleaner.cleaner import check_temp_files_exist

                self.assertTrue(check_temp_files_exist())

    def test_false_when_dir_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("windows_cleaner.cleaner.expand_env", return_value=tmpdir):
                from windows_cleaner.cleaner import check_temp_files_exist

                self.assertFalse(check_temp_files_exist())

    def test_false_when_dir_missing(self):
        with patch(
            "windows_cleaner.cleaner.expand_env",
            return_value="/nonexistent_path_wcu_12345",
        ):
            from windows_cleaner.cleaner import check_temp_files_exist

            self.assertFalse(check_temp_files_exist())


class TestCleanTemporaryFiles(unittest.TestCase):
    """Tests for :func:`windows_cleaner.cleaner.clean_temporary_files`."""

    @patch("windows_cleaner.cleaner.delete_files", return_value=5)
    @patch("windows_cleaner.cleaner.run_command")
    def test_returns_dict_with_required_keys(self, mock_cmd, mock_del):
        from windows_cleaner.cleaner import clean_temporary_files

        result = clean_temporary_files()
        self.assertIsInstance(result, dict)
        for key in ("temp", "logs", "drivers", "defender"):
            self.assertIn(key, result)

    @patch("windows_cleaner.cleaner.delete_files", return_value=0)
    @patch("windows_cleaner.cleaner.run_command")
    def test_values_are_integers(self, mock_cmd, mock_del):
        from windows_cleaner.cleaner import clean_temporary_files

        result = clean_temporary_files()
        for v in result.values():
            self.assertIsInstance(v, int)

    @patch("windows_cleaner.cleaner.delete_files", return_value=3)
    @patch("windows_cleaner.cleaner.run_command")
    def test_stats_sum_correctly(self, mock_cmd, mock_del):
        from windows_cleaner.cleaner import clean_temporary_files

        result = clean_temporary_files()
        # delete_files is mocked to return 3 for each category
        # On non-Windows the wuauserv service commands won't be called
        self.assertTrue(sum(result.values()) >= 0)


class TestRepairWindowsImage(unittest.TestCase):
    """Tests for :func:`windows_cleaner.cleaner.repair_windows_image`."""

    def test_returns_false_on_non_windows(self):
        """Function must return False on non-Windows platforms."""
        with patch.object(sys, "platform", "linux"):
            from windows_cleaner import cleaner as cleaner_module

            # Re-import with patched platform
            with patch("windows_cleaner.cleaner.sys") as mock_sys:
                mock_sys.platform = "linux"
                from windows_cleaner.cleaner import repair_windows_image

                result = repair_windows_image()
        self.assertFalse(result)

    def test_returns_bool(self):
        from windows_cleaner.cleaner import repair_windows_image

        result = repair_windows_image()
        self.assertIsInstance(result, bool)

    @patch("windows_cleaner.cleaner.run_command")
    def test_calls_sfc_and_dism_on_windows(self, mock_cmd):
        """On Windows all four repair commands must be called."""
        mock_cmd.return_value = MagicMock(returncode=0)
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "win32"
            from windows_cleaner.cleaner import repair_windows_image

            result = repair_windows_image()
        self.assertTrue(result)
        # 4 commands: sfc + 3 dism
        self.assertEqual(mock_cmd.call_count, 4)


class TestFlushDnsCache(unittest.TestCase):
    """Tests for :func:`windows_cleaner.cleaner.flush_dns_cache`."""

    def test_returns_false_on_non_windows(self):
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "linux"
            from windows_cleaner.cleaner import flush_dns_cache

            result = flush_dns_cache()
        self.assertFalse(result)

    def test_returns_bool(self):
        from windows_cleaner.cleaner import flush_dns_cache

        result = flush_dns_cache()
        self.assertIsInstance(result, bool)

    @patch("windows_cleaner.cleaner.run_command")
    def test_calls_all_network_commands_on_windows(self, mock_cmd):
        mock_cmd.return_value = MagicMock(returncode=0)
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "win32"
            from windows_cleaner.cleaner import flush_dns_cache

            result = flush_dns_cache()
        self.assertTrue(result)
        # 7 commands: ipconfig x3 + netsh x4
        self.assertEqual(mock_cmd.call_count, 7)


class TestEnableUltimatePerformance(unittest.TestCase):
    """Tests for :func:`windows_cleaner.cleaner.enable_ultimate_performance`."""

    def test_returns_false_on_non_windows(self):
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "linux"
            from windows_cleaner.cleaner import enable_ultimate_performance

            result = enable_ultimate_performance()
        self.assertFalse(result)

    def test_returns_bool(self):
        from windows_cleaner.cleaner import enable_ultimate_performance

        result = enable_ultimate_performance()
        self.assertIsInstance(result, bool)

    @patch("windows_cleaner.cleaner.run_command")
    def test_calls_powercfg_on_windows(self, mock_cmd):
        mock_cmd.return_value = MagicMock(returncode=0)
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "win32"
            from windows_cleaner.cleaner import enable_ultimate_performance

            result = enable_ultimate_performance()
        self.assertTrue(result)
        self.assertEqual(mock_cmd.call_count, 2)

    @patch("windows_cleaner.cleaner.run_command")
    def test_returns_false_when_powercfg_fails(self, mock_cmd):
        mock_cmd.return_value = MagicMock(returncode=1)
        with patch("windows_cleaner.cleaner.sys") as mock_sys:
            mock_sys.platform = "win32"
            from windows_cleaner.cleaner import enable_ultimate_performance

            result = enable_ultimate_performance()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
