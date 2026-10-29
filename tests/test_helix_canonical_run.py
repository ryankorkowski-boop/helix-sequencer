from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

from helix.run import run_pipeline
from tools.validate_xsq_structure import validate_xsq


def _write_test_wav(path: Path, duration: float = 1.0, sr: int = 22050) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        for idx in range(int(duration * sr)):
            t = idx / sr
            tone = 0.35 * math.sin(2 * math.pi * 220 * t)
            click = 0.45 * math.exp(-((t % 0.25) * 80.0))
            sample = int(max(-0.9, min(0.9, tone + click)) * 32767)
            handle.writeframes(struct.pack("<h", sample))


def test_canonical_run_writes_xsq_mp4_audio_and_diagnostics(tmp_path: Path) -> None:
    audio = tmp_path / "input.wav"
    _write_test_wav(audio)

    manifest = run_pipeline(audio, Path("allmodels/xlights_rgbeffects.xml"), tmp_path / "out" / "Helix_test")

    artifacts = manifest["artifacts"]
    xsq = Path(artifacts["xsq"])
    mp4 = Path(artifacts["mp4"])
    wav = Path(artifacts["wav"])
    analysis = Path(artifacts["analysis"])
    events = Path(artifacts["events"])
    validation = Path(artifacts["validation"])

    validate_xsq(xsq)
    assert mp4.exists() and mp4.stat().st_size > 0
    assert wav.exists() and wav.stat().st_size > 0
    assert analysis.exists()
    assert events.exists()
    payload = json.loads(validation.read_text(encoding="utf-8"))
    assert payload["media"]["has_audio"]
    assert payload["media"]["has_video"]
    assert payload["required_drummer_submodels"]["HX_SNOWMAN_DRUMMER_V3_KICK"]
    assert payload["required_drummer_submodels"]["HX_SNOWMAN_DRUMMER_V3_SNARE"]
