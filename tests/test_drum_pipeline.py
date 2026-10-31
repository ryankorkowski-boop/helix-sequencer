from types import SimpleNamespace

import numpy as np

from core.drum_pipeline import (
    PercussionMarks, apply_stem_percussion, build_drum_cues, classify_percussion_onsets,
)


def test_centroid_thresholds_and_nonfinite_inputs_preserve_fallback_roles():
    audio = SimpleNamespace(times_s=np.arange(6, dtype=float),
                            centroid=np.array([2199., 2200., 4499., 4500., np.nan, np.inf]))
    assert classify_percussion_onsets(audio, [0, 1000, 2000, 3000, 4000, 5000]) == PercussionMarks(
        kicks=[0], snares=[1000, 2000], hats=[3000])


def test_isolated_stem_overrides_only_roles_with_real_marks():
    fallback = PercussionMarks([100], [200], [300])
    stems = SimpleNamespace(drum_kicks_ms=[], drum_snares_ms=[1000, 1005, 1400], drum_hats_ms=[])
    result = apply_stem_percussion(fallback, stems)
    assert result == PercussionMarks([100], [1000, 1400], [300])
    assert result.kicks is fallback.kicks
    assert fallback.snares == [200]


def test_empty_source_does_not_invent_drum_cues():
    cues, kit, debug = build_drum_cues([], part_label=lambda parts, at: "SECTION",
                                      drum_event_streams={}, kicks=[], snares=[], hats=[], releases=[])
    assert cues == [] and kit == []
    assert not debug["mapping"] and not debug["motion_events"]
