from __future__ import annotations

from core.birdsong_feature_state import FeatureState
from core.birdsong_motion import MotionPulse, advance_motion_pulses, create_motion_pulse, direction_motion
from core.birdsong_phrase_engine import Phrase


def _state(*, energy: float = 0.5, onset: float = 0.0) -> FeatureState:
    state = FeatureState(smoothing_alpha=1.0)
    state.update({"energy": energy, "onset": onset, "bands": (0.3, 0.4, 0.3)})
    return state


def _phrase(direction: str = "left_to_right") -> Phrase:
    return Phrase(start_time=0.0, duration=4.0, motif="wave_sweep", direction=direction, energy_anchor=0.5)


def test_motion_pulse_advances_position_and_decays_strength() -> None:
    pulse = MotionPulse(position=(0.0, 0.0, 0.0), step=(1.0, 0.5, 0.0), strength=1.0, decay=0.5)

    advanced = pulse.advance(2.0)

    assert advanced.position == (2.0, 1.0, 0.0)
    assert advanced.strength == 0.5
    assert advanced.step == pulse.step


def test_motion_pulse_rejects_negative_time() -> None:
    pulse = MotionPulse(position=(0.0, 0.0, 0.0), step=(1.0, 0.0, 0.0), strength=1.0)

    try:
        pulse.advance(-0.1)
    except ValueError as exc:
        assert "seconds must be >= 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative time")


def test_direction_motion_is_deterministic() -> None:
    assert direction_motion("left_to_right") == ((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    assert direction_motion("right_to_left") == ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0))
    assert direction_motion("center_out") == ((0.0, 0.0, 0.0), (1.0, 0.2, 0.0))
    assert direction_motion("bottom_up") == ((0.0, -1.0, 0.0), (0.0, 1.0, 0.0))
    assert direction_motion("top_down") == ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0))
    assert direction_motion("unknown") == direction_motion("left_to_right")


def test_create_motion_pulse_requires_meaningful_trigger() -> None:
    quiet = _state(energy=0.2, onset=0.1)
    loud = _state(energy=0.6, onset=0.1)
    onset = _state(energy=0.1, onset=0.8)

    assert create_motion_pulse(quiet, _phrase()) is None
    assert create_motion_pulse(loud, _phrase()) is not None
    assert create_motion_pulse(onset, _phrase()) is not None


def test_create_motion_pulse_uses_phrase_direction() -> None:
    pulse = create_motion_pulse(_state(energy=0.8), _phrase("top_down"))

    assert pulse is not None
    assert pulse.position == (0.0, 1.0, 0.0)
    assert pulse.step == (0.0, -1.0, 0.0)
    assert pulse.strength == 0.8


def test_advance_motion_pulses_prunes_inactive_pulses() -> None:
    active = MotionPulse(position=(0.0, 0.0, 0.0), step=(1.0, 0.0, 0.0), strength=0.5, decay=0.9)
    fading = MotionPulse(position=(0.0, 0.0, 0.0), step=(1.0, 0.0, 0.0), strength=0.01, decay=0.5)

    advanced = advance_motion_pulses((active, fading), 1.0)

    assert len(advanced) == 1
    assert advanced[0].position == (1.0, 0.0, 0.0)
    assert advanced[0].strength == 0.45
