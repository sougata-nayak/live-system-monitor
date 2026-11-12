"""Labels shared by every widget."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from ui.theme import MUTED, ui_font


def make_label(text="", size=12, color=MUTED, weight=QFont.Normal) -> QLabel:
    label = QLabel(text)
    label.setFont(ui_font(size, weight))
    label.setStyleSheet(f"color:{color}; background:transparent;")
    return label


class ElidedLabel(QWidget):
    """One line of text that shrinks with its column and ends in '…' when cut off
    (a QLabel would instead force the layout wider)."""

    def __init__(self, font: QFont, color: str):
        super().__init__()
        self._text = ""
        self._color = QColor(color)
        self.setFont(font)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumHeight(self.fontMetrics().height())

    def text(self) -> str:
        return self._text

    def setText(self, text: str):
        if text != self._text:
            self._text = text
            self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setPen(self._color)
        elided = self.fontMetrics().elidedText(self._text, Qt.ElideRight, self.width())
        painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignLeft, elided)
