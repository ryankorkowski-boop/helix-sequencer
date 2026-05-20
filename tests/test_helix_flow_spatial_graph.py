from __future__ import annotations

from pathlib import Path

from core.helix_flow_spatial_graph import (
    SpatialNode,
    build_spatial_graph,
    fallback_spatial_nodes,
    parse_xlights_spatial_nodes,
)


def test_parse_xlights_spatial_nodes_reads_coordinates(tmp_path: Path) -> None:
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text(
        '<xrgb><models>'
        '<model name="Left" WorldPosX="0" WorldPosY="10" WorldPosZ="0" />'
        '<model name="Right" WorldPosX="100" WorldPosY="20" WorldPosZ="5" />'
        '</models></xrgb>',
        encoding="utf-8",
    )

    nodes = parse_xlights_spatial_nodes(layout)

    assert nodes == (
        SpatialNode(name="Left", x=0.0, y=10.0, z=0.0),
        SpatialNode(name="Right", x=100.0, y=20.0, z=5.0),
    )


def test_spatial_graph_orders_by_direction() -> None:
    graph = build_spatial_graph(model_names=("A", "B", "C"), layout_path=Path("missing.xml"))

    assert [node.name for node in graph.ordered_for_direction("left_to_right")] == ["A", "B", "C"]
    assert [node.name for node in graph.ordered_for_direction("right_to_left")] == ["C", "B", "A"]


def test_spatial_graph_top_down_uses_z_axis() -> None:
    graph = build_spatial_graph(model_names=("A", "B", "C", "D", "E", "F"), layout_path=Path("missing.xml"))

    ordered = graph.ordered_for_direction("top_down")

    assert ordered[0].z >= ordered[-1].z


def test_nearest_neighbors_are_deterministic() -> None:
    graph = build_spatial_graph(model_names=("A", "B", "C", "D"), layout_path=Path("missing.xml"))

    first = graph.nearest_neighbors("B", count=2)
    second = graph.nearest_neighbors("B", count=2)

    assert first == second
    assert len(first) == 2
    assert "B" not in first


def test_fallback_spatial_nodes_are_deterministic() -> None:
    first = fallback_spatial_nodes(("A", "B", "C"))
    second = fallback_spatial_nodes(("A", "B", "C"))

    assert first == second
    assert [node.name for node in first] == ["A", "B", "C"]


def test_build_spatial_graph_uses_layout_when_available(tmp_path: Path) -> None:
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text(
        '<xrgb><models>'
        '<model name="B" WorldPosX="200" WorldPosY="0" WorldPosZ="0" />'
        '<model name="A" WorldPosX="100" WorldPosY="0" WorldPosZ="0" />'
        '</models></xrgb>',
        encoding="utf-8",
    )

    graph = build_spatial_graph(layout_path=layout, model_names=("A", "B"))

    assert [node.name for node in graph.ordered_for_direction("left_to_right")] == ["A", "B"]
