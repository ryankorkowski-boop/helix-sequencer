"""Exercise the real shared timeline and performer planners together."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from core import band_planning


@pytest.fixture
def inputs():
    parts = [SimpleNamespace(label=label, start_ms=i * 1000,
                             end_ms=(i + 1) * 1000, energy=energy)
             for i, (label, energy) in enumerate([
                 ("VERSE", .3), ("CHORUS", .9), ("VERSE", .3), ("CHORUS", .9)])]
    notes = [SimpleNamespace(
        start_ms=start, end_ms=start + 180, notes=[(pitch, .8)],
        source_owner=owner,
    ) for start, pitch, owner in [
        (100, 60, None),
        (1200, 64, dict(performer="keyboardist", confidence=.9,
                        origin="estimated", source_id="piano")),
        (2200, 67, dict(performer="guitarist", confidence=.99,
                        origin="detected", source_id="guitar")),
    ]]
    return dict(
        parsed_layout=None, parts=parts, lyric_events=[], note_events=notes,
        beat_ms=list(range(0, 4000, 500)), onset_ms=[100, 1200, 2200, 3200],
        kicks=[100, 1200], snares=[600, 1600], hats=[], bass_peaks=[100, 1200],
        vocal_peaks=[], build_lifts=[], releases=[], song_length_ms=4000,
        enable_lyrics=False,
    )


def test_shared_section_focus_and_returning_motifs_reach_band(inputs):
    before = deepcopy(inputs)
    sync, band = band_planning.build_band_plans(**inputs)
    assert [s["section_type"] for s in sync["timeline"]] == ["verse", "chorus", "verse", "chorus"]
    assert len(sync["state_frames"]) == 4
    assert len(sync["performer_focus"]) == 4
    assert len(sync["phrase_motifs"]) == 4
    assert sync["phrase_motifs"][-1]["variation"] != "base"
    assert band["enabled"]
    assert band["debug"]["band_sync_frames"] == 4
    assert band["band_sync"]["performer_focus"] == sync["performer_focus"]
    assert inputs == before


def test_ownership_controls_reach_only_keyboard_consumer(inputs):
    default_sync, default = band_planning.build_band_plans(**inputs)
    strict_sync, strict = band_planning.build_band_plans(
        **inputs, require_keyboard_source_ownership=True)
    assert strict_sync == default_sync
    assert [c["pitch_midi"] for c in default["cues"]["keyboardist"]] == [60, 64, 67]
    assert [c["pitch_midi"] for c in strict["cues"]["keyboardist"]] == [64]
    for role in ("drummer", "guitarist", "bassist", "lead_singer", "background_vocals"):
        assert strict["cues"][role] == default["cues"][role]
    _, higher_threshold = band_planning.build_band_plans(
        **inputs, require_keyboard_source_ownership=True, keyboard_ownership_threshold=.95)
    assert higher_threshold["cues"]["keyboardist"] == []


def test_sync_failure_is_reported_and_does_not_disable_band(inputs, monkeypatch):
    def fail(**kwargs):
        raise ValueError("invalid timeline fixture")
    monkeypatch.setattr(band_planning.band_sync, "build_band_sync_plan", fail)
    warnings = []
    sync, band = band_planning.build_band_plans(**inputs, log_fn=warnings.append)
    assert sync["debug"]["planning_error"]["type"] == "ValueError"
    assert "invalid timeline fixture" in warnings[0]
    assert band["enabled"]
    assert band["cues"]["drummer"]


def test_performer_failure_retains_shared_musical_evidence(inputs, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("invalid performer fixture")
    monkeypatch.setattr(band_planning.snowman_band, "build_snowman_band_plan", fail)
    sync, band = band_planning.build_band_plans(**inputs)
    assert sync["timeline"] and sync["phrase_motifs"]
    assert band["enabled"] is False
    assert band["debug"]["planning_error"]["message"] == "invalid performer fixture"
