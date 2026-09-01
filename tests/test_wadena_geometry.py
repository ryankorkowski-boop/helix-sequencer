from math import hypot

from core.wadena_geometry import ConeTree, MegaTree, Point3, SpiralTree


def test_spiral_tree_has_shared_rgw_geometry_and_apex_descent():
    tree = SpiralTree(center=Point3(0, 0, 0), height=10, base_radius=2, up_turns=3, down_turns=2)
    paths = tree.paths()
    assert [p.color for p in paths] == ["red", "green", "white"]
    assert paths[0].points == paths[1].points == paths[2].points
    points = paths[0].points
    assert max(p.y for p in points) == 10
    # The path rises, reaches the apex, then visibly descends.
    apex_index = max(range(len(points)), key=lambda i: points[i].y)
    assert apex_index > 0
    assert apex_index < len(points) - 1
    assert points[-1].y < points[apex_index].y
    # The descending spiral is intentionally broader than the trunk radius.
    max_desc_radius = max(hypot(p.x, p.z) for p in points[apex_index:])
    assert max_desc_radius > 2.0


def test_spiral_direction_is_deterministic():
    cw = SpiralTree(Point3(0, 0, 0), 10, 2, clockwise=True).paths()[0].points
    ccw = SpiralTree(Point3(0, 0, 0), 10, 2, clockwise=False).paths()[0].points
    assert cw != ccw
    assert cw[1].x == ccw[1].x
    assert cw[1].z == -ccw[1].z


def test_cone_tree_is_tapered_physical_placeholder():
    tree = ConeTree(Point3(5, 0, 7), 3, 1)
    paths = tree.paths()
    assert len(paths) == 3
    assert all(path.points[0] == Point3(5, 0, 7) for path in paths)
    assert all(path.points[-1] == Point3(5, 3, 7) for path in paths)


def test_mega_tree_has_many_strings_and_circular_ring():
    tree = MegaTree(Point3(0, 0, 0), 12, 4, string_count=32)
    strings = tree.string_points()
    assert len(strings) == 32
    assert all(len(s) >= 2 for s in strings)
    ring = tree.ring(0.5)
    assert len(ring) >= 32
    assert len({(round(p.x, 6), round(p.y, 6), round(p.z, 6)) for p in ring}) == len(ring)
    assert all(abs(p.y - 6.0) < 1e-9 for p in ring)


def test_invalid_geometry_is_rejected():
    try:
        SpiralTree(Point3(0, 0, 0), 0, 1).paths()
    except ValueError:
        pass
    else:
        raise AssertionError("zero-height spiral must be rejected")
