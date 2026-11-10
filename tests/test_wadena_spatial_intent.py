from core.wadena_spatial_intent import SpatialGesture, compile_gesture, propagate_route
from core.wadena_spatial_graph import wadena_spatial_graph


def test_explicit_route_preserves_physical_topology() -> None:
    intents = propagate_route("LEFT_TREE", "RIGHT_LINDEN", strength=0.8)
    assert tuple(item.landmark for item in intents) == (
        "LEFT_TREE",
        "BLVD_LEFT",
        "BLVD_CENTER",
        "BLVD_RIGHT",
        "RIGHT_LINDEN",
    )
    assert all(0.0 < item.weight <= 0.8 for item in intents)
    assert tuple(item.order for item in intents) == tuple(range(5))


def test_invalid_explicit_route_fails_safe() -> None:
    assert compile_gesture(SpatialGesture(start="NO_SUCH_PROP", end="WREATH")) == ()


def test_partial_explicit_route_fails_safe() -> None:
    assert compile_gesture(SpatialGesture(start="WREATH")) == ()


def test_strength_is_clamped_and_zero_is_silent() -> None:
    graph = wadena_spatial_graph()
    assert compile_gesture(SpatialGesture(direction="center_out", strength=0.0), graph) == ()
    intents = compile_gesture(SpatialGesture(direction="center_out", strength=4.0), graph)
    assert max(item.weight for item in intents) == 1.0


def test_directional_gesture_is_deterministic() -> None:
    graph = wadena_spatial_graph()
    first = compile_gesture(SpatialGesture(direction="right_to_left", spread=2.0), graph)
    second = compile_gesture(SpatialGesture(direction="right_to_left", spread=2.0), graph)
    assert first == second
    assert tuple(item.landmark for item in first) == graph.order("right_to_left")


def test_spread_changes_weights_not_topology() -> None:
    graph = wadena_spatial_graph()
    narrow = compile_gesture(SpatialGesture(direction="left_to_right", spread=0.5), graph)
    broad = compile_gesture(SpatialGesture(direction="left_to_right", spread=4.0), graph)
    assert tuple(item.landmark for item in narrow) == tuple(item.landmark for item in broad)
    assert narrow != broad
