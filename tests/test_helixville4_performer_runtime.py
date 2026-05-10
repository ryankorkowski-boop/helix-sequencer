from __future__ import annotations

from core.band_intent_adapter import BandIntentAdapter
from core.choreography_intent import IntentLayerRole, MotionVocabulary
from core.intent_layer_expander import SequentialLayerEvent
from models.helixville4_performer_runtime import (
    HELIXVILLE4_PERFORMERS,
    build_performer_runtime_catalog,
    validate_performer_runtime_catalog,
)


def test_performer_runtime_catalog_is_valid() -> None:
    result = validate_performer_runtime_catalog()
    assert result["valid"], result["errors"]
    assert result["performer_count"] == 5


def test_all_performers_have_states_and_audio_inputs() -> None:
    for performer in HELIXVILLE4_PERFORMERS:
        assert performer.states
        assert performer.audio_inputs
        assert performer.submodels
        assert "HX_SNOWMAN_BAND" in performer.sequencing_groups


def test_catalog_contains_all_expected_models() -> None:
    catalog = build_performer_runtime_catalog()
    names = set(catalog["model_names"])

    assert names == {
        "HX_SNOWMAN_DRUMMER",
        "HX_SNOWMAN_GUITARIST",
        "HX_SNOWMAN_BASSIST",
        "HX_SNOWMAN_SINGER",
        "HX_SNOWMAN_SINGER_FEMALE",
    }


def test_band_intent_adapter_uses_all_runtime_performers() -> None:
    adapter = BandIntentAdapter()

    event = SequentialLayerEvent(
        intent_id="test:intro:0",
        intent_source="pytest",
        start=0.0,
        duration=2.0,
        layer_role=IntentLayerRole.ACCENT,
        motion=MotionVocabulary.IMPACT,
        spatial_mode="impact_flash",
        intensity=1.0,
        target_region="center_stage",
    )

    adapted = adapter.adapt_event(event)

    performers = {entry.performer for entry in adapted}

    assert performers == {
        "drummer",
        "guitarist",
        "bassist",
        "singer",
        "female_singer",
    }


def test_harmony_vocalist_has_harmony_emphasis() -> None:
    adapter = BandIntentAdapter()

    emphasis = adapter._instrument_emphasis(
        "female_singer",
        IntentLayerRole.ACCENT,
    )

    assert emphasis == "harmony_vocal_accent"
