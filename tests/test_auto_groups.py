"""Geometry-only prop grouping. Does not depend on the unmerged v2 layout builders."""
import numpy as np

from helix_spatial.auto_groups import auto_group, detect_prop


class Model:
    def __init__(self, name, points):
        self.name = name
        self.points = np.asarray(points, dtype=float)
        self.kind = "pixel"
        self.zone = "UNKNOWN"
        self.details = {}


def _arch(cx):
    pts = []
    for i in range(24):
        ang = np.pi * (1 - i / 23)
        pts.append((cx + np.cos(ang) * 6, np.sin(ang) * 8, 0.0))
    return pts


def _cone(cx, height):
    pts = []
    for y in np.linspace(0, height, 10):
        radius = 4 * (1 - y / height)
        for ang in np.linspace(0, 2 * np.pi, 10, endpoint=False):
            pts.append((cx + radius * np.cos(ang), y, radius * np.sin(ang)))
    return pts


def test_geometry_classifier_ignores_names():
    arch = detect_prop(_arch(0))[0]
    mini = detect_prop(_cone(-20, 12))[0]
    mega = detect_prop(_cone(0, 36))[0]
    assert arch == "arch"
    assert mini == "mini_tree"
    assert mega == "mega_tree"


def test_auto_group_orders_arches_and_keeps_phase_monotonic():
    models = [Model(f"A{i}", _arch(x)) for i, x in enumerate((-30, -10, 10, 30))]
    models += [Model(f"T{i}", _cone(x, 12)) for i, x in enumerate((-40, -28, 28, 40))]
    for model in models:
        model.name, model.zone = "X", "UNKNOWN"
    report = auto_group(models, role_for_prop={"mini_tree": "guitarist", "arch": "drummer"})
    arches = [m for m in models if m.details["auto_prop"] == "arch"]
    assert len({m.details["auto_group"] for m in arches}) == 1
    ordered = sorted(arches, key=lambda m: m.points[:, 0].mean())
    assert [m.details["percussion_component"] for m in ordered] == ["kick", "snare", "hihat", "cymbal"]
    trees = [m for m in models if m.details["auto_prop"] == "mini_tree"]
    assert len({m.details["auto_group"] for m in trees}) == 2
    assert all(m.details["source_route_count"] == 2 for m in trees)
    phases = sorted((m.points[:, 0].mean(), m.details["spatial_phase"]) for m in models)
    assert all(pa <= pb for (xa, pa) in phases for (xb, pb) in phases if xa < xb - 1)
    assert report["group_count"] >= 2
