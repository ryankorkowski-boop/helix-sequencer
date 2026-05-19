from __future__ import annotations

from core.birdsong_generative import RenderEvent
from core.choreography import ChoreographyEngine, infer_role


def test_infer_role_from_model_name() -> None:
    assert infer_role("kick_drum_ground") == "drummer"
    assert infer_role("bass_player") == "bass"
    assert infer_role("lead_singer_face") == "lead"
    assert infer_role("roof_star_snowflake") == "sparkle"
    assert infer_role("guitar_left") == "guitar"
    assert infer_role("plain_line") == "generic"


def test_choreography_engine_returns_replacement_event() -> None:
    engine = ChoreographyEngine(["kick_drum_ground"])
    event = RenderEvent(
        model="kick_drum_ground",
        start_ms=1000,
        end_ms=1300,
        effect="Wave",
        motif="pulse_cascade",
        intensity=0.8,
    )

    transformed = engine.transform_event(event)

    assert transformed is not event
    assert transformed.end_ms - transformed.start_ms <= 150
    assert transformed.intensity > event.intensity


def test_choreography_engine_gives_sparkles_short_twinkle_identity() -> None:
    engine = ChoreographyEngine(["roof_star"])
    event = RenderEvent(
        model="roof_star",
        start_ms=1000,
        end_ms=1400,
        effect="On",
        motif="sparkle_field",
        intensity=1.0,
    )

    transformed = engine.transform_event(event)

    assert transformed.effect == "Twinkle"
    assert transformed.end_ms - transformed.start_ms <= 170
    assert transformed.intensity <= 0.82


def test_choreography_engine_extends_bass_foundation_events() -> None:
    engine = ChoreographyEngine(["bass_player"])
    event = RenderEvent(
        model="bass_player",
        start_ms=1000,
        end_ms=1080,
        effect="On",
        motif="pulse_cascade",
        intensity=0.6,
    )

    transformed = engine.transform_event(event)

    assert transformed.end_ms - transformed.start_ms >= 220
