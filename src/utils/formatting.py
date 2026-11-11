"""Pure functions that turn numbers into display strings."""
from typing import Tuple

_BYTE_UNITS = ("B", "KB", "MB", "GB", "TB")


def split_bytes(n: float) -> Tuple[str, str]:
    """Return ('1.2', 'MB') for a byte count."""
    i = 0
    while abs(n) >= 1024 and i < len(_BYTE_UNITS) - 1:
        n /= 1024
        i += 1
    return (f"{n:.0f}" if n >= 100 or i == 0 else f"{n:.1f}"), _BYTE_UNITS[i]


def format_bytes(n: float) -> str:
    value, unit = split_bytes(n)
    return f"{value} {unit}"


def format_byte_rate(n: float) -> str:
    return format_bytes(n) + "/s"


def format_percent(value: float) -> str:
    return f"{value:.0f}%"


def format_uptime(seconds: int) -> str:
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    return f"{days}d {hours}h {remainder // 60}m"
