"""Native XYZ layout and source-event gates for the 16-panel redesign."""
from __future__ import annotations

import numpy as np
import pytest

from models.advanced_full_song_showcase import build_showcase
from tools.source_spatial_direction import schedule


@pytest.mark.parametrize("panel,minimum", [(13, 15), (14, 16), (15, 21), (16, 32)])
def test_new_spatial_models_are_physical_native_3d(panel, minimum):
    g, _ = build_showcase(panel, {"cues": {}}, duration=1.,
                          native_band=lambda *args, **kwargs: None)
    added = [m for m in g.models if m.details.get("spatial_showcase_native_xyz")]
    assert len(added) >= minimum
    assert len({m.name for m in added}) == len(added)
    assert len({m.zone for m in added}) >= 2
    for m in added:
        assert m.kind == "pixel"
        assert len(m.colors) == len(m.points)
        assert m.channels == 3 * len(m.points)
        assert sum(np.ptp(m.points[:, axis]) > 0 for axis in range(3)) >= 2
        assert m.details["advanced_spatial_routing"] is True
        assert m.details["source_display_floor"] <= .25
    assert any(m.details.get("source_route_count", 1) > 1 for m in added)


@pytest.mark.parametrize("panel", [13, 14, 15, 16])
def test_spatial_layout_never_invents_unmeasured_audio_events(panel):
    g, _ = build_showcase(panel, {"cues": {}}, duration=1.,
                          native_band=lambda *args, **kwargs: None)
    empty = {"cues": {role: [] for role in
                       ("guitarist", "keyboardist", "bassist", "drummer")}}
    for model in g.models:
        if model.details.get("spatial_showcase_native_xyz"):
            assert schedule(model, empty, {}, 1000) == []


@pytest.mark.parametrize("panel", [13, 14, 15, 16])
def test_spatial_source_clock_clamps_to_real_note_boundaries(panel):
    plan = {"cues": {role: [{"start_ms": 200, "end_ms": 740,
                             "kind": "pitched_note", "pitch_midi": 64,
                             "velocity": .8, "section": "chorus"}]
                     for role in ("guitarist", "keyboardist", "bassist")}}
    g, _ = build_showcase(panel, plan, duration=1.,
                          native_band=lambda *args, **kwargs: None)
    results = [event for model in g.models
               if model.details.get("spatial_showcase_native_xyz")
               for event in schedule(model, plan, {}, 1000)]
    assert results, "At least one measured event must survive spatial routing"
    assert all(200 <= event["start_ms"] < event["end_ms"] <= 740
               for event in results)
    assert all(event["source_start_ms"] == 200
               and event["source_end_ms"] == 740 for event in results)
    assert all(event["role"] in ("guitarist", "keyboardist", "bassist")
               for event in results)
