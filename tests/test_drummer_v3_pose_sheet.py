from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_v3_poses

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "fixtures/band_geometry/drummer_v3_pose_spec.json"
SOURCE = ROOT / "fixtures/band_geometry/source/drummerbg.png"
POSE_SHEET = ROOT / "fixtures/band_geometry/previews/HX_SNOWMAN_DRUMMER_V3_pose_sheet.png"
XMODEL = ROOT / "fixtures/band_geometry/models/HX_SNOWMAN_DRUMMER_V3.xmodel"
RANGE_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")
CANONICAL_SURFACES = {
    "HX_SNOWMAN_DRUMMER_V3_TOM_HIGH_SURFACE",
    "HX_SNOWMAN_DRUMMER_V3_TOM_MID_SURFACE",
    "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR_SURFACE",
}


def _ranges(value: str) -> set[int]:
    nodes: set[int] = set()
    for chunk in value.split(","):
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            nodes.update(range(int(a), int(b) + 1))
        else:
            nodes.add(int(chunk))
    return nodes


def _submodels() -> dict[str, set[int]]:
    root = ET.parse(XMODEL).getroot()
    return {s.attrib["name"]: _ranges(s.attrib.get("line0", "")) for s in root.findall("./subModels/subModel")}


def _centroid(nodes: set[int], width: int = 96) -> tuple[float, float]:
    points = [((n - 1) % width, (n - 1) // width) for n in nodes]
    return sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)


def test_drummer_v3_source_and_pose_sheet_are_real_images() -> None:
    assert SOURCE.exists()
    assert POSE_SHEET.exists()
    with Image.open(SOURCE) as source:
        assert source.format == "PNG" and source.width >= 128 and source.height >= 128
    with Image.open(POSE_SHEET) as sheet:
        assert sheet.format == "PNG" and sheet.getbbox() is not None


def test_pose_spec_is_three_tom_eight_target_source_normalized_contract() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["schema"] == "helix.drummer_v3_pose_spec.v6"
    assert spec["canonical_toms"] == ["HIGH", "MID", "FLOOR"]
    assert len(spec["lighting_targets"]) == 8
    zones = {zone["id"]: zone for zone in spec["zones"]}
    assert {"TOM_HIGH_SURFACE", "TOM_MID_SURFACE", "TOM_FLOOR_SURFACE"} <= zones.keys()
    assert "TOM_4_SURFACE" not in zones
    for zone in zones.values():
        for command in zone["commands"]:
            assert command["shape"] == "polygon"
            assert all(0.0 <= value <= 1.0 for point in command["points"] for value in point)

    target_map = {target["id"]: target for target in spec["lighting_targets"]}
    assert target_map["KICK"]["actuators"] == []
    assert target_map["HI_HAT"]["actuators"] == ["HI_HAT_FOOT"]
    assert target_map["TOM_HIGH"]["actuators"] == ["TOM_HIGH_ARM_STICK"]
    assert target_map["TOM_MID"]["actuators"] == ["TOM_MID_ARM_STICK"]
    assert target_map["TOM_FLOOR"]["actuators"] == ["TOM_FLOOR_ARM_STICK"]


def test_xmodel_has_dense_grid_and_surface_orientation() -> None:
    root = ET.parse(XMODEL).getroot()
    assert root.get("CustomModel")
    rows = root.get("CustomModel", "").split(";")
    assert len(rows) == 72 and all(len(row.split(",")) == 96 for row in rows)
    assert root.get("CustomBkgImage") == "../source/drummer_idle.png"
    assert root.get("HelixVisualSource") == "../source/drummerbg.png"
    submodels = {sm.get("name", ""): sm.get("line0", "") for sm in root.findall("./subModels/subModel")}
    assert CANONICAL_SURFACES <= set(submodels)
    for name, line0 in submodels.items():
        assert RANGE_RE.match(line0), f"{name} has invalid ranges: {line0}"

    high_x, high_y = _centroid(_ranges(submodels["HX_SNOWMAN_DRUMMER_V3_TOM_HIGH_SURFACE"]))
    mid_x, mid_y = _centroid(_ranges(submodels["HX_SNOWMAN_DRUMMER_V3_TOM_MID_SURFACE"]))
    floor_x, floor_y = _centroid(_ranges(submodels["HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR_SURFACE"]))
    assert high_x > 48 and mid_x < 48 and floor_x < 48
    assert high_x > mid_x
    assert floor_y > high_y and floor_y > mid_y
    assert max((n - 1) % 96 for n in _ranges(submodels["HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR_SURFACE"])) < 48


def test_public_targets_integrate_required_actuator_geometry() -> None:
    submodels = _submodels()
    cases = {
        "SNARE": "SNARE_ARM_STICK",
        "TOM_HIGH": "TOM_HIGH_ARM_STICK",
        "TOM_MID": "TOM_MID_ARM_STICK",
        "TOM_FLOOR": "TOM_FLOOR_ARM_STICK",
        "CYMBAL_LEFT": "CYMBAL_LEFT_ARM_STICK",
        "CYMBAL_RIGHT": "CYMBAL_RIGHT_ARM_STICK",
        "HI_HAT": "HI_HAT_FOOT",
    }
    for target, actuator in cases.items():
        public = submodels[f"HX_SNOWMAN_DRUMMER_V3_{target}"]
        surface = submodels[f"HX_SNOWMAN_DRUMMER_V3_{target}_SURFACE"]
        actuator_nodes = submodels[f"HX_SNOWMAN_DRUMMER_V3_{actuator}"]
        assert surface <= public
        assert public & actuator_nodes
    assert submodels["HX_SNOWMAN_DRUMMER_V3_KICK"] == submodels["HX_SNOWMAN_DRUMMER_V3_KICK_SURFACE"]


def test_detected_events_map_to_exact_public_components_and_three_tom_poses() -> None:
    events = [
        DrumEvent(0.10, 0.8, 0.7, {}, 1, "kick", "test"),
        DrumEvent(0.20, 0.9, 0.8, {}, 2, "snare", "test"),
        DrumEvent(0.30, 0.5, 0.7, {}, 3, "hihat", "test"),
        DrumEvent(0.40, 0.7, 0.7, {"tom_class": "high"}, 4, "tom", "test"),
        DrumEvent(0.50, 0.7, 0.7, {"tom_class": "mid"}, 5, "tom", "test"),
        DrumEvent(0.60, 0.7, 0.7, {"tom_class": "floor"}, 6, "tom", "test"),
        DrumEvent(0.70, 1.0, 0.8, {}, 7, "cymbal", "test"),
        DrumEvent(0.90, 1.0, 0.8, {}, 8, "cymbal", "test"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    assert [event["component"] for event in mapped[:6]] == [
        *DRUMMER_COMPONENTS[:3],
        *DRUMMER_COMPONENTS[3:6],
    ]
    assert [event["pose"] for event in mapped[3:6]] == [
        "tom_high_hit",
        "tom_mid_hit",
        "tom_floor_hit",
    ]
    assert mapped[6]["pose"] == "left_crash"
    assert mapped[6]["components"] == [DRUMMER_COMPONENTS[6]]
    assert mapped[7]["pose"] == "right_crash"
    assert mapped[7]["components"] == [DRUMMER_COMPONENTS[7]]
    assert all(set(event["submodels"]).issubset(set(DRUMMER_COMPONENTS)) for event in mapped)

