from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.musical_event_model import MusicalEvent, clamp01


_CANONICAL = {
    "kick": "kick",
    "bass_drum": "kick",
    "snare": "snare",
    "clap": "snare",
    "hat": "hat",
    "hihat": "hat",
    "hi_hat": "hat",
    "tom": "tom",
    "low_tom": "tom",
    "mid_tom": "tom",
    "high_tom": "tom",
    "crash": "crash",
    "ride": "ride",
    "cymbal": "cymbal",
    "drum": "drum",
    "drum_hit": "drum",
}


@dataclass(frozen=True)
class DrumFusionConfig:
    """Deterministic evidence-fusion settings for normalized drum events."""

    time_tolerance_ms: int = 45
    minimum_confidence: float = 0.45
    support_gain: float = 0.22
    strength_floor: float = 0.05


def canonical_drum_kind(event: MusicalEvent) -> str | None:
    value = (event.instrument or event.kind.removeprefix("drum_").removeprefix("stem_drum_")).lower()
    return _CANONICAL.get(value, value if value in _CANONICAL.values() else None)


def _fused_confidence(events: list[MusicalEvent], support_gain: float) -> float:
    ordered = sorted((clamp01(e.confidence) for e in events), reverse=True)
    if not ordered:
        return 0.0
    confidence = ordered[0]
    for extra in ordered[1:]:
        confidence += (1.0 - confidence) * support_gain * extra
    return clamp01(confidence)


def fuse_drum_events(
    events: Iterable[MusicalEvent],
    *,
    config: DrumFusionConfig = DrumFusionConfig(),
) -> tuple[list[MusicalEvent], dict[str, int]]:
    """Collapse same-type near-coincident hits while preserving independent evidence.

    Events from different drum classes never merge. Source labels and raw evidence
    are retained so downstream renderers can inspect provenance without knowing
    the provider-specific detector formats.
    """

    candidates = [
        e for e in events
        if (e.kind.startswith("drum_") or e.kind.startswith("stem_drum_"))
        and e.confidence >= config.minimum_confidence
        and canonical_drum_kind(e) is not None
    ]
    candidates.sort(key=lambda e: (e.time_ms, canonical_drum_kind(e) or "", -e.confidence))

    fused: list[MusicalEvent] = []
    suppressed = 0
    multi_source = 0

    for event in candidates:
        drum_kind = canonical_drum_kind(event)
        match_index = None
        for index in range(len(fused) - 1, -1, -1):
            prior = fused[index]
            if prior.instrument != drum_kind:
                if prior.time_ms < event.time_ms - config.time_tolerance_ms:
                    break
                continue
            if abs(prior.time_ms - event.time_ms) <= config.time_tolerance_ms:
                prior_sources = prior.metadata.get("sources", [])
                # Do not collapse two hits reported by the same provider; close
                # same-source transients can be genuine rapid drum strokes.
                if event.source not in prior_sources:
                    match_index = index
                    break
            if prior.time_ms < event.time_ms - config.time_tolerance_ms:
                break

        if match_index is None:
            fused.append(MusicalEvent(
                time_ms=event.time_ms,
                kind=f"drum_{drum_kind}",
                confidence=event.confidence,
                strength=max(config.strength_floor, event.strength),
                source="helix.drum_fusion",
                instrument=drum_kind,
                duration_ms=event.duration_ms,
                pitch_midi=event.pitch_midi,
                metadata={
                    "sources": [event.source],
                    "evidence": [event.to_dict()],
                },
            ))
            continue

        prior = fused[match_index]
        sources = list(prior.metadata.get("sources", []))
        if event.source not in sources:
            sources.append(event.source)
        evidence = list(prior.metadata.get("evidence", []))
        evidence.append(event.to_dict())
        merged = MusicalEvent(
            time_ms=round((prior.time_ms * prior.confidence + event.time_ms * event.confidence) /
                          max(prior.confidence + event.confidence, 1e-9)),
            kind=prior.kind,
            confidence=_fused_confidence(
                [MusicalEvent(prior.time_ms, prior.kind, prior.confidence),
                 event],
                config.support_gain,
            ),
            strength=clamp01(max(prior.strength, event.strength)),
            source="helix.drum_fusion",
            instrument=drum_kind,
            metadata={"sources": sources, "evidence": evidence},
        )
        fused[match_index] = merged
        suppressed += 1
        if len(sources) > 1:
            multi_source += 1

    fused.sort(key=lambda e: (e.time_ms, e.kind, -e.confidence))
    return fused, {
        "input_candidates": len(candidates),
        "fused_events": len(fused),
        "duplicates_suppressed": suppressed,
        "multi_source_events": multi_source,
    }
