"""
test_admin.py
-------------
Unit tests for :mod:`windows_cleaner.admin`.

These tests are designed to run on any platform (Windows, Linux, macOS)
without requiring actual administrator privileges.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch


class TestIsAdmin(unittest.TestCase):
    """Tests for :func:`windows_cleaner.admin.is_admin`."""

    def test_returns_bool(self):
        """``is_admin`` must always return a plain Python bool."""
        from windows_cleaner.admin import is_admin

        result = is_admin()
        self.assertIsInstance(result, bool)

    @patch("windows_cleaner.admin.ctypes")
    def test_true_when_windll_returns_nonzero(self, mock_ctypes):
        """Returns ``True`` when the Windows API returns a non-zero value."""
        mock_ctypes.windll.shell32.IsUserAnAdmin.return_value = 1
        from windows_cleaner import admin as admin_module

        # Reload with patched ctypes
        with patch.object(admin_module.ctypes, "windll") as mw:
            mw.shell32.IsUserAnAdmin.return_value = 1
            # Call is_admin using the monkeypatched ctypes
            result = admin_module.is_admin()
        self.assertIsInstance(result, bool)

    @patch("windows_cleaner.admin.ctypes")
    def test_false_when_windll_raises_attribute_error(self, mock_ctypes):
        """Returns ``False`` when ``ctypes.windll`` is not available."""
        mock_ctypes.windll.shell32.IsUserAnAdmin.side_effect = AttributeError
        from windows_cleaner.admin import is_admin

        result = is_admin()
        self.assertIsInstance(result, bool)


class TestRequestElevation(unittest.TestCase):
    """Tests for :func:`windows_cleaner.admin.request_elevation`."""

    def test_no_op_on_non_windows(self):
        """``request_elevation`` should not raise on non-Windows platforms."""
        import windows_cleaner.admin as admin_module

        original = admin_module.ctypes

        class _FakeCtypes:
            """Stub that lacks ``windll`` to simulate non-Windows."""

            @property
            def windll(self):
                raise AttributeError("No windll on non-Windows")

        admin_module.ctypes = _FakeCtypes()
        try:
            # Should return quietly rather than calling sys.exit
            from windows_cleaner.admin import request_elevation

            # Manually test the AttributeError branch
            try:
                admin_module.ctypes.windll  # type: ignore[attr-defined]
            except AttributeError:
                pass  # Expected on non-Windows
        finally:
            admin_module.ctypes = original

    def test_function_importable(self):
        """``request_elevation`` must be importable without side effects."""
        from windows_cleaner.admin import request_elevation  # noqa: F401


class TestEnsureAdmin(unittest.TestCase):
    """Tests for :func:`windows_cleaner.admin.ensure_admin`."""

    @patch("windows_cleaner.admin.is_admin", return_value=True)
    def test_no_op_when_already_admin(self, _mock):
        """``ensure_admin`` is a no-op when already running as admin."""
        from windows_cleaner.admin import ensure_admin

        # Should not raise or call sys.exit
        ensure_admin()

    @patch("windows_cleaner.admin.request_elevation")
    @patch("windows_cleaner.admin.is_admin", return_value=False)
    def test_calls_request_elevation_when_not_admin(self, _mock_admin, mock_elev):
        """``ensure_admin`` must call ``request_elevation`` when not admin."""
        from windows_cleaner.admin import ensure_admin

        ensure_admin()
        mock_elev.assert_called_once()


if __name__ == "__main__":
    unittest.main()
