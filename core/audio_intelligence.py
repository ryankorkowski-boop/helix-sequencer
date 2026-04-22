from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import random
import xml.etree.ElementTree as ET

import numpy as np

from core import model_parser as xmp

try:
    import librosa
except Exception:  # pragma: no cover - optional dependency in some environments
    librosa = None  # type: ignore[assignment]


@dataclass
class LyricEvent:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class StemAnalysis:
    source: str
    stems: dict[str, Path]
    bass_peaks_ms: list[int]
    vocal_peaks_ms: list[int]
    drum_kicks_ms: list[int]
    drum_snares_ms: list[int]
    drum_hats_ms: list[int]


def normalize_name(name: str) -> str:
    return " ".join((name or "").lower().replace("_", " ").replace("-", " ").split())


def _log(log_fn: Callable[[str], None] | None, text: str) -> None:
    if log_fn is None:
        return
    try:
        log_fn(text)
    except Exception:
        pass


def _compress_ms(values: list[int], min_gap_ms: int) -> list[int]:
    if not values:
        return []
    ordered = sorted(int(value) for value in values)
    out = [ordered[0]]
    last = ordered[0]
    for value in ordered[1:]:
        if value - last >= int(min_gap_ms):
            out.append(value)
            last = value
    return out


def _peak_times_ms(times_s: np.ndarray, env: np.ndarray, threshold: float, wait: int) -> list[int]:
    if librosa is None or env.size == 0 or times_s.size == 0:
        return []
    peaks = librosa.util.peak_pick(env, pre_max=2, post_max=2, pre_avg=4, post_avg=4, delta=threshold, wait=max(1, wait))
    out: list[int] = []
    for idx in peaks:
        if 0 <= idx < len(times_s):
            out.append(int(round(float(times_s[idx]) * 1000.0)))
    return out


def _analyze_drum_events(audio_path: Path) -> tuple[list[int], list[int], list[int]]:
    if librosa is None or not audio_path.exists():
        return ([], [], [])
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=False)
    times = librosa.frames_to_time(frames, sr=sr)

    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr)

    kicks: list[int] = []
    snares: list[int] = []
    hats: list[int] = []
    for ts in times:
        idx = int(np.searchsorted(cent_times, ts))
        idx = max(0, min(len(cent) - 1, idx))
        centroid = float(cent[idx]) if len(cent) else 0.0
        ms = int(round(float(ts) * 1000.0))
        if centroid >= 4200:
            hats.append(ms)
        elif centroid >= 1800:
            snares.append(ms)
        else:
            kicks.append(ms)
    return (_compress_ms(kicks, 40), _compress_ms(snares, 32), _compress_ms(hats, 24))


def _analyze_peak_events(audio_path: Path, kind: str) -> list[int]:
    if librosa is None or not audio_path.exists():
        return []
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    if kind == "bass":
        threshold = float(np.quantile(rms, 0.78)) if rms.size else 0.0
        wait = 7
        gap = 70
    else:
        threshold = float(np.quantile(rms, 0.70)) if rms.size else 0.0
        wait = 9
        gap = 95
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    peaks = _peak_times_ms(np.asarray(times), np.asarray(rms), threshold=max(0.01, threshold * 0.20), wait=wait)
    return _compress_ms(peaks, gap)


def build_stem_analysis(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    cache_dir: Path,
    log_fn: Callable[[str], None] | None = None,
) -> StemAnalysis:
    """Rule-based stem/event fallback used by the effect engine.

    This intentionally keeps a stable local path first. Network/API integrations can
    be layered back in separately without breaking the baseline engine.
    """
    _ = (use_moises, api_key, cache_dir)

    if not audio_path.exists():
        _log(log_fn, f"Audio analysis skipped; file does not exist: {audio_path}")
        return StemAnalysis(
            source="direct",
            stems={},
            bass_peaks_ms=[],
            vocal_peaks_ms=[],
            drum_kicks_ms=[],
            drum_snares_ms=[],
            drum_hats_ms=[],
        )

    kicks, snares, hats = _analyze_drum_events(audio_path)
    bass_peaks = _analyze_peak_events(audio_path, "bass")
    vocal_peaks = _analyze_peak_events(audio_path, "vocals")
    return StemAnalysis(
        source="direct",
        stems={},
        bass_peaks_ms=bass_peaks,
        vocal_peaks_ms=vocal_peaks,
        drum_kicks_ms=kicks,
        drum_snares_ms=snares,
        drum_hats_ms=hats,
    )


def extract_lyrics_events(
    audio_path: Path,
    use_moises: bool,
    api_key: str | None,
    log_fn: Callable[[str], None] | None = None,
) -> list[LyricEvent]:
    _ = (audio_path, use_moises, api_key)
    _log(log_fn, "Lyrics extraction is currently disabled in the rule-based baseline.")
    return []


