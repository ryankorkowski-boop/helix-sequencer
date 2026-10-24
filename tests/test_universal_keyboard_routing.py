"""Port the legacy PR #179 keyboard event router to the current effect planner.

Only explicit non-keyboard performer assignments are excluded. Imported
unclassified MIDI and old Helix events retain their original interpretation.
"""
from effects.piano_effect import (
    route_universal_keyboard_notes, build_piano_effect_plan, PianoEffectConfig
)
from music.note_events import NoteEvent


def test_universal_effects_router_rejects_known_guitar_bass_drum_and_voice():
    notes = [
        NoteEvent(.100, .330, 60, .70, source="piano"),
        NoteEvent(.100, .400, 64, .80, source="xylophone"),
        NoteEvent(.100, .500, 67, .90, source="synth"),
        NoteEvent(.100, .250, 66, .90, source="electric_guitar_harmonic"),
        NoteEvent(.120, .280, 45, .90, source="bass_guitar_pitched"),
        NoteEvent(.130, .210, 73, .90, source="drums"),
        NoteEvent(.140, .270, 75, .90, source="vocal_pitched"),
    ]
    routed = route_universal_keyboard_notes(notes)
    assert [(e.pitch, e.source) for e in routed] == [
        (60, "piano"), (64, "xylophone"), (67, "synth")
    ]
    assert [(e.start, e.end, e.velocity) for e in routed] == [
        (.1, .33, .7), (.1, .4, .8), (.1, .5, .9)
    ]


def test_effect_plan_applies_role_ownership_to_actual_frames_and_buckets():
    notes = [
        NoteEvent(.20, .42, 60, .9, source="marimba"),
        NoteEvent(.20, .48, 64, .7, source="electric_piano"),
        NoteEvent(.20, .46, 67, 1.0, source="electric_guitar_harmonic"),
    ]
    plan = build_piano_effect_plan(
        notes,
        PianoEffectConfig(note_range_start=60, note_range_end=72),
        frame_times=[.21],
    )
    assert [e["pitch"] for e in plan["note_events"]] == [60, 64]
    assert [e["pitch"] for e in plan["note_bucket_activations"]] == [60, 64]
    assert [e["source"] for e in plan["note_events"]] == [
        "marimba", "electric_piano"
    ]
    assert [e["start"] for e in plan["note_events"]] == [.20, .20]


def test_effect_legacy_unknown_midi_and_helix_chords_stay_available():
    notes = [
        NoteEvent(1., 1.5, 60, .5, source="unknown"),
        NoteEvent(1., 1.5, 64, .6, source="helix_polyphonic"),
        NoteEvent(1., 1.5, 67, .8, source="piano"),
    ]
    routed = route_universal_keyboard_notes(notes)
    assert len(routed) == 3
    assert [e.pitch for e in routed] == [60, 64, 67]
