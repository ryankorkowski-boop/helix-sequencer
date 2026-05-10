from core.choreography_correction_loop import ChoreographyCorrectionLoop
from core.choreography_intent import (
    ChoreographyIntent,
    ContrastStrategy,
    DominanceStrategy,
    MotionVocabulary,
)
from core.intent_graph import IntentGraph


def make_intent(
    *,
    section="drop",
    contrast_strategy=ContrastStrategy.NONE,
    dominance_strategy=DominanceStrategy.ORBITAL,
    density_budget=0.95,
    intensity=1.0,
):
    return ChoreographyIntent(
        start=0.0,
        duration=4.0,
        section=section,
        event_type="impact",
        style="SpatialHelix",
        emotional_energy=1.0,
        intensity=intensity,
        focal_region="center_stage",
        dominant_prop="megatree",
        dominance_strategy=dominance_strategy,
        motion_vocabulary=(
            MotionVocabulary.PULSE,
            MotionVocabulary.CHASE,
            MotionVocabulary.SWEEP,
            MotionVocabulary.BLOOM,
            MotionVocabulary.IMPACT,
        ),
        contrast_strategy=contrast_strategy,
        density_budget=density_budget,
        source="test",
    )


def test_correction_loop_improves_problematic_graph():
    graph = IntentGraph([make_intent()])

    result = ChoreographyCorrectionLoop().run(graph)

    assert result.improved is True
    assert len(result.actions) >= 3
    assert result.corrected_report.overall_score >= result.original_report.overall_score


def test_motion_vocab_is_trimmed():
    graph = IntentGraph([make_intent()])

    result = ChoreographyCorrectionLoop().run(graph)

    corrected = next(iter(result.corrected_graph))

    assert len(corrected.motion_vocabulary) <= 3


def test_missing_contrast_is_added():
    graph = IntentGraph([make_intent(contrast_strategy=ContrastStrategy.NONE)])

    result = ChoreographyCorrectionLoop().run(graph)

    corrected = next(iter(result.corrected_graph))

    assert corrected.contrast_strategy != ContrastStrategy.NONE


def test_density_is_reduced():
    graph = IntentGraph([make_intent(density_budget=1.0, intensity=1.0)])

    result = ChoreographyCorrectionLoop().run(graph)

    corrected = next(iter(result.corrected_graph))

    assert corrected.density_budget <= 0.75
    assert corrected.intensity <= 0.9
