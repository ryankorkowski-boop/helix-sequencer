"""Build a source-audited six-song, 180-second high-complexity montage.

The video is a musical spectrum reference, NOT a native Helix/xLights render.
Use its exact selection manifest to drive a subsequent native band showcase.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.signal import stft

ROOT = Path(__file__).resolve().parents[1]
SONGS = [
    ("Wire Tree", "evidence/showcase_audio/source/1-Wire-Tree.mp3"),
    ("Tinsel Sawtooth", "evidence/showcase_audio/source/2-Tinsel-Sawtooth-1-.mp3"),
    ("Frostbitten Fingerboard", "evidence/showcase_audio/source/3-Frostbitten-Fingerboard-1-.mp3"),
    ("Holly Steel Run", "evidence/showcase_audio/source/4-Holly-Steel-Run-1-.mp3"),
    ("Bell Circuit Carol", "evidence/showcase_audio/source/5-Bell-Circuit-Carol-1-.mp3"),
    ("Helix Audiolights", "Helix Audiolights.mp3"),
]


def run(*args: str) -> None:
    subprocess.run(list(args), check=True)


def mono_audio(path: Path, sr: int = 11025) -> np.ndarray:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
         "-ar", str(sr), "-f", "f32le", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return np.frombuffer(result.stdout, dtype="<f4").copy()


def choose_window(y: np.ndarray, sr: int, seconds: int = 30) -> tuple[float, dict]:
    """Prefer dense, varied, multiband musical passages, not merely loud ones."""
    if len(y) < sr * seconds:
        raise ValueError("Song shorter than requested selection")
    _, times, z = stft(y, fs=sr, nperseg=1024, noverlap=512)
    mag = abs(z).astype(np.float32)
    power = mag * mag
    bands = [(45, 180), (180, 900), (900, 3500), (3500, 5300)]
    frequencies = np.fft.rfftfreq(1024, 1 / sr)
    energies = np.stack([np.sqrt(np.mean(power[(frequencies >= lo) & (frequencies < hi)], axis=0) + 1e-12)
                         for lo, hi in bands])
    flux = np.maximum(0, np.diff(mag, axis=1, prepend=mag[:, :1])).sum(axis=0)
    hop = 512 / sr
    length = max(1, round(seconds / hop))
    stride = max(1, round(0.5 / hop))
    features = []
    # Log compression prevents a loud bass track from overwhelming note density.
    for start in range(0, len(times) - length + 1, stride):
        sl = slice(start, start + length)
        band = energies[:, sl]
        onset = flux[sl]
        active = (band > np.maximum(np.quantile(energies, .45, axis=1)[:, None], 1e-5)).sum(axis=0)
        score = (1.35 * np.mean(active) +
                 1.2 * np.mean(np.log1p(onset * 100)) +
                 .8 * np.std(np.log1p(onset * 100)) +
                 .7 * np.mean(np.log1p(band[1:] * 120)) +
                 .5 * np.std(np.log1p(band[1:] * 120)))
        features.append((float(score), float(times[start]), float(np.mean(active)),
                         float(np.mean(onset))))
    if not features:
        raise ValueError("No valid selection window")
    best = max(features, key=lambda row: row[0])
    # Never request audio beyond source bounds.
    start = min(best[1], len(y) / sr - seconds)
    return max(0., start), dict(complexity_score=round(best[0], 5),
                               mean_active_bands=round(best[2], 4),
                               mean_spectral_flux=round(best[3], 5))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=ROOT / "outputs/six_song_technical_montage")
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"selection_method": "30-second multiband activity + spectral flux + variation",
                "render_type": "musical spectrum reference (not native Helix render)",
                "segments": []}
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        clips = []
        for index, (title, relative) in enumerate(SONGS):
            source = ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            start, metrics = choose_window(mono_audio(source), 11025)
            manifest["segments"].append(dict(order=index + 1, title=title, source=relative,
                                             source_start_seconds=round(start, 3),
                                             duration_seconds=30, **metrics))
            clip = tmpdir / f"segment_{index:02d}.mp4"
            # Native audio from the six source files. Video makes dense spectral
            # activity reviewable; it does not fabricate a Helix band performance.
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{start:.3f}", "-t", "30", "-i", str(source),
                "-filter_complex",
                "[0:a]asplit=2[hear][viz];"
                "[viz]showfreqs=s=1280x720:mode=bar:ascale=log:fscale=log:"
                "colors=cyan|magenta|yellow:win_size=2048:rate=20,"
                "format=yuv420p[v]",
                "-map", "[v]", "-map", "[hear]", "-r", "20",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-ac", "2", "-shortest", str(clip))
            clips.append(clip)
        concat = tmpdir / "clips.txt"
        concat.write_text("".join(f"file '{p}'\\n" for p in clips))
        final = out / "Helix_Six_Song_Technical_180s.mp4"
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", str(final))
        probe = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                         "format=duration", "-of", "default=nw=1:nk=1", str(final)])
        manifest["rendered_duration_seconds"] = float(probe)
        (out / "selection_manifest.json").write_text(json.dumps(manifest, indent=2) + "\\n")
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
