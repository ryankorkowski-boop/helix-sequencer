from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from mapping.drum_mapper import map_events_to_drummer_v3_poses
from audio.drum_classification import DrumEvent

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "fixtures" / "band_geometry" / "drummer_v3_pose_spec.json"
SOURCE = ROOT / "fixtures" / "band_geometry" / "source" / "drummerbg.png"
POSE_SHEET = ROOT / "fixtures" / "band_geometry" / "previews" / "HX_SNOWMAN_DRUMMER_V3_pose_sheet.png"
XMODEL = ROOT / "fixtures" / "band_geometry" / "models" / "HX_SNOWMAN_DRUMMER_V3.xmodel"
RANGE_RE = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")

REQUIRED_SUBMODELS = {
    "HX_SNOWMAN_DRUMMER_V3_HEAD", "HX_SNOWMAN_DRUMMER_V3_FACE", "HX_SNOWMAN_DRUMMER_V3_HAT",
    "HX_SNOWMAN_DRUMMER_V3_SCARF", "HX_SNOWMAN_DRUMMER_V3_TORSO", "HX_SNOWMAN_DRUMMER_V3_BUTTONS",
    "HX_SNOWMAN_DRUMMER_V3_PLATFORM", "HX_SNOWMAN_DRUMMER_V3_LEFT_ARM_IDLE", "HX_SNOWMAN_DRUMMER_V3_RIGHT_ARM_IDLE",
    "HX_SNOWMAN_DRUMMER_V3_LEFT_STICK_IDLE", "HX_SNOWMAN_DRUMMER_V3_RIGHT_STICK_IDLE", "HX_SNOWMAN_DRUMMER_V3_KICK",
    "HX_SNOWMAN_DRUMMER_V3_KICK_RIM", "HX_SNOWMAN_DRUMMER_V3_SNARE", "HX_SNOWMAN_DRUMMER_V3_SNARE_RIM",
    "HX_SNOWMAN_DRUMMER_V3_TOM_LEFT", "HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT", "HX_SNOWMAN_DRUMMER_V3_HI_HAT",
    "HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT", "HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT", "HX_SNOWMAN_DRUMMER_V3_STANDS",
    "HX_SNOWMAN_DRUMMER_V3_HIT_KICK", "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE", "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT",
    "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_TOM", "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_TOM", "HX_SNOWMAN_DRUMMER_V3_HIT_LEFT_CRASH",
    "HX_SNOWMAN_DRUMMER_V3_HIT_RIGHT_CRASH", "HX_SNOWMAN_DRUMMER_V3_HIT_BOTH_CRASH", "HX_SNOWMAN_DRUMMER_V3_DRUMKIT_ALL",
}


def _ranges(value: str) -> set[int]:
    nodes: set[int] = set()
    for chunk in value.split(","):
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1); nodes.update(range(int(start_s), int(end_s) + 1))
        else:
            nodes.add(int(chunk))
    return nodes


def _submodels() -> dict[str, set[int]]:
    root = ET.parse(XMODEL).getroot()
    return {submodel.attrib["name"]: _ranges(submodel.attrib.get("line0", "")) for submodel in root.findall("./subModels/subModel")}


def test_drummer_v3_source_and_pose_sheet_are_real_images() -> None:
    assert SOURCE.exists()
    assert POSE_SHEET.exists()
    with Image.open(SOURCE) as source:
        assert source.format == "PNG" and source.width >= 128 and source.height >= 128
    with Image.open(POSE_SHEET) as sheet:
        assert sheet.format == "PNG" and sheet.width > 0 and sheet.height > 0 and sheet.getbbox() is not None


def test_drummer_v3_pose_spec_declares_visual_first_contract() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["source_image"] == "fixtures/band_geometry/source/drummerbg.png"
    assert spec["source_image_b64"] == "fixtures/band_geometry/source/drummerbg.png.b64"
    assert spec["model_name"] == "HX_SNOWMAN_DRUMMER_V3"
    assert len(spec["required_pose_frames"]) == 10
    zone_ids = {zone["id"] for zone in spec["zones"]}
    assert {"LEFT_STICK_SNARE", "RIGHT_STICK_SNARE", "LEFT_STICK_CRASH", "RIGHT_STICK_CRASH"} <= zone_ids
    composites = {item["id"]: set(item["members"]) for item in spec["composites"]}
    assert {"SNARE", "SNARE_RIM", "LEFT_STICK_SNARE", "RIGHT_STICK_SNARE"} <= composites["HIT_SNARE"]
    assert {"CYMBAL_LEFT", "CYMBAL_RIGHT", "LEFT_STICK_CRASH", "RIGHT_STICK_CRASH"} <= composites["HIT_BOTH_CRASH"]


def test_drummer_v3_xmodel_has_named_zones_and_nontrivial_ranges() -> None:
    root = ET.parse(XMODEL).getroot()
    assert root.tag == "custommodel" and root.attrib["name"] == "HX_SNOWMAN_DRUMMER_V3"
    assert int(root.attrib["parm1"]) >= 90 and int(root.attrib["parm2"]) >= 70
    submodels = {s.attrib["name"]: s.attrib.get("line0", "") for s in root.findall("./subModels/subModel")}
    assert REQUIRED_SUBMODELS <= set(submodels)
    assert len(submodels) >= 35
    for name, line0 in submodels.items():
        assert RANGE_RE.match(line0), f"{name} has invalid ranges: {line0}"


def test_drummer_v3_hit_composites_include_contact_pose_nodes() -> None:
    submodels = _submodels()
    for pose, base in (("HIT_KICK", "KICK"), ("HIT_SNARE", "SNARE"), ("HIT_HIHAT", "HI_HAT"), ("HIT_LEFT_TOM", "TOM_LEFT"), ("HIT_RIGHT_TOM", "TOM_RIGHT")):
        assert submodels[f"HX_SNOWMAN_DRUMMER_V3_{pose}"] > submodels[f"HX_SNOWMAN_DRUMMER_V3_{base}"]
    assert submodels["HX_SNOWMAN_DRUMMER_V3_HIT_BOTH_CRASH"] > (submodels["HX_SNOWMAN_DRUMMER_V3_CYMBAL_LEFT"] | submodels["HX_SNOWMAN_DRUMMER_V3_CYMBAL_RIGHT"])
    assert submodels["HX_SNOWMAN_DRUMMER_V3_SNARE"] != submodels["HX_SNOWMAN_DRUMMER_V3_KICK"]
    assert submodels["HX_SNOWMAN_DRUMMER_V3_TOM_LEFT"] != submodels["HX_SNOWMAN_DRUMMER_V3_TOM_RIGHT"]


def test_detected_drum_events_map_to_drummer_v3_pose_names() -> None:
    events = [
        DrumEvent(0.10, 0.8, 0.7, {}, 1, "kick", "test"),
        DrumEvent(0.20, 0.9, 0.8, {}, 2, "snare", "test"),
        DrumEvent(0.30, 0.5, 0.7, {}, 3, "hihat", "test"),
        DrumEvent(0.40, 0.7, 0.7, {}, 4, "tom", "test"),
        DrumEvent(0.50, 1.0, 0.8, {}, 5, "cymbal", "test"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    poses = [event["pose"] for event in mapped]
    assert poses == ["kick_hit", "snare_hit", "hi_hat_pulse", "right_tom_hit", "both_crash"]
    assert mapped[1]["submodels"] == ["HX_SNOWMAN_DRUMMER_V3_HIT_SNARE"]
