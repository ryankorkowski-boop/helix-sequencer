"""Separate the authenticated 256s sampler with Demucs, preserving review gates.

Run: python -m tools.separate_sampler_vocals AUDIO.mp3 OUTPUT_DIR
This produces *candidate* stems, never a falsely certified singer timeline.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

EXPECTED_SHA256 = "ffeaba9b9f8fc253a0356505c2b4147b7576b772db42a1c8ea63094b42545acf"


def separate(audio: Path, output: Path) -> dict:
    if not audio.is_file() or hashlib.sha256(audio.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Authenticated starred sampler required; source hash mismatch")
    executable = shutil.which("demucs")
    if not executable:
        raise RuntimeError("Demucs executable missing")
    output.mkdir(parents=True, exist_ok=True)
    command = [executable, "--two-stems=vocals", "-n", "htdemucs", "-o", str(output), str(audio)]
    subprocess.run(command, check=True)
    folder = output / "htdemucs" / audio.stem
    stems = {}
    for role in ("vocals", "no_vocals"):
        path = folder / (role + ".wav")
        if not path.is_file() or path.stat().st_size <= 44:
            raise RuntimeError(f"Missing or empty separated stem: {role}")
        stems[role] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    report = {
        "schema": "helix.sampler-stem-candidates.v1",
        "source_audio_sha256": EXPECTED_SHA256,
        "separator": "demucs-htdemucs",
        "verification_status": "candidate_unverified",
        "stems": stems,
        "note": "Separation is not independent validation of vocal presence or lead/backing roles. "
                "Do not feed these stems directly to verified_sampler_vocals.json.",
    }
    (output / "sampler_stem_candidates.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(separate(args.audio, args.output), indent=2))
