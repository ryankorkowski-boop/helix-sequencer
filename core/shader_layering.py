from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.lazy_imports import LazyModule

np = LazyModule("numpy")


@dataclass
class LayerProfile:
    name: str
    blend_mode: str
    role: str
    density: float
    brightness: float
    motion: float
    complexity: float


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _blend_conflict_score(a: str, b: str) -> float:
    pair = {a.lower(), b.lower()}
    if pair == {"additive", "additive"}:
        return 0.88
    if pair == {"screen", "additive"}:
        return 0.72
    if pair == {"overlay", "additive"}:
        return 0.64
    if pair == {"multiply", "additive"}:
        return 0.42
    if pair == {"normal", "normal"}:
        return 0.48
    return 0.35


def compatibility_score(layers: list[LayerProfile]) -> float:
    if not layers:
        return 0.0
    if len(layers) == 1:
        return 1.0
    density_mean = float(np.mean([layer.density for layer in layers]))
    brightness_mean = float(np.mean([layer.brightness for layer in layers]))
    complexity_mean = float(np.mean([layer.complexity for layer in layers]))
    conflict = 0.0
    checks = 0
    for i in range(len(layers)):
        for j in range(i + 1, len(layers)):
            checks += 1
            conflict += _blend_conflict_score(layers[i].blend_mode, layers[j].blend_mode)
    conflict = (conflict / checks) if checks else 0.0
    raw = (
        (0.46 * (1.0 - conflict))
        + (0.20 * (1.0 - min(1.0, density_mean)))
        + (0.16 * (1.0 - min(1.0, brightness_mean)))
        + (0.18 * (1.0 - min(1.0, complexity_mean)))
    )
    return _clamp01(raw)


def coordinate_uniforms(
    trajectory: list[dict[str, Any]],
    *,
    focus_depth: float = 0.5,
) -> dict[str, list[float]]:
    if not trajectory:
        return {"u_focus_x": [], "u_focus_y": [], "u_slice_z": [], "u_path_speed": []}
    x = np.asarray([float(point.get("x", 0.0)) for point in trajectory], dtype=float)
    y = np.asarray([float(point.get("y", 0.0)) for point in trajectory], dtype=float)
    z = np.asarray([float(point.get("z", 0.0)) for point in trajectory], dtype=float)
    if len(z) > 1:
        speed = np.abs(np.gradient(z))
    else:
        speed = np.zeros_like(z)
    fx = np.clip((x - np.min(x)) / max(1e-9, float(np.max(x) - np.min(x))), 0.0, 1.0)
    fy = np.clip((y - np.min(y)) / max(1e-9, float(np.max(y) - np.min(y))), 0.0, 1.0)
    fz = np.clip((z - np.min(z)) / max(1e-9, float(np.max(z) - np.min(z))), 0.0, 1.0)
    slice_z = np.clip((0.65 * fz) + (0.35 * _clamp01(focus_depth)), 0.0, 1.0)
    path_speed = np.clip(speed / max(1e-9, float(np.max(speed))), 0.0, 1.0)
    return {
        "u_focus_x": [float(round(v, 6)) for v in fx.tolist()],
        "u_focus_y": [float(round(v, 6)) for v in fy.tolist()],
        "u_slice_z": [float(round(v, 6)) for v in slice_z.tolist()],
        "u_path_speed": [float(round(v, 6)) for v in path_speed.tolist()],
    }


def recommend_layer_stack(
    *,
    energy: float,
    onset: float,
    spread: float,
    contrast: float,
) -> list[LayerProfile]:
    energy = _clamp01(energy)
    onset = _clamp01(onset)
    spread = _clamp01(spread)
    contrast = _clamp01(contrast)
    base = LayerProfile(
        name="base_field",
        blend_mode="Normal",
        role="base",
        density=0.22 + (0.26 * spread),
        brightness=0.24 + (0.32 * energy),
        motion=0.18 + (0.22 * spread),
        complexity=0.20 + (0.25 * contrast),
    )
    mid = LayerProfile(
        name="mid_detail",
        blend_mode="Overlay" if contrast >= 0.42 else "Screen",
        role="mid",
        density=0.24 + (0.40 * contrast),
        brightness=0.20 + (0.30 * energy),
        motion=0.22 + (0.42 * onset),
        complexity=0.24 + (0.32 * spread),
    )
    top = LayerProfile(
        name="accent_transients",
        blend_mode="Additive" if onset >= 0.36 else "Screen",
        role="accent",
        density=0.10 + (0.45 * onset),
        brightness=0.25 + (0.55 * energy),
        motion=0.40 + (0.45 * onset),
        complexity=0.28 + (0.42 * contrast),
    )
    return [base, mid, top]
