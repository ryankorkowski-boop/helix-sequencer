"""Integration checks for truthful 30-second band-preview audio."""
from __future__ import annotations

import re
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import pytest

from tools.run_helixville4_full_band_lightsouttheme_30s import _trim_audio_to_30s


def _silent_wav(path: Path, seconds: int = 35) -> None:
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(8000)
        # Write chunks to bound memory rather than allocating a whole long song.
        for _ in range(seconds):
            writer.writeframes(b"\x00\x00" * 8000)


def _duration(path: Path) -> float:
    probe = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path)],
        capture_output=True, text=True, check=False,
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    assert match, probe.stderr
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def test_trim_real_audio_is_bounded_and_named_for_source(tmp_path: Path) -> None:
    audio = tmp_path / "Real source song.wav"
    _silent_wav(audio)
    clip = _trim_audio_to_30s(audio, tmp_path / "clips")
    assert clip.name == "Real source song_30s.mp3"
    assert clip.is_file() and clip.stat().st_size > 0
    assert clip.read_bytes()[:12] != audio.read_bytes()[:12]
    assert 29.5 <= _duration(clip) <= 30.5


def test_missing_audio_never_creates_fake_clip(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _trim_audio_to_30s(tmp_path / "missing.mp3", tmp_path / "clips")
    assert not (tmp_path / "clips").exists()


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    target = _trim_audio_to_30s(tmp_path / "preview.mp3", tmp_path / "clips", dry_run=True)
    assert target.name == "preview_30s.mp3"
    assert not target.exists()
