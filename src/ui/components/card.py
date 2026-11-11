"""Base surface used by every dashboard panel."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame

from ui.theme import CARD


class Card(QFrame):
    """Rounded surface with a hairline border and an optional accent strip."""

    def __init__(self, accent=None):
        super().__init__()
        self.accent = accent
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setStyleSheet("QLabel { background: transparent; }")

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        painter.fillPath(path, QColor(CARD))
        if self.accent:
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 2), QColor(self.accent))
            painter.restore()
        painter.setPen(QPen(QColor(255, 255, 255, 16), 1))
        painter.drawPath(path)
