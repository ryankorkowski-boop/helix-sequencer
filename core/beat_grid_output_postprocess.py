from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core import self_improving_scoring
from core.snowman_band_beat_grid import snap_snowman_band_payload_to_grid
from xlights.beat_grid_timing import snap_xsq_timing_tracks


def _json_read(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _json_write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _recent(path: Path, since: float | None) -> bool:
    if since is None:
        return True
    try:
        return path.stat().st_mtime >= since - 1.0
    except OSError:
        return False


def _snap_report_payload(payload: dict[str, Any], beat_grid) -> dict[str, Any]:
    snowman = payload.get("snowman_band")
    if isinstance(snowman, dict):
        payload["snowman_band"] = snap_snowman_band_payload_to_grid(snowman, beat_grid)
    payload.setdefault("beat_grid", {})
    if isinstance(payload["beat_grid"], dict):
        payload["beat_grid"].update(
            {
                "snapped": True,
                "subdivision": beat_grid.subdivision,
                "bpm": beat_grid.bpm,
                "offset_ms": beat_grid.offset_ms,
                "mode": beat_grid.mode,
                "max_shift_ms": beat_grid.max_shift_ms,
                "source": "beat_grid_output_postprocess",
            }
        )
    payload["self_improving_scoring"] = self_improving_scoring.score_sequence(payload).as_dict()
    return payload


def postprocess_generated_outputs(root: Path, beat_grid, *, since: float | None = None) -> dict[str, Any]:
    """Snap generated report sidecars, snowman exports, and XSQ timing tracks."""

    root = root.resolve()
    reports = 0
    snowman_exports = 0
    xsq_files = 0
    xsq_events_changed = 0
    warnings: list[str] = []

    for path in root.rglob("*.report.json"):
        if not _recent(path, since):
            continue
        payload = _json_read(path)
        if not payload or not self_improving_scoring.is_helix_generated_payload(payload):
            continue
        if ((payload.get("beat_grid") or {}) or {}).get("snapped"):
            continue
        _json_write(path, _snap_report_payload(payload, beat_grid))
        reports += 1

    for path in root.rglob("*.snowman_band.json"):
        if not _recent(path, since):
            continue
        payload = _json_read(path)
        if not payload:
            continue
        if ((payload.get("beat_grid") or {}) or {}).get("snapped"):
            continue
        _json_write(path, snap_snowman_band_payload_to_grid(payload, beat_grid))
        snowman_exports += 1

    for path in root.rglob("*.xsq"):
        if not _recent(path, since):
            continue
        if path.name.endswith(".orchestrated.xsq"):
            continue
        try:
            result = snap_xsq_timing_tracks(path, beat_grid)
        except Exception as exc:
            warnings.append(f"{path.name}: {exc!r}")
            continue
        xsq_files += 1
        xsq_events_changed += int(result.get("events_changed", 0) or 0)

    return {
        "enabled": True,
        "reports": reports,
        "snowman_exports": snowman_exports,
        "xsq_files": xsq_files,
        "xsq_events_changed": xsq_events_changed,
        "warnings": warnings[:20],
        "subdivision": beat_grid.subdivision,
        "mode": beat_grid.mode,
        "root": str(root),
    }
