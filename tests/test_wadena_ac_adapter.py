from core.wadena_ac_adapter import compile_wadena_ac_cues, compile_wadena_ac_events
from core.wadena_temporal_renderer import ACSafeLandmarkEvent


def test_only_explicit_landmarks_are_bound():
    events = (
        ACSafeLandmarkEvent("LEFT_TREE", 0.0, 0.2, 0.8, "Ramp", 0),
        ACSafeLandmarkEvent("UNKNOWN", 0.1, 0.3, 1.2, "Level", 1),
    )
    compiled = compile_wadena_ac_events(events, {"LEFT_TREE": "CH_001"})
    assert len(compiled) == 1
    assert compiled[0].channel_name == "CH_001"
    assert compiled[0].start_ms == 0
    assert compiled[0].end_ms == 200
    assert compiled[0].value == 0.8


def test_cue_payload_is_stable_and_explicit():
    events = (ACSafeLandmarkEvent("WREATH", 0.25, 0.5, 0.6, "On", 2),)
    cues = compile_wadena_ac_cues(events, {"WREATH": "WREATH_MAIN"})
    assert cues == (
        {
            "channel_name": "WREATH_MAIN",
            "start_ms": 250,
            "end_ms": 500,
            "value": 0.6,
            "effect": "On",
            "landmark": "WREATH",
            "order": 2,
            "kind": "wadena_spatial_propagation",
        },
    )
