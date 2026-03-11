"""
about_page.py
-------------
About / Help page with version, license, and links.
"""

from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QFrame,
        QTextBrowser,
    )

    _PYSIDE6_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYSIDE6_AVAILABLE = False
    QWidget = object  # type: ignore[assignment,misc]

from windows_cleaner_gui import __version__

_ABOUT_TEXT = f"""\
<h2>Windows Cleaner  v{__version__}</h2>

<p>
An enterprise-grade graphical interface for the
<b>Windows Cleaner Utility</b> backend, originally created by
<b>Chainski Tools</b>.
</p>

<h3>Features</h3>
<ul>
  <li>Temporary file &amp; cache cleaning</li>
  <li>Windows image repair via SFC / DISM</li>
  <li>DNS cache flush &amp; network stack reset</li>
  <li>Ultimate Performance power plan activation</li>
  <li>Live log viewer with severity filtering</li>
  <li>Persistent settings (Windows Registry / INI)</li>
</ul>

<h3>Requirements</h3>
<ul>
  <li>Python 3.11+</li>
  <li>PySide6 6.x</li>
  <li>Windows 10 / 11 (for cleaning features)</li>
  <li>Administrator privileges for most operations</li>
</ul>

<h3>License</h3>
<p>GNU General Public License v3.0</p>

<h3>Original Backend</h3>
<p>
  <a href="https://github.com/Chainski/WindowsCleanerUtility">
    https://github.com/Chainski/WindowsCleanerUtility
  </a>
</p>
"""

_GITHUB_URL = "https://github.com/jeffmaxey/jeffmaxey"


class AboutPage(QWidget):  # type: ignore[misc]
    """About / Help page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _PYSIDE6_AVAILABLE:  # pragma: no cover
            return
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("About")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        layout.addWidget(sep)

        browser = QTextBrowser()
        browser.setHtml(_ABOUT_TEXT)
        browser.setOpenExternalLinks(True)
        browser.setObjectName("aboutBrowser")
        layout.addWidget(browser)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        github_btn = QPushButton("🌐  Open on GitHub")
        github_btn.setObjectName("secondaryButton")
        github_btn.clicked.connect(self._open_github)
        btn_layout.addWidget(github_btn)

        layout.addLayout(btn_layout)

    def _open_github(self) -> None:
        if _PYSIDE6_AVAILABLE:
            QDesktopServices.openUrl(QUrl(_GITHUB_URL))
