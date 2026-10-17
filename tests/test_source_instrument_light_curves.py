"""Source-note lighting regressions; no xLights executable needed."""
from types import SimpleNamespace
import pytest
import numpy as np
from tools.build_spatial_review import band_curves, _note_curves


def test_note_curves_hold_exact_pitch_and_keep_octaves_separate():
    events=[SimpleNamespace(start=.05,end=.15,pitch=60,velocity=.7),
            SimpleNamespace(start=.10,end=.20,pitch=72,velocity=.9)]
    notes=_note_curves(events,5)
    assert set(notes)=={60,72}
    np.testing.assert_allclose(notes[60],[0,.7,.7,0,0])
    np.testing.assert_allclose(notes[72],[0,0,.9,.9,0])


def _instrument(role):
    return SimpleNamespace(details={"review_role":role},
        submodels={f"STRING_{j}":[] for j in range(4 if role=="bass" else 6)})


def test_only_routed_bass_strings_illuminate():
    p=SimpleNamespace(n=4,keyboard_events=[],curves={
        "bass_routes":[[(2,5)],[],[(0,3),(2,7)],[]],
        "bass_energy":np.array([.8,1.,.4,.7]),
        "bass_attack":np.zeros(4),
    })
    result=band_curves(_instrument("bass"),p)
    np.testing.assert_allclose(result["STRING_0"],[0,0,.4,0])
    np.testing.assert_allclose(result["STRING_1"],[0,0,0,0])
    np.testing.assert_allclose(result["STRING_2"],[.8,0,.4,0])
    np.testing.assert_allclose(result["STRING_3"],[0,0,0,0])


def test_only_routed_guitar_strings_illuminate():
    p=SimpleNamespace(n=3,keyboard_events=[],curves={
        "guitar_routes":[[],[(1,2),(4,7)],[]],
        "guitar_energy":np.array([1.,.75,1.]),
        "guitar_attack":np.zeros(3),
    })
    result=band_curves(_instrument("guitar"),p)
    for j in range(6):
        np.testing.assert_allclose(result[f"STRING_{j}"],
            [0,.75 if j in (1,4) else 0,0])


def test_rejects_invalid_note_velocity():
    for velocity in (float('nan'), -0.1, 1.1):
        with pytest.raises(ValueError):
            _note_curves([SimpleNamespace(start=0,end=.1,pitch=60,velocity=velocity)],3)
