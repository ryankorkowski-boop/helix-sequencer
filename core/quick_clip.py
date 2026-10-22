"""Create a short, lossless sequencing input without modifying the source song."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile


def prepare_quick_clip(source: Path, output: Path) -> Path:
    import soundfile as sf

    source = source.resolve(strict=True)
    directory = output.resolve() / "quick-clip-input"
    directory.mkdir(parents=True, exist_ok=True)
    # Each run owns its input, even when several jobs use the same song.
    run_directory = Path(tempfile.mkdtemp(prefix="run-", dir=directory))
    # The engine seeds visual choices from the basename. Keep it stable while
    # isolating concurrent runs in separate directories.
    clip = run_directory / (source.stem + "-quick-10s.wav")
    try:
        try:
            with sf.SoundFile(source) as audio:
                samples = audio.read(min(audio.frames, audio.samplerate * 10), dtype="float32", always_2d=True)
                sf.write(clip, samples, audio.samplerate, subtype="FLOAT")
        except sf.LibsndfileError:
            import imageio_ffmpeg
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-nostdin", "-y",
                            "-i", str(source), "-t", "10", "-vn", "-c:a", "pcm_f32le", str(clip)],
                           check=True, timeout=120)
        info = sf.info(clip)
        if not 0 < info.frames <= info.samplerate * 10:
            raise ValueError("Quick clip must contain at most ten seconds of audio")
        clip.with_suffix(".json").write_text(json.dumps({
            "source": str(source), "clip": str(clip), "start_seconds": 0,
            "duration_seconds": info.duration, "mode": "quick_clip",
        }, indent=2) + "\n", encoding="utf-8")
        return clip
    except BaseException:
        clip.unlink(missing_ok=True)
        raise
