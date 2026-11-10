"""Animation intensity helpers for preview events."""


def clamp_strength(value: float) -> float:
    return max(0.0, min(1.0, value))


def pose_duration(base_duration: float, strength: float) -> float:
    """Shorter, sharper animations for stronger hits."""
    strength = clamp_strength(strength)
    return base_duration * (1.0 - (strength * 0.5))
