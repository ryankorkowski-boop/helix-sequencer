"""Opt-in source ownership integration regression checks."""
from types import SimpleNamespace

from core.snowman_band import _build_keyboard_note_cues


def _note(owner=None):
    return SimpleNamespace(start_ms=100, end_ms=300, notes=[(60, .8)], source_owner=owner)


def test_legacy_keyboard_behavior_unchanged():
    assert len(_build_keyboard_note_cues([_note()], [])) == 1


def test_strict_mode_rejects_unowned_pitch():
    assert _build_keyboard_note_cues([_note()], [], require_source_ownership=True) == []


def test_strict_mode_accepts_detected_keyboard():
    owner = dict(performer="keyboardist", confidence=.95, origin="detected", source_id="stem:keys")
    cues = _build_keyboard_note_cues([_note(owner)], [], require_source_ownership=True)
    assert len(cues) == 1
    assert cues[0]["pitch_midi"] == 60


def test_strict_mode_rejects_guitar_and_low_confidence():
    guitar = dict(performer="guitarist", confidence=.99, origin="detected")
    weak_keys = dict(performer="keyboardist", confidence=.4, origin="estimated")
    assert _build_keyboard_note_cues([_note(guitar), _note(weak_keys)], [], require_source_ownership=True) == []
