from __future__ import annotations

from core.band_intent_adapter import BandIntentAdapter
from core.band_performance_timeline import BandPerformanceTimelineCompiler
from core.band_xlights_export import BandXLightsExportCompiler
from core.choreography_intent import (
    ChoreographyIntent,
    ChoreographyTarget,
    IntentLayerRole,
    MotionVocabulary,
)
from core.intent_layer_expander import IntentLayerExpander


def test_end_to_end_band_pipeline_generates_effects() -> None:
    intent = ChoreographyIntent(
        start=0.0,
        duration=4.0,
        section="chorus",
        event_type="downbeat",
        style="helixville4",
        emotional_energy=0.95,
        intensity=1.0,
        focal_region="center_stage",
        target_families=(ChoreographyTarget.PERFORMER,),
        motion_vocabulary=(
            MotionVocabulary.IMPACT,
            MotionVocabulary.PULSE,
        ),
        layer_roles=(
            IntentLayerRole.EVENT,
            IntentLayerRole.ACCENT,
        ),
        source="pytest_smoke",
    )

    expanded = IntentLayerExpander().expand_intent(intent)
    assert expanded

    adapted = BandIntentAdapter().adapt_many(expanded)
    assert adapted

    performers = {event.performer for event in adapted}

    assert performers == {
        "drummer",
        "guitarist",
        "bassist",
        "singer",
        "female_singer",
    }

    timeline = BandPerformanceTimelineCompiler().compile_many(adapted)

    assert timeline
    assert any(event.state == "downbeat_impact" for event in timeline)
    assert any(event.state == "big_vocal" for event in timeline)

    export_effects = BandXLightsExportCompiler().compile_many(timeline)

    assert export_effects

    model_names = {effect.model_name for effect in export_effects}

    assert model_names == {
        "HX_SNOWMAN_DRUMMER",
        "HX_SNOWMAN_GUITARIST",
        "HX_SNOWMAN_BASSIST",
        "HX_SNOWMAN_SINGER",
        "HX_SNOWMAN_SINGER_FEMALE",
    }

    assert any(effect.effect_type == "On" for effect in export_effects)
    assert any(effect.effect_type == "Shockwave" for effect in export_effects)
    assert any(effect.effect_type == "Ripple" for effect in export_effects)


def test_export_manifest_contains_all_band_members() -> None:
    intent = ChoreographyIntent(
        start=10.0,
        duration=2.0,
        section="bridge",
        event_type="transition",
        style="helixville4",
        emotional_energy=0.6,
        intensity=0.75,
        focal_region="front_stage",
        target_families=(ChoreographyTarget.PERFORMER,),
        motion_vocabulary=(MotionVocabulary.SHIMMER,),
        layer_roles=(IntentLayerRole.MOTION,),
        source="pytest_manifest",
    )

    expanded = IntentLayerExpander().expand_intent(intent)
    adapted = BandIntentAdapter().adapt_many(expanded)
    timeline = BandPerformanceTimelineCompiler().compile_many(adapted)

    manifest = BandXLightsExportCompiler().build_manifest(timeline)

    assert manifest["schema"] == "helixville4.band_xlights_export.v1"
    assert sorted(manifest["performers"]) == [
        "bassist",
        "drummer",
        "female_singer",
        "guitarist",
        "singer",
    ]

    assert manifest["effect_count"] > 0
