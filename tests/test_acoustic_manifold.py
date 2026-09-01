from core.acoustic_manifold import build_state, spatial_intent


def test_state_is_safe_for_missing_or_invalid_features():
    state = build_state(
        time_ms=100,
        energy=float("nan"),
        pitch_hz=0,
        centroid_hz=float("inf"),
        bandwidth_hz=-10,
        flux=float("nan"),
    )
    assert 0 <= state.energy <= 1
    assert 0 <= state.pitch <= 1
    assert 0 <= state.centroid <= 1
    assert 0 <= state.tension <= 1


def test_rising_pitch_moves_spatial_intent_upward():
    low = build_state(time_ms=0, energy=0.5, pitch_hz=100, centroid_hz=500)
    high = build_state(time_ms=1, energy=0.5, pitch_hz=2000, centroid_hz=500)
    assert spatial_intent(high)["y"] > spatial_intent(low)["y"]


def test_energy_drives_brightness_and_onset_drives_velocity():
    quiet = build_state(time_ms=0, energy=0.1, onset=0.0)
    hit = build_state(time_ms=1, energy=0.1, onset=1.0)
    assert spatial_intent(hit)["brightness"] > spatial_intent(quiet)["brightness"]
    assert spatial_intent(hit)["velocity"] > spatial_intent(quiet)["velocity"]


def test_acoustic_state_is_deterministic():
    args = dict(
        time_ms=1234,
        energy=0.72,
        onset=0.31,
        pitch_hz=523.25,
        pitch_confidence=0.88,
        centroid_hz=2400,
        bandwidth_hz=1300,
        flux=0.41,
        low_energy=0.2,
        mid_energy=0.5,
        high_energy=0.3,
    )
    assert build_state(**args) == build_state(**args)
