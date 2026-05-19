from __future__ import annotations

from core.show_director import DirectorState, ShowDirector


def test_show_director_starts_sparse_intro() -> None:
    director = ShowDirector(song_length_s=60.0)

    state = director.update(time_s=1.0, energy=0.25)

    assert isinstance(state, DirectorState)
    assert state.section == "intro"
    assert 0.0 < state.intensity < 0.5


def test_show_director_marks_high_energy_drop() -> None:
    director = ShowDirector(song_length_s=60.0)

    state = director.update(time_s=20.0, energy=0.9)

    assert state.section == "drop"
    assert state.intensity > 0.9


def test_show_director_marks_late_outro() -> None:
    director = ShowDirector(song_length_s=60.0)

    state = director.update(time_s=55.0, energy=0.8)

    assert state.section == "outro"
    assert state.intensity < 0.7


def test_show_director_builds_on_rising_energy() -> None:
    director = ShowDirector(song_length_s=60.0)
    director.update(time_s=10.0, energy=0.25)

    state = director.update(time_s=12.0, energy=0.45)

    assert state.section == "build"
    assert 0.5 < state.intensity < 0.9
