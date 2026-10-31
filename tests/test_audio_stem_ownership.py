from core.audio_intelligence import NoteEvent
from core.source_ownership import ownership_from_stem
from core.snowman_band import _event_owner


def _audio_note(stem, confidence=.95):
    return NoteEvent(
        timestamp_ms=100, duration_ms=200, pitch_hz=440.0,
        midi_note=69, note_name="A4", velocity=.8,
        confidence=confidence, source_stem=stem,
    )


def test_explicit_keyboard_stem_routes_to_keyboard():
    owner = _event_owner(_audio_note("piano"))
    assert owner is not None
    assert owner.performer == "keyboardist"
    assert owner.permitted()


def test_guitar_stem_not_keyboard():
    owner = _event_owner(_audio_note("electric_guitar"))
    assert owner is not None
    assert owner.performer == "guitarist"


def test_mixed_stem_does_not_guess_keyboard():
    owner = _event_owner(_audio_note("other"))
    assert owner is not None
    assert owner.performer is None
    assert not owner.permitted()


def test_low_confidence_piano_is_suppressed():
    assert not _event_owner(_audio_note("piano", .2)).permitted()


def test_original_audio_serialization_unchanged():
    assert "source_owner" not in _audio_note("piano").to_dict()


def test_estimated_keyboard_stem_passes_strict_cue_routing():
    from core.snowman_band import _build_keyboard_note_cues
    from types import SimpleNamespace
    note = SimpleNamespace(
        start_ms=100, end_ms=200, notes=[(60, .9)],
        source_owner=_audio_note("piano", .9).ownership(),
    )
    assert len(_build_keyboard_note_cues([note], [], require_source_ownership=True)) == 1


def test_nonfinite_confidence_fails_closed():
    import math
    import pytest
    from core.source_ownership import SourceOwnership
    with pytest.raises(ValueError):
        SourceOwnership("keyboardist", math.nan, "estimated")
    with pytest.raises(ValueError):
        SourceOwnership("keyboardist", math.inf, "detected")
    assert not ownership_from_stem("piano", math.nan).permitted()


def test_invalid_source_identity_fails_closed():
    import pytest
    from core.source_ownership import SourceOwnership
    with pytest.raises(ValueError):
        SourceOwnership("xylophonist", .9, "detected")
    with pytest.raises(ValueError):
        SourceOwnership("keyboardist", .9, "unverified")


def test_real_audio_note_event_produces_strict_keyboard_cue():
    from core.snowman_band import _build_keyboard_note_cues
    cues = _build_keyboard_note_cues(
        [_audio_note("piano", .93)], [], require_source_ownership=True,
    )
    assert len(cues) == 1
    assert cues[0]["start_ms"] == 100
    assert cues[0]["end_ms"] == 300
    assert cues[0]["pitch_midi"] == 69
    assert cues[0]["velocity"] == .8


def test_real_audio_guitar_note_not_sent_to_keyboard():
    from core.snowman_band import _build_keyboard_note_cues
    assert _build_keyboard_note_cues(
        [_audio_note("guitar", .98)], [], require_source_ownership=True,
    ) == []


def test_real_audio_unknown_stem_not_sent_to_keyboard():
    from core.snowman_band import _build_keyboard_note_cues
    assert _build_keyboard_note_cues(
        [_audio_note("mix", .99)], [], require_source_ownership=True,
    ) == []


def test_nonfinite_stem_pitch_is_ignored():
    from types import SimpleNamespace
    from core.snowman_band import _build_keyboard_note_cues
    note = SimpleNamespace(
        timestamp_ms=100, duration_ms=150, midi_note=float("nan"),
        velocity=.8, source_owner=_audio_note("piano").ownership(),
    )
    assert _build_keyboard_note_cues([note], [], require_source_ownership=True) == []


def test_nonfinite_stem_velocity_is_ignored():
    from types import SimpleNamespace
    from core.snowman_band import _build_keyboard_note_cues
    note = SimpleNamespace(
        timestamp_ms=100, duration_ms=150, midi_note=60,
        velocity=float("inf"), source_owner=_audio_note("piano").ownership(),
    )
    assert _build_keyboard_note_cues([note], [], require_source_ownership=True) == []
