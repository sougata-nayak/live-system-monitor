"""Static facts about the machine (read once at startup)."""
import platform
import sys

import psutil

from monitors.models import SystemInfo


def read_system_info() -> SystemInfo:
    logical = psutil.cpu_count(logical=True)
    physical = psutil.cpu_count(logical=False) or logical
    os_name = "macOS" if sys.platform == "darwin" else platform.system()
    return SystemInfo(logical, physical, os_name)


def battery_available() -> bool:
    try:
        return bool(hasattr(psutil, "sensors_battery") and psutil.sensors_battery())
    except Exception:
        return False
