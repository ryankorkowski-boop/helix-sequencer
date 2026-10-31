from types import SimpleNamespace

from core.event_provenance import summarize_note_provenance


def test_mixed_harmonic_notes_remain_unknown():
    events = [SimpleNamespace(start_ms=120, notes=[(60, .8)], section="verse")]
    result = summarize_note_provenance(events)
    assert result["unknown_ownership_events"] == 1
    assert result["sample"][0]["source_stem"] == "mixed_unknown"
    assert result["sample"][0]["performer"] is None
    assert result["sample"][0]["features"]["pitch_count"] == 1


def test_explicit_stem_confidence_is_preserved():
    event = SimpleNamespace(
        timestamp_ms=210, midi_note=69, source_stem="piano",
        source_owner={"performer": "keyboardist", "confidence": .91,
                      "origin": "estimated", "source_id": "piano"},
    )
    result = summarize_note_provenance([event])
    assert result["sample"][0]["performer"] == "keyboardist"
    assert result["sample"][0]["confidence"] == .91
    assert result["unknown_ownership_events"] == 0


def test_provenance_is_bounded_without_losing_counts():
    events = [SimpleNamespace(start_ms=i, notes=[]) for i in range(20)]
    result = summarize_note_provenance(events, limit=3)
    assert result["total_events"] == 20
    assert result["unknown_ownership_events"] == 20
    assert len(result["sample"]) == 3
    assert result["sample_truncated"]


def test_invalid_confidence_does_not_escape_to_json():
    event = SimpleNamespace(timestamp_ms=0, source_owner={
        "performer": "keyboardist", "confidence": float("nan"),
        "origin": "estimated",
    })
    assert summarize_note_provenance([event])["sample"][0]["confidence"] is None


def test_explicit_unknown_owner_is_unresolved():
    event = SimpleNamespace(timestamp_ms=50, source_owner={
        "performer": "unknown", "confidence": 0.0,
        "origin": "fallback", "source_id": "mix_harmonic",
    })
    result = summarize_note_provenance([event])
    assert result["unknown_ownership_events"] == 1
    assert result["sample"][0]["performer"] == "unknown"
