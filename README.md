# Windows Cleaner Utility

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build](https://github.com/jeffmaxey/jeffmaxey/actions/workflows/build-windows.yml/badge.svg)](https://github.com/jeffmaxey/jeffmaxey/actions/workflows/build-windows.yml)

A **Python 3.11** port of the [Windows Cleaner Utility](https://github.com/Chainski/WindowsCleanerUtility) batch script originally by **Chainski Tools**, with an **enterprise-grade PySide6 GUI frontend**.

The project ships two separate, independently usable components:

| Component | Package | Description |
|-----------|---------|-------------|
| **Backend (CLI)** | `windows_cleaner` | Core cleaning logic; importable as a library or run as a CLI |
| **Frontend (GUI)** | `windows_cleaner_gui` | PySide6 desktop application with sidebar navigation, progress reporting, and live log viewer |

---

## Features

### Backend (`windows_cleaner`)
- **Admin / UAC elevation** – Automatically detects and re-launches with elevated privileges (Windows only).
- **Temporary file cleaning** – Removes `%TEMP%`, `%WINDIR%\Temp`, Recycle Bin, crash dumps, Windows Update download cache, thumbnail caches, Windows Defender logs, remnant GPU driver files, and more.
- **Windows image repair** – Runs `sfc /scannow` followed by the three DISM health-check / restore commands.
- **DNS cache flush** – Releases/renews the IP address and resets Winsock / IPv4 / IPv6 stacks.
- **Ultimate Performance power plan** – Duplicates and activates the built-in Ultimate Performance power scheme via `powercfg`.
- **Structured logging** – Every operation is logged to both the console and `windows_cleaner.log`.

### Frontend (`windows_cleaner_gui`)
- **Dark-themed PySide6 UI** – Sidebar navigation, multi-page layout (Scan, Clean, Results, Settings, Logs, About).
- **Background threading** – All backend calls run off the UI thread via `QThread` workers with cancellation support.
- **Live log viewer** – Real-time, colour-coded log panel with severity filtering.
- **Persistent settings** – Window geometry, preferences, and log level saved to `QSettings` (Windows Registry / INI file).
- **Progress reporting** – Per-step progress bar and status messages during long-running operations.
- **PyInstaller packaging** – Spec file + build scripts to produce a self-contained Windows `.exe` and MSI installer.

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| PySide6 | 6.6+ (GUI only) |
| Windows | 10 / 11 (for cleaning features; tests run on any OS) |
| Administrator | Required for most operations |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/jeffmaxey/jeffmaxey.git
cd jeffmaxey

# (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux / macOS (for development/testing)

# Install backend only (CLI)
pip install -e .

# Install with GUI extras (PySide6)
pip install -e ".[gui]"

# Install with development tools
pip install -e ".[dev]"
```

---

## Usage

### Command-Line Interface

```bash
# Run via the installed console script
windows-cleaner

# Or run directly as a module
python -m windows_cleaner

# Show help / version
python -m windows_cleaner --help
python -m windows_cleaner --version

# Enable verbose debug logging
python -m windows_cleaner --debug

# Skip the UAC elevation check (useful for testing)
python -m windows_cleaner --no-admin-check
```

### GUI Application

```bash
# Run via the installed console script
windows-cleaner-gui

# Or run directly as a module
python -m windows_cleaner_gui
```

---

## Project Structure

```
jeffmaxey/
├── windows_cleaner/              # Backend package (CLI + library)
│   ├── __init__.py               # Package metadata (version, license)
│   ├── __main__.py               # CLI entry point (argparse, logging setup)
│   ├── admin.py                  # UAC / administrator-privilege detection
│   ├── cleaner.py                # Core cleaning, repair, optimisation routines
│   ├── menu.py                   # Interactive menu loop
│   └── utils.py                  # Shared helpers (subprocess, file deletion, ANSI)
│
├── windows_cleaner_gui/          # Frontend package (PySide6 GUI)
│   ├── __init__.py
│   ├── __main__.py               # GUI entry point
│   ├── app.py                    # QApplication bootstrap, logging bridge
│   ├── services/
│   │   ├── cleaner_service.py    # Service layer wrapping the backend
│   │   └── settings_service.py  # QSettings-backed preferences
│   ├── workers/
│   │   └── cleaner_worker.py    # QThread worker for background operations
│   ├── views/
│   │   ├── main_window.py       # Main window with sidebar navigation
│   │   ├── scan_page.py         # Scan / analyse page
│   │   ├── clean_page.py        # Clean operations page with progress
│   │   ├── results_page.py      # Results table view
│   │   ├── settings_page.py     # Preferences editor
│   │   ├── logs_page.py         # Live log viewer panel
│   │   └── about_page.py        # About / help page
│   └── resources/
│       ├── icons/app.ico        # Application icon
│       └── styles/dark.qss      # Dark theme stylesheet
│
├── tests/
│   ├── __init__.py
│   ├── test_admin.py            # Tests for admin.py
│   ├── test_cleaner.py          # Tests for cleaner.py
│   ├── test_menu.py             # Tests for menu.py
│   ├── test_utils.py            # Tests for utils.py
│   └── test_gui_import.py       # GUI import + smoke tests
│
├── installer/
│   └── Product.wxs              # WiX v4 installer definition
│
├── scripts/
│   ├── build_exe.ps1            # PowerShell: build Windows .exe with PyInstaller
│   └── build_msi.ps1            # PowerShell: build MSI with WiX
│
├── .github/workflows/
│   └── build-windows.yml        # GitHub Actions: test + build exe + build MSI
│
├── windows_cleaner_gui.spec     # PyInstaller spec file
└── pyproject.toml               # Build system, project metadata, dependencies
```

---

## Running the Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests (backend + GUI smoke tests)
pytest

# Run with coverage report
pytest --cov=windows_cleaner --cov=windows_cleaner_gui --cov-report=term-missing

# Run only GUI tests (no display required)
pytest tests/test_gui_import.py -v
```

---

## Packaging

### Prerequisites (Windows)

```powershell
# Python 3.11+ and pip must be in PATH
python --version

# Install GUI dependencies + PyInstaller
pip install -e ".[gui]"
pip install "pyinstaller>=6.0"

# For MSI: install .NET SDK and WiX v4
winget install Microsoft.DotNet.SDK.8
dotnet tool install --global wix
```

### Build Executable

```powershell
# Using the build script (recommended)
.\scripts\build_exe.ps1

# Or manually with PyInstaller
pyinstaller windows_cleaner_gui.spec --distpath dist --workpath build --noconfirm
```

Output: `dist\WindowsCleaner\WindowsCleaner.exe`

### Build MSI Installer

```powershell
# Build exe and MSI in one step
.\scripts\build_msi.ps1

# Or skip exe build (use existing dist\)
.\scripts\build_msi.ps1 -SkipExeBuild

# Use WiX v3 instead of v4
.\scripts\build_msi.ps1 -WixVersion 3
```

Output: `dist\WindowsCleaner-1.0.0.msi`

The MSI installer:
- Installs to `%ProgramFiles%\Chainski\Windows Cleaner\`
- Creates a Start Menu shortcut
- Creates an optional Desktop shortcut
- Registers in Add/Remove Programs
- Supports major-upgrade (remove old version on install of new)

### CI / GitHub Actions

The workflow at `.github/workflows/build-windows.yml` runs automatically on push/PR and:
1. Runs unit tests on Ubuntu, Windows, and macOS (Python 3.11 + 3.12)
2. Runs GUI import smoke tests (headless, `QT_QPA_PLATFORM=offscreen`)
3. Builds the Windows executable with PyInstaller
4. Builds the MSI installer with WiX v4
5. Uploads both as downloadable artifacts

On version tags (`v*`), it additionally creates a GitHub Release with the MSI and portable ZIP attached.

---

## Logging

The backend writes `DEBUG`-level logs to `windows_cleaner.log` in the current working directory and `INFO`-level messages to `stderr`. Pass `--debug` to also see debug output in the terminal.

The GUI additionally writes logs to `%APPDATA%\Chainski\Windows Cleaner\logs\windows_cleaner_gui.log` and displays them in the live **Logs** page.

---

## License

GNU General Public License v3.0 – see the [LICENSE](LICENSE) file for details.

---

## Credits

Original batch script by **Chainski** – <https://github.com/Chainski/WindowsCleanerUtility>

The application provides an interactive command-line menu to:

| Option | Description |
|--------|-------------|
| 1 | Delete temporary files, caches, logs, and driver remnants |
| 2 | Scan and repair the Windows system image via SFC / DISM |
| 3 | Display program and license information |
| 4 | Open the project GitHub page |
| 5 | Exit the application |

---

## Features

- **Admin / UAC elevation** – Automatically detects whether the process has administrator rights and re-launches with elevated privileges when needed (Windows only).
- **Temporary file cleaning** – Removes files from `%TEMP%`, `%WINDIR%\Temp`, the Recycle Bin, crash dumps, Windows Update download cache, thumbnail caches, Windows Defender logs, remnant GPU driver files, and more.
- **Windows image repair** – Runs `sfc /scannow` followed by the three DISM health-check / restore commands.
- **DNS cache flush** – Releases/renews the IP address and resets Winsock / IPv4 / IPv6 stacks.
- **Ultimate Performance power plan** – Duplicates and activates the built-in Ultimate Performance power scheme via `powercfg`.
- **Structured logging** – Every operation is logged to both the console (configurable level) and `windows_cleaner.log`.
- **Cross-platform safety** – Windows-only operations gracefully degrade on other platforms so that unit tests can run anywhere.

---

## Requirements

- Python 3.11 or later
- Windows 10 / 11 (for the cleaning / repair features)
- Administrator privileges (the application will prompt for UAC elevation automatically)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/jeffmaxey/jeffmaxey.git
cd jeffmaxey

# (Optional) create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux / macOS (for development/testing)

# Install in editable mode
pip install -e .
```

---

## Usage

```bash
# Run via the installed console script
windows-cleaner

# Or run directly as a module
python -m windows_cleaner

# Show help / version
python -m windows_cleaner --help
python -m windows_cleaner --version

# Enable verbose debug logging
python -m windows_cleaner --debug

# Skip the UAC elevation check (useful for testing)
python -m windows_cleaner --no-admin-check
```

---

## Project Structure

```
jeffmaxey/
├── windows_cleaner/
│   ├── __init__.py       # Package metadata (version, license, GitHub URL)
│   ├── __main__.py       # CLI entry point (argument parsing, logging setup)
│   ├── admin.py          # UAC / administrator-privilege detection & elevation
│   ├── cleaner.py        # Core cleaning, repair, and optimisation routines
│   ├── menu.py           # Interactive menu loop
│   └── utils.py          # Shared helpers (subprocess, file deletion, ANSI output)
├── tests/
│   ├── __init__.py
│   ├── test_admin.py     # Tests for admin.py
│   ├── test_cleaner.py   # Tests for cleaner.py
│   ├── test_menu.py      # Tests for menu.py
│   └── test_utils.py     # Tests for utils.py
├── pyproject.toml        # Build system and project metadata
└── README.md
```

---

## Running the Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage report
pytest --cov=windows_cleaner --cov-report=term-missing
```

---

## Logging

By default the application writes `DEBUG`-level logs to `windows_cleaner.log` in the current working directory and `INFO`-level messages to `stderr`.  Pass `--debug` to also see debug output in the terminal.

---

## License

GNU General Public License v3.0 – see the [LICENSE](LICENSE) file for details.

---

## Credits

Original batch script by **Chainski** – <https://github.com/Chainski/WindowsCleanerUtility>
