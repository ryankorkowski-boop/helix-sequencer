from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from tools.build_helpers.variant_lanes import build_variant_lane_plan


def _coerce_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("entries", "candidates", "variants", "assignments"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if "label" in payload:
        return [payload]
    return []


def load_entries(paths: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries.extend(_coerce_entries(payload))
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a report-only Helix variant lane plan from JSON candidate reports.")
    parser.add_argument("reports", nargs="+", type=Path, help="Candidate report JSON files or a JSON list of candidates.")
    parser.add_argument("--output", type=Path, default=None, help="Optional path to write the lane plan JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    entries = load_entries(list(args.reports))
    plan = build_variant_lane_plan(entries)
    text = json.dumps(plan, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
