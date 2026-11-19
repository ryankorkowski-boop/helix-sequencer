"""Integration contract for opt-in strict keyboard source ownership."""
from core.effect_engine import NoteEvent, RuntimeTuning
from core.snowman_band import _build_keyboard_note_cues


def _event(owner=None):
    return NoteEvent(
        start_ms=100, end_ms=250, notes=[(60, .8)],
        part="verse", section="verse", source_owner=owner,
    )


def test_default_runtime_preserves_existing_band_behavior():
    tuning = RuntimeTuning()
    assert tuning.require_keyboard_source_ownership is False
    assert len(_build_keyboard_note_cues([_event()], [])) == 1


def test_harmonic_events_do_not_claim_instrument_identity():
    assert _event().source_owner is None
    assert _build_keyboard_note_cues([_event()], [], require_source_ownership=True) == []


def test_explicit_verified_keyboard_identity_can_pass():
    owner = {"performer": "keyboardist", "confidence": .95, "origin": "detected", "source_id": "stem:keys"}
    cues = _build_keyboard_note_cues([_event(owner)], [], require_source_ownership=True)
    assert len(cues) == 1


def test_explicit_guitar_identity_not_sent_to_keyboard():
    owner = {"performer": "guitarist", "confidence": .99, "origin": "detected", "source_id": "stem:guitar"}
    assert _build_keyboard_note_cues([_event(owner)], [], require_source_ownership=True) == []
