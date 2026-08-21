from __future__ import annotations
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import preview_renderer as pr  # noqa: E402

@dataclass(frozen=True)
class Preset:
    width: int
    height: int
    fps: int
    crf: int
    preset: str

PRESETS = {
    "draft": Preset(1280, 720, 15, 23, "veryfast"),
    "standard": Preset(1280, 720, 30, 20, "fast"),
    "xlights": Preset(1920, 1080, 30, 18, "fast"),
    "archival": Preset(2560, 1440, 30, 16, "medium"),
}

def even(n: int) -> int:
    n = max(2, int(n))
    return n + (n % 2)

def ffmpeg_params(p: Preset, codec: str, bitrate: str | None, faststart: bool) -> list[str]:
    args = ["-preset", p.preset]
    args += ["-b:v", bitrate] if bitrate else ["-crf", str(p.crf)]
    args += ["-g", "40", "-bf", "0"]
    args += ["-color_range", "pc", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    if faststart:
        args += ["-movflags", "+faststart"]
    return args

def audio_reactive_envelope(audio: Path, frame_count: int, fps: int):
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(str(audio), sr=22050, mono=True)
        if y.size == 0:
            return np.ones(frame_count, dtype=np.float32)
        hop = 512
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop, center=True)[0]
        onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        rms_t = librosa.times_like(rms, sr=sr, hop_length=hop)
        onset_t = librosa.times_like(onset, sr=sr, hop_length=hop)
        frame_t = np.arange(frame_count, dtype=np.float32) / float(fps)
        def normalize(values):
            values = np.asarray(values, dtype=np.float32)
            lo, hi = np.percentile(values, [10, 95])
            if hi <= lo + 1e-8:
                return np.zeros_like(values)
            return np.clip((values - lo) / (hi - lo), 0.0, 1.0)
        rms_n = normalize(np.interp(frame_t, rms_t, rms, left=rms[0], right=rms[-1]))
        onset_n = normalize(np.interp(frame_t, onset_t, onset, left=onset[0], right=onset[-1]))
        gain = 0.45 + 0.75 * rms_n + 0.65 * onset_n
        return np.clip(gain, 0.35, 1.8).astype(np.float32)
    except Exception as exc:
        print(f"Audio-reactive modulation unavailable: {exc}; using neutral gain.", flush=True)
        return __import__("numpy").ones(frame_count, dtype=__import__("numpy").float32)

def _run_ffmpeg(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "ffmpeg returned a non-zero exit code").strip()
        print(f"FFmpeg failed ({proc.returncode}):\n{detail}", file=sys.stderr, flush=True)
    return proc

