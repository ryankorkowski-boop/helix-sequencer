"""The snowman band planner must survive drum maps and still emit Faces cues."""

from types import SimpleNamespace

from audio.drum_classification import DrumEvent
from core.snowman_band import build_snowman_band_plan
from mapping.drum_mapper import map_events_to_submodels


def test_mapped_drum_events_include_composite_submodels():
    event = DrumEvent(
        timestamp=1.25,
        velocity=0.8,
        confidence=0.7,
        frequency_band_info={"legacy_ms": 1250.0},
        cluster_id=0,
        drum_type="kick",
        source="test",
    )
    mapped = map_events_to_submodels([event])
    assert mapped[0]["composite_submodels"]
    assert mapped[0]["submodel"] == "kick"


def test_snowman_plan_survives_drum_streams_and_emits_faces():
    streams = {
        "kick_events": [
            DrumEvent(0.4, 0.7, 0.6, {}, 0, "kick", "test"),
        ]
    }
    layout = SimpleNamespace(models={"Singing Face 1": object(), "Mega Tree": object()})
    lyric = SimpleNamespace(text="hello", start_ms=200, end_ms=700, confidence=0.8)
    plan = build_snowman_band_plan(
        parsed_layout=layout,
        parts=[],
        lyric_events=[lyric],
        note_events=[],
        beat_ms=[0, 500, 1000],
        kicks=[400],
        snares=[],
        hats=[],
        bass_peaks=[],
        vocal_peaks=[200, 500],
        build_lifts=[],
        releases=[],
        enable_lyrics=True,
        drum_event_streams=streams,
    )
    assert plan["enabled"] is True
    instructions = plan["xlights_translation"]["sequence_effect_instructions"]
    assert instructions
    assert any(item.get("effect") == "Faces" for item in instructions)
    assert any(item.get("target_model") == "Singing Face 1" for item in instructions)
