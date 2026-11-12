"""Headline-number tile: label, big value, unit, one-line detail."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ui.components.card import Card
from ui.components.labels import make_label
from ui.theme import MUTED, TEXT


class KpiTile(Card):
    def __init__(self, title, accent):
        super().__init__(accent)
        self.value_label = make_label("–", 34, TEXT, QFont.DemiBold)
        self.unit_label = make_label("", 15, MUTED, QFont.Medium)
        self.detail_label = make_label("", 12, MUTED)
        title_label = make_label(title.upper(), 11, MUTED, QFont.Medium)
        title_label.setFont(self._with_letter_spacing(title_label.font()))

        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        value_row.addWidget(self.value_label, 0, Qt.AlignBottom)
        value_row.addWidget(self.unit_label, 0, Qt.AlignBottom)
        value_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        layout.addWidget(title_label)
        layout.addLayout(value_row)
        layout.addWidget(self.detail_label)

    @staticmethod
    def _with_letter_spacing(font):
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        return font

    def set_values(self, value, unit, detail):
        self.value_label.setText(value)
        self.unit_label.setText(unit)
        self.detail_label.setText(detail)