def parse_layout_coordinates(layout_path: Path, available_names: list[str]) -> dict[str, tuple[float, float]]:
    """Parse xLights layout model centers (x,y) for spatial chase routing."""
    if not layout_path.exists():
        return {}
    try:
        parsed = xmp.parse_layout(layout_path)
        return parsed.coordinate_map(available_names)
    except Exception:
        tree = ET.parse(layout_path)
        root = tree.getroot()
        available_map = {normalize_name(name): name for name in available_names}
        out: dict[str, tuple[float, float]] = {}

        model_root = root.find(".//models")
        if model_root is not None:
            for model in model_root.findall("model"):
                name = (model.attrib.get("name") or "").strip()
                if not name:
                    continue
                key = normalize_name(name)
                actual = available_map.get(key)
                if not actual:
                    continue
                try:
                    x = float(model.attrib.get("WorldPosX", "0") or 0)
                    y = float(model.attrib.get("WorldPosY", "0") or 0)
                    dx = float(model.attrib.get("X2", "0") or 0)
                    dy = float(model.attrib.get("Y2", "0") or 0)
                except Exception:
                    continue
                out[actual] = (x + (dx * 0.5), y + (dy * 0.5))

        group_root = root.find(".//modelGroups")
        if group_root is not None:
            for group in group_root.findall("modelGroup"):
                name = (group.attrib.get("name") or "").strip()
                if not name:
                    continue
                key = normalize_name(name)
                actual = available_map.get(key)
                if not actual or actual in out:
                    continue
                try:
                    x = float(group.attrib.get("centrex", "0") or 0)
                    y = float(group.attrib.get("centrey", "0") or 0)
                except Exception:
                    continue
                out[actual] = (x, y)

        return out


def ordered_spatial_path(
    models: list[str],
    coords: dict[str, tuple[float, float]],
    chase_style: str,
    rng,
) -> list[str]:
    if not models:
        return []
    usable = [name for name in models if name in coords]
    if len(usable) < 2:
        return models[:]

    style = chase_style.strip().lower()
    if style in {"none", ""}:
        return models[:]

    if style == "left_to_right":
        return sorted(usable, key=lambda name: (coords[name][0], coords[name][1], name.lower()))

    if style == "top_to_bottom":
        return sorted(usable, key=lambda name: (coords[name][1], coords[name][0], name.lower()))

    if style == "radial_out":
        xs = [coords[name][0] for name in usable]
        ys = [coords[name][1] for name in usable]
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        return sorted(usable, key=lambda name: ((coords[name][0] - cx) ** 2 + (coords[name][1] - cy) ** 2, name.lower()))

    if style == "group_to_group":
        quadrants: dict[int, list[str]] = {0: [], 1: [], 2: [], 3: []}
        xs = [coords[name][0] for name in usable]
        ys = [coords[name][1] for name in usable]
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        for name in usable:
            x, y = coords[name]
            quadrant = 0
            if x >= cx and y >= cy:
                quadrant = 1
            elif x < cx and y >= cy:
                quadrant = 2
            elif x < cx and y < cy:
                quadrant = 3
            quadrants[quadrant].append(name)
        ordered: list[str] = []
        for quadrant in (0, 1, 2, 3):
            ordered.extend(sorted(quadrants[quadrant], key=lambda value: value.lower()))
        return ordered if ordered else usable

    if style == "random_walk":
        randomizer = rng if rng is not None else random
        remaining = usable[:]
        start = randomizer.choice(remaining)
        walk = [start]
        remaining.remove(start)
        while remaining:
            cur = walk[-1]
            cx, cy = coords[cur]
            nxt = min(remaining, key=lambda name: ((coords[name][0] - cx) ** 2 + (coords[name][1] - cy) ** 2))
            walk.append(nxt)
            remaining.remove(nxt)
        return walk

    if style == "wave":
        xs = [coords[name][0] for name in usable]
        min_x, max_x = min(xs), max(xs)
        span = max(0.001, max_x - min_x)
        return sorted(
            usable,
            key=lambda name: (
                coords[name][0],
                np.sin(((coords[name][0] - min_x) / span) * np.pi * 2.0) + coords[name][1] * 0.04,
                name.lower(),
            ),
        )

    return usable


def nearest_mark_distance_ms(target_ms: int, marks: list[int]) -> int | None:
    if not marks:
        return None
    idx = bisect_left(marks, int(target_ms))
    best: int | None = None
    for probe in (idx - 1, idx):
        if 0 <= probe < len(marks):
            dist = abs(int(marks[probe]) - int(target_ms))
            if best is None or dist < best:
                best = dist
    return best


def proximity_confidence(target_ms: int, marks: list[int], window_ms: int, floor: float = 0.0) -> float:
    distance = nearest_mark_distance_ms(target_ms, marks)
    if distance is None:
        return float(np.clip(floor, 0.0, 1.0))
    if window_ms <= 0:
        return 1.0 if distance == 0 else float(np.clip(floor, 0.0, 1.0))
    score = 1.0 - min(1.0, float(distance) / float(window_ms))
    return float(np.clip(max(floor, score), 0.0, 1.0))
