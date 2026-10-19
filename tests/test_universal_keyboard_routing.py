from effects.piano_effect import route_universal_keyboard_notes
from music.note_events import NoteEvent


def test_universal_keyboard_keeps_mallets_and_keys_without_stealing_band():
    events = [
        NoteEvent(0.0, 0.3, 60, source="piano"),
        NoteEvent(0.1, 0.2, 72, source="xylophone"),
        NoteEvent(0.1, 0.2, 40, source="bass"),
        NoteEvent(0.2, 0.3, 67, source="guitar"),
        NoteEvent(0.2, 0.3, 69, source="drums"),
        NoteEvent(0.3, 0.5, 64, source="marimba"),
    ]
    selected = route_universal_keyboard_notes(events)
    assert [event.source for event in selected] == ["piano", "xylophone", "marimba"]


def test_universal_keyboard_preserves_unknown_legacy_events_and_chords():
    events = [
        NoteEvent(1.0, 1.5, 60, source="unknown"),
        NoteEvent(1.0, 1.5, 64, source="helix_polyphonic"),
        NoteEvent(1.0, 1.5, 67, source="synth"),
    ]
    assert len(route_universal_keyboard_notes(events)) == 3
