"""Regression coverage for optional composite drum metadata in band planning."""

from core.snowman_band import _build_intelligent_drum_cues


def test_legacy_drum_marks_do_not_abort_band_planning():
    cues, kit, debug = _build_intelligent_drum_cues(
        [], drum_event_streams=None,
        kicks=[100, 500], snares=[250], hats=[125, 375], releases=[750],
    )
    assert cues, "Legacy drum marks should produce band cues"
    assert {"kick", "snare", "hihat", "cymbal"} <= set(kit)
    assert all(isinstance(cue["composite_submodels"], list) for cue in cues)
    assert all(cue["submodel"] for cue in cues)
    assert debug["fallback_mode"] == "legacy_marks"


def test_empty_drum_marks_remain_valid():
    cues, kit, debug = _build_intelligent_drum_cues(
        [], drum_event_streams=None,
        kicks=[], snares=[], hats=[], releases=[],
    )
    assert cues == []
    assert kit == []
    assert debug["fallback_mode"] == "legacy_marks"
