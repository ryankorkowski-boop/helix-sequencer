from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from core.beat_grid import BeatGrid
from core.beat_grid_bpm import bpm_from_report_file, resolve_bpm
from core.beat_grid_output_postprocess import postprocess_generated_outputs
from core.self_improving_scoring import rhythmic_accuracy_score, score_sequence


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _report_summary(path: Path) -> dict[str, Any]:
    payload = _read_json(path) or {}
    score = score_sequence(payload).as_dict() if payload else {}
    return {
        "path": str(path),
        "bpm": bpm_from_report_file(path),
        "rhythmic_accuracy": rhythmic_accuracy_score(payload) if payload else 0.0,
        "total_score": score.get("total_score", 0.0),
        "beat_grid": payload.get("beat_grid", {}) if payload else {},
    }


def summarize_reports(root: Path) -> dict[str, Any]:
    reports = [_report_summary(path) for path in sorted(root.rglob("*.report.json"))]
    accuracies = [float(item["rhythmic_accuracy"]) for item in reports]
    totals = [float(item["total_score"]) for item in reports]
    bpms = [float(item["bpm"]) for item in reports if item.get("bpm") is not None]
    return {
        "report_count": len(reports),
        "avg_rhythmic_accuracy": round(mean(accuracies), 4) if accuracies else 0.0,
        "avg_total_score": round(mean(totals), 4) if totals else 0.0,
        "detected_bpm": round(resolve_bpm(None, [], fallback_bpm=mean(bpms)) if bpms else 120.0, 3),
        "reports": reports,
    }


def run_validation(root: Path, *, bpm: float | None, subdivision: int, mode: str, max_shift_ms: int) -> dict[str, Any]:
    before = summarize_reports(root)
    grid = BeatGrid(
        bpm=resolve_bpm(bpm, [], fallback_bpm=float(before.get("detected_bpm") or 120.0)),
        subdivision=subdivision,
        mode=mode,  # type: ignore[arg-type]
        max_shift_ms=max_shift_ms,
    )
    postprocess = postprocess_generated_outputs(root, grid)
    after = summarize_reports(root)
    return {
        "root": str(root.resolve()),
        "grid": {
            "bpm": grid.bpm,
            "subdivision": grid.subdivision,
            "mode": grid.mode,
            "max_shift_ms": grid.max_shift_ms,
        },
        "before": before,
        "postprocess": postprocess,
        "after": after,
        "delta": {
            "avg_rhythmic_accuracy": round(float(after["avg_rhythmic_accuracy"]) - float(before["avg_rhythmic_accuracy"]), 4),
            "avg_total_score": round(float(after["avg_total_score"]) - float(before["avg_total_score"]), 4),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate BeatGrid snapping against generated Helix outputs.")
    parser.add_argument("root", nargs="?", default=".", help="Folder containing generated XSQ/report sidecars.")
    parser.add_argument("--bpm", type=float, help="Override BPM. Defaults to report-derived BPM or 120.")
    parser.add_argument("--subdivision", type=int, default=16, choices=(4, 8, 16, 24, 32))
    parser.add_argument("--mode", choices=("strict", "musical", "humanized"), default="musical")
    parser.add_argument("--max-shift-ms", type=int, default=40)
    parser.add_argument("--out", help="Optional JSON summary output path.")
    args = parser.parse_args(argv)

    result = run_validation(
        Path(args.root),
        bpm=args.bpm,
        subdivision=args.subdivision,
        mode=args.mode,
        max_shift_ms=args.max_shift_ms,
    )
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
