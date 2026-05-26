from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from core.birdsong_completion_gate import (
    BirdsongCompletionGateConfig,
    BirdsongCompletionGateReport,
    run_birdsong_completion_gate,
)
from core.feature_state import FeatureState


DEFAULT_MODELS: tuple[str, ...] = (
    "HX_MEGA_TREE",
    "HX_ARCHES",
    "HX_ROOFLINE",
    "HX_MATRIX",
    "HX_STAGE_BAND",
    "HX_SNOWMAN_DRUMMER",
)


def _demo_frames(duration_seconds: float, step_seconds: float, *, bpm: float) -> list:
    state = FeatureState(ema_alpha=0.35)
    frames = []
    steps = max(1, int(round(duration_seconds / step_seconds)))
    for index in range(steps):
        time_s = round(index * step_seconds, 6)
        phase = min(1.0, time_s / max(duration_seconds, 0.001))
        beat_phase = ((time_s / max(0.001, 60.0 / max(1.0, bpm))) % 1.0)
        if phase < 0.25:
            energy, onset, centroid, bands = 0.42 + phase, 0.82 if index == 0 else 0.20, 1200.0, (0.70, 0.22, 0.08)
        elif phase < 0.50:
            energy, onset, centroid, bands = 0.70, 0.88 if index % 4 == 0 else 0.28, 3600.0, (0.18, 0.70, 0.12)
        elif phase < 0.75:
            energy, onset, centroid, bands = 0.86, 0.90 if index % 4 == 0 else 0.35, 7200.0, (0.10, 0.20, 0.70)
        else:
            energy, onset, centroid, bands = 0.62, 0.72 if index % 4 == 0 else 0.22, 2600.0, (0.30, 0.48, 0.22)
        low, mid, high = bands
        frames.append(
            state.update(
                index,
                energy=energy,
                onset=onset,
                centroid=centroid,
                low=low,
                mid=mid,
                high=high,
                beat_phase=beat_phase,
                time_s=time_s,
            )
        )
    return frames


def verify_issue_2_birdsong_contract(
    *,
    output: Path,
    duration_seconds: float = 20.0,
    step_seconds: float = 1.0,
    bpm: float = 120.0,
    min_quality_score: float = 0.35,
    model_pool: Sequence[str] = DEFAULT_MODELS,
) -> BirdsongCompletionGateReport:
    frames = _demo_frames(duration_seconds, step_seconds, bpm=bpm)
    report = run_birdsong_completion_gate(
        frames,
        model_pool,
        config=BirdsongCompletionGateConfig(
            bpm=bpm,
            min_quality_score=min_quality_score,
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the Issue #2 Birdsong completion contract.")
    parser.add_argument("--output", type=Path, default=Path("test_runs/issue_2_birdsong_contract/contract_report.json"))
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--step-seconds", type=float, default=1.0)
    parser.add_argument("--bpm", type=float, default=120.0)
    parser.add_argument("--min-quality-score", type=float, default=0.35)
    parser.add_argument("--model", action="append", dest="models", default=None, help="Model name to include in the proof pool. May be repeated.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_issue_2_birdsong_contract(
        output=args.output,
        duration_seconds=args.duration_seconds,
        step_seconds=args.step_seconds,
        bpm=args.bpm,
        min_quality_score=args.min_quality_score,
        model_pool=tuple(args.models) if args.models else DEFAULT_MODELS,
    )
    print(json.dumps({"output": str(args.output), "passed": report.passed, "score": report.quality.get("score")}, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
