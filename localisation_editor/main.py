#!/usr/bin/env python3
"""
Stellaris Thai Translation MOD — Localisation Editor

A desktop GUI application for browsing, searching, and editing
Stellaris .yml localisation files with Thai translations.

Usage:
    pip install PyQt6
    python main.py
"""

import sys
import os

# Ensure the project root is on sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from localisation_editor.ui.main_window import MainWindow


def main():
    # Point Qt to Windows fonts (suppress "cannot find font directory" warning)
    if os.path.isdir("C:/Windows/Fonts"):
        os.environ["QT_QPA_FONTDIR"] = "C:/Windows/Fonts"

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SLE")
    app.setOrganizationName("StellarisThaiMod")

    # Set readable font for Thai + English
    font = QFont("Segoe UI", 12)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
