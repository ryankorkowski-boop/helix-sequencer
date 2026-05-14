from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Sequence


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if out != out:
        return default
    return out


@dataclass(frozen=True)
class MotifFingerprint:
    key: str
    contour: str
    interval_signature: tuple[int, ...]
    rhythm_signature: tuple[int, ...]
    strength: float

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["interval_signature"] = list(self.interval_signature)
        data["rhythm_signature"] = list(self.rhythm_signature)
        return data


@dataclass(frozen=True)
class MotifMatch:
    fingerprint: MotifFingerprint
    occurrences: tuple[dict[str, object], ...]
    hook_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "fingerprint": self.fingerprint.to_dict(),
            "occurrences": [dict(item) for item in self.occurrences],
            "repeat_count": len(self.occurrences),
            "hook_score": self.hook_score,
        }


def _notes_from_event(event: Any) -> list[tuple[int, float]]:
    notes = getattr(event, "notes", []) or []
    out: list[tuple[int, float]] = []
    for item in notes:
        try:
            midi, strength = item
        except Exception:
            continue
        out.append((_safe_int(midi), max(0.0, min(1.0, _safe_float(strength, 0.5)))))
    return sorted(out, key=lambda item: item[0])


def fingerprint_event(event: Any) -> MotifFingerprint:
    notes = _notes_from_event(event)
    midis = [midi for midi, _strength in notes]
    if not midis:
        intervals: tuple[int, ...] = ()
        contour = "rest"
    else:
        root = midis[0]
        intervals = tuple(max(-24, min(24, midi - root)) for midi in midis[:6])
        if len(midis) == 1:
            contour = "single"
        elif midis[-1] > midis[0]:
            contour = "rise"
        elif midis[-1] < midis[0]:
            contour = "fall"
        else:
            contour = "arc"
    start_ms = _safe_int(getattr(event, "start_ms", 0))
    end_ms = max(start_ms + 1, _safe_int(getattr(event, "end_ms", start_ms + 1), start_ms + 1))
    duration = max(1, end_ms - start_ms)
    rhythm = (min(8, max(1, int(round(duration / 120.0)))), min(6, max(1, len(notes))))
    strengths = [strength for _midi, strength in notes]
    strength = sum(strengths) / float(len(strengths)) if strengths else 0.0
    key = f"{contour}:{','.join(str(value) for value in intervals)}:{','.join(str(value) for value in rhythm)}"
    return MotifFingerprint(
        key=key,
        contour=contour,
        interval_signature=intervals,
        rhythm_signature=rhythm,
        strength=round(float(strength), 4),
    )


def detect_motifs(note_events: Sequence[Any], *, min_repeats: int = 2) -> list[MotifMatch]:
    buckets: dict[str, list[tuple[Any, MotifFingerprint]]] = {}
    for event in note_events:
        fingerprint = fingerprint_event(event)
        if fingerprint.contour == "rest":
            continue
        buckets.setdefault(fingerprint.key, []).append((event, fingerprint))

    matches: list[MotifMatch] = []
    for key, items in buckets.items():
        if len(items) < int(min_repeats):
            continue
        fingerprint = items[0][1]
        parts = Counter(str(getattr(event, "part", getattr(event, "section", "")) or "") for event, _fp in items)
        occurrences = tuple(
            {
                "start_ms": _safe_int(getattr(event, "start_ms", 0)),
                "end_ms": _safe_int(getattr(event, "end_ms", 0)),
                "part": str(getattr(event, "part", "")),
                "section": str(getattr(event, "section", "")),
            }
            for event, _fp in items
        )
        spread_bonus = min(0.25, max(0.0, (len(parts) - 1) * 0.08))
        hook_score = min(1.0, (len(items) / 6.0) + (fingerprint.strength * 0.34) + spread_bonus)
        matches.append(MotifMatch(fingerprint=fingerprint, occurrences=occurrences, hook_score=round(float(hook_score), 4)))
    matches.sort(key=lambda item: (-item.hook_score, item.fingerprint.key))
    return matches


def build_motif_report(note_events: Sequence[Any], *, min_repeats: int = 2) -> dict[str, object]:
    matches = detect_motifs(note_events, min_repeats=min_repeats)
    return {
        "schema": "helix.motif_fingerprinting.v1",
        "event_count": len(note_events),
        "motif_count": len(matches),
        "hooks": [match.to_dict() for match in matches[:16]],
    }
