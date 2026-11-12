"""Entry point. Run from the project root with:  python src/main.py"""
import sys

from PySide6.QtWidgets import QApplication

from ui.components.logo_mark import logo_icon
from ui.main_window import MainWindow
from ui.theme import ui_font


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("System Monitor")
    app.setWindowIcon(logo_icon())  # Dock / taskbar icon when run from source
    app.setFont(ui_font(13))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
