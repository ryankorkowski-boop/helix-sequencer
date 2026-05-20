from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

from core.feature_state import FeatureStateFrame


_ALLOWED_MOTIFS = ("wave_sweep", "spiral", "pulse_cascade", "orbit", "sparkle_field")


@dataclass(frozen=True)
class BirdsongRuntimeConfig:
    """Conservative, explicit gate for the Issue #2 generative path."""

    enabled: bool = False
    min_onset: float = 0.55
    min_energy: float = 0.25
    duration_ms: int = 180
    max_targets_per_frame: int = 3


@dataclass(frozen=True)
class BirdsongSequenceRow:
    model: str
    start_ms: int
    end_ms: int
    label: str
    effect: str
    motif: str
    intensity: float


def generate_birdsong_rows(
    frames: Sequence[FeatureStateFrame],
    model_names: Sequence[str],
    *,
    config: BirdsongRuntimeConfig | None = None,
) -> list[BirdsongSequenceRow]:
    """Turn feature-state frames into deterministic placement rows.

    This is a guarded adapter for Issue #2. It intentionally does not touch the
    main effect engine by default. Callers must pass config.enabled=True before
    any rows are emitted, which lets the new generative path be tested without
    altering stable v27.3 output.
    """

    cfg = config or BirdsongRuntimeConfig()
    if not cfg.enabled:
        return []

    models = _clean_models(model_names)
    if not frames or not models:
        return []

    duration_ms = max(50, int(cfg.duration_ms))
    target_cap = max(1, int(cfg.max_targets_per_frame))
    rows: list[BirdsongSequenceRow] = []

    for index, frame in enumerate(frames):
        energy = _finite01(frame.energy_smooth if frame.energy_smooth > 0 else frame.energy)
        onset = _finite01(frame.onset)
        if energy < cfg.min_energy and onset < cfg.min_onset:
            continue

        motif = _motif_for_frame(frame)
        effect = _effect_for_motif(motif, frame)
        start_ms = max(0, int(round(frame.time_s * 1000.0)))
        intensity = _finite01(max(energy, onset))
        selected = _select_models(models, frame, index, limit=target_cap)
        for step, model in enumerate(selected):
            st = start_ms + (step * 24)
            en = st + duration_ms + int(round(intensity * 80.0))
            rows.append(
                BirdsongSequenceRow(
                    model=model,
                    start_ms=st,
                    end_ms=max(st + 1, en),
                    label="birdsong_issue2",
                    effect=effect,
                    motif=motif,
                    intensity=intensity,
                )
            )
    return rows


def emit_birdsong_rows(rows: Iterable[BirdsongSequenceRow], add_model) -> int:
    """Emit rows through the existing add_model callback contract."""

    count = 0
    for row in rows:
        add_model(
            row.model,
            int(row.start_ms),
            int(row.end_ms),
            row.label,
            eff=row.effect,
            stem="other",
        )
        count += 1
    return count


def _clean_models(model_names: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in model_names:
        model = str(raw).strip()
        key = model.lower()
        if not model or key in seen:
            continue
        seen.add(key)
        out.append(model)
    return out


def _motif_for_frame(frame: FeatureStateFrame) -> str:
    low = _finite01(frame.low)
    mid = _finite01(frame.mid)
    high = _finite01(frame.high)
    onset = _finite01(frame.onset)
    beat_phase = _finite01(frame.beat_phase)
    if high >= max(low, mid) and high >= 0.35:
        return "sparkle_field"
    if low >= max(mid, high) and onset >= 0.45:
        return "pulse_cascade"
    if 0.35 <= beat_phase <= 0.65:
        return "orbit"
    if mid >= low and mid >= high:
        return "spiral"
    return "wave_sweep"


def _effect_for_motif(motif: str, frame: FeatureStateFrame) -> str:
    if motif == "sparkle_field":
        return "Twinkle"
    if motif == "pulse_cascade":
        return "On" if frame.onset >= 0.70 else "Ramp"
    if motif == "orbit":
        return "Spirals"
    if motif == "spiral":
        return "Wave"
    return "Single Strand"


def _select_models(models: Sequence[str], frame: FeatureStateFrame, frame_index: int, *, limit: int) -> list[str]:
    if not models:
        return []
    count = min(len(models), max(1, limit))
    if frame.high >= max(frame.low, frame.mid):
        start = (frame_index * 2) % len(models)
    elif frame.low >= max(frame.mid, frame.high):
        start = frame_index % len(models)
    else:
        start = (frame_index + int(round(frame.beat_phase * len(models)))) % len(models)
    return [models[(start + offset) % len(models)] for offset in range(count)]


def _finite01(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(out):
        return 0.0
    if out <= 0.0:
        return 0.0
    if out >= 1.0:
        return 1.0
    return out


__all__ = [
    "BirdsongRuntimeConfig",
    "BirdsongSequenceRow",
    "emit_birdsong_rows",
    "generate_birdsong_rows",
]
