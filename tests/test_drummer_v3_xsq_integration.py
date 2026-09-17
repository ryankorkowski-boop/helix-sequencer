from __future__ import annotations

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from audio.drum_classification import DrumEvent
from mapping.drum_mapper import map_events_to_drummer_v3_poses


POSE_TO_CHANNELS = {
    "kick_hit": {257, 264},
    "snare_hit": {258, 262, 263},
    "hi_hat_pulse": {259, 262},
    "left_tom_hit": {260, 262},
    "right_tom_hit": {260, 263},
    "left_crash": {261, 262},
    "right_crash": {261, 263},
    "both_crash": {261, 262, 263},
    "downbeat_impact": {264, 257, 258, 261, 262, 263},
}


def test_v3_mapper_only_emits_declared_v3_poses_and_targets() -> None:
    events = [
        DrumEvent(0.1, 0.8, 0.7, {}, 1, "kick"),
        DrumEvent(0.2, 0.9, 0.8, {}, 2, "snare"),
        DrumEvent(0.3, 0.6, 0.7, {}, 3, "hihat"),
        DrumEvent(0.4, 0.7, 0.7, {}, 4, "tom"),
        DrumEvent(0.5, 1.0, 0.8, {}, 5, "cymbal"),
    ]
    mapped = map_events_to_drummer_v3_poses(events)
    for item in mapped:
        pose = str(item["pose"])
        assert pose in POSE_TO_CHANNELS
        assert str(item["model"]) == "HX_SNOWMAN_DRUMMER_V3"
        assert all(str(name).startswith("HX_SNOWMAN_DRUMMER_V3_") for name in item["submodels"])


def test_injection_helper_preserves_existing_xlights_effect_container() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence><ElementEffects><Element type='model' name='Existing'/></ElementEffects></xsequence>")
    container = _find_or_create_element_effects(root)
    assert container is root.find("ElementEffects")
    assert [e.get("name") for e in container.findall("Element")] == ["Existing"]


def test_injection_helper_creates_current_xlights_container_without_legacy_effects() -> None:
    from tools.integrate_drummer_v3_into_xsq import _find_or_create_element_effects

    root = ET.fromstring("<xsequence/>")
    container = _find_or_create_element_effects(root)
    assert container.tag == "ElementEffects"
    assert root.find("effects") is None
