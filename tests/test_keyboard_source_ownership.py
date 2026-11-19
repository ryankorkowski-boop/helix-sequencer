"""Production keyboard ownership: no guitar, bass, drum or voice stealing."""
from music.magic_keyboard import magic_keyboard_events
from music.note_events import NoteEvent


def test_explicit_keyboard_and_mallet_roles_join_one_source_timed_stream():
    events = [
        NoteEvent(.125, .380, 60, .7, source="piano"),
        NoteEvent(.125, .400, 64, .8, source="electric_piano"),
        NoteEvent(.125, .410, 67, .9, source="marimba"),
        NoteEvent(.200, .450, 72, .5, source="xylophone"),
        NoteEvent(.230, .510, 79, .6, source="celesta"),
    ]
    routed = magic_keyboard_events(events, duration=2)
    assert len(routed) == len(events)
    assert [(e.start, e.end, e.pitch, e.source) for e in routed] == [
        (e.start, e.end, e.pitch, e.source) for e in events
    ]


def test_other_performers_cannot_route_even_with_high_pitch_confidence():
    forbidden = [
        "electric_guitar_harmonic", "guitar_pitched_onset",
        "bass_stem_harmonic_estimate", "bass_guitar_pitched",
        "drum_pitched", "percussion_harmonic", "vocal_pitched",
        "voice_harmonic", "kick_pitched", "snare_harmonic",
    ]
    events = [NoteEvent(i/10, i/10+.1, 60+i, .9, source=source, confidence=.99)
              for i, source in enumerate(forbidden)]
    routed = magic_keyboard_events(events, duration=3)
    assert routed == []


def test_chords_keep_provenance_and_duplicate_only_exact_same_pitch_and_time():
    events = [
        NoteEvent(.3, .8, 60, .3, source="piano"),
        NoteEvent(.3, .8, 60, .8, source="marimba"),
        NoteEvent(.3, .8, 64, .6, source="synth", confidence=.9),
        NoteEvent(.3, .8, 67, .5, source="vibraphone"),
    ]
    routed = magic_keyboard_events(events, duration=1)
    assert [(e.pitch, e.source, e.velocity) for e in routed] == [
        (60, "marimba", .8), (64, "synth", .6), (67, "vibraphone", .5)
    ]


def test_unknown_pitch_labels_do_not_make_up_keyboard_activity():
    events = [
        NoteEvent(0, .2, 60, source="unknown", confidence=.99),
        NoteEvent(.3, .5, 67, source="unclassified", confidence=.99),
        NoteEvent(.5, .7, 70, source="synth_pitched_onset", confidence=.30),
    ]
    assert magic_keyboard_events(events, duration=1) == []


def test_original_source_timing_does_not_move_to_visual_frames():
    source = NoteEvent(.173, .343, 74, .75, source="bells", confidence=.92)
    (result,) = magic_keyboard_events([source], duration=2)
    assert (result.start, result.end, result.velocity, result.source) == (
        .173, .343, .75, "bells"
    )
