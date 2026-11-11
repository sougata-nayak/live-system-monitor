"""Window background with two soft color glows."""
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from ui.theme import BACKGROUND, BLUE, VIOLET, with_alpha


class Backdrop(QWidget):
    # (x fraction, y fraction, color, radius, alpha)
    GLOWS = ((0.15, -0.05, BLUE, 700, 30), (1.0, 0.0, VIOLET, 650, 24))

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BACKGROUND))
        for x_fraction, y_fraction, color, radius, alpha in self.GLOWS:
            gradient = QRadialGradient(
                QPointF(self.width() * x_fraction, self.height() * y_fraction), radius)
            gradient.setColorAt(0, with_alpha(color, alpha))
            gradient.setColorAt(1, with_alpha(color, 0))
            painter.fillRect(self.rect(), gradient)
