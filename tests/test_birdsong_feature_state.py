from __future__ import annotations

from core.birdsong_feature_state import AudioFeatureFrame, FeatureState


def test_feature_state_updates_and_smooths_energy() -> None:
    state = FeatureState(smoothing_alpha=0.25)

    state.update(AudioFeatureFrame(energy=1.0, onset=0.5, bands=(0.2, 0.3, 0.5)))

    assert state.energy == 1.0
    assert state.energy_smooth == 0.25
    assert state.onset == 0.5
    assert state.low == 0.2
    assert state.mid == 0.3
    assert state.high == 0.5

    state.update(AudioFeatureFrame(energy=0.0, onset=0.0, bands=(0.5, 0.25, 0.25)))

    assert state.energy == 0.0
    assert round(state.energy_smooth, 6) == 0.1875


def test_feature_state_history_is_bounded() -> None:
    state = FeatureState(history_size=3)

    for idx in range(10):
        state.update(AudioFeatureFrame(energy=idx / 10.0))

    assert len(state.history) == 3
    assert [round(frame.energy, 2) for frame in state.history] == [0.7, 0.8, 0.9]


def test_feature_state_accepts_mapping_updates() -> None:
    state = FeatureState()

    state.update(
        {
            'energy': 0.8,
            'onset': 0.6,
            'centroid': 2450,
            'bands': (0.1, 0.7, 0.2),
            'beat_phase': 0.4,
        }
    )

    assert state.energy == 0.8
    assert state.onset == 0.6
    assert state.centroid == 2450
    assert state.band_balance == (0.1, 0.7, 0.2)


def test_audio_feature_frame_requires_three_bands() -> None:
    try:
        AudioFeatureFrame.from_mapping({'bands': (0.1, 0.2)})
    except ValueError as exc:
        assert 'bands must contain low, mid, high' in str(exc)
    else:
        raise AssertionError('Expected ValueError for invalid band tuple')
