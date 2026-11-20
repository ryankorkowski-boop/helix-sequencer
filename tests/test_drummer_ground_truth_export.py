from __future__ import annotations

import xml.etree.ElementTree as ET

from tools.drummer_ground_truth_oracle import TARGETS, fixture_events
from tools.export_drummer_ground_truth_xsq import (
    CHANNEL_HEX,
    CHANNEL_TO_PHYSICAL,
    build_drummer_ground_truth_xsq_text,
)


def test_ground_truth_oracle_covers_all_nine_canonical_components() -> None:
    assert TARGETS == (
        "KICK", "SNARE", "HI_HAT", "TOM_HIGH", "TOM_MID", "TOM_FLOOR",
        "CYMBAL_LEFT", "CYMBAL_RIGHT", "RIDE",
    )
    assert len(TARGETS) == len(set(TARGETS)) == 9
    assert set(CHANNEL_HEX) == set(TARGETS)
    assert set(CHANNEL_TO_PHYSICAL) == set(TARGETS)


def test_ground_truth_schedule_contains_a_real_ride_event() -> None:
    events = fixture_events(12)
    assert any(event.target == "RIDE" for event in events)
    assert all(event.target in TARGETS for event in events)


def test_ground_truth_xsq_exports_nine_lanes_and_nine_physical_targets() -> None:
    root = ET.fromstring(build_drummer_ground_truth_xsq_text(12))
    expected_models = {f"HX_SNOWMAN_DRUMMER_V3_{name}" for name in TARGETS}
    track = root.find("./timingtrack")
    assert track is not None
    assert set(track.get("channels", "").split(",")) == set(TARGETS)
    assert root.get("drummerChannels") == "9"
    assert set(root.find("./ElementEffects").findall("Element")[i].get("name")
               for i in range(9)) == expected_models
    contract = root.find("./effects/effect")
    assert contract is not None
    assert contract.get("channel_contract") == "9"
