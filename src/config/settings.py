"""Application behaviour constants (timing, history, window size).

Visual design tokens (colors, fonts) live in ``theme.py``.
"""

APP_NAME = "System Monitor"

# How much history the charts show, and how long samples are kept beyond that.
HISTORY_SECONDS = 60
HISTORY_RETENTION_MARGIN_SECONDS = 5

# Sampling: how often psutil is polled. (label, milliseconds)
SAMPLE_INTERVAL_OPTIONS = (("0.5 s", 500), ("1 s", 1000), ("2 s", 2000), ("5 s", 5000))
DEFAULT_SAMPLE_INTERVAL_MS = 1000

# Top processes view: how many rows (refreshed with each sample while the view is shown).
TOP_PROCESS_COUNT = 6

# Rendering:~60 fps, independent of the sampling interval.
RENDER_INTERVAL_MS = 16

# Animation easing time constants (seconds).
VALUE_EASE_SECONDS = 0.25      # newest chart point easing to a new sample
SCALE_EASE_SECONDS = 0.6       # auto Y-scale easing
CORE_BAR_EASE_SECONDS = 0.2    # per-core bars easing

# Vertical gap between page sections (header, tiles, chart grid). The header's own
# horizontal spacing uses the same value, as it did when it was a nested layout.
SECTION_SPACING = 22

# Window geometry (width, height).
WINDOW_SIZE = (1360, 900)
WINDOW_MIN_SIZE = (1040, 700)
