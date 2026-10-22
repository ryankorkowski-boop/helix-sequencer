"""Preview diagnostic panels must not cover the user's model geometry."""
import numpy as np
from tools.preview_renderer import HouseRenderer, LayoutData, ModelGeom


def scene():
    top = ModelGeom("Top", 0, 100, 20, 100, ((0, 100), (20, 100)), "Single Line", (255, 255, 255))
    bottom = ModelGeom("Bottom", 0, 0, 100, 0, ((0, 0), (100, 0)), "Single Line", (255, 255, 255))
    return HouseRenderer(LayoutData({"Top": top, "Bottom": bottom}, {}, (0, 0, 100, 100)), 640, 360)


def frame(renderer, values, **options):
    return renderer.render_frame(["Top", "Bottom"], np.array(values), "Source title", 200, 1000, {}, **options)


def test_default_preview_has_no_burned_in_diagnostic_panels():
    renderer = scene()
    assert frame(renderer, [0, 0]).tobytes() == renderer._base_canvas.tobytes()


def test_upper_lights_remain_visible_and_legacy_debug_panels_are_opt_in():
    renderer = scene()
    clean = frame(renderer, [1, 0])
    diagnostic = frame(renderer, [1, 0], diagnostic_overlay=True)
    assert min(clean.getpixel((100, 60))[:3]) > 240
    assert max(diagnostic.getpixel((100, 60))[:3]) < 100
