from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from core.custom_model_grid import parse_custom_model_attributes
from core.model_parser import parse_layout
from helix_layout.layout_health import build_layout_health_report

ROOT = Path(__file__).resolve().parents[1]


def _layout(path: Path, extra: str = "") -> None:
    path.write_text(
        f"""
        <xrgb>
          <models>
            <model name="Sign" DisplayAs="Custom" StringType="RGB Nodes"
              WorldPosX="0" WorldPosY="0" WorldPosZ="0" X2="10" Y2="20" Z2="0"
              StartChannel="1" CustomModel="1,2;3," {extra}/>
          </models>
        </xrgb>
        """,
        encoding="utf-8",
    )


def test_plain_grid_node_count_order_and_world_bounds(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    _layout(path, 'subModel=""')
    # The attribute above is ignored; submodels are child elements.
    root = ET.parse(path).getroot()
    model_el = root.find("./models/model")
    assert model_el is not None
    ET.SubElement(model_el, "subModel", {"name": "Tail", "line0": "3"})
    ET.SubElement(model_el, "subModel", {"name": "Pair", "line0": "2-3"})
    ET.ElementTree(root).write(path, encoding="utf-8")

    parsed = parse_layout(path)
    sign = parsed.models["Sign"]
    assert sign.total_pixels == 3
    assert sign.custom_grid_missing is False
    pixels = sign.virtual_pixel_map()
    assert [point.index for point in pixels] == [0, 1, 2]
    assert [point.node_index for point in pixels] == [0, 1, 2]
    assert pixels[0].x == 2.5
    assert pixels[0].y == 15.0
    assert pixels[2].x == 2.5
    assert pixels[2].y == 5.0
    for point in pixels:
        assert 0.0 <= point.x <= 10.0
        assert 0.0 <= point.y <= 20.0
        assert point.z == 0.0

    tail = parsed.models["Sign/Tail"]
    assert tail.total_pixels == 1
    assert tail.geometry_points == [(pixels[2].x, pixels[2].y, pixels[2].z)]
    pair = parsed.models["Sign/Pair"]
    assert [point[:2] for point in pair.geometry_points] == [(pixels[1].x, pixels[1].y), (pixels[2].x, pixels[2].y)]
    assert sign.end_channel == 9
    assert tail.start_channel == 7
    assert tail.end_channel == 9


def test_compressed_grid_matches_plain_and_wins_when_both_are_present() -> None:
    plain = parse_custom_model_attributes({"CustomModel": "1,2;3,"})
    compressed = parse_custom_model_attributes({"CustomModelCompressed": "1,0,0;2,0,1;3,1,0"})
    assert plain is not None and compressed is not None
    assert [(node.number, node.column, node.row, node.layer) for node in plain.nodes] == [
        (node.number, node.column, node.row, node.layer) for node in compressed.nodes
    ]
    both = parse_custom_model_attributes(
        {"CustomModel": "9,9;9,9", "CustomModelCompressed": "1,0,0;2,0,1;3,1,0"}
    )
    assert both is not None
    assert both.source == "CustomModelCompressed"
    assert [node.number for node in both.nodes] == [1, 2, 3]


def test_layers_duplicate_nodes_and_empty_cells() -> None:
    layered = parse_custom_model_attributes({"CustomModel": "1|2"})
    assert layered is not None
    assert layered.depth == 2
    assert [(node.number, node.layer) for node in layered.nodes] == [(1, 0), (2, 1)]
    compressed = parse_custom_model_attributes({"CustomModelCompressed": "4,1,2,1;5,0,0,0"})
    assert compressed is not None
    assert compressed.width == 3
    assert compressed.height == 2
    assert compressed.depth == 2
    assert [node.number for node in compressed.nodes] == [4, 5]
    duplicates = parse_custom_model_attributes({"CustomModel": "1,1;0,"})
    assert duplicates is not None
    assert len(duplicates.nodes) == 1
    assert duplicates.nodes[0].column == 0
    assert duplicates.nodes[0].row == 0


def test_missing_grid_is_a_layout_health_error_and_has_no_fake_pixels(tmp_path: Path) -> None:
    path = tmp_path / "layout.xml"
    path.write_text(
        """
        <xrgb>
          <models>
            <model name="Blank" DisplayAs="Custom" StringType="RGB Nodes"
              WorldPosX="0" WorldPosY="0" WorldPosZ="0" X2="24" Y2="18" Z2="0"
              StartChannel="1" CustomWidth="12" CustomHeight="12" parm1="12" parm2="12">
              <subModel name="HEAD" line0="1-4"/>
            </model>
          </models>
        </xrgb>
        """,
        encoding="utf-8",
    )
    parsed = parse_layout(path)
    blank = parsed.models["Blank"]
    assert blank.custom_grid_missing is True
    assert blank.total_pixels == 0
    assert blank.virtual_pixel_map() == []
    head = parsed.models["Blank/HEAD"]
    assert head.geometry_points == []
    assert head.total_pixels == 0
    assert "custom-model grid" in (head.start_channel_error or "")
    report = build_layout_health_report(path)
    assert report.custom_models_missing_grid == ["Blank"]


def test_helixville4_custom_models_have_no_authored_grid() -> None:
    layout = ROOT / "helixville4" / "xlights_rgbeffects.xml"
    parsed = parse_layout(layout)
    missing = [
        name
        for name, model in parsed.models.items()
        if not model.is_submodel and model.display_as == "Custom" and model.custom_grid_missing
    ]
    assert len(missing) == 24
    sign = parsed.models["HX_HOUSE_1_4_CUSTOM"]
    assert sign.total_pixels == 0
    assert sign.virtual_pixel_map() == []
    head = parsed.models["HX_HOUSE_1_4_CUSTOM/HEAD"]
    assert head.geometry_points == []
    report = build_layout_health_report(layout)
    assert "HX_HOUSE_1_4_CUSTOM" in report.custom_models_missing_grid
    assert len(report.custom_models_missing_grid) == 24
