"""Visual design tokens: colors and the UI font."""
import sys
from typing import Optional

from PySide6.QtGui import QColor, QFont, QFontDatabase

# ---- Colors ----------------------------------------------------------------
BACKGROUND = "#090B0F"
CARD = "#12151C"
TEXT = "#E8EAF0"
MUTED = "#8B93A5"
SEGMENT_ACTIVE = "#232837"
LOGO_GLYPH = "#0A0C12"

BLUE, VIOLET, AMBER = "#5EA8FF", "#B28CFF", "#FFB454"
TEAL, ORANGE = "#3DDBB0", "#FF9A5C"
YELLOW, PINK = "#FFD166", "#FF6B8A"

# ---- Fonts -----------------------------------------------------------------
FONT_FAMILIES = ["Inter", "Segoe UI", "Roboto", "Arial"]  # non-macOS preference order
_font_family: Optional[str] = None


def with_alpha(hex_color: str, alpha: int) -> QColor:
    """Return ``hex_color`` as a QColor with the given alpha (0-255)."""
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


def ui_font(size: int, weight=QFont.Normal) -> QFont:
    """macOS: the system font (San Francisco). Elsewhere: first installed family."""
    global _font_family
    if _font_family is None:
        system = QFontDatabase.systemFont(QFontDatabase.GeneralFont).family()
        if sys.platform == "darwin":
            _font_family = system
        else:
            installed = set(QFontDatabase.families())
            _font_family = next((f for f in FONT_FAMILIES if f in installed), system)
    font = QFont(_font_family)
    font.setPixelSize(size)
    font.setWeight(weight)
    return font
