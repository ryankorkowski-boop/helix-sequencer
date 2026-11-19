"""Conservative, bounded event provenance for Helix sequence diagnostics.

Mixed harmonic estimates are explicitly labeled unknown; never infer a drum
component or instrument from pitch alone.
"""
from __future__ import annotations

import math
from typing import Any


def _finite_confidence(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(1.0, number)), 4) if math.isfinite(number) else None


def summarize_note_provenance(events: list[Any], *, limit: int = 512) -> dict[str, Any]:
    """Capture bounded diagnostic evidence without altering event placement."""
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    sample: list[dict[str, Any]] = []
    unknown = 0
    for event in events:
        owner = getattr(event, "source_owner", None)
        if owner is None:
            method = getattr(event, "ownership", None)
            owner = method() if callable(method) else None
        if isinstance(owner, dict):
            performer = owner.get("performer")
            confidence = _finite_confidence(owner.get("confidence"))
            source_id = str(owner.get("source_id") or "")
            origin = str(owner.get("origin") or "fallback")
        elif owner is not None:
            performer = getattr(owner, "performer", None)
            confidence = _finite_confidence(getattr(owner, "confidence", None))
            source_id = str(getattr(owner, "source_id", "") or "")
            origin = str(getattr(owner, "origin", "fallback"))
        else:
            performer, confidence, source_id, origin = None, None, "", "fallback"
        # A label alone is not proof of ownership. Invalid confidence or
        # fallback provenance must remain unresolved in diagnostics.
        if (performer is None or performer == "unknown"
                or confidence is None or confidence <= 0.0
                or origin not in ("detected", "estimated")):
            unknown += 1
        if len(sample) < limit:
            sample.append({
                "time_ms": int(getattr(event, "start_ms", getattr(event, "timestamp_ms", 0)) or 0),
                "source_stem": str(getattr(event, "source_stem", "") or source_id or "mixed_unknown"),
                "performer": performer,
                "confidence": confidence,
                "origin": origin,
                "features": {
                    "pitch_count": len(getattr(event, "notes", []) or []) if hasattr(event, "notes") else (1 if hasattr(event, "midi_note") else 0),
                    "section": str(getattr(event, "section", "") or ""),
                },
            })
    return {
        "schema": "helix.event_provenance.v1",
        "total_events": len(events),
        "unknown_ownership_events": unknown,
        "sample_limit": limit,
        "sample_truncated": len(events) > limit,
        "sample": sample,
    }
