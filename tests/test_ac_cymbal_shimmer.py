import pytest

from core.ac_cymbal_shimmer import cymbal_shimmer, cymbal_circuits


def test_strike_shimmer_follows_audio_tail():
    values = cymbal_shimmer([1.0, .85, .65, .45, .3, .1, .02, 0])
    assert values[0] == 100
    assert all(0 <= x <= 100 for x in values)
    assert values[1] > values[4] > values[5]
    assert values[-2:] == (0, 0)


def test_silent_tail_does_not_create_light():
    assert cymbal_shimmer([0, 0, 0]) == (0, 0, 0)
    assert cymbal_shimmer([]) == ()
    assert cymbal_circuits() == {"left": 2, "right": 10}


def test_invalid_envelope_rejected():
    with pytest.raises(ValueError):
        cymbal_shimmer([1, float("nan")])
    with pytest.raises(ValueError):
        cymbal_shimmer([1, 0], fps=0)
