from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.theme import build_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ReaperSniff")
    app.setOrganizationName("ReaperSniff")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
