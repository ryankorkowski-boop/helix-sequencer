"""Phrase-level choreography and motif reuse for Helix.

This layer makes repeated phrases feel intentionally related instead of random.
It detects repeated chorus/verse-like groups from effect rows, assigns motif IDs,
and reuses the same visual motif with small deterministic variations on repeats.

Placement in pipeline:
    realism rows -> cinematic arc -> motif reuse -> stabilizer -> xLights XML
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


MOTIF_SECTIONS = {"chorus", "verse", "build", "drop", "bridge", "finale"}
VARIATION_SEQUENCE = ("original", "brighter", "wider", "sparkle_accent", "finale_peak")


@dataclass(frozen=True)
class MotifConfig:
    phrase_window_seconds: float = 8.0
    repeated_phrase_tolerance: float = 0.42
    max_variation_boost: float = 0.18


def _section(row: dict) -> str:
    return str(row.get("section", row.get("intent", "unknown"))).lower().replace(" ", "_")


def _bucket_start(row: dict, window: float) -> int:
    start = float(row.get("start", 0.0))
    if window <= 0:
        return int(start)
    return int(start // window)


def _row_signature(row: dict) -> str:
    """Create a coarse phrase signature that survives small timing differences."""

    section = _section(row)
    stem = str(row.get("stem", "unknown")).lower()
    submodel = str(row.get("submodel", row.get("motion", "unknown"))).lower()
    intent = str(row.get("intent", "unknown")).lower()
    effect_family = str(row.get("effect", "unknown")).lower().split("_")[0]
    return f"{section}:{stem}:{submodel}:{intent}:{effect_family}"


def _phrase_key(rows: list[dict]) -> tuple[str, tuple[str, ...]]:
    if not rows:
        return ("unknown", tuple())
    section = _section(rows[0])
    signatures = sorted({_row_signature(row) for row in rows})
    return (section, tuple(signatures[:24]))


def _group_phrase_rows(rows: list[dict], config: MotifConfig) -> list[list[dict]]:
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        section = _section(row)
        if section not in MOTIF_SECTIONS:
            section = "support"
        key = (section, _bucket_start(row, config.phrase_window_seconds))
        groups.setdefault(key, []).append(row)
    return [groups[key] for key in sorted(groups, key=lambda item: (item[1], item[0]))]


def _variation_for_repeat(repeat_index: int) -> str:
    if repeat_index <= 1:
        return VARIATION_SEQUENCE[0]
    index = min(repeat_index - 1, len(VARIATION_SEQUENCE) - 1)
    return VARIATION_SEQUENCE[index]


def _apply_variation(row: dict, repeat_index: int, variation: str, config: MotifConfig) -> dict:
    out = dict(row)
    boost = min(config.max_variation_boost, max(0, repeat_index - 1) * 0.045)

    intensity = float(out.get("intensity", 0.5))
    coverage = float(out.get("coverageScale", 0.5))

    if variation == "brighter":
        intensity += boost
    elif variation == "wider":
        coverage += boost + 0.04
    elif variation == "sparkle_accent":
        intensity += boost * 0.7
        coverage += boost
        out["motifAccent"] = "sparkle"
    elif variation == "finale_peak":
        intensity += boost + 0.08
        coverage = max(coverage, 0.92)
        out["motifAccent"] = "finale_peak"

    out["intensity"] = round(max(0.0, min(1.0, intensity)), 3)
    out["coverageScale"] = round(max(0.0, min(1.0, coverage)), 3)
    out["motifVariation"] = variation
    out["motifRepeatIndex"] = repeat_index
    return out


def apply_phrase_motif_reuse(rows: Iterable[dict], config: MotifConfig = MotifConfig()) -> list[dict]:
    """Assign motif IDs and reuse repeated phrase motifs with slight variation."""

    row_list = [dict(row) for row in rows]
    if not row_list:
        return []

    phrase_groups = _group_phrase_rows(row_list, config)
    motif_ids_by_key: dict[tuple[str, tuple[str, ...]], str] = {}
    repeat_counts: dict[str, int] = {}
    output: list[dict] = []

    for group in phrase_groups:
        key = _phrase_key(group)
        if key not in motif_ids_by_key:
            motif_ids_by_key[key] = f"motif_{len(motif_ids_by_key) + 1:02d}_{key[0]}"
        motif_id = motif_ids_by_key[key]
        repeat_counts[motif_id] = repeat_counts.get(motif_id, 0) + 1
        repeat_index = repeat_counts[motif_id]
        variation = _variation_for_repeat(repeat_index)

        for row in group:
            out = _apply_variation(row, repeat_index, variation, config)
            out["motifId"] = motif_id
            out["phraseSignature"] = "|".join(key[1])[:512]
            output.append(out)

    return sorted(output, key=lambda row: (float(row.get("start", 0.0)), str(row.get("model", ""))))
