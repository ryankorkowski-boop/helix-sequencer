from core.choreography_intent import (
    ChoreographyIntent,
    ChoreographyTarget,
    ContrastStrategy,
    DominanceStrategy,
    IntentLayerRole,
    MotionVocabulary,
    PaletteFamily,
    validate_intents,
)


def build_sample_intent() -> ChoreographyIntent:
    return ChoreographyIntent(
        start=12.5,
        duration=4.0,
        section="chorus",
        event_type="drop",
        style="SpatialHelix",
        emotional_energy=0.92,
        intensity=0.88,
        focal_region="band_center",
        support_regions=("arches", "roofline"),
        target_families=(
            ChoreographyTarget.CENTERPIECE,
            ChoreographyTarget.SEQUENTIAL,
        ),
        dominant_prop="mega_tree",
        dominance_strategy=DominanceStrategy.MEGATREE_CENTRIC,
        motion_vocabulary=(
            MotionVocabulary.ORBITAL,
            MotionVocabulary.HELIX_SPIRAL,
            MotionVocabulary.IMPACT,
        ),
        contrast_strategy=ContrastStrategy.DARK_PRE_DROP,
        escalation_phase=3,
        palette_family=PaletteFamily.SPATIAL_HELIX,
        density_budget=0.72,
        layer_roles=(
            IntentLayerRole.BASE,
            IntentLayerRole.MOTION,
            IntentLayerRole.ACCENT,
        ),
        source="style_engine_v2",
        metadata={"test": True},
    )


def test_intent_validation_passes():
    intent = build_sample_intent()
    result = intent.validate()

    assert result.valid is True
    assert result.errors == ()


def test_intent_end_time_is_correct():
    intent = build_sample_intent()
    assert intent.end == 16.5


def test_intent_id_contains_key_fields():
    intent = build_sample_intent()
    assert "SpatialHelix" in intent.intent_id
    assert "chorus" in intent.intent_id
    assert "drop" in intent.intent_id


def test_intent_serialization_roundtrip():
    original = build_sample_intent()

    serialized = original.to_dict()
    restored = ChoreographyIntent.from_mapping(serialized)

    assert restored == original


def test_invalid_intent_fails_validation():
    intent = ChoreographyIntent(
        start=-1.0,
        duration=0.0,
        section="",
        event_type="",
        style="",
        emotional_energy=2.0,
        intensity=-1.0,
        focal_region="",
    )

    result = intent.validate()

    assert result.valid is False
    assert len(result.errors) >= 6


def test_validate_intents_aggregates_results():
    valid_intent = build_sample_intent()

    invalid_intent = ChoreographyIntent(
        start=-5.0,
        duration=-1.0,
        section="",
        event_type="",
        style="",
        emotional_energy=5.0,
        intensity=5.0,
        focal_region="",
    )

    result = validate_intents([valid_intent, invalid_intent])

    assert result.valid is False
    assert len(result.errors) > 0