def _validate_mp4(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"MP4 validation failed: missing or empty file: {path}")
    ffmpeg = pr.imageio_ffmpeg.get_ffmpeg_exe()
    # FFmpeg itself can probe the container without requiring a separate ffprobe binary.
    cmd = [ffmpeg, "-v", "error", "-i", str(path), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"]
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "ffmpeg validation failed").strip()
        raise RuntimeError(f"FFmpeg validation failed for {path}: {detail}")
    probe = [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"]
    probe_proc = subprocess.run(probe, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if probe_proc.returncode != 0:
        detail = (probe_proc.stderr or probe_proc.stdout or "ffmpeg probe failed").strip()
        raise RuntimeError(f"FFmpeg probe failed for {path}: {detail}")

def _mux_audio_video(silent_path: Path, audio_path: Path, out_path: Path, faststart: bool) -> Path:
    if not silent_path.exists():
        raise RuntimeError(f"Silent render does not exist: {silent_path}")
    out_path.unlink(missing_ok=True)
    ffmpeg = pr.imageio_ffmpeg.get_ffmpeg_exe()
    attempts = []
    base = [ffmpeg, "-y", "-i", str(silent_path), "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest"]
    if faststart:
        base += ["-movflags", "+faststart"]
    base += [str(out_path)]
    attempts.append(("standard", base))
    fallback = [ffmpeg, "-y", "-fflags", "+genpts", "-i", str(silent_path), "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-avoid_negative_ts", "make_zero"]
    if faststart:
        fallback += ["-movflags", "+faststart"]
    fallback += [str(out_path)]
    attempts.append(("timestamp-normalized fallback", fallback))
    errors: list[str] = []
    for label, cmd in attempts:
        print(f"Mux attempt: {label}", flush=True)
        out_path.unlink(missing_ok=True)
        proc = _run_ffmpeg(cmd)
        if proc.returncode != 0:
            errors.append(f"{label}: exit {proc.returncode}")
            continue
        try:
            _validate_mp4(out_path)
        except Exception as exc:
            errors.append(f"{label}: validation failed: {exc}")
            out_path.unlink(missing_ok=True)
            continue
        silent_path.unlink(missing_ok=True)
        print(f"✓ Valid MP4: {out_path} ({out_path.stat().st_size} bytes)", flush=True)
        return out_path
    raise RuntimeError(f"All MP4 mux attempts failed: {'; '.join(errors)}")

def render_one(seq_path: Path, layout: pr.LayoutData, audio: Path | None, p: Preset, codec: str, bitrate: str | None, faststart: bool, audio_reactive: bool) -> Path:
    seq = pr.parse_sequence(seq_path)
    leaf_names, intensity = pr.build_leaf_intensity_matrix(layout, seq, p.fps)
    tracks = {"song part": pr.choose_track(seq, "song parts"), "piano": pr.choose_track(seq, "piano"), "sweep": pr.choose_track(seq, "sweeps"), "drop": pr.choose_track(seq, "drops")}
    renderer = pr.HouseRenderer(layout, width=p.width, height=p.height)
    out_path = seq_path.with_suffix(".mp4")
    temp_path = out_path.with_suffix(".silent.mp4")
    audio_gain = audio_reactive_envelope(audio, intensity.shape[1], p.fps) if audio_reactive and audio and audio.exists() else None
    writer = pr.imageio.get_writer(temp_path, fps=p.fps, codec=codec, ffmpeg_log_level="error", pixelformat="yuv420p", macro_block_size=None, output_params=ffmpeg_params(p, codec, bitrate, faststart))
    try:
        for frame_idx in range(intensity.shape[1]):
            t_ms = int(round(frame_idx * 1000.0 / p.fps))
            frame_values = intensity[:, frame_idx]
            if audio_gain is not None:
                frame_values = frame_values * float(audio_gain[frame_idx])
            frame = renderer.render_frame(leaf_names=leaf_names, frame_values=frame_values, title=seq_path.name, t_ms=t_ms, duration_ms=seq.duration_ms, overlays={k: pr.active_label(v, t_ms) for k, v in tracks.items()})
            writer.append_data(pr.np.asarray(frame.convert("RGB"), dtype=pr.np.uint8))
    finally:
        writer.close()
    if audio and audio.exists():
        return _mux_audio_video(temp_path, audio, out_path, faststart)
    temp_path.replace(out_path)
    _validate_mp4(out_path)
    return out_path

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render higher-quality Helix preview MP4s.")
    parser.add_argument("xsq", nargs="*")
    parser.add_argument("--layout", default=pr.DEFAULT_LAYOUT)
    parser.add_argument("--audio", default="13.wav")
    parser.add_argument("--quality-preset", choices=PRESETS, default="xlights")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=int)
    parser.add_argument("--codec", default="libx264")
    parser.add_argument("--video-bitrate")
    parser.add_argument("--no-faststart", action="store_true")
    parser.add_argument("--audio-reactive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--validate-quality-presets", action="store_true")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    if args.validate_quality_presets:
        for name, p in PRESETS.items():
            print(f"{name}: {p.width}x{p.height} {p.fps}fps crf={p.crf} preset={p.preset}")
        return 0
    base = PRESETS[args.quality_preset]
    p = replace(base, width=even(args.width or base.width), height=even(args.height or base.height), fps=args.fps or base.fps)
    layout_path = (ROOT / args.layout).resolve() if not Path(args.layout).is_absolute() else Path(args.layout)
    audio = (ROOT / args.audio).resolve() if args.audio else None
    targets = [(ROOT / x).resolve() if not Path(x).is_absolute() else Path(x) for x in args.xsq] or pr.default_targets(ROOT)
    if not targets:
        raise RuntimeError("No XSQ files found to render.")
    layout = pr.parse_models(layout_path)
    print(f"HQ preview encode: {p.width}x{p.height} {p.fps}fps codec={args.codec} crf={p.crf} preset={p.preset}")
    print(f"Audio-reactive preview: {'enabled' if args.audio_reactive else 'disabled'}")
    for target in targets:
        print(f"Rendering {target.name} ...", flush=True)
        print(f"Created {render_one(target, layout, audio, p, args.codec, args.video_bitrate, not args.no_faststart, args.audio_reactive)}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
