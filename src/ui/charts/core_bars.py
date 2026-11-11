"""Two-column list of per-core load bars with eased fills."""
import numpy as np
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from config.settings import CORE_BAR_EASE_SECONDS
from ui.theme import AMBER, BLUE, MUTED, PINK, TEXT, ui_font
from utils.animation import ease_factor


class CoreBars(QWidget):
    def __init__(self, core_count):
        super().__init__()
        self.core_count = core_count
        self.target_loads = np.zeros(core_count)
        self.displayed_loads = np.zeros(core_count)
        self.setMinimumHeight(max(60, ((core_count + 1) // 2) * 26))

    def advance_frame(self, dt):
        self.displayed_loads += (self.target_loads - self.displayed_loads) * ease_factor(
            dt, CORE_BAR_EASE_SECONDS)
        self.update()

    @staticmethod
    def color_for_load(percent):
        return PINK if percent > 75 else (AMBER if percent > 50 else BLUE)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rows = (self.core_count + 1) // 2
        column_gap, row_height = 24, min(30, self.height() / max(rows, 1))
        column_width = (self.width() - column_gap) / 2
        top = (self.height() - rows * row_height) / 2
        for i in range(self.core_count):
            column, row = divmod(i, rows)
            x = column * (column_width + column_gap)
            y = top + row * row_height
            load = float(self.displayed_loads[i])
            painter.setFont(ui_font(13))
            painter.setPen(QColor(MUTED))
            painter.drawText(QRectF(x, y, 24, row_height), Qt.AlignVCenter | Qt.AlignLeft, str(i))
            track = QRectF(x + 30, y + row_height / 2 - 4, column_width - 30 - 52, 8)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 15))
            painter.drawRoundedRect(track, 4, 4)
            fill = QRectF(track.left(), track.top(), max(track.width() * load / 100, 0), track.height())
            if fill.width() > 0:
                painter.setBrush(QColor(self.color_for_load(load)))
                painter.drawRoundedRect(fill, 4, 4)
            painter.setPen(QColor(TEXT))
            painter.drawText(QRectF(track.right() + 6, y, 46, row_height),
                             Qt.AlignVCenter | Qt.AlignRight, f"{load:.0f}%")
