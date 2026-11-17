import pytest

from core.music_structure_candidates import detect_structure_candidates


def test_change_point_detected_near_real_feature_transition():
    times = [float(i) for i in range(60)]
    energy = [0.2 if i < 30 else 0.9 for i in range(60)]
    chroma = [[1.0, 0.0] if i < 30 else [0.0, 1.0] for i in range(60)]
    changes = detect_structure_candidates(times, energy, chroma, duration_s=60)
    assert changes
    assert any(abs(change["time_seconds"] - 30) <= 2 for change in changes)
    assert all(change["confidence"] < 0.7 for change in changes)
    assert all(change["reason"] == "energy_chroma_novelty_candidate" for change in changes)


def test_static_music_does_not_generate_fake_sections():
    times = [float(i) for i in range(60)]
    assert detect_structure_candidates(times, [0.4] * 60, [[0.5, 0.5]] * 60, duration_s=60) == []


def test_deterministic_and_bounded_candidates():
    times = [float(i) for i in range(100)]
    energy = [0.1 if (i // 20) % 2 == 0 else 0.9 for i in range(100)]
    chroma = [[1, 0] if (i // 20) % 2 == 0 else [0, 1] for i in range(100)]
    a = detect_structure_candidates(times, energy, chroma, duration_s=100, max_boundaries=3)
    b = detect_structure_candidates(times, energy, chroma, duration_s=100, max_boundaries=3)
    assert a == b
    assert len(a) <= 3
    assert all(y["time_seconds"] - x["time_seconds"] >= 8 for x, y in zip(a, a[1:]))


@pytest.mark.parametrize("times,energy,chroma", [
    ([0, 1, 2], [0, 1], [[0], [1], [0]]),
    ([0, 1, 1, 2], [0, 1, 0, 1], [[0]] * 4),
    ([0, 1, 2, 3], [0, float("nan"), 0, 1], [[0]] * 4),
    ([0, 1, 2, 3], [0, 1, 0, 1], [[0], [1, 0], [0], [1]]),
])
def test_invalid_features_rejected(times, energy, chroma):
    with pytest.raises(ValueError):
        detect_structure_candidates(times, energy, chroma, duration_s=60)


def test_short_audio_has_no_forced_boundaries():
    times = [float(i) for i in range(10)]
    assert detect_structure_candidates(times, [0.2] * 5 + [0.9] * 5, [[0]] * 5 + [[1]] * 5, duration_s=10) == []
