from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any, Iterable


BPM_KEYS = (
    "tempo_bpm",
    "bpm",
    "detected_bpm",
    "estimated_bpm",
    "beat_bpm",
)


def _valid_bpm(value: Any) -> float | None:
    try:
        bpm = float(value)
    except Exception:
        return None
    if 30.0 <= bpm <= 240.0:
        return bpm
    return None


def _walk_for_bpm(value: Any) -> list[float]:
    found: list[float] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in BPM_KEYS:
                bpm = _valid_bpm(child)
                if bpm is not None:
                    found.append(bpm)
            found.extend(_walk_for_bpm(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_for_bpm(child))
    return found


def bpm_from_payload(payload: dict[str, Any]) -> float | None:
    """Resolve the best BPM estimate from a Helix report payload."""

    preferred_paths = [
        ("advanced_audio", "tempo_bpm"),
        ("analysis", "tempo_bpm"),
        ("audio", "tempo_bpm"),
        ("beat_grid", "bpm"),
        ("chronoflow", "tempo_bpm"),
    ]
    for path in preferred_paths:
        current: Any = payload
        for key in path:
            current = current.get(key) if isinstance(current, dict) else None
        bpm = _valid_bpm(current)
        if bpm is not None:
            return bpm
    all_values = _walk_for_bpm(payload)
    if not all_values:
        return None
    return float(median(all_values))


def bpm_from_report_file(path: Path) -> float | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return bpm_from_payload(payload) if isinstance(payload, dict) else None


def bpm_from_recent_reports(root: Path, *, since: float | None = None) -> float | None:
    values: list[float] = []
    for path in root.resolve().rglob("*.report.json"):
        if since is not None:
            try:
                if path.stat().st_mtime < since - 1.0:
                    continue
            except OSError:
                continue
        bpm = bpm_from_report_file(path)
        if bpm is not None:
            values.append(bpm)
    if not values:
        return None
    return float(median(values))


def resolve_bpm(explicit_bpm: float | None, payloads: Iterable[dict[str, Any]] = (), *, fallback_bpm: float = 120.0) -> float:
    bpm = _valid_bpm(explicit_bpm)
    if bpm is not None:
        return bpm
    values = [candidate for payload in payloads if (candidate := bpm_from_payload(payload)) is not None]
    if values:
        return float(median(values))
    return float(fallback_bpm)
