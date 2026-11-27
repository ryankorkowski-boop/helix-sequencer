"""Generate *estimated* RoFormer vocal review clocks from one original recording.

Demucs extracts the combined vocal bus when --vocals is omitted. RoFormer
then splits that bus into karaoke model outputs. Neither output name nor
spectral independence establishes an actual singer's identity. The strict
source-verified approval gate must remain separate from these review clocks.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools.roformer_review_fixture import build as build_review_fixture
from tools.separate_vocal_roles import MODEL, sha256, write_manifest


def select_model_outputs(directory: Path) -> tuple[Path, Path]:
    """Require one of each karaoke output; never guess ambiguous filenames."""
    directory = directory.resolve()
    files = [
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() == ".wav"
        and not p.name.lower().endswith(".normalized.wav")
    ]
    lead = [p for p in files if "vocals" in p.stem.lower()
            and "instrumental" not in p.stem.lower()]
    backing = [p for p in files if "instrumental" in p.stem.lower()]
    if len(lead) != 1 or len(backing) != 1 or lead[0] == backing[0]:
        raise ValueError(
            "Expected exactly one Vocals and one Instrumental karaoke output; "
            "review actual model results instead of guessing singer roles"
        )
    return lead[0], backing[0]


def prepare(audio: Path, output: Path, *, vocals: Path | None = None,
            model: str = MODEL) -> Path:
    audio, output = audio.resolve(strict=True), output.resolve()
    if not audio.is_file():
        raise ValueError("Original audio must be an existing file")
    # A fresh location is required: never accidentally reuse estimates from
    # another recording or allow cached model outputs to appear source-verified.
    if output.exists():
        raise FileExistsError(f"Review output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    if vocals is None:
        demucs_root = output / "demucs"
        subprocess.run(
            [sys.executable, "-m", "demucs", "-n", "htdemucs_6s",
             "--two-stems", "vocals", "-o", str(demucs_root), str(audio)],
            check=True,
        )
        candidates = list(demucs_root.rglob("vocals.wav"))
        if len(candidates) != 1:
            raise ValueError("Demucs must produce exactly one combined vocals.wav")
        vocals = candidates[0]
    vocals = vocals.resolve(strict=True)
    model_root = output / "roformer"
    model_root.mkdir()
    separator = shutil.which("audio-separator")
    if separator is None:
        raise RuntimeError("Install audio-separator to run the RoFormer review model")
    subprocess.run(
        [separator, str(vocals), "--model_filename", model,
         "--output_format", "WAV", "--output_dir", str(model_root)],
        check=True,
    )
    lead_raw, backing_raw = select_model_outputs(model_root)
    normalized = []
    for role, raw in (("lead", lead_raw), ("backing", backing_raw)):
        dest = model_root / f"{role}.normalized.wav"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-y", "-i", str(raw), "-ac", "1", "-ar", "44100",
             "-c:a", "pcm_s16le", str(dest)],
            check=True,
        )
        normalized.append(dest)
    manifest = write_manifest(
        audio, *normalized, model_root / "vocal_separation_manifest.json",
        model=model, combined_vocals=vocals,
        # Review-only fallback suppresses a silent backing candidate; never
        # upgrades model-estimated tracks into verified independent singers.
        allow_silent_harmony_review=True,
    )
    fixture = build_review_fixture(audio, manifest, output / "vocal-fixture")
    receipt = json.loads((fixture / "diagnostic.json").read_text())
    if (receipt["audio_sha256"] != sha256(audio)
            or receipt["verification_state"] != "ESTIMATED_REVIEW"
            or receipt["independent_backing_verified"] is not False):
        raise ValueError("Invalid model-estimated review provenance")
    (output / "review_origin.json").write_text(json.dumps({
        "source_sha256": sha256(audio),
        "vocal_bus_sha256": sha256(vocals),
        "model": model,
        "mode": "estimated_review_only",
        "independent_singer_identity_verified": False,
        "fixture": "vocal-fixture",
    }, indent=2) + "\n")
    return fixture


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--vocals", type=Path,
                        help="Optional already-separated Demucs vocal bus")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    fixture = prepare(args.audio, args.output, vocals=args.vocals,
                      model=args.model)
    print(fixture)


if __name__ == "__main__":
    main()
