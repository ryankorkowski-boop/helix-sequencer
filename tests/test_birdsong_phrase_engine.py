from __future__ import annotations

from core.birdsong_feature_state import FeatureState
from core.birdsong_phrase_engine import (
    BIRDSONG_MOTIFS,
    PhraseEngine,
    choose_direction,
    choose_motif,
)


def _state(*, energy: float = 0.5, onset: float = 0.0, bands=(0.3, 0.4, 0.3)) -> FeatureState:
    state = FeatureState(smoothing_alpha=1.0)
    state.update({"energy": energy, "onset": onset, "bands": bands})
    return state


def test_phrase_duration_is_tied_to_bpm_and_bounded() -> None:
    fast = PhraseEngine(bpm=240, min_duration=2.0, max_duration=8.0)
    normal = PhraseEngine(bpm=120, min_duration=2.0, max_duration=8.0)
    slow = PhraseEngine(bpm=30, min_duration=2.0, max_duration=8.0)

    assert fast.phrase_duration() == 2.0
    assert normal.phrase_duration() == 4.0
    assert slow.phrase_duration() == 8.0


def test_motif_selection_is_bounded_to_five_motifs() -> None:
    states = [
        _state(bands=(0.7, 0.2, 0.1)),
        _state(bands=(0.2, 0.7, 0.1)),
        _state(bands=(0.1, 0.2, 0.7)),
        _state(onset=0.8, bands=(0.3, 0.3, 0.4)),
    ]

    for index, state in enumerate(states):
        assert choose_motif(state, index) in BIRDSONG_MOTIFS


def test_direction_selection_tracks_dominant_band() -> None:
    assert choose_direction(_state(bands=(0.8, 0.1, 0.1))) == "center_out"
    assert choose_direction(_state(bands=(0.1, 0.1, 0.8))) == "top_down"
    assert choose_direction(_state(bands=(0.1, 0.8, 0.1))) == "left_to_right"


def test_phrase_engine_reuses_phrase_until_boundary() -> None:
    engine = PhraseEngine(bpm=120)
    state = _state(energy=0.5)

    first = engine.update(0.0, state)
    second = engine.update(1.0, state)

    assert second == first


def test_phrase_engine_starts_new_phrase_on_time_boundary() -> None:
    engine = PhraseEngine(bpm=120)
    state = _state(energy=0.5)

    first = engine.update(0.0, state)
    second = engine.update(first.end_time, state)

    assert second != first
    assert second.start_time == first.end_time


def test_phrase_engine_starts_new_phrase_on_strong_onset_after_min_duration() -> None:
    engine = PhraseEngine(bpm=120, min_duration=2.0, onset_threshold=0.7)

    first = engine.update(0.0, _state(energy=0.4, onset=0.1))
    early = engine.update(1.0, _state(energy=0.4, onset=0.9))
    later = engine.update(2.0, _state(energy=0.4, onset=0.9))

    assert early == first
    assert later != first
    assert later.start_time == 2.0


def test_phrase_engine_starts_new_phrase_on_energy_shift_after_min_duration() -> None:
    engine = PhraseEngine(bpm=120, min_duration=2.0, energy_shift_threshold=0.2)

    first = engine.update(0.0, _state(energy=0.2))
    same = engine.update(1.0, _state(energy=0.9))
    shifted = engine.update(2.0, _state(energy=0.9))

    assert same == first
    assert shifted != first
    assert shifted.energy_anchor == 0.9
