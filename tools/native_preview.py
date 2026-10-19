"""Native xLights headless FSEQ -> House Preview -> original-audio MP4.

Explicit post-run operation; never changes sequencing or enables light output.
The caller supplies a prepared show folder with its referenced assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from tools import check_xlights_rest_sequence as rest
from tools.quality.native import inspect_fseq


def _run(command: list[str], timeout: float) -> str:
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed: "
                           f"{result.stderr[-2000:]}")
    return result.stdout


def probe_media(path: Path, ffprobe: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(_run([
        ffprobe, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path)], 30))
    if (not isinstance(value, dict)
            or not isinstance(value.get("streams"), list)):
        raise ValueError("ffprobe did not return media streams")
    return value


def _stream(probe: dict[str, Any], kind: str) -> dict[str, Any]:
    streams = [s for s in probe["streams"] if s.get("codec_type") == kind
               and not s.get("disposition", {}).get("attached_pic")]
    if not streams:
        raise ValueError(f"Missing {kind} stream")
    stream: dict[str, Any] = streams[0]
    return stream


def _duration(stream: dict[str, Any]) -> float:
    duration = float(stream["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Missing or invalid stream duration")
    return duration


def mux_original_audio(video: Path, audio: Path, output: Path, *,
                       duration: float, ffmpeg: str,
                       ffprobe: str) -> dict[str, Any]:
    """Copy native video packets, mux original audio, verify both streams."""
    if output.exists():
        raise ValueError(f"Refusing to overwrite output: {output}")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Expected duration must be positive and finite")
    native = _stream(probe_media(video, ffprobe), "video")
    source = _stream(probe_media(audio, ffprobe), "audio")
    if abs(_duration(native) - duration) > .1:
        raise ValueError("Native video duration differs from sequence")
    if abs(float(native.get("start_time", 0))) > .03:
        raise ValueError("Native video does not start at timeline zero")
    if _duration(source) < duration - .03:
        raise ValueError("Original audio is shorter than the sequence")
    if abs(float(source.get("start_time", 0))) > .03:
        raise ValueError("Original audio does not start at timeline zero")
    try:
        _run([ffmpeg, "-v", "error", "-nostdin", "-n", "-i", str(video),
              "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
              "-c:v", "copy", "-c:a", "aac", "-t", str(duration),
              "-movflags", "+faststart", str(output)], max(60, duration * 2))
        probe = probe_media(output, ffprobe)
        for kind in ("video", "audio"):
            stream = _stream(probe, kind)
            if abs(_duration(stream) - duration) > .1:
                raise ValueError(f"Muxed {kind} duration mismatch")
            if abs(float(stream.get("start_time", 0))) > .03:
                raise ValueError(f"Muxed {kind} start-time mismatch")
        # Decode both streams too: a stream header alone is insufficient.
        _run([ffmpeg, "-v", "error", "-nostdin", "-i", str(output),
              "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"],
             max(60, duration * 2))
        return probe
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        output.unlink(missing_ok=True)
        raise


def _command(endpoint: str, cmd: str, **params: str) -> dict[str, Any]:
    response = rest._request_json(
        "POST", f"{endpoint}/xlDoAutomation", {"cmd": cmd, **params},
        timeout=60)
    if not rest._response_ok(response):
        raise RuntimeError(f"xLights {cmd} rejected: {response}")
    return response


def _export_size() -> tuple[int, int]:
    """Always request the same native dimensions enforced by acceptance."""
    size = tuple(int(os.environ.get("HELIX_NATIVE_PREVIEW_" + key, default))
                 for key, default in (("WIDTH", "1920"), ("HEIGHT", "1080")))
    if any(pixels < 320 or pixels > 4096 or pixels % 2 for pixels in size):
        raise ValueError("Native export dimensions must be even pixels in 320..4096")
    return size


def _resize_native_canvas(staged: Path, actual: tuple[int, int],
                          desired: tuple[int, int]) -> dict[str, Any]:
    """Resize only a uniquely identified canvas in our fresh sequence window.

    wxGTK's getWidth/getHeight are cached by its size event. Maximizing the
    top-level frame does not resize a docked House Preview. Prime that real
    X11 child and let its resize event run before requesting another export.
    Never infer HD success from X11 geometry; ffprobe remains authoritative.
    """
    for utility in ("wmctrl", "xwininfo", "xdotool"):
        if not shutil.which(utility):
            raise RuntimeError("Native canvas resize needs " + utility)
    clients = _run(["wmctrl", "-lp"], 5)
    owners = []
    for line in clients.splitlines():
        fields = line.split(None, 4)
        if len(fields) == 5 and str(staged) in fields[4]:
            if re.fullmatch(r"0x[0-9a-fA-F]+", fields[0]):
                owners.append(fields[0])
    if len(owners) != 1:
        raise ValueError("Cannot uniquely identify this native sequence's X11 window")
    tree = _run(["xwininfo", "-id", owners[0], "-tree"], 5)
    matches = []
    for line in tree.splitlines():
        entry = re.match(r"^(\s+)(0x[0-9a-fA-F]+)\s.*?\s(\d+)x(\d+)[+-]", line)
        if entry and entry[2] != owners[0] and (int(entry[3]), int(entry[4])) == actual:
            matches.append((len(entry[1]), entry[2]))
    # X11 can include a same-sized container and its child; use the deepest
    # unique match. Ambiguous sibling canvases must never be guessed.
    if not matches:
        raise ValueError("No native X11 canvas matches the exported dimensions")
    deepest = max(depth for depth, _ in matches)
    candidates = [window for depth, window in matches if depth == deepest]
    if len(candidates) != 1:
        raise ValueError("Ambiguous native X11 canvases; refusing to resize")
    window = candidates[0]
    _run(["xdotool", "windowsize", "--sync", window,
          str(desired[0]), str(desired[1])], 5)
    time.sleep(1)  # Allow wxGTK to consume the actual ConfigureNotify event.
    geometry = _run(["xwininfo", "-id", window], 5)
    width = re.search(r"\bWidth:\s*(\d+)", geometry)
    height = re.search(r"\bHeight:\s*(\d+)", geometry)
    if not width or not height or (int(width[1]), int(height[1])) != desired:
        raise ValueError("Native canvas did not retain the requested X11 size")
    return {"window": window, "original_resolution": list(actual),
            "requested_resolution": list(desired), "geometry": geometry}


def _native_export(xlights: str, show: Path, staged: Path,
                   port: int) -> dict[str, Any]:
    # Own a fresh process. Never close/switch an existing user's sequence.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", port))
    endpoint = f"http://127.0.0.1:{port}"
    with (staged.parent / "native_gui.log").open("w") as log:
        app = subprocess.Popen([xlights, "--quiet", "-a" if port == 49913
                                else "-b", "--show", str(show)],
                               stdout=log, stderr=log)
        try:
            # Cold AppImage startup under software GL/Xvfb can exceed 30s.
            # Allow a bounded startup window without relaxing output QA.
            deadline = time.monotonic() + 120
            while True:
                if app.poll() is not None:
                    raise RuntimeError(f"xLights exited {app.returncode}")
                try:
                    version = rest._request_json(
                        "GET", f"{endpoint}/getVersion", timeout=1)
                    if not rest._response_ok(version):
                        raise ValueError("xLights version request rejected")
                    break
                except (OSError, ValueError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("xLights REST startup timed out")
                    time.sleep(.1)
            folder = _command(endpoint, "getShowFolder")
            if Path(folder.get("folder", "")).resolve() != show:
                raise ValueError("xLights opened an unexpected show folder")
            opened = _command(endpoint, "openSequence", seq=str(staged),
                              promptIssues="false")
            if Path(opened.get("fullseq", "")).resolve() != staged:
                raise ValueError("xLights opened an unexpected sequence")
            video = staged.parent / "native-silent.mp4"
            width, height = _export_size()
            options: dict[str, str] = {"filename": str(video),
                                       "width": str(width), "height": str(height)}
            # Some xLights 2026.18 builds ignore exportVideoPreview width/height
            # and capture the docked preview at its on-screen dimensions.
            # Maximize the real GUI window before exporting, without rescaling
            # any encoded frames after export. This requires wmctrl on Linux.
            if shutil.which("wmctrl"):
                # A headless X11 session may expose no matching titled window.
                # Window maximization is best effort, never a prerequisite for
                # the native REST export or the strict ffprobe resolution gate.
                maximize = subprocess.run(
                    ["wmctrl", "-r", "xLights", "-b",
                     "add,maximized_vert,maximized_horz"],
                    capture_output=True, text=True, check=False, timeout=5)
                if maximize.returncode == 0:
                    time.sleep(2)
            # Preserve actual X11 geometry for diagnosing docked-preview exports.
            # Never upscale or claim that window size proves native resolution.
            with (staged.parent / "native_window_geometry.txt").open("w") as evidence:
                evidence.write("requested_options=" + repr(options) + "\n")
                for utility, args in (("wmctrl", ["-lG"]), ("xrandr", ["--current"]), ("xwininfo", ["-root", "-tree"])):
                    binary = shutil.which(utility)
                    if not binary:
                        evidence.write(utility + ": unavailable\n")
                        continue
                    try:
                        result = subprocess.run([binary, *args], capture_output=True,
                                                text=True, timeout=10, check=False)
                        evidence.write(utility + " exit=" + str(result.returncode) + "\n")
                        evidence.write(result.stdout[-12000:] + result.stderr[-2000:] + "\n")
                    except (OSError, subprocess.SubprocessError) as exc:
                        evidence.write(utility + ": " + str(exc) + "\n")
            # Emit the window-tree evidence into Actions logs as well as the
            # artifact. The export may fail acceptance before anyone downloads
            # its diagnostics, and the GUI preview size is the current blocker.
            geometry_report = staged.parent / "native_window_geometry.txt"
            if geometry_report.is_file():
                print("HELIX_NATIVE_X11_GEOMETRY_BEGIN", flush=True)
                print(geometry_report.read_text()[-16000:], flush=True)
                print("HELIX_NATIVE_X11_GEOMETRY_END", flush=True)
            _command(endpoint, "exportVideoPreview", **options)
            if not video.is_file() or video.stat().st_size == 0:
                raise ValueError("xLights did not create a fresh native video")
            native_stream = _stream(probe_media(video, "ffprobe"), "video")
            actual = (int(native_stream["width"]), int(native_stream["height"]))
            attempts = [{"video": str(video), "resolution": list(actual)}]
            if actual != (width, height) and os.environ.get("DISPLAY"):
                resize = _resize_native_canvas(staged, actual, (width, height))
                (staged.parent / "native_canvas_resize.json").write_text(
                    json.dumps(resize, indent=2) + "\n")
                print("HELIX_NATIVE_CANVAS_RESIZE " + json.dumps(resize), flush=True)
                # Keep the rejected first export as diagnostic evidence, and
                # ask xLights for an entirely new video from the real canvas.
                video = staged.parent / "native-resized.mp4"
                _command(endpoint, "exportVideoPreview", **{**options, "filename": str(video)})
                native_stream = _stream(probe_media(video, "ffprobe"), "video")
                attempts.append({"video": str(video), "resolution": [
                    int(native_stream["width"]), int(native_stream["height"])]})
            return {"xlights_version": rest._version_from_response(version),
                    "open_response": opened, "native_video": str(video),
                    "native_export_attempts": attempts}
        finally:
            if app.poll() is None:
                app.terminate()
                try:
                    app.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    app.kill()
                    app.wait(timeout=5)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_manifest(path: Path, report: dict[str, Any]) -> None:
    manifest = json.loads(path.read_text())
    if not isinstance(manifest, dict):
        raise ValueError("Run manifest must be an object")
    manifest["native_preview"] = report
    warnings = manifest.setdefault("warnings", [])
    if not isinstance(warnings, list):
        raise ValueError("Run manifest warnings must be a list")
    for warning in report["warnings"]:
        message = f"native_preview: {warning}"
        if message not in warnings:
            warnings.append(message)
    fd, raw = tempfile.mkstemp(prefix=".native-preview-", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def preview_run(run_dir: Path, *, xsq: Path, audio: Path,
                xlights: str = "xLights", port: int = 49914) -> dict[str, Any]:
    """Keep XSQ usable and record fallback when preview is unavailable."""
    run_dir = run_dir.resolve()
    xsq, audio = xsq.resolve(), audio.resolve()
    manifest = run_dir / "run_manifest.json"
    # Validate before external work; never replace a malformed manifest.
    current = json.loads(manifest.read_text())
    if not isinstance(current, dict) or not isinstance(
            current.get("warnings", []), list):
        raise ValueError("Invalid run manifest object/warnings")
    report: dict[str, Any] = {
        "schema": "helix.native_preview.v1",
        "backend": "xlights_house_preview",
        "status": "fallback", "warnings": [], "mp4": None,
        "audio_stream_verified": False, "audio_offset_ms": 0,
        "visual_review_status": "not_reviewed",
        "controller_channel_safety": "not_tested",
    }
    try:
        if port not in (49913, 49914):
            raise ValueError("xLights automation port must be 49913 or 49914")
        binaries = {name: shutil.which(value) for name, value in (
            ("xLights", xlights), ("ffmpeg", "ffmpeg"),
            ("ffprobe", "ffprobe"))}
        missing = [name for name, value in binaries.items() if not value]
        if missing:
            raise ValueError("Missing dependencies: " + ", ".join(missing))
        native_bin, ffmpeg, ffprobe = (
            str(binaries[name]) for name in ("xLights", "ffmpeg", "ffprobe"))
        layout = run_dir / "xlights_rgbeffects.xml"
        for source in (xsq, audio, layout):
            if not source.is_file():
                raise ValueError(f"Missing input: {source}")
        root = ET.parse(xsq).getroot()
        duration = float(root.findtext("head/sequenceDuration", "0"))
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("XSQ must declare its positive duration")
        stage = Path(tempfile.mkdtemp(prefix="native-preview-", dir=run_dir))
        staged = stage / xsq.name
        # Preserve source; media resolution remains under the original show.
        # Mux chosen original audio explicitly below, once at time zero.
        shutil.copyfile(xsq, staged)
        report.update({"evidence_dir": str(stage),
                       "duration_seconds": duration,
                       "xsq_sha256": _sha256(xsq),
                       "layout_sha256": _sha256(layout),
                       "audio_sha256": _sha256(audio),
                       "audio_source": str(audio)})
        with (stage / "native_headless.log").open("w") as log:
            result = subprocess.run(
                [native_bin, "--headless", "--quiet", "--show", str(run_dir),
                 "--outputdir", str(stage), str(staged)],
                stdout=log, stderr=log, timeout=max(60, duration * 3),
                check=False)
        if result.returncode:
            raise RuntimeError(
                f"Native headless render exited {result.returncode}")
        fseq = staged.with_suffix(".fseq")
        channel_report = inspect_fseq(fseq)
        if abs(channel_report["duration_ms"] - duration * 1000) > 100:
            raise ValueError("Native FSEQ duration differs from sequence")
        (stage / "native_channels.json").write_text(
            json.dumps(channel_report, indent=2, sort_keys=True) + "\n")
        report["native_fseq_sha256"] = _sha256(fseq)
        report.update(_native_export(native_bin, run_dir, staged, port))
        # Reject xLights docked-preview exports before muxing or reporting success.
        expected_width, expected_height = _export_size()
        native_stream = _stream(probe_media(Path(report["native_video"]), ffprobe), "video")
        actual_size = (int(native_stream["width"]), int(native_stream["height"]))
        expected_size = (expected_width, expected_height)
        report["requested_resolution"] = list(expected_size)
        report["native_export_resolution"] = list(actual_size)
        if actual_size != expected_size:
            raise ValueError(
                f"xLights native export resolution {actual_size[0]}x{actual_size[1]} "
                f"does not match required {expected_width}x{expected_height}; "
                "the docked House Preview may have been exported. "
                "Configure genuine full-size native export; do not upscale GUI capture."
            )
        output = stage / "preview.mp4"
        report["ffprobe"] = mux_original_audio(
            Path(report["native_video"]), audio, output, duration=duration,
            ffmpeg=ffmpeg, ffprobe=ffprobe)
        report.update(status="success", mp4=str(output),
                      audio_stream_verified=True, mp4_sha256=_sha256(output))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            ET.ParseError, subprocess.SubprocessError) as exc:
        report["warnings"].append(
            f"Native audio preview unavailable; retain XSQ for xLights: {exc}")
    _save_manifest(manifest, report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--xsq", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--xlights", default="xLights")
    parser.add_argument("--port", type=int, choices=(49913, 49914),
                        default=49914)
    args = parser.parse_args(argv)
    report = preview_run(args.run_dir, xsq=args.xsq, audio=args.audio,
                         xlights=args.xlights, port=args.port)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())

