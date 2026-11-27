"""Regression gate: generic band choreography must not activate every performer."""
from core.band_intent_adapter import BandIntentAdapter
from core.choreography_intent import IntentLayerRole, MotionVocabulary
from core.intent_layer_expander import SequentialLayerEvent
from tools.export_band_performance_manifest import build_demo_manifest


def event(source: str) -> SequentialLayerEvent:
    return SequentialLayerEvent(
        intent_id="test", intent_source=source, start=1.0, duration=0.2,
        layer_role=IntentLayerRole.EVENT, motion=MotionVocabulary.IMPACT,
        spatial_mode="impact_flash", intensity=0.8, target_region="stage",
    )


def test_generic_event_never_fans_out_to_band():
    adapter = BandIntentAdapter()
    assert adapter.adapt_event(event("audio_beat")) == ()
    assert adapter.adapt_event(event("band_manifest_exporter")) == ()


def test_targeted_event_only_animates_its_performer():
    adapter = BandIntentAdapter()
    result = adapter.adapt_event(event("performer:drummer"))
    assert len(result) == 1
    assert result[0].performer == "drummer"
    assert adapter.adapt_event(event("performer:unknown")) == ()


def test_distinct_targets_do_not_duplicate_events():
    adapter = BandIntentAdapter()
    result = adapter.adapt_many((event("performer:drummer"), event("performer:guitarist")))
    assert [e.performer for e in result] == ["drummer", "guitarist"]


def test_demo_export_has_targeted_events():
    manifest = build_demo_manifest()
    assert manifest["adapted_event_count"] > 0
    assert manifest["timeline_event_count"] > 0
