"""Segmented control for the sampling interval."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton

from config.settings import DEFAULT_SAMPLE_INTERVAL_MS, SAMPLE_INTERVAL_OPTIONS
from ui.theme import CARD, MUTED, SEGMENT_ACTIVE, TEXT


class IntervalSelector(QFrame):
    """Emits the chosen interval in milliseconds."""

    interval_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"QFrame#interval_selector {{ background:{CARD}; border:1px solid rgba(255,255,255,18);"
            " border-radius:11px; }"
            f"QPushButton {{ color:{MUTED}; background:transparent; border:none;"
            " border-radius:8px; padding:6px 14px; font-size:12px; font-weight:500; }"
            f"QPushButton:hover {{ color:{TEXT}; }}"
            f"QPushButton:checked {{ color:{TEXT}; background:{SEGMENT_ACTIVE}; }}")
        self.setObjectName("interval_selector")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.button_group = QButtonGroup(self)
        for index, (text, milliseconds) in enumerate(SAMPLE_INTERVAL_OPTIONS):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setChecked(milliseconds == DEFAULT_SAMPLE_INTERVAL_MS)
            button.clicked.connect(
                lambda _=False, ms=milliseconds: self.interval_selected.emit(ms))
            self.button_group.addButton(button, index)
            layout.addWidget(button)
