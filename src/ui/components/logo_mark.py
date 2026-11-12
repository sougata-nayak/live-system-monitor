"""App logo: a gradient rounded square with a pulse-line glyph.

``paint_logo`` is shared by the header widget and the app/Dock icon.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ui.theme import BLUE, LOGO_GLYPH, VIOLET

LOGO_SIZE = 36  # design size; everything below is drawn in this coordinate space


def paint_logo(painter: QPainter):
    """Draw the logo in a LOGO_SIZE x LOGO_SIZE box at the origin (scale the painter to resize)."""
    painter.setRenderHint(QPainter.Antialiasing)
    gradient = QLinearGradient(0, 0, LOGO_SIZE, LOGO_SIZE)
    gradient.setColorAt(0, QColor(BLUE))
    gradient.setColorAt(1, QColor(VIOLET))
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(QRectF(0, 0, LOGO_SIZE, LOGO_SIZE), 10, 10)
    pen = QPen(QColor(LOGO_GLYPH), 2.4)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    points = [(9, 19), (14, 19), (17, 12), (21, 25), (24, 17), (28, 17)]
    painter.drawPolyline([QPointF(x, y) for x, y in points])


def logo_pixmap(canvas: int, margin_fraction: float = 0.0) -> QPixmap:
    """The logo on a transparent square canvas. ``margin_fraction`` leaves padding on
    each side (macOS app icons use ~10%, so they line up with other Dock icons)."""
    pixmap = QPixmap(canvas, canvas)
    pixmap.fill(Qt.transparent)
    margin = canvas * margin_fraction
    painter = QPainter(pixmap)
    painter.translate(margin, margin)
    painter.scale((canvas - 2 * margin) / LOGO_SIZE, (canvas - 2 * margin) / LOGO_SIZE)
    paint_logo(painter)
    painter.end()
    return pixmap


def logo_icon() -> QIcon:
    return QIcon(logo_pixmap(512, margin_fraction=0.1))


class LogoMark(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(LOGO_SIZE, LOGO_SIZE)

    def paintEvent(self, _):
        painter = QPainter(self)
        paint_logo(painter)
