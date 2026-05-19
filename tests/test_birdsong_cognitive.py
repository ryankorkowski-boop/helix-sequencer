from __future__ import annotations

from core.birdsong_cognitive import (
    CognitiveBirdsongPipeline,
    EnergyField,
    EnergySource,
    IntentEngine,
    IntentAwarePhraseEngine,
    LAYERS,
    MotifEvolutionEngine,
    MultiLayerRenderer,
    SpatialFlowField,
    score_birdsong_events,
)
from core.birdsong_generative import BIRDSONG_MOTIFS, FeatureState, PhraseEngine, SpatialMap



def _state(energy: float, onset: float, bands=(0.3, 0.5, 0.2)) -> FeatureState:
    state = FeatureState()
    state.update({"energy": energy, "onset": onset, "centroid": 0.4, "bands": bands}, 0.0)
    return state



def test_intent_engine_classifies_build_break_and_finale() -> None:
    engine = IntentEngine()

    assert engine.update(0.0, _state(0.1, 0.1)) == "BREAK"
    assert engine.update(1.0, _state(0.8, 0.4)) == "BUILD"
    assert engine.update(2.0, _state(1.0, 0.9)) == "FINALE"



def test_intent_aware_phrase_engine_limits_motif_by_intent() -> None:
    state = _state(0.8, 0.8, bands=(0.2, 0.7, 0.2))
    engine = IntentAwarePhraseEngine()

    phrase = engine.update_with_intent(0.0, state, "BREAK")

    assert phrase.motif == "sparkle_field"
    assert phrase.motif in BIRDSONG_MOTIFS



def test_energy_field_samples_overlapping_sources() -> None:
    field = EnergyField()
    field.add_source(EnergySource(position=(0.0, 0.0, 0.0), amplitude=0.7, radius=1.0, start_time=0.0))
    field.add_source(EnergySource(position=(0.2, 0.0, 0.0), amplitude=0.7, radius=1.0, start_time=0.0))

    value = field.sample((0.1, 0.0, 0.0), 0.1)

    assert 0.0 < value <= 1.0



def test_motif_evolution_preserves_five_base_motifs_and_mutates_parameters() -> None:
    engine = MotifEvolutionEngine()
    state = _state(0.75, 0.8, bands=(0.2, 0.4, 0.7))

    motif = engine.evolve("spiral", "BUILD", state)

    assert tuple(BIRDSONG_MOTIFS) == ("wave_sweep", "spiral", "pulse_cascade", "orbit", "sparkle_field")
    assert motif.base_name == "spiral"
    assert motif.speed > 0
    assert 0.15 <= motif.spread <= 1.0



def test_spatial_flow_field_curves_spiral_motion() -> None:
    flow = SpatialFlowField()
    motif = MotifEvolutionEngine().evolve("spiral", "BUILD", _state(0.7, 0.8))

    vector = flow.sample((0.5, 0.2, 0.4), motif)

    assert vector.dz > 0
    assert vector.dx != 0 or vector.dy != 0



def test_multilayer_renderer_returns_three_layers() -> None:
    renderer = MultiLayerRenderer()
    state = _state(0.7, 0.8, bands=(0.4, 0.6, 0.9))

    contexts = renderer.contexts(state, "BUILD")

    assert tuple(context.layer for context in contexts) == LAYERS
    assert {context.preferred_spatial_role for context in contexts} == {"ground", "horizontal", "vertical"}



def test_cognitive_pipeline_generates_events_and_quality_score() -> None:
    spatial = SpatialMap.from_model_names(("BassGround", "CenterArch", "RoofStar", "SnowflakeHigh"))
    pipeline = CognitiveBirdsongPipeline(spatial)
    frames = []
    for index in range(40):
        time_s = index * 0.5
        onset = 0.9 if index % 4 == 0 else 0.25
        energy = 0.45 + (0.35 if 8 <= index <= 28 else 0.05)
        high = 0.8 if index % 5 == 0 else 0.25
        frames.append((time_s, {"energy": energy, "onset": onset, "centroid": 0.5, "bands": (0.5, 0.6, high)}))

    events, score = pipeline.run(frames)

    assert events
    assert score.overall > 0.0
    assert score.weakest_category in {"musicality", "spatial_coherence", "layering", "novelty", "emotion"}
    assert {event.layer for event in events}.issubset(set(LAYERS))



def test_quality_score_empty_events_is_zero() -> None:
    score = score_birdsong_events([])

    assert score.overall == 0.0
    assert score.weakest_category == "musicality"
