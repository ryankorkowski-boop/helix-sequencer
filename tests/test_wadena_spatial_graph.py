from core.wadena_spatial_graph import wadena_spatial_graph


def test_left_to_right_order_is_physical() -> None:
    graph = wadena_spatial_graph()
    order = graph.order("left_to_right")
    assert order.index("LEFT_TREE") < order.index("BLVD_CENTER") < order.index("RIGHT_LINDEN")


def test_right_to_left_is_exact_reverse_of_x_order() -> None:
    graph = wadena_spatial_graph()
    assert graph.order("right_to_left") == tuple(reversed(graph.order("left_to_right")))


def test_center_out_starts_at_hero() -> None:
    graph = wadena_spatial_graph()
    assert graph.order("center_out")[0] == "WREATH"


def test_route_is_deterministic_and_uses_named_neighbors() -> None:
    graph = wadena_spatial_graph()
    assert graph.route("LEFT_TREE", "RIGHT_LINDEN") == (
        "LEFT_TREE",
        "BLVD_LEFT",
        "BLVD_CENTER",
        "BLVD_RIGHT",
        "RIGHT_LINDEN",
    )


def test_unknown_route_fails_safe() -> None:
    graph = wadena_spatial_graph()
    assert graph.route("NOT_A_PROP", "WREATH") == ()
