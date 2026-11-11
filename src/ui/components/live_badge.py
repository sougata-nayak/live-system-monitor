"""'Live' pill with a softly pulsing dot."""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from ui.theme import TEAL, ui_font, with_alpha


class LiveBadge(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(66, 28)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setBrush(with_alpha(TEAL, 26))
        painter.setPen(QPen(with_alpha(TEAL, 64), 1))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        pulse = 0.5 + 0.5 * math.sin(time.monotonic() * 3)
        center = QPointF(15, rect.center().y())
        glow = QRadialGradient(center, 9)
        glow.setColorAt(0, with_alpha(TEAL, int(120 * pulse)))
        glow.setColorAt(1, with_alpha(TEAL, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, 9, 9)
        painter.setBrush(QColor(TEAL))
        painter.drawEllipse(center, 3.5, 3.5)
        painter.setPen(QColor(TEAL))
        painter.setFont(ui_font(12, QFont.Medium))
        painter.drawText(QRectF(26, 0, 38, rect.height()), Qt.AlignVCenter | Qt.AlignLeft, "Live")
