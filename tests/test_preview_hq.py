from __future__ import annotations

from dataclasses import replace

from tools.preview_hq import PRESETS, Preset, even, ffmpeg_params


def test_preview_quality_presets_are_review_ready() -> None:
    assert set(PRESETS) >= {"draft", "standard", "xlights", "archival"}

    draft = PRESETS["draft"]
    xlights = PRESETS["xlights"]
    archival = PRESETS["archival"]

    assert draft.width == 1280
    assert draft.height == 720
    assert draft.fps == 15

    assert xlights.width == 1920
    assert xlights.height == 1080
    assert xlights.fps == 30
    assert xlights.crf <= draft.crf

    assert archival.width >= xlights.width
    assert archival.height >= xlights.height
    assert archival.crf <= xlights.crf


def test_even_dimension_helper_for_video_encoders() -> None:
    assert even(1) == 2
    assert even(2) == 2
    assert even(1279) == 1280
    assert even(1280) == 1280
    assert even(1281) == 1282


def test_ffmpeg_params_include_review_friendly_flags() -> None:
    params = ffmpeg_params(PRESETS["xlights"], codec="libx264", bitrate=None, faststart=True)

    assert "-crf" in params
    assert str(PRESETS["xlights"].crf) in params
    assert "-movflags" in params
    assert "+faststart" in params
    assert "-colorspace" in params
    assert "bt709" in params
    assert "-bf" in params
    assert "0" in params


def test_ffmpeg_params_prefer_bitrate_when_supplied() -> None:
    params = ffmpeg_params(
        Preset(width=1280, height=720, fps=30, crf=18, preset="fast"),
        codec="libx264",
        bitrate="6000k",
        faststart=False,
    )

    assert "-b:v" in params
    assert "6000k" in params
    assert "-crf" not in params
    assert "+faststart" not in params


def test_preset_overrides_keep_even_dimensions() -> None:
    base = PRESETS["xlights"]
    overridden = replace(base, width=even(1919), height=even(1079), fps=24)

    assert overridden.width == 1920
    assert overridden.height == 1080
    assert overridden.fps == 24
