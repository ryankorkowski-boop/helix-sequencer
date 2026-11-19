import numpy as np
import pytest
from music.vocal_presence import screen_clock


def test_periodic_leakage_cannot_open_mouth_without_its_own_presence_evidence():
    clock = dict(energy=np.ones(320, 'f4'), shapes=np.full(320, 2, 'i1'))
    lead = np.zeros(100, 'f4'); lead[15:35] = .9
    backing = np.zeros(100, 'f4'); backing[55:75] = .9
    a = screen_clock(clock, lead)
    b = screen_clock(clock, backing)
    assert np.any(a['energy'][:160] > 0) and not np.any(a['energy'][160:] > 0)
    assert np.any(b['energy'][160:] > 0) and not np.any(b['energy'][:160] > 0)
    assert np.all(a['shapes'][a['energy'] == 0] == 0)
    assert np.all(b['shapes'][b['energy'] == 0] == 0)


def test_presence_cannot_fabricate_energy_or_move_source_boundaries():
    energy = np.zeros(320, 'f4'); energy[250:290] = .7
    clock = dict(energy=energy, shapes=np.where(energy > 0, 3, 0))
    result = screen_clock(clock, np.ones(100, 'f4'))
    np.testing.assert_array_equal(result['energy'], energy)
    assert np.any(result['energy'][250:] > 0)  # No blanket ending mute.


def test_mismatched_source_clock_is_rejected():
    with pytest.raises(ValueError, match='different durations'):
        screen_clock(dict(energy=np.ones(100), shapes=np.ones(100)), np.ones(100))
