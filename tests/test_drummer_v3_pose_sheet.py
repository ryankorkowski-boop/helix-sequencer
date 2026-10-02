from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import DRUMMER_COMPONENTS, map_events_to_drummer_v3_poses

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
SOURCE = ROOT / "fixtures" / "band_geometry" / "source" / "drummerbg.png"
POSE_SHEET = ROOT / "fixtures" / "band_geometry" / "previews" / "HX_SNOWMAN_DRUMMER_V3_pose_sheet.png"
XMODEL = ROOT / "fixtures" / "band_geometry" / "models" / "HX_SNOWMAN_DRUMMER_V3.xmodel"
RANGE_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")
CANONICAL_TOM_ZONES = {"HX_SNOWMAN_DRUMMER_V3_TOM_HIGH", "HX_SNOWMAN_DRUMMER_V3_TOM_MID", "HX_SNOWMAN_DRUMMER_V3_TOM_FLOOR"}


def _ranges(value: str) -> set[int]:
    nodes: set[int] = set()
    for chunk in value.split(","):
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1); nodes.update(range(int(start_s), int(end_s) + 1))
        else: nodes.add(int(chunk))
    return nodes


def _submodels() -> dict[str, set[int]]:
    root = ET.parse(XMODEL).getroot()
    return {s.attrib["name"]: _ranges(s.attrib.get("line0", "")) for s in root.findall("./subModels/subModel")}


def test_drummer_v3_source_and_pose_sheet_are_real_images() -> None:
    assert SOURCE.exists(); assert POSE_SHEET.exists()
    with Image.open(SOURCE) as source: assert source.format == "PNG" and source.width >= 128 and source.height >= 128
    with Image.open(POSE_SHEET) as sheet: assert sheet.format == "PNG" and sheet.width > 0 and sheet.height > 0 and sheet.getbbox() is not None


def test_drummer_v3_pose_spec_is_three_tom_visual_first_contract() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["source_image"] == "fixtures/band_geometry/source/drummerbg.png"
    assert spec["source_image_b64"] == "fixtures/band_geometry/source/drummerbg.png.b64"
    assert spec["model_name"] == "HX_SNOWMAN_DRUMMER_V3"
    assert spec["canonical_tom_count"] == 3
    assert spec["canonical_toms"] == ["HIGH", "MID", "FLOOR"]
    zone_ids = {zone["id"] for zone in spec["zones"]}
    assert {"TOM_HIGH", "TOM_MID", "TOM_FLOOR"} <= zone_ids
    assert "TOM_4" not in zone_ids
    assert {"TOM_HIGH_CONTACT_STICK", "TOM_MID_CONTACT_STICK", "TOM_FLOOR_CONTACT_STICK"} <= zone_ids
    assert "TOM_4_CONTACT_STICK" not in zone_ids
    composites = {item["id"]: set(item["members"]) for item in spec["composites"]}
    assert {"TOM_HIGH", "TOM_HIGH_CONTACT_STICK"} <= composites["DRUMMER_TOM_HIGH"]
    assert {"TOM_MID", "TOM_MID_CONTACT_STICK"} <= composites["DRUMMER_TOM_MID"]
    assert {"TOM_FLOOR", "TOM_FLOOR_CONTACT_STICK"} <= composites["DRUMMER_TOM_FLOOR"]
    assert all("TOM_4" not in json.dumps(item) for item in spec["zones"] + spec["composites"])


def test_drummer_v3_xmodel_has_exactly_three_tom_zones() -> None:
    root = ET.parse(XMODEL).getroot()
    assert root.tag == "custommodel" and root.attrib["name"] == "HX_SNOWMAN_DRUMMER_V3"
    submodels = {s.attrib["name"]: s.attrib.get("line0", "") for s in root.findall("./subModels/subModel")}
    assert CANONICAL_TOM_ZONES <= set(submodels)
    assert not any("TOM_4" in name for name in submodels)
    assert len([name for name in submodels if "TOM_" in name and "CONTACT" not in name]) == 3
    for name, line0 in submodels.items(): assert RANGE_RE.match(line0), f"{name} has invalid ranges: {line0}"


def test_drummer_v3_tom_composites_include_contact_pose_nodes() -> None:
    submodels = _submodels()
    for base, composite in (("TOM_HIGH", "DRUMMER_TOM_HIGH"), ("TOM_MID", "DRUMMER_TOM_MID"), ("TOM_FLOOR", "DRUMMER_TOM_FLOOR")):
        assert submodels[f"HX_SNOWMAN_DRUMMER_V3_{composite}"] > submodels[f"HX_SNOWMAN_DRUMMER_V3_{base}"]


def test_detected_drum_events_map_to_canonical_drummer_components() -> None:
    events = [
        DrumEvent(0.10, 0.8, 0.7, {}, 1, "kick", "test"), DrumEvent(0.20, 0.9, 0.8, {}, 2, "snare", "test"),
        DrumEvent(0.30, 0.5, 0.7, {}, 3, "hihat", "test"), DrumEvent(0.40, 0.7, 0.7, {"tom_class":"high"}, 4, "tom", "test"),
        DrumEvent(0.50, 0.7, 0.7, {"tom_class":"mid"}, 5, "tom", "test"), DrumEvent(0.60, 0.7, 0.7, {"tom_class":"floor"}, 6, "tom", "test"),
        DrumEvent(0.70, 1.0, 0.8, {}, 7, "cymbal", "test"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    assert [event["component"] for event in mapped] == [*DRUMMER_COMPONENTS[:3], *DRUMMER_COMPONENTS[3:6], DRUMMER_COMPONENTS[6]]
    assert all("TOM_4" not in str(event["component"]) for event in mapped)
    assert mapped[3]["tom_class"] == "high" and mapped[4]["tom_class"] == "mid" and mapped[5]["tom_class"] == "floor"
