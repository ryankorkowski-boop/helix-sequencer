"""Canonical drummer geometry correction: keep exactly three toms.

Ground-truth image mapping (viewer-facing image coordinates):
  TOM_HIGH  -> upper-right tom (#12), drummer's left
  TOM_MID   -> upper-left tom (#11), drummer's right
  TOM_FLOOR -> lower-left large drum (#7), drummer's right/lower
  lower-right drum (#8) is not a tom.

This helper is intentionally explicit so future xmodel generation cannot infer
TOM_FLOOR from the right-hand extra drum or reverse the High/Mid order.
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
# Viewer-facing image coordinates: right is the drummer's left.
CANONICAL_TOMS = (
    TomZone("TOM_HIGH", 61.0, 31.0, 6.0, 5.0),
    TomZone("TOM_MID", 25.0, 31.0, 6.0, 5.0),
    TomZone("TOM_FLOOR", 23.0, 43.0, 8.0, 8.0),
)

# Explicit exclusion: the extra lower-right viewer-facing drum is not part of
# the drummer's three-tom performance model.
EXCLUDED_EXTRA_DRUM_CENTER = (78.0, 43.0)


def canonical_tom_zones():
    """Return the immutable three-tom ground-truth mapping."""
    return CANONICAL_TOMS


def is_extra_right_drum(x: float, y: float) -> bool:
    ex, ey = EXCLUDED_EXTRA_DRUM_CENTER
    return abs(x - ex) < 10 and abs(y - ey) < 10


if __name__ == "__main__":
    assert len(CANONICAL_TOMS) == 3
    high, mid, floor = CANONICAL_TOMS
    assert high.name == "TOM_HIGH" and mid.name == "TOM_MID" and floor.name == "TOM_FLOOR"
    assert high.center_x > mid.center_x, "High tom must be viewer-right / drummer-left"
    assert floor.center_x < mid.center_x, "Floor tom must be viewer-left / drummer-right"
    assert floor.center_y > high.center_y and floor.center_y > mid.center_y, "Floor tom must be lower"
    assert not is_extra_right_drum(floor.center_x, floor.center_y)
    print("PASS: canonical drummer tom order is HIGH(right), MID(left), FLOOR(lower-left); extra right drum excluded")
