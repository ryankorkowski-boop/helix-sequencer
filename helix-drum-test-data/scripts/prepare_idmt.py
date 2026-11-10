#!/usr/bin/env python3
"""Select and normalize a compact deterministic IDMT-SMT-Drums benchmark subset."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

SUBSETS = ("RealDrum", "WaveDrum", "TechnoDrum")
INSTRUMENTS = {"KD": "kick", "SD": "snare", "HH": "hihat"}


def annotation_candidates(root: Path, wav: Path) -> list[Path]:
    ann = root / "annotation_xml"
    base = wav.stem.replace("#MIX", "")
    return [
        ann / f"{wav.stem}.xml",
        ann / f"{base}.xml",
        *sorted(ann.glob(f"{base}*.xml")),
    ]


def parse_idmt_xml(path: Path) -> list[dict]:
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    out = []
    for event in root.iter("event"):
        instrument = (event.findtext("instrument") or "").strip().upper()
        code = instrument if instrument in INSTRUMENTS else None
        if code is None:
            try:
                pitch = int(float(event.findtext("pitch") or ""))
            except ValueError:
                pitch = -1
            code = {35:"KD",36:"KD",37:"SD",38:"SD",40:"SD",42:"HH",44:"HH",46:"HH"}.get(pitch)
        if code is None:
            continue
        try:
            t = float(event.findtext("onsetSec") or "")
        except ValueError:
            continue
        out.append({"time": round(t, 6), "drum": INSTRUMENTS[code], "velocity": 1.0})
    if not out:
        # SVL-style fallback
        for point in root.iter("point"):
            try:
                t = float(point.attrib.get("time", point.attrib.get("onset", "")))
            except ValueError:
                continue
            label = (point.attrib.get("label") or point.text or "").upper()
            code = next((c for c in INSTRUMENTS if c in label), None)
            if code:
                out.append({"time": round(t, 6), "drum": INSTRUMENTS[code], "velocity": 1.0})
    return sorted(out, key=lambda e: (e["time"], e["drum"]))


def choose_files(root: Path, per_subset: int) -> list[Path]:
    audio = root / "audio"
    if not audio.is_dir():
        raise SystemExit(f"Expected IDMT audio directory: {audio}")
    chosen = []
    for subset in SUBSETS:
        files = sorted(audio.glob(f"{subset}*#MIX.wav"))
        if not files:
            continue
        if len(files) <= per_subset:
            chosen.extend(files)
        elif per_subset == 1:
            chosen.append(files[len(files)//2])
        else:
            # Evenly spread deterministic picks across the subset.
            idx = [round(i * (len(files)-1) / (per_subset-1)) for i in range(per_subset)]
            chosen.extend(files[i] for i in idx)
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idmt-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("helix-drum-test-data"))
    ap.add_argument("--per-subset", type=int, default=2)
    args = ap.parse_args()
    if args.per_subset < 1:
        raise SystemExit("--per-subset must be >= 1")

    selected = choose_files(args.idmt_root, args.per_subset)
    if not selected:
        raise SystemExit("No IDMT *#MIX.wav files found")

    out_audio = args.output / "audio" / "idmt"
    out_ann = args.output / "annotations" / "idmt"
    out_gt = args.output / "ground_truth"
    for d in (out_audio, out_ann, out_gt): d.mkdir(parents=True, exist_ok=True)

    manifest = []
    for wav in selected:
        xml = next((p for p in annotation_candidates(args.idmt_root, wav) if p.exists()), None)
        if xml is None:
            raise SystemExit(f"Missing matching annotation for {wav.name}")
        dst_wav = out_audio / wav.name
        dst_xml = out_ann / xml.name
        shutil.copy2(wav, dst_wav); shutil.copy2(xml, dst_xml)
        events = parse_idmt_xml(xml)
        gt = out_gt / f"{wav.stem}.json"
        gt.write_text(json.dumps({
            "track_id": wav.stem,
            "audio_path": f"audio/idmt/{wav.name}",
            "events": events,
            "source_format": "idmt",
            "annotation_path": f"annotations/idmt/{xml.name}",
        }, indent=2) + "\n", encoding="utf-8")
        manifest.append({"track_id": wav.stem, "subset": next(s for s in SUBSETS if wav.name.startswith(s)), "audio_path": f"audio/idmt/{wav.name}", "ground_truth": f"ground_truth/{gt.name}", "events": len(events)})

    (args.output / "annotations" / "idmt_selection.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Selected and normalized {len(manifest)} IDMT tracks")

if __name__ == "__main__": main()
