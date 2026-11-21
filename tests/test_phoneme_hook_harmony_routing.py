"""Phoneme Test Hook: source-qualified harmony must reach the harmony snowman."""
from types import SimpleNamespace

from core.vocal_timeline import LyricTimeline, detect_background_vocal_windows


def test_explicit_harmony_singer_is_not_routed_to_instrumentalists():
    empty = LyricTimeline(lines=[], words=[], phoneme_events=[], confidence_summary={})
    event = SimpleNamespace(start_ms=1000, end_ms=1450, confidence=0.95,
                            energy=0.9, role="harmony", performer_hint="harmony_singer",
                            source_reason="distinct_user_supplied_stem_identity_unverified")
    windows = detect_background_vocal_windows(empty, [], [], classifier_events=[event])
    assert len(windows) == 1
    assert windows[0]["performer"] == "female_singer"
    assert windows[0]["source_reason"] == event.source_reason


def test_explicit_lead_singer_routes_to_lead_snowman():
    empty = LyricTimeline(lines=[], words=[], phoneme_events=[], confidence_summary={})
    event = SimpleNamespace(start_ms=1000, end_ms=1450, confidence=0.95,
                            energy=0.9, role="lead", performer_hint="lead_singer")
    windows = detect_background_vocal_windows(empty, [], [], classifier_events=[event])
    assert windows[0]["performer"] == "singer"
