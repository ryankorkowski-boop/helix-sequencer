#!/usr/bin/env python3
"""Select a compact, deterministic IDMT-SMT-Drums subset for Helix benchmarking.

The source archive remains outside git. This script copies selected MIX WAV/XML pairs
into helix-drum-test-data and converts their annotations to the common GT schema.
"""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

SUBSETS = ("RealDrum", "WaveDrum", "TechnoDrum")
DEFAULT_PER_SUBSET = 2

def choose_files(root: Path, per_subset: int) -> list[Path]:
    audio = root / "audio"
    if not audio.is_dir():
        raise SystemExit(f"Expected IDMT audio directory: {audio}")
    chosen: list[Path] = []
    for subset in SUBSETS:
        files = sorted(p for p in audio.glob(f"{subset}*#MIX.wav"))
        if not files:
            continue
        # Deterministic spread: first and last files for each subset when possible.
        picks = files[:per_subset] if len(files) <= per_subset else [files[0], files[-1]][:per_subset]
        chosen.extend(picks)
    return chosen

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idmt-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("helix-drum-test-data"))
    ap.add_argument("--per-subset", type=int, default=DEFAULT_PER_SUBSET)
    args = ap.parse_args()

    if args.per_subset < 1:
        raise SystemExit("--per-subset must be >= 1")
    selected = choose_files(args.idmt_root, args.per_subset)
    if not selected:
        raise SystemExit("No IDMT *#MIX.wav files found")

    annotation_dir = args.idmt_root / "annotation_xml"
    out_audio = args.output / "audio" / "idmt"
    out_ann = args.output / "annotations" / "idmt"
    out_gt = args.output / "ground_truth"
    for d in (out_audio, out_ann, out_gt): d.mkdir(parents=True, exist_ok=True)

    manifest = []
    for wav in selected:
        xml = annotation_dir / f"{wav.stem}.xml"
        if not xml.exists():
            raise SystemExit(f"Missing matching annotation: {xml}")
        shutil.copy2(wav, out_audio / wav.name)
        shutil.copy2(xml, out_ann / xml.name)
        manifest.append({
            "track_id": wav.stem,
            "subset": next(s for s in SUBSETS if wav.name.startswith(s)),
            "audio_path": f"audio/idmt/{wav.name}",
            "annotation_path": f"annotations/idmt/{xml.name}",
        })

    (args.output / "annotations" / "idmt_selection.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Selected {len(manifest)} IDMT tracks")
    for item in manifest:
        print(item["track_id"])
    print("Convert with convert_to_helix_gt.py --format idmt for each annotation, or use the batch command documented in README.md.")

if __name__ == "__main__":
    main()
