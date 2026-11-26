"""Optional local karaoke-model adapter for the Phoneme Test Hook.

Never infer singer identity from an arbitrary 'Vocals'/'Instrumental' pair.
The operator must explicitly map model outputs to lead/backing, then the
existing source-bound manifest and independent-vocal gates validate them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil

MODEL = "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(source: Path, lead: Path, backing: Path, output: Path,
                   *, model: str = MODEL, combined_vocals: Path | None = None,
                   allow_silent_harmony_review: bool = False) -> Path:
    from core.vocal_separation_manifest import validate_vocal_separation_manifest
    from core.independent_vocals import analyze_independent_vocals
    source, lead, backing, output = (p.resolve() for p in (source, lead, backing, output))
    output.parent.mkdir(parents=True, exist_ok=True)
    if not lead.is_relative_to(output.parent) or not backing.is_relative_to(output.parent):
        raise ValueError("Singer stems must be inside the manifest directory")
    # The current independent-vocal gate requires aligned mono 16-bit PCM WAV.
    silent_harmony = False
    try:
        result = analyze_independent_vocals(lead, backing)
    except ValueError as exc:
        if not allow_silent_harmony_review or str(exc) != 'Harmony stem is silent; no second singer can be verified':
            raise
        silent_harmony = True
        result = {'independence': 'not_established_harmony_silent'}
    data = {
        "schema": ("helix.vocal-separation.silent-harmony-review.v1"
                   if silent_harmony else "helix.vocal-separation.v1"),
        "method": "vocals_first_then_lead_backing",
        "source_sha256": sha256(source),
        "model": model,
        "identity_evidence": "unverified_roles_not_individual_singer_identity",
        "independence": result["independence"],
        "lead": {"path": str(lead.relative_to(output.parent)), "sha256": sha256(lead)},
        "backing": {"path": str(backing.relative_to(output.parent)), "sha256": sha256(backing)},
    }
    if combined_vocals is not None:
        data["combined_vocals_sha256"] = sha256(combined_vocals.resolve())
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if not silent_harmony:
        validate_vocal_separation_manifest(output, source)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--vocals", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--skip-separation", action="store_true", help="Reuse existing model outputs without rerunning inference")
    parser.add_argument("--allow-silent-harmony-review", action="store_true",
                        help="Write an explicitly unqualified review-only manifest if the second candidate is silent")
    parser.add_argument("--lead-output", help="Exact filename returned by audio-separator")
    parser.add_argument("--backing-output", help="Exact filename returned by audio-separator")
    args = parser.parse_args()
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not args.skip_separation:
        exe = shutil.which("audio-separator")
        if not exe:
            raise SystemExit("Install audio-separator in the current Python environment")
        cmd = [exe, str(args.vocals.resolve()),
               "--model_filename", args.model, "--output_format", "WAV",
               "--output_dir", str(root)]
        subprocess.run(cmd, check=True)
    if not args.lead_output or not args.backing_output:
        raise SystemExit(
            "Separation completed, but singer roles are unverified. Inspect outputs in "
            f"{root}; rerun with --lead-output and --backing-output to map actual model labels."
        )
    lead_raw, backing_raw = (root / args.lead_output).resolve(), (root / args.backing_output).resolve()
    if any(not p.is_relative_to(root) or not p.is_file() for p in (lead_raw, backing_raw)):
        raise SystemExit("Model output filename missing or escapes output directory")
    if lead_raw == backing_raw:
        raise SystemExit("Lead and backing cannot be mapped to the same output")
    # Karaoke-model secondary output may be named Instrumental even when
    # applied to an isolated vocal stem. Never infer singer identity from
    # filenames; the source-bound audio independence gate runs below.
    # Normalize to the format expected by the existing independent-vocal gate.
    normalized = []
    for role, raw in (("lead", lead_raw), ("backing", backing_raw)):
        dest = root / (role + ".normalized.wav")
        subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                        "-y", "-i", str(raw), "-ac", "1", "-ar", "44100",
                        "-c:a", "pcm_s16le", str(dest)], check=True)
        normalized.append(dest)
    manifest = write_manifest(args.source, *normalized, root / "vocal_separation_manifest.json",
                              model=args.model, combined_vocals=args.vocals,
                              allow_silent_harmony_review=args.allow_silent_harmony_review)
    print(manifest)


if __name__ == "__main__":
    main()
