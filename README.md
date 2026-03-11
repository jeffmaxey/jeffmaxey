# Windows Cleaner Utility

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A **Python 3.11** port of the [Windows Cleaner Utility](https://github.com/Chainski/WindowsCleanerUtility) batch script originally by **Chainski Tools**.

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
