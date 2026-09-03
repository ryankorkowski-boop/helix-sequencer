from core.wadena_av_sync import (
    AnchorMatch,
    EnvelopePoint,
    assess_piecewise_alignment,
    match_transition_anchors,
    piecewise_offset_intervals,
)


def test_matches_local_audio_anchors_without_warping():
    video = [EnvelopePoint(t, 1.0) for t in (10.0, 40.0, 100.0)]
    audio = [EnvelopePoint(t, 0.9) for t in (10.2, 40.2, 100.2)]
    anchors = match_transition_anchors(video, audio, tolerance=0.5)
    assert [round(a.offset, 3) for a in anchors] == [0.2, 0.2, 0.2]
    assert all(a.uncertainty >= 0.05 for a in anchors)


def test_no_match_outside_tolerance():
    video = [EnvelopePoint(10.0, 1.0)]
    audio = [EnvelopePoint(12.0, 1.0)]
    assert match_transition_anchors(video, audio, tolerance=0.5) == ()


def test_stable_offsets_are_supported_but_not_declared_same_performance():
    anchors = tuple(
        AnchorMatch(t, t + 0.25, 0.25, 0.8, 0.1)
        for t in (10.0, 40.0, 100.0)
    )
    assessment = assess_piecewise_alignment(anchors)
    assert assessment.stable is True
    assert assessment.same_performance_supported is False
    assert "stable local offset" in assessment.reason


def test_disagreeing_offsets_require_uncertain_alignment():
    anchors = (
        AnchorMatch(10.0, 10.1, 0.1, 0.8, 0.1),
        AnchorMatch(40.0, 40.9, 0.9, 0.8, 0.1),
        AnchorMatch(100.0, 100.1, 0.1, 0.8, 0.1),
    )
    assessment = assess_piecewise_alignment(anchors, max_offset_spread=0.75)
    assert assessment.stable is False
    assert assessment.same_performance_supported is False


def test_piecewise_intervals_are_deterministic_and_non_overlapping():
    anchors = (
        AnchorMatch(10.0, 10.2, 0.2, 0.8, 0.1),
        AnchorMatch(40.0, 40.2, 0.2, 0.8, 0.1),
        AnchorMatch(100.0, 100.2, 0.2, 0.8, 0.1),
    )
    intervals = piecewise_offset_intervals(anchors)
    assert intervals == (
        (10.0, 25.0, 0.2, 0.1),
        (25.0, 70.0, 0.2, 0.1),
        (70.0, 100.0, 0.2, 0.1),
    )
