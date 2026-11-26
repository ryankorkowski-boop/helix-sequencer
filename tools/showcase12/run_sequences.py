#!/usr/bin/env python3
"""Sequence the showcase12 layouts with the Helix master profile.

Audio and generated XSQ files stay outside git.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "fixtures" / "showcase12" / "manifest.json"


def canonical_xsq(folder: Path, audio_stem: str) -> Path | None:
    matches = [path for path in folder.glob(f"{audio_stem},*.xsq") if "orchestrated" not in path.name]
    if not matches:
        return None
    matches.sort(key=lambda path: (path.name.count("("), len(path.name), path.name))
    return matches[0]


def run_one(entry: dict, audio: Path, out_root: Path) -> dict:
    layout_id = entry["id"]
    out_dir = out_root / layout_id
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = canonical_xsq(out_dir, audio.stem)
    if existing is not None:
        return {"layout": layout_id, "audio": audio.name, "returncode": 0, "xsq": str(existing), "skipped": True}
    log_path = out_dir / f"{audio.stem}.log"
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--profile",
        "master",
        "--",
        "--template",
        str(ROOT / entry["template"]),
        "--audio",
        str(audio),
        "--layout-file",
        str(ROOT / entry["layout"]),
        "--single",
        "--variants",
        "1",
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--no-learning-memory",
        "--sync-lyrics-heads",
        "--output-dir",
        str(out_dir),
    ]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["NUMBA_NUM_THREADS"] = "1"
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)
    xsq = canonical_xsq(out_dir, audio.stem)
    result = {"layout": layout_id, "audio": audio.name, "returncode": completed.returncode, "xsq": str(xsq) if xsq else "", "log": str(log_path)}
    if completed.returncode != 0 or xsq is None:
        result["error_tail"] = log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--songs", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "test_runs" / "showcase12")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    songs = []
    for name in args.songs:
        path = args.audio_dir / name
        if not path.exists():
            print(f"Missing audio {path}", file=sys.stderr)
            return 2
        songs.append(path)
    jobs = [(entry, song) for song in songs for entry in manifest]
    print(f"Running {len(jobs)} sequences with {args.workers} workers.", flush=True)
    results = []
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
    report = args.output_dir / "run_report.json"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in results if item["returncode"] != 0 or not item.get("xsq")]
    print(f"failures={len(failed)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
