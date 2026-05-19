from __future__ import annotations

from core.birdsong_generative import (
    BIRDSONG_MOTIFS,
    BehaviorEngine,
    BirdsongPipeline,
    EffectCandidate,
    EffectScoringEngine,
    EnergyWave,
    FeatureState,
    PhraseEngine,
    Phrase,
    RenderEvent,
    SpatialMap,
    spawn_trigger_wave,
)


FEATURES = {
    "time_s": 1.0,
    "energy": 0.9,
    "onset": 0.8,
    "centroid": 0.7,
    "bands": [0.8, 0.4, 0.2],
    "beat_phase": 0.0,
}


def test_feature_state_smooths_energy_using_ema() -> None:
    state = FeatureState(ema_alpha=0.5)

    first = state.update({**FEATURES, "energy": 0.0}, time_s=0.0)
    second = state.update({**FEATURES, "energy": 1.0}, time_s=0.1)

    assert first.energy_smooth == 0.0
    assert second.energy == 1.0
    assert second.energy_smooth == 0.5


def test_feature_state_history_is_capped_at_128_frames() -> None:
    state = FeatureState()

    for index in range(140):
        state.update({**FEATURES, "time_s": float(index)}, time_s=float(index))

    assert len(state.history) == 128
    assert state.history[0].time_s == 12.0
    assert state.history[-1].time_s == 139.0


def test_phrase_engine_returns_allowed_motif() -> None:
    state = FeatureState()
    state.update(FEATURES, time_s=1.0)

    phrase = PhraseEngine().update(1.0, state)

    assert phrase.motif in set(BIRDSONG_MOTIFS)


def test_spatial_map_from_model_names_assigns_stable_coordinates_and_categories() -> None:
    names = ["bass_drum_ground", "roof_star", "north_arch_line", "plain_model"]

    first = SpatialMap.from_model_names(names)
    second = SpatialMap.from_model_names(names)

    assert first.models == second.models
    assert first.adjacency == second.adjacency
    assert [model.category for model in first.models] == [
        "ground",
        "vertical",
        "perimeter",
        "horizontal",
    ]


def test_spatial_map_feature_anchor_tracks_dominant_band() -> None:
    spatial_map = SpatialMap.from_model_names(["floor_bass", "mid_line", "roof_star"])
    state = FeatureState()

    state.update({**FEATURES, "bands": [0.9, 0.2, 0.1]}, time_s=1.0)
    assert spatial_map.feature_anchor(state) == (0.0, -0.65, 0.05)

    state.update({**FEATURES, "bands": [0.1, 0.2, 0.9]}, time_s=1.1)
    assert spatial_map.feature_anchor(state) == (0.0, 0.25, 0.95)

    state.update({**FEATURES, "bands": [0.1, 0.8, 0.2]}, time_s=1.2)
    assert spatial_map.feature_anchor(state) == (0.0, 0.0, 0.35)


def test_energy_wave_update_moves_wave_and_decays_energy() -> None:
    wave = EnergyWave(position=(0.0, 0.0, 0.0), velocity=(1.0, 0.5, 0.25), energy=1.0)

    wave.update(0.5)

    assert wave.position == (0.5, 0.25, 0.125)
    assert wave.energy < 1.0
    assert wave.radius > 0.22


def test_effect_scoring_engine_select_returns_deterministic_choice() -> None:
    spatial_map = SpatialMap.from_model_names(["bass_drum_ground"])
    model = spatial_map.models[0]
    wave = EnergyWave(position=(model.x, model.y, model.z), velocity=(0.0, 0.0, 0.0), energy=0.8)
    phrase = Phrase(start_time=1.0, duration=2.0, motif="pulse_cascade")

    first = EffectScoringEngine().select(model, wave, phrase)
    second = EffectScoringEngine().select(model, wave, phrase)

    assert first == second


def test_effect_scoring_engine_accepts_legacy_spatial_bias_aliases() -> None:
    spatial_map = SpatialMap.from_model_names(["bass_drum_ground"])
    model = spatial_map.models[0]
    wave = EnergyWave(position=(model.x, model.y, model.z), velocity=(0.0, 0.0, 0.0), energy=0.8)
    phrase = Phrase(start_time=1.0, duration=2.0, motif="pulse_cascade")
    scorer = EffectScoringEngine()

    modern = scorer.score(EffectCandidate("On", 0.35, "ground"), model, wave, {"On"})
    legacy = scorer.score(EffectCandidate("On", 0.35, "center_ground"), model, wave, {"On"})

    assert legacy == modern


def test_birdsong_pipeline_update_returns_render_events_for_high_energy_onset() -> None:
    spatial_map = SpatialMap.from_model_names(["left_arch_line", "kick_drum_ground", "roof_star"])
    pipeline = BirdsongPipeline(spatial_map)

    events = pipeline.update(FEATURES, time_s=1.0)

    assert events
    assert all(isinstance(event, RenderEvent) for event in events)
    assert all(event.start_ms == 1000 for event in events)
    assert all(event.end_ms > event.start_ms for event in events)
    assert all(event.motif in set(BIRDSONG_MOTIFS) for event in events)


def test_spawn_trigger_wave_returns_deterministic_kick_wave() -> None:
    spatial_map = SpatialMap.from_model_names(["floor_bass", "mid_line", "roof_star"])
    state = FeatureState()
    state.update(FEATURES, time_s=1.0)

    first = spawn_trigger_wave("kick", state, spatial_map)
    second = spawn_trigger_wave("kick", state, spatial_map)

    assert first == second
    assert first is not None
    assert first.position == (0.0, -0.65, 0.05)
    assert first.velocity[0] > first.velocity[2]
    assert first.energy >= 0.72


def test_spawn_trigger_wave_unknown_trigger_returns_none() -> None:
    spatial_map = SpatialMap.from_model_names(["floor_bass"])
    state = FeatureState()
    state.update(FEATURES, time_s=1.0)

    assert spawn_trigger_wave("not_a_trigger", state, spatial_map) is None


def test_behavior_engine_inject_wave_accepts_wave_or_none() -> None:
    spatial_map = SpatialMap.from_model_names(["floor_bass"])
    state = FeatureState()
    state.update(FEATURES, time_s=1.0)
    engine = BehaviorEngine(spatial_map)

    engine.inject_wave(None)
    assert engine.waves == []

    wave = spawn_trigger_wave("hat", state, spatial_map)
    engine.inject_wave(wave)

    assert engine.waves == [wave]
