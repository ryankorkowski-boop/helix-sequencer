#!/usr/bin/env python3
"""Run the Helix master profile once per layout bench fixture and song.

Audio files and generated sequences stay outside git (test_runs/ is ignored).
This script does not change sequencing behavior. It only invokes main.py.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "fixtures" / "layout_bench" / "manifest.json"
DEFAULT_OUT = ROOT / "test_runs" / "layout_bench"


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def effect_report(xsq_path: Path, layout_entry: dict) -> dict:
    root = ET.parse(xsq_path).getroot()
    effects_root = root.find("./ElementEffects")
    per_model: dict[str, dict[str, int]] = {}
    if effects_root is not None:
        for element in effects_root.findall("Element"):
            name = (element.attrib.get("name") or "").strip()
            kind = (element.attrib.get("type") or "").strip().lower()
            if not name or kind == "timing":
                continue
            counts: dict[str, int] = {}
            for effect in element.iter("Effect"):
                label = (effect.attrib.get("name") or effect.attrib.get("label") or "").strip() or "(unnamed)"
                counts[label] = counts.get(label, 0) + 1
            if counts:
                per_model[name] = counts
    layout_path = ROOT / layout_entry["layout"]
    layout_root = ET.parse(layout_path).getroot()
    prop_names = [model.attrib.get("name", "") for model in layout_root.findall("./models/model")]
    sub_names = []
    for model in layout_root.findall("./models/model"):
        parent = model.attrib.get("name", "")
        for sub in model.findall("./subModel"):
            sub_names.append(f"{parent}/{sub.attrib.get('name', '')}")
    group_names = [group.attrib.get("name", "") for group in layout_root.findall("./modelGroups/modelGroup")]

    def hit(name: str) -> bool:
        if name in per_model:
            return True
        return any(key == name or key.startswith(name + "/") for key in per_model)

    dark_props = [name for name in prop_names if name and not hit(name)]
    effect_hist: dict[str, int] = {}
    for counts in per_model.values():
        for label, count in counts.items():
            effect_hist[label] = effect_hist.get(label, 0) + count
    return {
        "xsq": str(xsq_path),
        "models_with_effects": len(per_model),
        "effect_total": sum(effect_hist.values()),
        "effect_names": dict(sorted(effect_hist.items(), key=lambda item: (-item[1], item[0]))),
        "dark_props": dark_props,
        "lit_prop_count": sum(1 for name in prop_names if hit(name)),
        "prop_count": len(prop_names),
        "submodels": sub_names,
        "lit_submodels": [name for name in sub_names if name in per_model],
        "groups_with_effects": [name for name in group_names if name in per_model],
    }


def canonical_xsq(folder: Path, audio_stem: str) -> Path | None:
    matches = sorted(folder.glob(f"{audio_stem},*.xsq"))
    matches = [path for path in matches if "orchestrated" not in path.name]
    if not matches:
        return None
    matches.sort(key=lambda path: (path.name.count("("), len(path.name), path.name))
    return matches[0]


def run_one(layout_entry: dict, audio: Path, out_root: Path) -> dict:
    layout_id = layout_entry["id"]
    out_dir = out_root / layout_id
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = canonical_xsq(out_dir, audio.stem)
    if existing is not None:
        return {
            "layout": layout_id,
            "audio": audio.name,
            "returncode": 0,
            "log": str(out_dir / f"{audio.stem}.log"),
            "xsq": str(existing),
            "skipped": True,
            "coverage": effect_report(existing, layout_entry),
        }
    log_path = out_dir / f"{audio.stem}.log"
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--profile",
        "master",
        "--",
        "--template",
        str(ROOT / layout_entry["template"]),
        "--audio",
        str(audio),
        "--layout-file",
        str(ROOT / layout_entry["layout"]),
        "--single",
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-learning-memory",
        "--output-dir",
        str(out_dir),
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["NUMBA_NUM_THREADS"] = "1"
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    xsq = canonical_xsq(out_dir, audio.stem)
    result = {
        "layout": layout_id,
        "audio": audio.name,
        "returncode": completed.returncode,
        "log": str(log_path),
        "xsq": str(xsq) if xsq else "",
    }
    if completed.returncode != 0 or xsq is None:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        result["error_tail"] = tail
        return result
    result["coverage"] = effect_report(xsq, layout_entry)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Helix master profile across layout-bench fixtures.")
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--layouts", nargs="*", help="Layout ids to run. Defaults to every fixture.")
    parser.add_argument("--songs", nargs="*", help="Audio filenames to run. Defaults to every file in --audio-dir.")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    manifest = load_manifest()
    if args.layouts:
        wanted = set(args.layouts)
        manifest = [entry for entry in manifest if entry["id"] in wanted]
    songs = sorted(path for path in args.audio_dir.iterdir() if path.suffix.lower() in {".mp3", ".wav", ".flac", ".ogg", ".m4a"})
    if args.songs:
        chosen = set(args.songs)
        songs = [path for path in songs if path.name in chosen]
    if not manifest or not songs:
        print("Nothing to run.", file=sys.stderr)
        return 2
    jobs = [(entry, song) for song in songs for entry in manifest]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Running {len(jobs)} master-profile sequences with {args.workers} workers.", flush=True)
    results: list[dict] = []
    if args.workers <= 1:
        for entry, song in jobs:
            print(f"START {entry['id']} {song.name}", flush=True)
            result = run_one(entry, song, args.output_dir)
            print(f"DONE {entry['id']} {song.name} rc={result['returncode']}", flush=True)
            results.append(result)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one, entry, song, args.output_dir): (entry["id"], song.name) for entry, song in jobs}
            for future in as_completed(futures):
                layout_id, song_name = futures[future]
                result = future.result()
                print(f"DONE {layout_id} {song_name} rc={result['returncode']}", flush=True)
                results.append(result)
    results.sort(key=lambda item: (item["audio"], item["layout"]))
    report_path = args.output_dir / "run_report.json"
    report_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in results if item["returncode"] != 0 or not item.get("xsq")]
    print(f"Wrote {report_path} failures={len(failed)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
