"""Window header: logo, title, live badge and the refresh-interval selector."""
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from config.settings import APP_NAME, SECTION_SPACING
from ui.components.interval_selector import IntervalSelector
from ui.components.labels import make_label
from ui.components.live_badge import LiveBadge
from ui.components.logo_mark import LogoMark
from ui.theme import TEXT


class Header(QWidget):
    def __init__(self, subtitle):
        super().__init__()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label(APP_NAME, 18, TEXT, QFont.DemiBold))
        titles.addWidget(make_label(subtitle, 12))
        brand = QHBoxLayout()
        brand.setSpacing(14)
        brand.addWidget(LogoMark())
        brand.addLayout(titles)

        self.live_badge = LiveBadge()
        self.interval_selector = IntervalSelector()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SECTION_SPACING)
        layout.addLayout(brand)
        layout.addStretch(1)
        layout.addWidget(self.live_badge)
        layout.addSpacing(8)
        layout.addWidget(self.interval_selector)

    def refresh_live_badge(self):
        self.live_badge.update()
