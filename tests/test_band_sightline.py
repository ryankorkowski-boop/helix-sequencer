"""The fixed front approval view must show the whole drum kit and all players."""
import numpy as np

from models.band_sightline import (front_camera_for, kit_interval, occluders,
                                   open_drummer_sightline, role_extents)
from models.final_band_scene import FinalBandScene


def scene():
    return FinalBandScene('glacier_pier', rock=False, full_keyboard=True)


def test_default_staging_hides_kit_edges_behind_both_singers():
    # Documents the defect this module repairs: without parallax the lead and
    # harmony singers cover the ride/crash and floor-tom sides of the kit.
    assert occluders(scene()) == ['harmony', 'lead']


def test_sightline_clears_kit_and_keeps_relative_staging():
    s = scene(); before = role_extents(s)
    report = open_drummer_sightline(s)
    after = role_extents(s); low, high = kit_interval(s)
    assert report['kit_occluded_by'] == [] and occluders(s) == []
    assert after['lead'][1] <= low-.15+1e-6 and after['harmony'][0] >= high+.15-1e-6
    # Each flank moves rigidly: widths and intra-group spacing are unchanged.
    for group, shift in ((('lead', 'bass'), report['left_group_shift']),
                         (('harmony', 'guitar', 'piano'), report['right_group_shift'])):
        for role in group:
            assert np.allclose(np.subtract(after[role], before[role]), shift, atol=1e-5)
    assert report['left_group_shift'] < 0 < report['right_group_shift']


def test_shift_carries_rigs_strings_mouths_and_keys():
    s = scene()
    rig = {(r['role'], r['side']): r['hand'].copy() for r in s.rigs}
    string = s.strings['guitar'][0]['a'].copy()
    mouth = s.expressive_mouths['lead']['center'].copy()
    key = next(o for o in s.instances if o['name'].startswith('piano_key_') and o['kind'] != 'hidden')
    key_x = float(key['matrix'][0, 3])
    report = open_drummer_sightline(s)
    left, right = report['left_group_shift'], report['right_group_shift']
    for r in s.rigs:
        expected = left if r['role'] in ('lead', 'bass') else right if r['role'] in ('harmony', 'guitar', 'piano') else 0
        assert np.allclose(r['hand']-rig[(r['role'], r['side'])], (expected, 0, 0), atol=1e-6)
    assert np.allclose(s.strings['guitar'][0]['a']-string, (right, 0, 0), atol=1e-6)
    assert np.allclose(s.expressive_mouths['lead']['center']-mouth, (left, 0, 0), atol=1e-6)
    assert s.expressive_mouths['lead']['center'] is s.instances[s.expressive_mouths['lead']['cavity']]['mouth_center']
    assert abs(float(key['matrix'][0, 3])-key_x-right) < 1e-6
    # Idempotent: a second call finds the corridor already clear.
    again = open_drummer_sightline(s)
    assert again['left_group_shift'] == 0 and again['right_group_shift'] == 0


def test_front_camera_frames_kit_and_every_player_at_1080p():
    s = scene(); open_drummer_sightline(s)
    camera = front_camera_for(s); vp, _ = camera(1920, 1080, 0.)
    spans = dict(role_extents(s)); spans['drummer'] = kit_interval(s)
    assert set(spans) == {'bass', 'guitar', 'piano', 'lead', 'harmony', 'drummer'}
    for low, high in spans.values():
        for x in (low, high):
            ndc = vp@np.array((x, 1.5, 0., 1.))
            assert -1 < ndc[0]/ndc[3] < 1
    # Fixed camera: independent of elapsed time.
    assert np.array_equal(vp, camera(1920, 1080, 12.5)[0])


def test_stage_deck_is_widened_to_carry_the_relocated_cast():
    s = scene()
    deck = next(o for o in s.instances if o['name'] == 'ice_pier_deck')
    riser = next(o for o in s.instances if o['name'] == 'drum_riser'); riser_before = riser['matrix'].copy()
    open_drummer_sightline(s)
    half = abs(float(deck['matrix'][0, 0]))/2; centre = float(deck['matrix'][0, 3])
    spans = role_extents(s)
    assert centre-half <= min(a for a, _ in spans.values())
    assert centre+half >= max(b for _, b in spans.values())
    assert np.array_equal(riser['matrix'], riser_before)
