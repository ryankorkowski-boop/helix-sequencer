"""Regression: uploaded Helix review videos show visually matching mouth shapes.

Matching shapes can be genuine unison. Only reject near-gain-scaled, nearly
frame-identical *unverified* estimates; never assert the MP4 proves singer ID.
"""
import numpy as np
from music.vocal_qualification import independence_metrics, screen_candidate_lanes


def test_nearly_identical_backing_clock_does_not_animate_second_mouth():
    n = 100
    t = np.arange(n, dtype='f8')
    lead = .55 + .18 * np.sin(t / 13)
    # Not byte-identical: pitch detection/encoding may produce slight drift.
    backing = lead * (.52 + .0015 * np.sin(t / 7))
    energy = np.column_stack((lead, backing))
    shapes = np.full((n, 2), 2, dtype='i1')
    shapes[10:25, :] = 3
    shapes[25:75, :] = 4
    shapes[39, 1] = 5
    p = np.full((n, 2), .92)
    screened, phones, report = screen_candidate_lanes(energy, shapes, p, fps=100)
    assert np.any(screened[:, 0])
    assert not np.any(screened[:, 1])
    assert not np.any(phones[:, 1])
    assert report['state'] == 'REJECTED'
    assert report['suppression_reason'] == 'near_mirrored_estimate'
    assert report['metrics_before_duplicate_suppression']['suspicious_mirror']


def test_independent_overlapping_harmony_with_different_dynamics_is_kept():
    n = 100
    t = np.arange(n, dtype='f8')
    lead = .48 + .18 * np.sin(t/15)
    backing = .4 + .25 * np.cos(t/8)
    energy = np.column_stack((lead, backing))
    shapes = np.full((n, 2), 2, dtype='i1')
    prob = np.full((n, 2), .92)
    screened, phones, report = screen_candidate_lanes(energy, shapes, prob, fps=100)
    assert np.all(screened[:, 0] > 0)
    assert np.all(screened[:, 1] > 0)
    assert np.all(phones[:, 1] == 2)
    assert report['state'] == 'ESTIMATED'
    assert report['suppression_reason'] is None


def test_backing_only_phrase_survives_and_does_not_get_copied_to_lead():
    energy = np.zeros((100,2), 'f4')
    energy[2:48,0] = .64
    energy[32:90,1] = .59
    shapes = np.zeros((100,2), 'i1')
    shapes[2:48,0] = 2
    shapes[32:90,1] = 4
    probs = np.where(energy>0,.93,.05)
    screened, phones, report = screen_candidate_lanes(energy,shapes,probs,fps=100)
    assert np.all(screened[50:90,0] == 0)
    assert np.all(screened[50:90,1] > 0)
    assert np.all(phones[50:90,1] == 4)
    assert report['state'] == 'ESTIMATED'


def test_exact_duplicate_clock_remains_rejected():
    x = np.linspace(.32,.88,100)
    y = x * .55
    energy = np.column_stack((x,y))
    shapes = np.full((100,2),2)
    metrics = independence_metrics(energy,shapes)
    assert metrics['duplicate_clock']
    kept,_,report = screen_candidate_lanes(energy,shapes,np.ones((100,2)),fps=100)
    assert not kept[:,1].any()
    assert report['suppression_reason'] == 'exact_duplicate'
