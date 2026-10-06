"""Canonical drummer geometry correction: keep exactly three toms.

Ground-truth image mapping:
  TOM_HIGH  -> upper-left tom (#11)
  TOM_MID   -> upper-right tom (#12)
  TOM_FLOOR -> lower-left large drum (#7)
  lower-right drum (#8) is not a tom.

This helper is intentionally explicit so future xmodel generation cannot infer
TOM_FLOOR from the right-hand drum.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TomZone:
    name: str
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float


# Coordinates are in the 83x57 ground-truth grid shown in drummerbg.png.
CANONICAL_TOMS = (
    TomZone("TOM_HIGH", 25.0, 31.0, 6.0, 5.0),
    TomZone("TOM_MID", 61.0, 31.0, 6.0, 5.0),
    TomZone("TOM_FLOOR", 23.0, 43.0, 8.0, 8.0),
)

# Explicit exclusion: the extra lower-right drum is not part of the drummer's
# three-tom performance model.
EXCLUDED_EXTRA_DRUM_CENTER = (78.0, 43.0)


def canonical_tom_zones():
    """Return the immutable three-tom ground-truth mapping."""
    return CANONICAL_TOMS


def is_extra_right_drum(x: float, y: float) -> bool:
    ex, ey = EXCLUDED_EXTRA_DRUM_CENTER
    return abs(x - ex) < 10 and abs(y - ey) < 10


if __name__ == "__main__":
    assert len(CANONICAL_TOMS) == 3
    assert not is_extra_right_drum(CANONICAL_TOMS[2].center_x, CANONICAL_TOMS[2].center_y)
    print("PASS: canonical drummer has exactly three tom zones; extra right drum excluded")
