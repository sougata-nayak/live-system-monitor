"""Label factory shared by every widget."""
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel

from ui.theme import MUTED, ui_font


def make_label(text="", size=12, color=MUTED, weight=QFont.Normal) -> QLabel:
    label = QLabel(text)
    label.setFont(ui_font(size, weight))
    label.setStyleSheet(f"color:{color}; background:transparent;")
    return label
