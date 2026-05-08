"""Bridge StyleDecision records toward xLights/xsq writer integration.

This module intentionally sits beside xsq_writer.py instead of changing existing
writer behavior. It converts StyleDecision objects into deterministic, writer-
ready effect rows that can be consumed by an XML/XSQ writer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from tools.style_engine import StyleDecision
from tools.style_to_effect_mapper import map_decision_to_effects


REQUIRED_EFFECT_KEYS = {
    "model",
    "start",
    "duration",
    "effect",
    "palette",
    "intensity",
    "motion",
    "intent",
}


def decisions_to_xsq_effect_rows(decisions: Iterable[StyleDecision]) -> list[dict]:
    """Convert StyleDecision objects into deterministic writer-ready rows."""

    rows: list[dict] = []
    for decision in decisions:
        rows.extend(map_decision_to_effects(decision))
    return rows


def validate_xsq_effect_rows(rows: Iterable[dict]) -> None:
    """Validate the minimal contract expected by downstream xLights writers."""

    for index, row in enumerate(rows):
        missing = REQUIRED_EFFECT_KEYS.difference(row)
        if missing:
            raise ValueError(f"Effect row {index} is missing required keys: {sorted(missing)}")
        if row["duration"] <= 0:
            raise ValueError(f"Effect row {index} has non-positive duration")
        if row["start"] < 0:
            raise ValueError(f"Effect row {index} has negative start time")
        if not row["model"]:
            raise ValueError(f"Effect row {index} has empty model target")


def write_xsq_effect_rows_json(rows: Iterable[dict], output_path: str | Path) -> Path:
    """Write effect rows as JSON for debugging or later XML conversion."""

    row_list = list(rows)
    validate_xsq_effect_rows(row_list)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row_list, indent=2), encoding="utf-8")
    return path
