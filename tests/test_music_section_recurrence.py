import pytest

from core.music_section_recurrence import find_recurrent_regions


def _frames():
    times = [float(i) for i in range(48)]
    # Two alternating textured 8-second phrases separated by 16 seconds.
    chroma = []
    for i in range(48):
        if i < 8 or 24 <= i < 32:
            chroma.append([0.8, 0.2] if i % 2 == 0 else [0.2, 0.8])
        else:
            chroma.append([0.9, 0.1] if i % 3 == 0 else [0.6, 0.4])
    return times, chroma


def test_repeated_textured_region_is_detected_deterministically():
    times, chroma = _frames()
    first = find_recurrent_regions(times, chroma, duration_s=48)
    assert first == find_recurrent_regions(times, chroma, duration_s=48)
    assert any(item["first_start_seconds"] == 0 and item["repeat_start_seconds"] == 24 for item in first)
    assert all(item["confidence"] < 0.7 for item in first)


def test_static_tone_not_mistaken_for_repeated_section():
    times = [float(i) for i in range(48)]
    assert find_recurrent_regions(times, [[0.5, 0.5]] * 48, duration_s=48) == []


def test_short_audio_and_limits():
    assert find_recurrent_regions([0.0, 1.0], [[1, 0], [0, 1]], duration_s=2) == []
    times, chroma = _frames()
    assert len(find_recurrent_regions(times, chroma, duration_s=48, max_pairs=1)) <= 1


@pytest.mark.parametrize("times,chroma", [
    ([0, 1, 1, 3], [[1, 0]] * 4),
    ([0, 1, 2, 3], [[1, 0], [0, float("nan")], [1, 0], [0, 1]]),
    ([0, 1, 2, 3], [[1, 0], [0, 1], [1, 0]]),
])
def test_invalid_input_rejected(times, chroma):
    with pytest.raises(ValueError):
        find_recurrent_regions(times, chroma, duration_s=48)
