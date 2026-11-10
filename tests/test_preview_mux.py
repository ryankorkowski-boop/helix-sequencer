from __future__ import annotations

import json
import subprocess
from pathlib import Path
import pytest

from tools import preview_hq as phq


class DummyProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_mux_success_first_attempt(tmp_path, monkeypatch):
    silent = tmp_path / "in.silent.mp4"
    out = tmp_path / "out.mp4"
    audio = tmp_path / "a.mp3"
    # create dummy files
    silent.write_bytes(b"0")
    audio.write_bytes(b"1")

    ffprobe_path = "/usr/bin/ffprobe"
    ffmpeg_path = "/usr/bin/ffmpeg"

    # monkeypatch ffmpeg and ffprobe lookup
    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffmpeg_exe", lambda: ffmpeg_path)
    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffprobe_exe", lambda: ffprobe_path)

    # First run: ffmpeg returns 0 and writes an output file and ffprobe returns json with streams/duration
    def fake_run_first(cmd, stdout, stderr, text=True, check=False):
        # emulate ffmpeg creating out file
        out.write_bytes(b"out")
        return DummyProc(returncode=0, stdout="", stderr="")

    def fake_run_probe(cmd, stdout, stderr, text=True, check=False):
        info = {"streams": [{"codec_type": "video"}, {"codec_type": "audio"}], "format": {"duration": "1.23"}}
        return DummyProc(returncode=0, stdout=json.dumps(info), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run_first)
    # ensure ffprobe called during validation uses our probe
    monkeypatch.setattr(phq.subprocess, "run", lambda *a, **k: fake_run_probe(*a, **k) if "ffprobe" in a[0][0] else fake_run_first(*a, **k))

    # Run mux — should not raise
    phq._mux_audio_video(silent, audio, out, faststart=False)
    assert not silent.exists()
    assert out.exists()


def test_mux_fallback_then_success(tmp_path, monkeypatch):
    silent = tmp_path / "in.silent.mp4"
    out = tmp_path / "out.mp4"
    audio = tmp_path / "a.mp3"
    silent.write_bytes(b"0")
    audio.write_bytes(b"1")

    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffprobe_exe", lambda: "/usr/bin/ffprobe")

    calls = {"first": False, "probe": False}

    def fake_run(cmd, stdout, stderr, text=True, check=False):
        s = " ".join(cmd)
        if "-fflags" in s:
            # fallback attempt: write out file and return success
            out.write_bytes(b"out2")
            calls["first"] = True
            return DummyProc(returncode=0, stdout="", stderr="fallback ok")
        if "-show_format" in s:
            calls["probe"] = True
            info = {"streams": [{"codec_type": "video"}, {"codec_type": "audio"}], "format": {"duration": "2.0"}}
            return DummyProc(returncode=0, stdout=json.dumps(info), stderr="")
        # initial ffmpeg attempt: fail
        return DummyProc(returncode=1, stdout="", stderr="initial failed")

    monkeypatch.setattr(phq.subprocess, "run", fake_run)

    phq._mux_audio_video(silent, audio, out, faststart=True)
    assert not silent.exists()
    assert out.exists()
    assert calls["first"] and calls["probe"]


def test_mux_both_fail_preserve_silent(tmp_path, monkeypatch):
    silent = tmp_path / "in.silent.mp4"
    out = tmp_path / "out.mp4"
    audio = tmp_path / "a.mp3"
    silent.write_bytes(b"0")
    audio.write_bytes(b"1")

    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr(phq.pr.imageio_ffmpeg, "get_ffprobe_exe", lambda: "/usr/bin/ffprobe")

    def fake_run_fail(cmd, stdout, stderr, text=True, check=False):
        s = " ".join(cmd)
        if "-show_format" in s:
            return DummyProc(returncode=0, stdout=json.dumps({"streams": []}), stderr="no streams")
        return DummyProc(returncode=1, stdout="", stderr="error")

    monkeypatch.setattr(phq.subprocess, "run", fake_run_fail)

    with pytest.raises(RuntimeError):
        phq._mux_audio_video(silent, audio, out, faststart=False)
    assert silent.exists()
    assert not out.exists()
