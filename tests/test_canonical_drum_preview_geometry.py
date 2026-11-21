"""Canonical preview kit geometry regression (does not claim native xLights approval)."""
from tools.performer_preview_renderer import BandRenderer


class CaptureDraw:
    def __init__(self):
        self.ellipses = []
        self.lines = []
    def ellipse(self, xy, **kwargs):
        self.ellipses.append((xy, kwargs))
    def line(self, xy, **kwargs):
        self.lines.append((xy, kwargs))


def test_canonical_kit_has_nine_distinct_percussion_pieces():
    draw = CaptureDraw()
    # No image/FFmpeg dependencies needed for this geometry-only check.
    BandRenderer.drums(None, draw, 170, 330, 1.0, 0.0, 0.0)
    # Four cymbals + five shells (2 rack toms, floor, snare, kick)
    # plus the bass-drum snowflake inset.
    assert len(draw.ellipses) == 10
    assert len(draw.lines) >= 10
    assert all(xy[0] < xy[2] and xy[1] < xy[3] for xy, _ in draw.ellipses)
