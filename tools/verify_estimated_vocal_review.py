"""Qualify estimated two-singer clocks for *experimental review*, never release.

This deliberately does not modify verify_native_vocal_source.py. It does not
authenticate singer identities, acoustic separation quality, or phoneme accuracy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from models.band_sampler_logic import NATIVE_SHAPE_NAMES
from music.vocal_qualification import independence_metrics, validate_lanes


def evaluate(analysis: Path) -> dict:
    with np.load(analysis / "voice_roles.npz", allow_pickle=False) as data:
        energy, shapes = validate_lanes(data["energy"], data["shapes"],
                                        shape_names=NATIVE_SHAPE_NAMES)
    metrics = independence_metrics(energy, shapes)
    lead, harmony = metrics["non_rest_frames"]
    distinct = metrics["unique_active_frames"]
    # A second lane that is only a gain/clock copy cannot pass.
    acceptable = bool(lead and harmony and not metrics["duplicate_clock"]
                      and (distinct[0] or distinct[1]))
    return {
        "state": "ESTIMATED_REVIEW" if acceptable else "REJECTED",
        "passed": acceptable,
        "release_verified": False,
        "identity_verified": False,
        "metrics": metrics,
        "limitations": ("Distinct mouth clocks do not prove two acoustic singers; "
                        "review separated stems against the original song. "
                        "Never use this report to satisfy the verified native release gate."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(args.analysis)
    except (OSError, ValueError, KeyError) as exc:
        report = {"state": "REJECTED", "passed": False,
                  "release_verified": False, "error": str(exc)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
