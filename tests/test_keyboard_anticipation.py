"""Motion regressions; synthetic notes are not real-song acceptance evidence."""
import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from models.keyboard_motion_plan import plan_keyboard_hands
from models.band_motion_refinement import elbow_3d
from models.band_instrument_logic import event_curves
from music.note_events import NoteEvent

ROOT = Path(__file__).resolve().parents[1]


def fixture(side='left', attack=20, frames=45):
    pitch = 60 if side == 'left' else 72
    held = np.full((frames, 1), -1)
    levels = np.zeros_like(held, dtype=float)
    held[attack, 0] = pitch
    levels[attack, 0] = .8
    centers = {60: np.array([-.6, .2, .25]), 72: np.array([.6, .2, .25])}
    rigs = {s: dict(shoulder=np.array([x, .8, 0]),
                   hand=np.array([x, .31, .315]),
                   link_lengths=(.52, .50))
            for s, x in [('left', -.3), ('right', .3)]}
    return held, levels, centers, rigs


@pytest.mark.parametrize('side', ['left', 'right'])
def test_idle_anticipation_reaches_short_note_without_early_contact(side):
    held, levels, centers, rigs = fixture(side)
    original = held.copy(), levels.copy()
    baseline = plan_keyboard_hands(held, levels, centers, rigs,
                                   max_step=.030, max_acceleration=.010)
    lanes, contacts, report = plan_keyboard_hands(
        held, levels, centers, rigs, max_step=.030, max_acceleration=.010,
        anticipation_frames=12)
    pitch = int(held[20, 0])
    assert baseline[1][side][20] is None
    assert contacts[side][20] == pitch
    assert all(value is None for value in contacts[side][:20] + contacts[side][21:])
    assert report[side]['source_active_frames'] == 1
    assert report[side]['contact_frames'] == 1
    assert report[side]['anticipated_idle_frames'] == 12
    np.testing.assert_array_equal(held, original[0])
    np.testing.assert_array_equal(levels, original[1])
    for hand, lane in lanes.items():
        positions = np.vstack([rigs[hand]['hand'], lane])
        speeds = np.diff(positions, axis=0)
        assert np.linalg.norm(speeds, axis=1).max() <= .03000001
        assert np.linalg.norm(np.diff(np.vstack([np.zeros(3), speeds]), axis=0),
                              axis=1).max() <= .01000001
        for point in lane:
            elbow = elbow_3d(rigs[hand]['shoulder'], point, .52, .50, (0, 0, 1))
            assert np.isfinite(elbow).all()
    assert np.all(lanes['left'][:, 0] <= lanes['right'][:, 0])


def test_no_movement_before_bounded_lookahead_and_no_future_contact():
    held, levels, centers, rigs = fixture(attack=40, frames=60)
    lanes, contacts, report = plan_keyboard_hands(
        held, levels, centers, rigs, anticipation_frames=12)
    np.testing.assert_allclose(lanes['left'][:28],
                               np.tile(rigs['left']['hand'], (28, 1)))
    assert all(value is None for value in contacts['left'][:40])
    assert report['anticipation_frames'] == 12


def test_unreachable_future_note_never_moves_hand_or_claims_contact():
    held, levels, centers, rigs = fixture()
    centers[60] = np.array([-20., .2, .25])
    lanes, contacts, report = plan_keyboard_hands(
        held, levels, centers, rigs, anticipation_frames=12)
    np.testing.assert_allclose(lanes['left'],
                               np.tile(rigs['left']['hand'], (len(held), 1)))
    assert not any(value is not None for value in contacts['left'])
    assert report['left']['anticipated_idle_frames'] == 0


@pytest.mark.parametrize('value', [-1, 121, .5, float('nan'), True])
def test_invalid_anticipation_window_is_rejected(value):
    with pytest.raises(ValueError, match='Anticipation'):
        plan_keyboard_hands(*fixture(), anticipation_frames=value)


def test_default_keeps_legacy_reactive_motion():
    held, levels, centers, rigs = fixture()
    lanes, contacts, report = plan_keyboard_hands(held, levels, centers, rigs)
    np.testing.assert_allclose(lanes['left'][:20],
                               np.tile(rigs['left']['hand'], (20, 1)))
    assert contacts['left'][20] is None
    assert report['anticipation_frames'] == 0


def install_method():
    # Execute the production method with its actual note compiler and planner.
    # Isolate it from renderer/device imports; no replacement motion algorithm.
    tree = ast.parse((ROOT / 'tools/musical_band_performance.py').read_text())
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == 'MusicalBandPerformance')
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == '_install_keyboard_events')
    namespace = {'np': np, 'event_curves': event_curves}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(ROOT), 'exec'), namespace)
    return namespace['_install_keyboard_events']


@pytest.mark.parametrize('legacy', [False, True])
def test_production_install_preserves_note_clock_and_limits_opt_in(legacy):
    _, _, centers, rigs = fixture()
    scene = SimpleNamespace(legacy_mallet_player=legacy,
                            rigs=[dict(role='piano', side=side, **rig)
                                  for side, rig in rigs.items()])
    performer = SimpleNamespace(n=45, curves={}, scene=scene, key_centers=centers)
    notes = [NoteEvent(1., 1.05, 60, .8, source='piano')]
    install_method()(performer, notes)
    held, levels, attacks, phase = event_curves(notes, 45, 6, release=0)
    np.testing.assert_array_equal(performer.curves['piano_notes'], held)
    np.testing.assert_array_equal(performer.curves['piano_note_levels'], levels)
    np.testing.assert_array_equal(performer.curves['piano_attack'], attacks)
    assert performer.keyboard_events == notes
    assert performer.keyboard_motion_report['accepted_events'] == 1
    assert performer.keyboard_motion_report['anticipation_frames'] == (0 if legacy else 12)
    if not legacy:
        assert performer.key_assignments['left'][20] == 60
