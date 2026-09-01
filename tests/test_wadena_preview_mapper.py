from core.wadena_preview_mapper import map_model_path


def test_blvd_maps_to_clockwise_spiral_path() -> None:
    mapped = map_model_path("Left Blvd Red", ((0.0, 0.0), (0.0, 40.0)))
    assert mapped is not None
    assert mapped.kind == "spiral_tree"
    assert len(mapped.points) > 50
    assert max(x for x, _ in mapped.points) > 0
    assert min(x for x, _ in mapped.points) < 0


def test_perimeter_linden_uses_spiral_geometry() -> None:
    mapped = map_model_path("Right Linden White", ((100.0, 10.0), (100.0, 55.0)))
    assert mapped is not None
    assert mapped.kind == "spiral_tree"
    assert mapped.points[0][1] < mapped.points[len(mapped.points) // 3][1]


def test_mini_tree_maps_to_tapered_cone_path() -> None:
    mapped = map_model_path("Mini Tree 7 Green", ((20.0, 0.0), (20.0, 20.0)))
    assert mapped is not None
    assert mapped.kind == "cone_tree"
    assert len(mapped.points) >= 40
    first_radius = abs(mapped.points[0][0] - 20.0)
    last_radius = abs(mapped.points[-1][0] - 20.0)
    assert last_radius <= first_radius


def test_unknown_model_preserves_legacy_geometry() -> None:
    points = ((1.0, 2.0), (3.0, 4.0))
    assert map_model_path("Arch 1", points) is None
