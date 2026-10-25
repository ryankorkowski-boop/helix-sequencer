from __future__ import annotations

import hashlib
import io
import json
import math
import os
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import check_xlights_rest_sequence as rest
from tools import native_preview as preview
from tools.prepare_native_preview_benchmark import prepare_benchmark


@pytest.mark.parametrize("missing", ["xLights", "ffmpeg", "ffprobe"])
def test_missing_dependency_records_fallback_and_preserves_run(
        tmp_path, missing):
    run = tmp_path / "run"
    prepare_benchmark(run)
    manifest = run / "run_manifest.json"
    original = json.loads(manifest.read_text())
    original["quality"] = {"preserve": True}
    manifest.write_text(json.dumps(original))
    xsq = run / "benchmark.xsq"
    before = xsq.read_bytes()
    with patch.object(preview.shutil, "which", side_effect=lambda name:
                      None if name == missing else "/bin/true"):
        result = preview.preview_run(run, xsq=xsq, audio=run / "original.wav")
    saved = json.loads(manifest.read_text())
    assert result["status"] == "fallback"
    assert result["mp4"] is None
    assert result["audio_stream_verified"] is False
    assert missing in saved["warnings"][-1]
    assert saved["quality"] == original["quality"]
    assert saved["status"] == original["status"]
    assert xsq.read_bytes() == before
    assert not list(run.glob("native-preview-*"))


def test_malformed_manifest_is_not_overwritten(tmp_path):
    path = tmp_path / "run_manifest.json"
    path.write_text('{"warnings": {}}')
    with pytest.raises(ValueError, match="manifest"):
        preview.preview_run(tmp_path, xsq=tmp_path / "a.xsq",
                            audio=tmp_path / "a.wav")
    assert path.read_text() == '{"warnings": {}}'


@pytest.mark.parametrize("body", [
    b'{"version":"2026.18"}', b'{"res":503,"msg":"rejected"}'])
def test_rest_uses_http_status_without_hiding_native_rejection(body):
    response = io.BytesIO(body)
    response.status = 200
    with patch.object(rest.urllib.request, "urlopen", return_value=response):
        actual = rest._request_json("GET", "http://127.0.0.1/getVersion")
    assert actual["res"] == json.loads(body).get("res", 200)
    assert rest._response_ok(actual) == (actual["res"] == 200)


def test_busy_rest_port_does_not_launch_or_close_a_user_app(tmp_path):
    with patch.object(preview.socket, "socket") as socket_factory:
        socket_factory.return_value.__enter__.return_value.bind.side_effect = (
            OSError("port occupied"))
        with patch.object(preview.subprocess, "Popen") as process:
            with pytest.raises(OSError, match="occupied"):
                preview._native_export("xLights", tmp_path,
                                       tmp_path / "seq.xsq", 49914)
            process.assert_not_called()


def _tone(path: Path, frequency: int, duration: float = 1) -> None:
    rate = 16000
    samples = [round(10000 * math.sin(2 * math.pi * frequency * i / rate))
               for i in range(round(rate * duration))]
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(struct.pack(f"<{len(samples)}h", *samples))


@pytest.fixture
def media_tools():
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("ffmpeg/ffprobe unavailable; required in native CI")
    return ffmpeg, ffprobe


def _synthetic_video(path: Path, ffmpeg: str) -> None:
    # Mux unit fixture only. This is never reported as native xLights output.
    subprocess.run([ffmpeg, "-v", "error", "-f", "lavfi", "-i",
                    "color=c=red:s=32x32:r=20:d=1", "-f", "lavfi", "-i",
                    "sine=frequency=220:duration=1", "-c:v", "libx264",
                    "-c:a", "aac", "-shortest", str(path)], check=True)


