"""Animation math."""
import math


def ease_factor(dt: float, tau: float) -> float:
    """Frame-rate independent exponential smoothing factor."""
    return 1.0 - math.exp(-dt / tau)
