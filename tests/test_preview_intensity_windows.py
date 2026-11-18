"""Windowed preview matrices must match the full-timeline matrix."""
import numpy as np

from tools.preview_renderer import (
    EffectRecord,
    HouseRenderer,
    LayoutData,
    ModelGeom,
    SequenceData,
    build_leaf_intensity_matrix,
)


def _layout():
    leaves = {
        "Left": ModelGeom("Left", 0, 0, 8, 0, ((0, 0), (8, 0)), "Arch", (20, 180, 40)),
        "Right": ModelGeom("Right", 12, 0, 20, 0, ((12, 0), (20, 0)), "Arch", (220, 40, 40)),
    }
    return LayoutData(leaf_models=leaves, groups={}, bounds=(0, 0, 20, 4))


def _sequence():
    return SequenceData(
        duration_ms=2000,
        model_effects={
            "Left": [
                EffectRecord("On", 0, 500),
                EffectRecord("Ramp", 400, 1200),
                EffectRecord("On", 1500, 1600),
            ],
            "Right": [EffectRecord("On", 800, 2000)],
        },
        timing_tracks={},
    )


def test_chunked_intensity_matches_full_matrix_including_ramps():
    layout, sequence, fps = _layout(), _sequence(), 10
    names, full = build_leaf_intensity_matrix(layout, sequence, fps)
    pieces = []
    covered = 0
    while covered < full.shape[1]:
        chunk_names, chunk = build_leaf_intensity_matrix(
            layout, sequence, fps, frame_start=covered, frame_limit=7)
        assert chunk_names == names
        pieces.append(chunk)
        covered += chunk.shape[1]
        assert chunk.shape[1] <= 7
    stacked = np.concatenate(pieces, axis=1)
    assert stacked.shape == full.shape
    assert np.array_equal(stacked, full)
    assert full[names.index("Left"), 0] == 1
    assert full[names.index("Right"), 0] == 0
    assert 0 < full[names.index("Left"), 8] < 1


def test_house_renderer_frame_signature_lights_active_model():
    layout = _layout()
    names, matrix = build_leaf_intensity_matrix(layout, _sequence(), 10)
    renderer = HouseRenderer(layout, width=320, height=180)
    dark = np.asarray(renderer.render_frame(names, np.zeros(len(names)), "t", 0, 2000, {}).convert("RGB"))
    lit = np.asarray(renderer.render_frame(names, matrix[:, 0], "t", 0, 2000, {
        "song part": "chorus", "piano": "", "sweep": "", "drop": "",
    }).convert("RGB"))
    assert dark.shape == lit.shape == (180, 320, 3)
    assert int(np.abs(lit.astype(int) - dark.astype(int)).sum()) > 0
