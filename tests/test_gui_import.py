"""
test_gui_import.py
------------------
Import-level and unit-level smoke tests for the ``windows_cleaner_gui``
package.  These tests do **not** require a display; they verify that:

1. The package and all sub-modules can be imported without crashing.
2. The service layer functions return the expected types.
3. The settings service reads/writes correctly without Qt.
4. The worker can be instantiated with a valid operation name.
"""

import importlib
import sys
import types
import unittest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helper: ensure PySide6 absence doesn't break imports
# ---------------------------------------------------------------------------

def _mock_pyside6():
    """Insert a minimal PySide6 stub into sys.modules if PySide6 is absent."""
    if "PySide6" not in sys.modules:
        pyside6 = types.ModuleType("PySide6")
        for sub in [
            "PySide6.QtCore",
            "PySide6.QtGui",
            "PySide6.QtWidgets",
        ]:
            mod = types.ModuleType(sub)
            # Provide stub classes
            for cls_name in [
                "QThread", "Signal", "QObject", "Qt", "QSettings",
                "QApplication", "QMainWindow", "QWidget", "QLabel",
                "QPushButton", "QVBoxLayout", "QHBoxLayout", "QListWidget",
                "QListWidgetItem", "QStackedWidget", "QStatusBar",
                "QSizePolicy", "QMessageBox", "QProgressBar", "QGroupBox",
                "QFormLayout", "QCheckBox", "QComboBox", "QTextEdit",
                "QTextBrowser", "QTableWidget", "QTableWidgetItem",
                "QFrame", "QHeaderView", "QAction", "QIcon", "QColor",
                "QTextCursor", "QDesktopServices", "QUrl", "QByteArray",
                "QMenuBar",
            ]:
                setattr(mod, cls_name, MagicMock)
            sys.modules[sub] = mod
        sys.modules["PySide6"] = pyside6


# ---------------------------------------------------------------------------
# Test: Package metadata
# ---------------------------------------------------------------------------

class TestPackageMetadata(unittest.TestCase):

    def test_version(self):
        import windows_cleaner_gui
        self.assertIsInstance(windows_cleaner_gui.__version__, str)
        # Must be semver-like
        parts = windows_cleaner_gui.__version__.split(".")
        self.assertEqual(len(parts), 3)

    def test_author(self):
        import windows_cleaner_gui
        self.assertIsInstance(windows_cleaner_gui.__author__, str)

    def test_license(self):
        import windows_cleaner_gui
        self.assertIn("General Public License", windows_cleaner_gui.__license__)


# ---------------------------------------------------------------------------
# Test: Sub-module imports
# ---------------------------------------------------------------------------

class TestModuleImports(unittest.TestCase):

    def _import(self, module_path: str):
        """Import a module path, failing loudly on ImportError."""
        return importlib.import_module(module_path)

    def test_import_services_cleaner(self):
        mod = self._import("windows_cleaner_gui.services.cleaner_service")
        self.assertTrue(hasattr(mod, "CleanerService"))

    def test_import_services_settings(self):
        mod = self._import("windows_cleaner_gui.services.settings_service")
        self.assertTrue(hasattr(mod, "SettingsService"))
        self.assertTrue(hasattr(mod, "DEFAULTS"))

    def test_import_workers(self):
        mod = self._import("windows_cleaner_gui.workers.cleaner_worker")
        self.assertTrue(hasattr(mod, "CleanerWorker"))
        self.assertTrue(hasattr(mod, "OPERATIONS"))

    def test_import_views_package(self):
        mod = self._import("windows_cleaner_gui.views")
        self.assertIsNotNone(mod)


# ---------------------------------------------------------------------------
# Test: CleanerService (synchronous, backend-level)
# ---------------------------------------------------------------------------

class TestCleanerService(unittest.TestCase):

    def setUp(self):
        from windows_cleaner_gui.services.cleaner_service import CleanerService
        self.svc = CleanerService()

    def test_is_windows_returns_bool(self):
        result = self.svc.is_windows()
        self.assertIsInstance(result, bool)

    def test_is_admin_returns_bool(self):
        result = self.svc.is_admin()
        self.assertIsInstance(result, bool)

    def test_check_temp_files_exist_returns_bool(self):
        result = self.svc.check_temp_files_exist()
        self.assertIsInstance(result, bool)

    def test_scan_returns_dict_with_expected_keys(self):
        result = self.svc.scan()
        self.assertIsInstance(result, dict)
        self.assertIn("temp_files_exist", result)
        self.assertIn("platform", result)
        self.assertIn("is_admin", result)

    def test_cancelled_check_raises(self):
        from windows_cleaner_gui.services.cleaner_service import CleanerService
        svc = CleanerService(cancelled_check=lambda: True)
        with self.assertRaises(CleanerService.OperationCancelledError):
            svc.scan()

    def test_progress_callback_called(self):
        calls = []
        from windows_cleaner_gui.services.cleaner_service import CleanerService
        svc = CleanerService(progress_callback=lambda s, t, m: calls.append((s, t, m)))
        svc.scan()
        self.assertGreater(len(calls), 0)


# ---------------------------------------------------------------------------
# Test: SettingsService (without Qt)
# ---------------------------------------------------------------------------

class TestSettingsService(unittest.TestCase):

    def setUp(self):
        from windows_cleaner_gui.services.settings_service import SettingsService
        self.svc = SettingsService()

    def test_defaults_theme(self):
        val = self.svc.theme
        self.assertIsInstance(val, str)

    def test_defaults_log_level(self):
        val = self.svc.log_level
        self.assertIsInstance(val, str)

    def test_set_and_get_roundtrip(self):
        self.svc.set("_test_key", "hello")
        self.assertEqual(self.svc.get("_test_key"), "hello")

    def test_confirm_before_clean_default(self):
        val = self.svc.confirm_before_clean
        self.assertIsInstance(val, bool)

    def test_auto_scan_default(self):
        val = self.svc.auto_scan_on_start
        self.assertIsInstance(val, bool)

    def test_save_load_geometry_none(self):
        geo, state = self.svc.load_geometry()
        # On first run there's no saved geometry
        self.assertIsNone(geo)
        self.assertIsNone(state)


# ---------------------------------------------------------------------------
# Test: Worker operation set
# ---------------------------------------------------------------------------

class TestCleanerWorkerOperations(unittest.TestCase):

    def test_operations_set_is_complete(self):
        from windows_cleaner_gui.workers.cleaner_worker import OPERATIONS
        expected = {"scan", "clean_temp", "repair", "flush_dns", "ultimate_perf"}
        self.assertEqual(OPERATIONS, expected)

    def test_invalid_operation_raises(self):
        _mock_pyside6()
        from windows_cleaner_gui.workers.cleaner_worker import CleanerWorker
        with self.assertRaises(ValueError):
            CleanerWorker("nonexistent_operation")


if __name__ == "__main__":
    unittest.main()
