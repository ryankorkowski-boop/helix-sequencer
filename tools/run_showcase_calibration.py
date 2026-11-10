"""Run showcase calibration and print JSON.

This is a convenience script to run Phase 5 calibration + Phase 6 stability
metrics without modifying the core engine.

Usage:
    python tools/run_showcase_calibration.py
"""

from __future__ import annotations

import json

from tools.build_helpers.showcase_stability_metrics import run_calibration_with_stability


def main() -> None:
    report = run_calibration_with_stability("showcase")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
