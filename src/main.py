"""Entry point. Run from the project root with:  python src/main.py"""
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import ui_font


def main():
    app = QApplication(sys.argv)
    app.setFont(ui_font(13))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
