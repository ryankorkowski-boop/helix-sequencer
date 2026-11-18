"""Index-aligned labels for simulated sequence previews.

These labels describe phone and desktop review movies. They are not native
xLights FSEQ evidence.
"""
from __future__ import annotations

from pathlib import Path

COMPLETED = "completed"
FAILED = "failed"
PENDING = "pending"
RUNNING = "running"
UNAVAILABLE = "unavailable"

_READY_PREFIX = "preview_mp4: "
_READY_SUFFIX = " (simulated, not native rendering)"
_STATE_PREFIX = "preview_state: "


def bounded_preview_limit(requested, cap: int = 8) -> int:
    return max(1, min(int(requested), cap))


def select_preview_candidates(valid, selected, preview_limit):
    """Primary sequence first, then the other exports, capped at the request."""
    limit = bounded_preview_limit(preview_limit)
    ordered = [selected] + [item for item in valid if item != selected]
    return ordered[:limit], limit


def _key(item) -> str:
    return str(item)


def align_preview_paths(valid, outcomes) -> list[str]:
    """Movie paths in sequence-list order. Missing and failed entries stay blank."""
    return [str(outcomes.get(_key(item)) or "") for item in valid]


def preview_states(valid, candidates, outcomes, active=None) -> list[str]:
    chosen = {_key(item) for item in candidates}
    active_key = None if active is None else _key(active)
    rows = []
    for item in valid:
        key = _key(item)
        if key not in chosen:
            rows.append(UNAVAILABLE)
        elif key in outcomes:
            rows.append(COMPLETED if outcomes[key] else FAILED)
        elif key == active_key:
            rows.append(RUNNING)
        else:
            rows.append(PENDING)
    return rows


def preview_stage(candidates, outcomes, preview_limit, running: bool) -> dict:
    keys = [_key(item) for item in candidates]
    completed = sum(1 for key in keys if outcomes.get(key))
    failed = [Path(key).name for key in keys if key in outcomes and not outcomes.get(key)]
    pending = [Path(key).name for key in keys if key not in outcomes]
    if running:
        status = RUNNING
    elif completed == int(preview_limit):
        status = "success"
    elif completed:
        status = "partial"
    else:
        status = FAILED
    return {
        "status": status,
        "rendered": completed,
        "requested": int(preview_limit),
        "attempted": len(candidates),
        "missing_candidates": max(0, int(preview_limit) - len(candidates)),
        "failed_variants": failed,
        "pending_variants": pending,
    }


def failed_preview_line(name: str) -> str:
    return f"{_STATE_PREFIX}{FAILED} {name}"


def classify_review_log(line: str):
    """Return ('ready', path) or ('failed', sequence name) for review-log lines."""
    text = line.strip()
    if text.startswith(_READY_PREFIX) and text.endswith(_READY_SUFFIX):
        return ("ready", text[len(_READY_PREFIX):-len(_READY_SUFFIX)])
    if text.startswith(_STATE_PREFIX):
        status, _, name = text[len(_STATE_PREFIX):].strip().partition(" ")
        if status == FAILED and name:
            return (FAILED, name)
    return None
