"""Segmented control: a row of mutually exclusive pill buttons."""
from typing import Any, Sequence, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton

from ui.theme import CARD, MUTED, SEGMENT_ACTIVE, TEXT

_SIZES = {  # name -> (outer radius, button radius, padding, font px)
    "regular": (11, 8, "6px 14px", 12),
    "compact": (9, 6, "3px 10px", 11),
}


class SegmentedControl(QFrame):
    """Emits ``selected(value)`` when the user picks an option."""

    selected = Signal(object)

    def __init__(self, options: Sequence[Tuple[str, Any]], initial_value: Any, size: str = "regular"):
        super().__init__()
        outer_radius, button_radius, padding, font_px = _SIZES[size]
        self.setObjectName("segmented_control")
        self.setStyleSheet(
            f"QFrame#segmented_control {{ background:{CARD}; border:1px solid rgba(255,255,255,18);"
            f" border-radius:{outer_radius}px; }}"
            f"QPushButton {{ color:{MUTED}; background:transparent; border:none;"
            f" border-radius:{button_radius}px; padding:{padding}; font-size:{font_px}px;"
            " font-weight:500; }"
            f"QPushButton:hover {{ color:{TEXT}; }}"
            f"QPushButton:checked {{ color:{TEXT}; background:{SEGMENT_ACTIVE}; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.button_group = QButtonGroup(self)
        for index, (text, value) in enumerate(options):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setChecked(value == initial_value)
            button.clicked.connect(lambda _=False, v=value: self.selected.emit(v))
            self.button_group.addButton(button, index)
            layout.addWidget(button)
