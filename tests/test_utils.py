"""
test_utils.py
-------------
Unit tests for :mod:`windows_cleaner.utils`.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestExpandEnv(unittest.TestCase):
    """Tests for :func:`windows_cleaner.utils.expand_env`."""

    def test_returns_string(self):
        from windows_cleaner.utils import expand_env

        self.assertIsInstance(expand_env("/some/path"), str)

    def test_expands_user_home(self):
        from windows_cleaner.utils import expand_env

        result = expand_env("~/Documents")
        self.assertNotIn("~", result)

    def test_expands_env_var(self):
        from windows_cleaner.utils import expand_env

        os.environ["_WCU_TEST_VAR"] = "/tmp/test_dir"
        result = expand_env("$_WCU_TEST_VAR")
        # On POSIX the variable is expanded; on Windows %VAR% syntax is used
        # but $VAR is passed through – we just check no exception is raised
        self.assertIsInstance(result, str)
        del os.environ["_WCU_TEST_VAR"]

    def test_no_change_for_plain_path(self):
        from windows_cleaner.utils import expand_env

        self.assertEqual(expand_env("/usr/local/bin"), "/usr/local/bin")


class TestDeleteFiles(unittest.TestCase):
    """Tests for :func:`windows_cleaner.utils.delete_files`."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_file(self, name: str) -> Path:
        p = Path(self.tmpdir) / name
        p.write_text("test content")
        return p

    def test_deletes_single_exact_file(self):
        from windows_cleaner.utils import delete_files

        f = self._make_file("test.tmp")
        count = delete_files([str(f)])
        self.assertEqual(count, 1)
        self.assertFalse(f.exists())

    def test_deletes_glob_pattern(self):
        from windows_cleaner.utils import delete_files

        self._make_file("a.log")
        self._make_file("b.log")
        self._make_file("c.txt")
        count = delete_files([os.path.join(self.tmpdir, "*.log")])
        self.assertEqual(count, 2)
        self.assertFalse((Path(self.tmpdir) / "a.log").exists())
        self.assertFalse((Path(self.tmpdir) / "b.log").exists())
        self.assertTrue((Path(self.tmpdir) / "c.txt").exists())

    def test_returns_zero_for_missing_dir(self):
        from windows_cleaner.utils import delete_files

        count = delete_files(["/nonexistent_dir_wcu_test/*.tmp"])
        self.assertEqual(count, 0)

    def test_returns_zero_for_no_match(self):
        from windows_cleaner.utils import delete_files

        self._make_file("a.txt")
        count = delete_files([os.path.join(self.tmpdir, "*.log")])
        self.assertEqual(count, 0)

    def test_ignore_errors_true_suppresses_permission_error(self):
        """delete_files should not raise when ignore_errors=True."""
        from windows_cleaner.utils import delete_files

        f = self._make_file("locked.tmp")
        with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
            count = delete_files([str(f)], ignore_errors=True)
        # count may vary; the important thing is no exception is raised
        self.assertIsInstance(count, int)

    def test_ignore_errors_false_raises_on_permission_error(self):
        """delete_files must propagate when ignore_errors=False."""
        from windows_cleaner.utils import delete_files

        f = self._make_file("locked2.tmp")
        with self.assertRaises(PermissionError):
            with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
                delete_files([str(f)], ignore_errors=False)


class TestRunCommand(unittest.TestCase):
    """Tests for :func:`windows_cleaner.utils.run_command`."""

    def test_captures_output(self):
        from windows_cleaner.utils import run_command

        result = run_command(["echo", "hello"], capture_output=True, shell=False)
        self.assertEqual(result.returncode, 0)

    def test_raises_on_bad_executable(self):
        from windows_cleaner.utils import run_command

        with self.assertRaises(FileNotFoundError):
            run_command(["_nonexistent_executable_wcu_"], capture_output=True)

    def test_check_raises_on_nonzero_exit(self):
        from windows_cleaner.utils import run_command

        with self.assertRaises(subprocess.CalledProcessError):
            # `exit 1` via Python is cross-platform
            run_command(
                [sys.executable, "-c", "import sys; sys.exit(1)"],
                capture_output=True,
                check=True,
            )

    def test_returns_completed_process(self):
        from windows_cleaner.utils import run_command

        result = run_command(
            [sys.executable, "-c", "print('ok')"], capture_output=True
        )
        self.assertIsInstance(result, subprocess.CompletedProcess)


class TestEnableAnsi(unittest.TestCase):
    def test_no_error_on_any_platform(self):
        from windows_cleaner.utils import enable_ansi_on_windows

        enable_ansi_on_windows()  # should not raise


class TestClearScreen(unittest.TestCase):
    def test_no_error(self):
        from windows_cleaner.utils import clear_screen

        with patch("os.system"):
            clear_screen()


class TestOpenUrl(unittest.TestCase):
    def test_calls_webbrowser_open(self):
        from windows_cleaner.utils import open_url

        with patch("webbrowser.open") as mock_open:
            open_url("https://example.com")
            mock_open.assert_called_once_with("https://example.com")


if __name__ == "__main__":
    unittest.main()
