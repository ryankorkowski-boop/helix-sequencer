from __future__ import annotations

from bisect import bisect_left
from dataclasses import asdict, dataclass
from statistics import median
from typing import Any, Iterable, Sequence


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    if out != out:
        return default
    return out


def _as_float_list(values: Any) -> list[float]:
    if values is None:
        return []
    try:
        return [_safe_float(value) for value in list(values)]
    except Exception:
        return []


def _normalize(values: Sequence[float]) -> list[float]:
    clean = [_safe_float(value) for value in values]
    if not clean:
        return []
    lo = min(clean)
    hi = max(clean)
    if hi <= lo:
        return [_clamp01(value) for value in clean]
    span = hi - lo
    return [_clamp01((value - lo) / span) for value in clean]


def _times_ms_for(audio: Any, sample_count: int) -> list[int]:
    raw_times = _as_float_list(getattr(audio, "times_s", []))
    if raw_times:
        return [max(0, int(round(value * 1000.0))) for value in raw_times[:sample_count]]
    dur_ms = max(0, int(round(_safe_float(getattr(audio, "dur_s", 0.0)) * 1000.0)))
    if sample_count <= 1:
        return [0]
    step = max(1, dur_ms // max(1, sample_count - 1))
    return [idx * step for idx in range(sample_count)]


def _sample_series(times_ms: Sequence[int], values: Sequence[float], t_ms: int) -> float:
    if not times_ms or not values:
        return 0.0
    idx = bisect_left(times_ms, int(t_ms))
    candidates: list[int] = []
    if idx > 0:
        candidates.append(idx - 1)
    if idx < len(times_ms):
        candidates.append(idx)
    if not candidates:
        return _safe_float(values[-1])
    best = min(candidates, key=lambda item: abs(int(times_ms[item]) - int(t_ms)))
    return _safe_float(values[min(best, len(values) - 1)])


def _sorted_ms(values: Iterable[int] | None) -> list[int]:
    if not values:
        return []
    return sorted({int(value) for value in values if int(value) >= 0})


def _nearby_density(t_ms: int, marks_ms: Sequence[int], radius_ms: int) -> float:
    if not marks_ms:
        return 0.0
    left = bisect_left(marks_ms, int(t_ms) - int(radius_ms))
    right = bisect_left(marks_ms, int(t_ms) + int(radius_ms) + 1)
    count = max(0, right - left)
    expected = max(1.0, float(radius_ms) / 180.0)
    return _clamp01(count / expected)


def _median_beat_ms(beat_ms: Sequence[int]) -> int:
    clean = _sorted_ms(beat_ms)
    spans = [clean[idx + 1] - clean[idx] for idx in range(len(clean) - 1)]
    spans = [span for span in spans if 80 <= span <= 3000]
    return int(round(median(spans))) if spans else 500


@dataclass(frozen=True)
class EnergyPoint:
    time_ms: int
    energy: float
    macro_ramp: float
    micro_accent: float
    rms: float
    spectral_flux: float
    chroma_density: float
    percussion_density: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class MacroRamp:
    start_ms: int
    end_ms: int
    direction: str
    strength: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


@dataclass(frozen=True)
class MicroAccent:
    time_ms: int
    strength: float
    reason: str

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


@dataclass(frozen=True)
class EnergyCurve:
    points: tuple[EnergyPoint, ...]
    macro_ramps: tuple[MacroRamp, ...]
    micro_accents: tuple[MicroAccent, ...]

    @property
    def beat_energy(self) -> list[dict[str, float | int]]:
        return [{"time_ms": point.time_ms, "energy": point.energy} for point in self.points]

    def sample(self, t_ms: int) -> float:
        if not self.points:
            return 0.0
        times = [point.time_ms for point in self.points]
        values = [point.energy for point in self.points]
        return _sample_series(times, values, int(t_ms))

    def energy_between(self, start_ms: int, end_ms: int) -> float:
        if not self.points:
            return 0.0
        values = [point.energy for point in self.points if int(start_ms) <= point.time_ms < int(end_ms)]
        if not values:
            midpoint = int(round((int(start_ms) + int(end_ms)) / 2.0))
            return self.sample(midpoint)
        return sum(values) / float(len(values))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "helix.energy_model.v1",
            "point_count": len(self.points),
            "beat_energy": self.beat_energy,
            "macro_ramps": [ramp.to_dict() for ramp in self.macro_ramps],
            "micro_accents": [accent.to_dict() for accent in self.micro_accents],
        }


def _series_from_multiband(multiband: Any, name: str) -> tuple[list[int], list[float]]:
    values = _as_float_list(getattr(multiband, name, []))
    frame_times = _as_float_list(getattr(multiband, "frame_times_s", []))
    if not values or not frame_times:
        return [], []
    return [max(0, int(round(value * 1000.0))) for value in frame_times[: len(values)]], _normalize(values)


