import math

import pytest

from utils.animation import ease_factor
from utils.formatting import (
    format_byte_rate,
    format_bytes,
    format_percent,
    format_uptime,
    split_bytes,
)


@pytest.mark.parametrize("n, expected", [
    (0, ("0", "B")),
    (512, ("512", "B")),
    (1024, ("1.0", "KB")),
    (1536, ("1.5", "KB")),
    (150 * 1024, ("150", "KB")),
    (5 * 1024 ** 3, ("5.0", "GB")),
    (3 * 1024 ** 5, ("3072", "TB")),  # TB is the largest unit
])
def test_split_bytes(n, expected):
    assert split_bytes(n) == expected


def test_format_helpers():
    assert format_bytes(1024 ** 2) == "1.0 MB"
    assert format_byte_rate(2048) == "2.0 KB/s"
    assert format_percent(42.6) == "43%"


def test_format_uptime():
    assert format_uptime(0) == "0d 0h 0m"
    assert format_uptime(3 * 86400 + 7 * 3600 + 21 * 60 + 59) == "3d 7h 21m"


def test_ease_factor():
    assert ease_factor(0.0, 0.25) == 0.0
    assert ease_factor(0.25, 0.25) == pytest.approx(1 - math.exp(-1))
    # Frame-rate independent: two half steps == one full step.
    half = ease_factor(0.1, 0.25)
    assert 1 - (1 - half) ** 2 == pytest.approx(ease_factor(0.2, 0.25))
