import numpy as np
import pytest

from core.native_rgb_quality import evaluate_rgb_frames


def test_colorful_changing_frames_pass():
    frames = []
    for i in range(12):
        f = np.zeros((32, 64, 3), dtype=np.uint8)
        f[:, (i * 4) % 48:(i * 4) % 48 + 12, i % 3] = 255
        frames.append(f)
    report = evaluate_rgb_frames(frames)
    assert report["passed"]
    assert report["sampled_frames"] == 12


def test_white_flash_regression_rejected():
    report = evaluate_rgb_frames([np.full((16, 16, 3), 255, np.uint8) for _ in range(6)])
    assert "white_dominant_frames" in report["failures"]


def test_blank_and_frozen_regressions_rejected():
    black = np.zeros((16, 16, 3), np.uint8)
    report = evaluate_rgb_frames([black] * 8)
    assert "excess_blank_frames" in report["failures"]
    assert "frozen_or_repeated_frames" in report["failures"]


def test_invalid_frames_rejected():
    with pytest.raises(ValueError):
        evaluate_rgb_frames([])
    with pytest.raises(ValueError):
        evaluate_rgb_frames([np.zeros((8, 8), np.uint8)])


def test_sparse_all_white_lighting_is_not_hidden_by_dark_yard():
    frames = []
    for i in range(12):
        f = np.zeros((96, 160, 3), dtype=np.uint8)
        f[10:20, 10+i*8:20+i*8] = 255
        frames.append(f)
    report = evaluate_rgb_frames(frames)
    assert report["white_dominant_frame_fraction"] == 1.0
    assert "white_dominant_frames" in report["failures"]


def test_sparse_colored_lighting_with_white_accents_is_not_white_dominant():
    frames = []
    for i in range(12):
        f = np.zeros((96, 160, 3), dtype=np.uint8)
        f[10:20, 10+i*8:20+i*8, 0] = 255
        f[10:12, 10+i*8:20+i*8] = 255
        frames.append(f)
    report = evaluate_rgb_frames(frames)
    assert report["white_dominant_frame_fraction"] == 0.0
    assert "white_dominant_frames" not in report["failures"]
