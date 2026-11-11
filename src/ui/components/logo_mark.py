"""App logo: a gradient rounded square with a pulse-line glyph."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import BLUE, LOGO_GLYPH, VIOLET


class LogoMark(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(36, 36)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, 36, 36)
        gradient.setColorAt(0, QColor(BLUE))
        gradient.setColorAt(1, QColor(VIOLET))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, 36, 36), 10, 10)
        pen = QPen(QColor(LOGO_GLYPH), 2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        points = [(9, 19), (14, 19), (17, 12), (21, 25), (24, 17), (28, 17)]
        painter.drawPolyline([QPointF(x, y) for x, y in points])