def test_ffprobe_confirms_audio_and_native_video_packets_are_preserved(
        tmp_path, media_tools):
    ffmpeg, ffprobe = media_tools
    video, audio = tmp_path / "native.mp4", tmp_path / "original.wav"
    output = tmp_path / "muxed.mp4"
    _synthetic_video(video, ffmpeg)
    _tone(audio, 880)
    before = hashlib.sha256(audio.read_bytes()).hexdigest()
    result = preview.mux_original_audio(
        video, audio, output, duration=1, ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert {s["codec_type"] for s in result["streams"]} == {"video", "audio"}
    assert preview._stream(result, "audio")["codec_name"] == "aac"
    assert hashlib.sha256(audio.read_bytes()).hexdigest() == before

    def packets(path):
        return subprocess.check_output([
            ffmpeg, "-v", "error", "-i", str(path), "-map", "0:v:0",
            "-c:v", "copy", "-f", "h264", "-"])
    assert packets(video) == packets(output)
    pcm = subprocess.check_output([
        ffmpeg, "-v", "error", "-i", str(output), "-map", "0:a:0",
        "-ar", "16000", "-ac", "1", "-f", "s16le", "-"])
    values = struct.unpack(f"<{len(pcm) // 2}h", pcm)
    assert len(values) >= 15500
    # Confirm the selected original (880 Hz), not the old video's 220 Hz audio.

    def amplitude(frequency):
        return abs(sum(value * complex(
            math.cos(2 * math.pi * frequency * i / 16000),
            math.sin(2 * math.pi * frequency * i / 16000))
                       for i, value in enumerate(values[2000:12000])))
    assert amplitude(880) > 10 * amplitude(220)


def test_short_audio_and_existing_output_are_not_silently_accepted(
        tmp_path, media_tools):
    ffmpeg, ffprobe = media_tools
    video, audio = tmp_path / "video.mp4", tmp_path / "audio.wav"
    output = tmp_path / "preview.mp4"
    _synthetic_video(video, ffmpeg)
    _tone(audio, 880, .2)
    with pytest.raises(ValueError, match="shorter"):
        preview.mux_original_audio(video, audio, output, duration=1,
                                   ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert not output.exists()
    output.write_bytes(b"preserve existing output")
    with pytest.raises(ValueError, match="overwrite"):
        preview.mux_original_audio(video, audio, output, duration=1,
                                   ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert output.read_bytes() == b"preserve existing output"


def test_interrupted_mux_never_exposes_partial_destination(tmp_path, media_tools):
    ffmpeg, ffprobe = media_tools
    video, audio = tmp_path / 'native.mp4', tmp_path / 'original.wav'
    output = tmp_path / 'muxed.mp4'
    _synthetic_video(video, ffmpeg)
    _tone(audio, 880)
    run = preview._run

    def interrupt(command, timeout):
        if '-movflags' in command:
            assert not output.exists()
            Path(command[-1]).write_bytes(b'incomplete container')
            assert not output.exists()
            raise RuntimeError('interrupted encoder')
        return run(command, timeout)

    with patch.object(preview, '_run', side_effect=interrupt):
        with pytest.raises(RuntimeError, match='interrupted encoder'):
            preview.mux_original_audio(video, audio, output, duration=1,
                                       ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert not output.exists()
    assert not list(tmp_path.glob('.native-mux-*'))
    assert video.is_file() and audio.is_file()


def test_mux_rechecks_closed_container_after_decode(tmp_path, media_tools):
    ffmpeg, ffprobe = media_tools
    video, audio = tmp_path / 'native.mp4', tmp_path / 'original.wav'
    output = tmp_path / 'muxed.mp4'
    _synthetic_video(video, ffmpeg)
    _tone(audio, 880)
    run = preview._run

    def corrupt_after_decode(command, timeout):
        result = run(command, timeout)
        if command[0] == ffmpeg and command[-2:] == ['null', '-']:
            Path(command[command.index('-i') + 1]).write_bytes(b'broken after decode')
        return result

    with patch.object(preview, '_run', side_effect=corrupt_after_decode):
        with pytest.raises(RuntimeError, match='ffprobe failed'):
            preview.mux_original_audio(video, audio, output, duration=1,
                                       ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert not output.exists()
    assert not list(tmp_path.glob('.native-mux-*'))


def test_mux_does_not_replace_destination_created_during_export(tmp_path, media_tools):
    ffmpeg, ffprobe = media_tools
    video, audio = tmp_path / 'native.mp4', tmp_path / 'original.wav'
    output = tmp_path / 'muxed.mp4'
    _synthetic_video(video, ffmpeg)
    _tone(audio, 880)
    run = preview._run

    def destination_appears(command, timeout):
        result = run(command, timeout)
        if '-movflags' in command:
            output.write_bytes(b'another writer owns this destination')
        return result

    with patch.object(preview, '_run', side_effect=destination_appears):
        with pytest.raises(FileExistsError):
            preview.mux_original_audio(video, audio, output, duration=1,
                                       ffmpeg=ffmpeg, ffprobe=ffprobe)
    assert output.read_bytes() == b'another writer owns this destination'
    assert not list(tmp_path.glob('.native-mux-*'))


def test_native_benchmark_artifact_streams_and_timeline(media_tools):
    raw = os.environ.get("HELIX_NATIVE_PREVIEW_MANIFEST")
    if not raw:
        pytest.skip("Set HELIX_NATIVE_PREVIEW_MANIFEST after native export")
    ffmpeg, ffprobe = media_tools
    manifest = Path(raw)
    report = json.loads(manifest.read_text())["native_preview"]
    assert report["status"] == "success"
    assert report["backend"] == "xlights_house_preview"
    assert report["audio_stream_verified"] is True
    assert not report["warnings"]
    video = Path(report["mp4"])
    assert (hashlib.sha256(video.read_bytes()).hexdigest()
            == report["mp4_sha256"])
    streams = preview.probe_media(video, ffprobe)["streams"]
    assert {s["codec_type"] for s in streams} == {"audio", "video"}
    for stream in streams:
        assert abs(float(stream["duration"]) - 4) < .1
        assert abs(float(stream["start_time"])) < .03
    channels = json.loads((Path(report["evidence_dir"])
                           / "native_channels.json").read_text())
    assert (channels["channels"], channels["frames"]) == (4, 80)
    assert channels["nonzero_samples"] == 78
    # Native visual samples must agree with native FSEQ effect windows.
    for second, lit in ((.1, True), (1.1, True), (2.1, False),
                        (2.6, True), (3.1, False)):
        pixels = subprocess.check_output([
            ffmpeg, "-v", "error", "-ss", str(second), "-i", str(video),
            "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
        assert pixels
        assert (max(pixels) > 50) is lit
    pcm = subprocess.check_output([
        ffmpeg, "-v", "error", "-i", str(video), "-map", "0:a:0",
        "-ar", "16000", "-ac", "1", "-f", "s16le", "-"])
    values = struct.unpack(f"<{len(pcm) // 2}h", pcm)
    for onset in (0, 1, 2.5):
        signal = values[round((onset + .04) * 16000):
                        round((onset + .11) * 16000)]
        assert max(abs(v) for v in signal) > 2000
    assert max(abs(v) for v in values[32000:36000]) < 100