def _chroma_density(multiband: Any, t_ms: int) -> float:
    times, stability = _series_from_multiband(multiband, "chroma_stability01")
    if times and stability:
        return _clamp01(1.0 - _sample_series(times, stability, t_ms))
    summary = getattr(multiband, "descriptor_summary", {}) or {}
    if isinstance(summary, dict) and "chroma_stability_mean" in summary:
        return _clamp01(1.0 - _safe_float(summary.get("chroma_stability_mean"), 0.5))
    return 0.35


def build_energy_curve(
    *,
    audio: Any,
    beat_ms: Sequence[int],
    onset_ms: Sequence[int] | None = None,
    multiband: Any | None = None,
    percussion_ms: Sequence[int] | None = None,
) -> EnergyCurve:
    rms = _normalize(_as_float_list(getattr(audio, "rms01", [])))
    audio_times = _times_ms_for(audio, len(rms))
    flux_times, flux_values = _series_from_multiband(multiband, "spectral_flux01") if multiband is not None else ([], [])
    clean_beats = _sorted_ms(beat_ms)
    if not clean_beats:
        clean_beats = audio_times[:: max(1, len(audio_times) // 96)] if audio_times else [0]
    clean_onsets = _sorted_ms(onset_ms)
    clean_percussion = _sorted_ms(percussion_ms) or clean_onsets
    beat_span = _median_beat_ms(clean_beats)
    radius = max(120, min(420, int(beat_span * 0.55)))

    raw_points: list[dict[str, float | int]] = []
    for t_ms in clean_beats:
        rms_value = _sample_series(audio_times, rms, t_ms)
        flux_value = _sample_series(flux_times, flux_values, t_ms) if flux_values else _nearby_density(t_ms, _sorted_ms(getattr(multiband, "spectral_flux_marks", [])), radius)
        chroma_value = _chroma_density(multiband, t_ms) if multiband is not None else 0.35
        percussion_value = _nearby_density(t_ms, clean_percussion, radius)
        energy = _clamp01((0.48 * rms_value) + (0.22 * flux_value) + (0.18 * chroma_value) + (0.12 * percussion_value))
        raw_points.append(
            {
                "time_ms": int(t_ms),
                "energy": energy,
                "rms": rms_value,
                "spectral_flux": flux_value,
                "chroma_density": chroma_value,
                "percussion_density": percussion_value,
            }
        )

    values = [float(point["energy"]) for point in raw_points]
    points: list[EnergyPoint] = []
    accents: list[MicroAccent] = []
    for idx, point in enumerate(raw_points):
        prev_value = values[max(0, idx - 1)]
        next_value = values[min(len(values) - 1, idx + 1)]
        ramp = _clamp01(((next_value - prev_value) + 1.0) / 2.0) * 2.0 - 1.0
        local_start = max(0, idx - 2)
        local_end = min(len(values), idx + 3)
        local_mean = sum(values[local_start:local_end]) / float(max(1, local_end - local_start))
        accent_strength = _clamp01(max(float(point["energy"]) - local_mean, float(point["spectral_flux"]) - 0.62, float(point["percussion_density"]) - 0.58))
        points.append(
            EnergyPoint(
                time_ms=int(point["time_ms"]),
                energy=round(float(point["energy"]), 4),
                macro_ramp=round(float(ramp), 4),
                micro_accent=round(float(accent_strength), 4),
                rms=round(float(point["rms"]), 4),
                spectral_flux=round(float(point["spectral_flux"]), 4),
                chroma_density=round(float(point["chroma_density"]), 4),
                percussion_density=round(float(point["percussion_density"]), 4),
            )
        )
        if accent_strength >= 0.18:
            reason = "percussion" if float(point["percussion_density"]) >= 0.72 else "flux" if float(point["spectral_flux"]) >= 0.66 else "energy"
            accents.append(MicroAccent(time_ms=int(point["time_ms"]), strength=round(float(accent_strength), 4), reason=reason))

    ramps: list[MacroRamp] = []
    idx = 0
    while idx < len(points) - 1:
        direction = "up" if points[idx + 1].energy > points[idx].energy else "down"
        start = idx
        idx += 1
        while idx < len(points) - 1:
            next_direction = "up" if points[idx + 1].energy > points[idx].energy else "down"
            if next_direction != direction:
                break
            idx += 1
        end = idx
        strength = abs(points[end].energy - points[start].energy)
        if end > start and strength >= 0.12:
            ramps.append(MacroRamp(start_ms=points[start].time_ms, end_ms=points[end].time_ms, direction=direction, strength=round(strength, 4)))
    return EnergyCurve(points=tuple(points), macro_ramps=tuple(ramps), micro_accents=tuple(accents))
