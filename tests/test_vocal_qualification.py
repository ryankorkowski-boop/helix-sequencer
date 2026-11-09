import numpy as np
import pytest
from music.vocal_qualification import screen_candidate_lanes


def test_harmony_owns_activity_and_phonemes_even_when_lead_is_silent():
    energy = np.zeros((40, 2), 'f4'); energy[2:12, 0] = .7; energy[20:32, 1] = .5
    shapes = np.where(energy > 0, [2, 5], 0)
    probability = np.where(energy > 0, .9, .1)
    result, phones, report = screen_candidate_lanes(energy, shapes, probability, fps=20)
    np.testing.assert_array_equal(result, energy)
    np.testing.assert_array_equal(phones, shapes)
    assert np.all(phones[20:32, 1] == 5)
    assert report['state'] == 'ESTIMATED' and report['identity_confidence'] is None


def test_hysteresis_rejects_uncertain_onset_blips_and_stale_tail():
    energy = np.zeros((30, 2), 'f4'); energy[2:18, 1] = .7; energy[21:23, 1] = .7
    probability = np.zeros((30, 2)); probability[2:5, 1] = .5
    probability[5:10, 1] = .9; probability[10:15, 1] = .5
    probability[15:18, 1] = .2; probability[21:23, 1] = .9
    result, phones, _ = screen_candidate_lanes(energy, np.where(energy > 0, 4, 0), probability, fps=20)
    assert np.flatnonzero(result[:, 1]).tolist() == list(range(5, 15))
    assert np.all(phones[result == 0] == 0)


def test_identical_candidate_clock_abstains_from_harmony():
    energy = np.column_stack([np.linspace(.1, .8, 20), .5*np.linspace(.1, .8, 20)])
    result, phones, report = screen_candidate_lanes(energy, np.full((20, 2), 2), np.ones((20, 2)), fps=20)
    assert np.any(result[:, 0]) and not np.any(result[:, 1])
    assert not np.any(phones[:, 1]) and report['state'] == 'REJECTED'


@pytest.mark.parametrize('bad', [np.nan, -1, 1.1])
def test_invalid_confidence_cannot_open_a_mouth(bad):
    probability = np.ones((20, 2)); probability[3, 1] = bad
    with pytest.raises(ValueError, match='probabilities'):
        screen_candidate_lanes(np.ones((20, 2)), np.ones((20, 2)), probability)
