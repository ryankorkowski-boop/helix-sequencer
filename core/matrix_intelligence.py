from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
from core import shader_layering


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return default


def _part_label(part: Any) -> str:
    return str(getattr(part, "label", "UNKNOWN")).upper()


def _part_start_ms(part: Any) -> int:
    return _safe_int(getattr(part, "start_ms", 0), 0)


def _part_end_ms(part: Any) -> int:
    return max(_part_start_ms(part) + 1, _safe_int(getattr(part, "end_ms", 0), _part_start_ms(part) + 1))


def _part_energy(part: Any) -> float:
    return _safe_float(getattr(part, "energy", 0.0), 0.0)


def _marks_in_window(marks: list[int], start_ms: int, end_ms: int) -> int:
    if not marks:
        return 0
    return sum(1 for t in marks if start_ms <= t < end_ms)


def _curve_triplet(start_ms: int, end_ms: int, start_value: float, peak_value: float, end_value: float) -> list[list[float]]:
    st = max(0.0, start_ms / 1000.0)
    en = max(st + 0.001, end_ms / 1000.0)
    mid = st + ((en - st) * 0.55)
    return [
        [round(st, 3), round(float(start_value), 4)],
        [round(mid, 3), round(float(peak_value), 4)],
        [round(en, 3), round(float(end_value), 4)],
    ]


def _hex_color(rgb: tuple[float, float, float]) -> str:
    r = int(_clamp(round(rgb[0]), 0, 255))
    g = int(_clamp(round(rgb[1]), 0, 255))
    b = int(_clamp(round(rgb[2]), 0, 255))
    return f"#{r:02X}{g:02X}{b:02X}"


def _mix_hex(colors: list[tuple[float, float, float]]) -> str:
    if not colors:
        return "#A0A8FF"
    arr = np.asarray(colors, dtype=float)
    return _hex_color((float(np.mean(arr[:, 0])), float(np.mean(arr[:, 1])), float(np.mean(arr[:, 2]))))


def discover_matrix_targets(parsed_layout: Any) -> list[dict[str, Any]]:
    if parsed_layout is None:
        return []
    out: list[dict[str, Any]] = []
    for model in getattr(parsed_layout, "models", {}).values():
        if getattr(model, "is_submodel", False):
            continue
        if str(getattr(model, "type", "")).lower() != "matrix":
            continue
        center = (0.0, 0.0, 0.0)
        try:
            center = getattr(model, "center")()
        except Exception:
            pass
        width = max(1, _safe_int(getattr(model, "strings", 1), 1))
        height = max(1, _safe_int(getattr(model, "nodes_per_string", 1), 1))
        pixels = max(1, _safe_int(getattr(model, "total_pixels", width * height), width * height))
        out.append(
            {
                "name": str(getattr(model, "name", "matrix")),
                "width": width,
                "height": height,
                "pixels": pixels,
                "orientation": str(getattr(model, "orientation", "") or ""),
                "center_x": _safe_float(center[0], 0.0),
                "center_y": _safe_float(center[1], 0.0),
            }
        )
    out.sort(key=lambda item: (-int(item["pixels"]), str(item["name"]).lower()))
    return out


def _spectrogram_mapping(width: int, height: int) -> str:
    if width >= int(height * 1.25):
        return "horizontal"
    if height >= int(width * 1.25):
        return "vertical"
    return "radial"


def _scene_shader(genre: str, mood: str, scene_mode: str, dominant_band: str, mapping: str) -> str:
    scene = (scene_mode or "balanced").lower()
    band = (dominant_band or "mid").lower()
    genre_key = (genre or "pop").lower()
    mood_key = (mood or "balanced").lower()
    if scene in {"build_tension", "build"}:
        return "ripple.glsl" if mapping == "radial" else "waveform_2d.glsl"
    if scene in {"wide_bright", "drop", "peak"}:
        if genre_key in {"edm", "hip_hop", "rock"}:
            return "radial_pulse.glsl"
        return "spectrum_bars.glsl"
    if scene in {"tight_minimal", "ambient_minimal", "breakdown"}:
        return "caustics.glsl" if mood_key in {"brooding", "calm"} else "plasma.glsl"
    if band in {"sub_bass", "bass"}:
        return "radial_pulse.glsl"
    if band == "high":
        return "twinkle_field.glsl"
    return "spectrum_bars.glsl"


def _compute_arousal_valence(summary: dict[str, float], tempo_bpm: float, rms_mean: float, percussive_ratio: float) -> tuple[float, float]:
    centroid = _safe_float(summary.get("centroid_mean"), 0.0)
    flux_density = _safe_float(summary.get("flux_density"), 0.0)
    chroma_stability = _safe_float(summary.get("chroma_stability_mean"), 0.0)
    tonnetz_motion = _safe_float(summary.get("tonnetz_motion_mean"), 0.0)
    contrast = _safe_float(summary.get("contrast_mean"), 0.0)
    arousal = _clamp(
        (0.26 * _clamp(tempo_bpm / 160.0, 0.0, 1.0))
        + (0.28 * _clamp(rms_mean, 0.0, 1.0))
        + (0.20 * _clamp(flux_density / 100.0, 0.0, 1.0))
        + (0.16 * _clamp(percussive_ratio, 0.0, 1.0))
        + (0.10 * _clamp(centroid, 0.0, 1.0)),
        0.0,
        1.0,
    )
    valence = _clamp(
        (0.38 * _clamp(chroma_stability, 0.0, 1.0))
        + (0.26 * (1.0 - _clamp(tonnetz_motion, 0.0, 1.0)))
        + (0.18 * _clamp(centroid, 0.0, 1.0))
        + (0.10 * (1.0 - _clamp(contrast, 0.0, 1.0)))
        + (0.08 * (0.50 + (_clamp(tempo_bpm / 200.0, 0.0, 1.0) * 0.5))),
        0.0,
        1.0,
    )
    return arousal, valence


def _mood_description(arousal: float, valence: float) -> str:
    if arousal >= 0.78 and valence >= 0.55:
        return "high-energy euphoric push"
    if arousal >= 0.78 and valence < 0.55:
        return "high-energy aggressive drop"
    if arousal <= 0.34 and valence <= 0.45:
        return "calm but dark atmospheric section"
    if arousal <= 0.34 and valence > 0.45:
        return "calm melodic verse"
    if valence < 0.45:
        return "tense groove with moderate lift"
    return "balanced melodic momentum"


def _load_blend_overrides(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _blend_pick(
    layer_role: str,
    scene_mode: str,
    arousal: float,
    valence: float,
    matrix_pixels: int,
    *,
    genre: str,
    mood: str,
    overrides: dict[str, Any],
) -> tuple[str, int, bool, str]:
    role = layer_role.lower()
    scene = scene_mode.lower()
    mood_map = ((overrides.get("mood_overrides") or {}).get(mood.lower()) or {}) if overrides else {}
    genre_map = ((overrides.get("genre_overrides") or {}).get(genre.lower()) or {}) if overrides else {}
    if role in mood_map:
        raw = mood_map.get(role)
        mix = int(_clamp(_safe_int(mood_map.get(f"{role}_mix", 62), 62), 0, 100))
        return str(raw), mix, True, "Blend override applied from mood_overrides."
    if role in genre_map:
        raw = genre_map.get(role)
        mix = int(_clamp(_safe_int(genre_map.get(f"{role}_mix", 62), 62), 0, 100))
        return str(raw), mix, True, "Blend override applied from genre_overrides."
    if role == "base":
        if arousal <= 0.35:
            return "Normal", 46, False, "Low arousal keeps the ambient base clean and stable."
        if valence < 0.45:
            return "Multiply", 52, False, "Lower valence darkens underlay for depth."
        return "Normal", 58, False, "Base layer carries the core canvas without overmixing."
    if role == "mid":
        if scene in {"build_tension", "build"}:
            return "Overlay", 58, True, "Build section uses contrast-driven mid texture."
        if arousal >= 0.72 and valence >= 0.52:
            return "Screen", 62, True, "Energetic and bright section benefits from Screen lift."
        if valence < 0.45:
            return "Multiply", 48, False, "Calmer mood keeps mid layer subtle."
        return "Overlay", 54, True, "Overlay balances color pop with scene detail."
    if scene in {"drop", "wide_bright"} or arousal >= 0.72:
        mix = 76 if matrix_pixels <= 4000 else 68
        return "Additive", mix, True, "Top transient layer pushes impact for drops and accents."
    if scene in {"ambient_minimal", "breakdown"}:
        return "Screen", 44, True, "Breakdown keeps highlights soft without clipping."
    return "Screen", 56, True, "Accent layer uses Screen to avoid harsh overdraw."


def _gpu_layer_limit(matrix_pixels: int, loudness: float, scene_mode: str) -> int:
    limit = 4 if matrix_pixels <= 4000 else 3
    if loudness <= 0.20 or scene_mode in {"ambient_minimal", "tight_minimal", "breakdown"}:
        return min(limit, 2)
    if scene_mode in {"build_tension", "wide_bright"} and loudness >= 0.55:
        return limit
    return min(limit, 3)


def analyze_video_reactivity(video_path: Path | None, parts: list[Any], log_fn: Callable[[str], None] | None = None) -> dict[str, Any]:
    if video_path is None:
        return {
            "video_available": False,
            "video_path": "",
            "scene_cut_timestamps_ms": [],
            "motion_energy": {"mean": 0.0, "peak": 0.0},
            "dominant_palette": {"global": [], "by_section": {}},
            "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
            "preview_video_suggestion": "Render a matrix-only MP4 preview and compare to the source song.",
            "analysis_note": "No video file provided.",
        }
    if not video_path.exists():
        return {
            "video_available": False,
            "video_path": str(video_path),
            "scene_cut_timestamps_ms": [],
            "motion_energy": {"mean": 0.0, "peak": 0.0},
            "dominant_palette": {"global": [], "by_section": {}},
            "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
            "preview_video_suggestion": "Render a matrix-only MP4 preview and compare to the source song.",
            "analysis_note": "Video path does not exist.",
        }
    imageio = None
    imageio_error: Exception | None = None
    for loader in (
        lambda: __import__("imageio.v2", fromlist=["get_reader"]),
        lambda: __import__("imageio", fromlist=["get_reader"]),
    ):
        try:
            imageio = loader()
            break
        except Exception as exc:
            imageio_error = exc
    if imageio is None:
        note = "imageio is unavailable; video analysis skipped."
        if imageio_error is not None:
            note = f"imageio is unavailable; video analysis skipped: {imageio_error!r}"
        return {
            "video_available": False,
            "video_path": str(video_path),
            "scene_cut_timestamps_ms": [],
            "motion_energy": {"mean": 0.0, "peak": 0.0},
            "dominant_palette": {"global": [], "by_section": {}},
            "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
            "preview_video_suggestion": "Render a matrix-only MP4 preview and compare to the source song.",
            "analysis_note": note,
        }
    try:
        reader = imageio.get_reader(str(video_path))
        meta = reader.get_meta_data() or {}
        fps = max(1.0, _safe_float(meta.get("fps"), 30.0))
        stride = max(1, int(round(fps / 4.0)))
        prev: np.ndarray | None = None
        stamps: list[float] = []
        motion_values: list[float] = []
        palette_samples: list[tuple[float, float, float]] = []
        for frame_idx, frame in enumerate(reader):
            if frame_idx % stride != 0:
                continue
            arr = np.asarray(frame, dtype=np.float32)
            if arr.ndim == 2:
                arr = np.stack((arr, arr, arr), axis=-1)
            arr = arr[..., :3]
            step_y = max(1, arr.shape[0] // 64)
            step_x = max(1, arr.shape[1] // 64)
            small = arr[::step_y, ::step_x, :]
            palette_samples.append((float(np.mean(small[..., 0])), float(np.mean(small[..., 1])), float(np.mean(small[..., 2]))))
            motion = 0.0 if prev is None else float(np.mean(np.abs(small - prev)) / 255.0)
            prev = small
            stamps.append(frame_idx / fps)
            motion_values.append(motion)
            if len(stamps) >= 900:
                break
        reader.close()
    except Exception as exc:
        return {
            "video_available": False,
            "video_path": str(video_path),
            "scene_cut_timestamps_ms": [],
            "motion_energy": {"mean": 0.0, "peak": 0.0},
            "dominant_palette": {"global": [], "by_section": {}},
            "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
            "preview_video_suggestion": "Render a matrix-only MP4 preview and compare to the source song.",
            "analysis_note": f"Video analysis failed: {exc!r}",
        }
    if not stamps:
        return {
            "video_available": False,
            "video_path": str(video_path),
            "scene_cut_timestamps_ms": [],
            "motion_energy": {"mean": 0.0, "peak": 0.0},
            "dominant_palette": {"global": [], "by_section": {}},
            "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
            "preview_video_suggestion": "Render a matrix-only MP4 preview and compare to the source song.",
            "analysis_note": "Video contained no readable frames.",
        }
    motion_arr = np.asarray(motion_values, dtype=float)
    mean_motion = float(np.mean(motion_arr))
    std_motion = float(np.std(motion_arr))
    threshold = mean_motion + (1.65 * std_motion)
    cuts: list[int] = []
    last_cut = -99999
    for idx, motion in enumerate(motion_values):
        stamp_ms = int(round(stamps[idx] * 1000.0))
        if motion >= threshold and (stamp_ms - last_cut) >= 620:
            cuts.append(stamp_ms)
            last_cut = stamp_ms
    by_section: dict[str, list[str]] = {}
    for part in parts:
        label = _part_label(part)
        st_s = _part_start_ms(part) / 1000.0
        en_s = _part_end_ms(part) / 1000.0
        colors = [palette_samples[i] for i, stamp in enumerate(stamps) if st_s <= stamp < en_s]
        if colors:
            by_section[label] = [_mix_hex(colors)]
    if log_fn is not None:
        log_fn(f"Video analysis: samples={len(stamps)}, scene_cuts={len(cuts)}, motion_mean={mean_motion:.4f}")
    return {
        "video_available": True,
        "video_path": str(video_path),
        "scene_cut_timestamps_ms": cuts[:320],
        "motion_energy": {
            "mean": round(mean_motion, 5),
            "peak": round(float(np.max(motion_arr)) if motion_arr.size else 0.0, 5),
            "std": round(std_motion, 5),
        },
        "dominant_palette": {
            "global": [_mix_hex(palette_samples)],
            "by_section": by_section,
        },
        "sync_tip": "Use video motion to boost top-layer particle bursts on the matrix.",
        "preview_video_suggestion": "Render matrix shader stacks to MP4, then compare scene cuts to transition timing.",
        "analysis_note": "Video motion/palette sampled at low rate for fast planning.",
    }


def _stem_weights(kicks: list[int], snares: list[int], hats: list[int], bass_peaks: list[int], vocal_peaks: list[int]) -> dict[str, float]:
    drums_score = float(len(kicks) + len(snares) + max(0, len(hats) // 2))
    bass_score = float(len(bass_peaks))
    vocal_score = float(len(vocal_peaks))
    other_score = max(1.0, float((len(hats) // 3) + 1))
    total = drums_score + bass_score + vocal_score + other_score
    return {
        "drums": round(drums_score / total, 4),
        "bass": round(bass_score / total, 4),
        "vocals": round(vocal_score / total, 4),
        "other": round(other_score / total, 4),
    }


def section_config_for_time(plan: dict[str, Any] | None, target_ms: int) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return {}
    per_section = (((plan.get("matrix_shader_config", {}) or {}).get("per_section", [])) if plan else []) or []
    fallback: dict[str, Any] = per_section[-1] if per_section else {}
    for section in per_section:
        start_ms = _safe_int(section.get("start_ms"), 0)
        end_ms = max(start_ms + 1, _safe_int(section.get("end_ms"), start_ms + 1))
        if start_ms <= int(target_ms) < end_ms:
            return section
    return fallback


def _shader_effect_hint(shader_filename: str) -> str:
    shader = str(shader_filename or "").strip().lower()
    if shader == "radial_pulse.glsl":
        return "Fire"
    if shader == "waveform_2d.glsl":
        return "Wave"
    if shader == "spectrum_bars.glsl":
        return "Bars"
    if shader == "twinkle_field.glsl":
        return "Life"
    if shader == "plasma.glsl":
        return "Plasma"
    if shader == "caustics.glsl":
        return "Pictures"
    if shader == "ripple.glsl":
        return "Ripple"
    return "Pictures"


def recommend_sequence_effect(
    plan: dict[str, Any] | None,
    *,
    cue: str,
    part_label: str,
    target_ms: int,
    index: int = 0,
    fallback: str = "Pictures",
    lyric_active: bool = False,
) -> str:
    cue_key = str(cue or "phrase").strip().lower()
    part = str(part_label or "VERSE").upper()
    section = section_config_for_time(plan, target_ms)
    scene_mode = str(section.get("scene_mode", "balanced") or "balanced").lower()
    shader = str(section.get("recommended_shader", "") or "")
    hinted = _shader_effect_hint(shader) if shader else str(fallback or "Pictures")

    if lyric_active and cue_key in {"vocal", "phrase"}:
        return "Text"
    if cue_key == "kick":
        return "Bars" if scene_mode not in {"ambient_minimal", "breakdown"} else "Ripple"
    if cue_key == "snare":
        return "Ripple" if scene_mode not in {"wide_bright", "drop"} else "Plasma"
    if cue_key == "hat":
        return "Life" if scene_mode in {"wide_bright", "drop"} or part == "CHORUS" else "Ripple"
    if cue_key == "bass":
        if scene_mode in {"wide_bright", "drop"} or hinted == "Fire":
            return "Fire" if (index % 3) == 0 else "Bars"
        return "Bars" if scene_mode != "ambient_minimal" else "Ripple"
    if cue_key == "build":
        return "Plasma" if hinted not in {"Fire", "Bars"} else hinted
    if cue_key == "vocal":
        if part == "CHORUS":
            return "Text" if (index % 2) == 0 else "Pictures"
        return "Pictures" if hinted == "Pictures" else "Wave"
    if cue_key == "phrase":
        if scene_mode in {"build_tension", "wide_bright"}:
            return "Plasma" if hinted == "Plasma" else "Wave"
        return hinted
    if cue_key == "accent":
        return "Ripple" if hinted not in {"Fire", "Plasma"} else hinted
    return hinted or str(fallback or "Pictures")


def build_matrix_intelligence_plan(
    *,
    parsed_layout: Any,
    parts: list[Any],
    multiband: Any,
    audio: Any,
    beat_ms: list[int],
    kicks: list[int],
    snares: list[int],
    hats: list[int],
    bass_peaks: list[int],
    vocal_peaks: list[int],
    video_path: Path | None = None,
    blend_overrides_path: Path | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    matrix_targets = discover_matrix_targets(parsed_layout)
    descriptor_summary = dict(getattr(multiband, "descriptor_summary", {}) or {})
    blend_overrides = _load_blend_overrides(blend_overrides_path)
    tempo_bpm = _safe_float(getattr(multiband, "tempo_bpm", 0.0), 0.0)
    genre = str(getattr(multiband, "genre_hint", "unknown") or "unknown")
    mood = str(getattr(multiband, "mood_hint", "neutral") or "neutral")
    rms_values = np.asarray(getattr(audio, "rms01", []), dtype=float)
    rms_mean = float(np.mean(rms_values)) if rms_values.size else 0.0
    percussive_ratio = float(len(kicks) + len(snares) + (0.5 * len(hats))) / float(max(1, len(beat_ms))) if beat_ms else 0.0
    arousal, valence = _compute_arousal_valence(descriptor_summary, tempo_bpm, rms_mean, percussive_ratio)
    mood_description = _mood_description(arousal, valence)
    video_data = analyze_video_reactivity(video_path, parts, log_fn=log_fn)
    if not matrix_targets:
        return {
            "enabled": True,
            "matrix_available": False,
            "matrix_count": 0,
            "blend_overrides_applied": bool(blend_overrides),
            "matrix_params": {},
            "matrix_shader_config": {"per_section": []},
            "frequency_layer_config": {},
            "stem_layer_weights": _stem_weights(kicks, snares, hats, bass_peaks, vocal_peaks),
            "video_data": video_data,
            "recommended_layering": "No matrix models found; use standard non-matrix sequencing layers.",
            "mood_description": mood_description,
            "classification": {"genre": genre, "mood": mood, "confidence": 0.62, "source": "rule_fallback"},
            "responsible_use": {
                "notice": "Helix creators are not responsible for misuse of training workflows or sequence data.",
                "copyright_warning": "Do not train on licensed third-party sequences or proprietary show files without explicit rights.",
                "build_rule": "During build and tuning, use only assets you own or are licensed to use.",
            },
        }
    primary = matrix_targets[0]
    mapping = _spectrogram_mapping(int(primary["width"]), int(primary["height"]))
    matrix_pixels = int(primary["pixels"])
    centroid_mean = _safe_float(descriptor_summary.get("centroid_mean"), 0.0)
    particle_density = _clamp(0.18 + (0.54 * percussive_ratio) + (0.12 * arousal), 0.10, 0.96)
    waveform_scroll_speed = _clamp((tempo_bpm / 120.0) * 0.95, 0.45, 2.8)
    color_boost = _clamp(0.92 + (centroid_mean * 0.85), 0.75, 1.95)
    section_profiles = dict(getattr(multiband, "section_profiles", {}) or {})
    section_configs: list[dict[str, Any]] = []
    transition_plan: list[dict[str, Any]] = []
    layer_stack_samples: list[dict[str, Any]] = []
    for idx, part in enumerate(parts):
        label = _part_label(part)
        start_ms = _part_start_ms(part)
        end_ms = _part_end_ms(part)
        profile = dict(section_profiles.get(label, {}) or {})
        loudness = _safe_float(profile.get("loudness"), _part_energy(part))
        complexity = _safe_float(profile.get("complexity"), 0.42)
        scene_mode = str(profile.get("scene_mode", "balanced"))
        dominant_band = str(profile.get("dominant_band", "mid"))
        section_beats = _marks_in_window(beat_ms, start_ms, end_ms)
        section_kicks = _marks_in_window(kicks, start_ms, end_ms)
        section_snares = _marks_in_window(snares, start_ms, end_ms)
        section_hats = _marks_in_window(hats, start_ms, end_ms)
        section_perc_ratio = (section_kicks + section_snares + (0.5 * section_hats)) / max(1.0, float(section_beats))
        layer_limit = _gpu_layer_limit(matrix_pixels, loudness, scene_mode)
        shader = _scene_shader(genre, mood, scene_mode, dominant_band, mapping)
        time_speed = _clamp((tempo_bpm / 120.0) * (0.76 + (0.42 * complexity)), 0.35, 2.8)
        intensity = _clamp((0.30 + (0.45 * loudness) + (0.30 * section_perc_ratio)), 0.10, 1.0)
        hue_shift = _clamp(((centroid_mean - 0.45) * 0.8) + ((valence - 0.50) * 0.5), -1.0, 1.0)
        distortion = _clamp(0.18 + (0.62 * _safe_float(profile.get("flux_motion"), 0.0)), 0.0, 1.0)
        particle_count = int(round(_clamp((matrix_pixels * particle_density * (0.35 + section_perc_ratio)), 20.0, 1800.0)))
        base_blend, base_mix, base_canvas, base_note = _blend_pick(
            "base",
            scene_mode,
            arousal,
            valence,
            matrix_pixels,
            genre=genre,
            mood=mood,
            overrides=blend_overrides,
        )
        mid_blend, mid_mix, mid_canvas, mid_note = _blend_pick(
            "mid",
            scene_mode,
            arousal,
            valence,
            matrix_pixels,
            genre=genre,
            mood=mood,
            overrides=blend_overrides,
        )
        top_blend, top_mix, top_canvas, top_note = _blend_pick(
            "accent",
            scene_mode,
            arousal,
            valence,
            matrix_pixels,
            genre=genre,
            mood=mood,
            overrides=blend_overrides,
        )
        if matrix_pixels > 4000:
            mid_mix = min(mid_mix, 70)
            top_mix = min(top_mix, 70)
        section_configs.append(
            {
                "label": label,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "scene_mode": scene_mode,
                "layer_limit": layer_limit,
                "recommended_shader": shader,
                "matrix_shader_config": {
                    "shader_filename": shader,
                    "xlights_parameters": {
                        "time_speed": round(time_speed, 4),
                        "intensity": round(intensity, 4),
                        "hue_shift": round(hue_shift, 4),
                        "zoom_or_distortion": round(distortion, 4),
                        "custom_uniforms": {
                            "bass_level": round(_clamp(section_perc_ratio, 0.0, 1.0), 4),
                            "mid_level": round(_clamp(complexity, 0.0, 1.0), 4),
                            "high_level": round(_clamp(_safe_float(profile.get("flux_motion"), 0.0), 0.0, 1.0), 4),
                            "particle_count": int(particle_count),
                            "wave_amplitude": round(_clamp(0.35 + (0.5 * loudness), 0.0, 1.0), 4),
                        },
                    },
                    "value_curves": {
                        "time_speed_curve": _curve_triplet(start_ms, end_ms, time_speed * 0.88, time_speed * 1.08, time_speed),
                        "intensity_curve": _curve_triplet(start_ms, end_ms, intensity * 0.80, min(1.0, intensity * 1.18), intensity * 0.92),
                        "hue_shift_curve": _curve_triplet(start_ms, end_ms, hue_shift * 0.7, hue_shift, hue_shift * 0.85),
                    },
                    "blend_layers": [
                        {"layer_role": "base", "blend_mode": base_blend, "mix_slider_value": base_mix, "canvas_mode": base_canvas, "blend_optimization_note": base_note},
                        {"layer_role": "mid", "blend_mode": mid_blend, "mix_slider_value": mid_mix, "canvas_mode": mid_canvas, "blend_optimization_note": mid_note},
                        {"layer_role": "accent", "blend_mode": top_blend, "mix_slider_value": top_mix, "canvas_mode": top_canvas, "blend_optimization_note": top_note},
                    ],
                },
            }
        )
        section_layers = shader_layering.recommend_layer_stack(
            energy=loudness,
            onset=min(1.0, section_perc_ratio),
            spread=_safe_float(profile.get("complexity"), complexity),
            contrast=_safe_float(profile.get("flux_motion"), 0.0),
        )
        layer_stack_samples.append(
            {
                "section": label,
                "compatibility_score": round(float(shader_layering.compatibility_score(section_layers)), 4),
                "layers": [
                    {
                        "name": layer.name,
                        "role": layer.role,
                        "blend_mode": layer.blend_mode,
                        "density": round(float(layer.density), 4),
                        "brightness": round(float(layer.brightness), 4),
                        "motion": round(float(layer.motion), 4),
                        "complexity": round(float(layer.complexity), 4),
                    }
                    for layer in section_layers
                ],
            }
        )
        if idx + 1 < len(parts):
            next_label = _part_label(parts[idx + 1])
            transition_plan.append(
                {
                    "from": label,
                    "to": next_label,
                    "start_ms": end_ms,
                    "crossfade_ms": int(_clamp(180 + (220 * complexity), 140, 520)),
                    "transition_type": "morph" if scene_mode in {"build_tension", "wide_bright"} else "blend",
                    "blend_type": "Morph" if scene_mode in {"build_tension", "wide_bright"} else "Fade",
                }
            )
    stem_weights = _stem_weights(kicks, snares, hats, bass_peaks, vocal_peaks)
    matrix_roles: dict[str, str] = {}
    sorted_x = sorted(matrix_targets, key=lambda item: float(item["center_x"]))
    if sorted_x:
        matrix_roles[sorted_x[0]["name"]] = "left" if len(sorted_x) > 1 else "front_primary"
        matrix_roles[sorted_x[-1]["name"]] = "right" if len(sorted_x) > 1 else "front_primary"
        matrix_roles[primary["name"]] = "front_primary"
    for target in matrix_targets:
        matrix_roles.setdefault(str(target["name"]), "background")
    return {
        "enabled": True,
        "matrix_available": True,
        "matrix_count": len(matrix_targets),
        "blend_overrides_applied": bool(blend_overrides),
        "matrices": [{**item, "role": matrix_roles.get(str(item["name"]), "background")} for item in matrix_targets],
        "classification": {"genre": genre, "mood": mood, "confidence": 0.62, "source": "rule_fallback"},
        "mood_description": mood_description,
        "emotional_narrative_curve": {"arousal": round(arousal, 4), "valence": round(valence, 4)},
        "matrix_params": {
            "target_model": primary["name"],
            "width": int(primary["width"]),
            "height": int(primary["height"]),
            "pixel_count": int(primary["pixels"]),
            "recommended_shader": _scene_shader(genre, mood, "balanced", "mid", mapping),
            "spectrogram_mapping": mapping,
            "particle_density": round(particle_density, 4),
            "waveform_scroll_speed": round(waveform_scroll_speed, 4),
            "color_brightness_boost": round(color_boost, 4),
            "gpu_budget": {"max_layers": 3 if int(primary["pixels"]) > 4000 else 4, "auto_prune": True},
        },
        "matrix_shader_config": {
            "global_blend_strategy": "Frequency-split with Additive highs + Screen mids + controlled base underlay.",
            "per_section": section_configs,
        },
        "frequency_layer_config": {
            "gpu_layer_cap": 3 if int(primary["pixels"]) > 4000 else 4,
            "bands": {
                "bass": {"range_hz": [20, 250], "shader": "plasma.glsl", "blend_mode": "Screen"},
                "mid": {"range_hz": [250, 4000], "shader": "waveform_2d.glsl", "blend_mode": "Overlay"},
                "high": {"range_hz": [4000, 12000], "shader": "twinkle_field.glsl", "blend_mode": "Additive"},
            },
        },
        "stem_layer_weights": stem_weights,
        "stem_configs": {
            "drums": {"shader_role": "top_transients", "intensity_weight": stem_weights.get("drums", 0.25), "attack_ms": 30, "release_ms": 180},
            "bass": {"shader_role": "base_pulse", "intensity_weight": stem_weights.get("bass", 0.25), "attack_ms": 40, "release_ms": 240},
            "vocals": {"shader_role": "melody_highlight", "intensity_weight": stem_weights.get("vocals", 0.25), "attack_ms": 75, "release_ms": 320},
            "other": {"shader_role": "harmonic_fill", "intensity_weight": stem_weights.get("other", 0.25), "attack_ms": 95, "release_ms": 360},
        },
        "layer_envelope_curves": {
            "global": {"percussive_attack_ms": 34, "percussive_release_ms": 190, "harmonic_attack_ms": 95, "harmonic_release_ms": 340}
        },
        "spatial_layer_mapping": {
            "matrix_roles": matrix_roles,
            "stereo_mapping": "left/right matrix emphasis follows matrix center X ordering.",
            "depth_mapping": "primary matrix carries transient layers; secondary matrices carry ambient layers.",
        },
        "transition_plan": transition_plan,
        "shader_layering": {
            "section_stacks": layer_stack_samples,
            "overall_compatibility": round(
                float(np.mean([float(item["compatibility_score"]) for item in layer_stack_samples]))
                if layer_stack_samples
                else 0.0,
                4,
            ),
            "coordinate_uniform_hints": {
                "u_focus_x": "Map to matrix center weighting for horizontal motion preference.",
                "u_focus_y": "Map to vertical melodic lift and lyric framing.",
                "u_slice_z": "Use as depth blend selector for 3D illusion layers.",
                "u_path_speed": "Use to modulate transition speed and blur amount.",
            },
        },
        "layer_personality_profile": {
            "arousal": round(arousal, 4),
            "valence": round(valence, 4),
            "description": mood_description,
        },
        "blend_summary": {
            "blend_mode_intent": "Use Additive/Screen for high-energy accents, Multiply/Normal for calmer sections.",
            "off_effect_safety": "Use Transparent/Canvas mode for top shader layers to avoid black overwrite artifacts.",
        },
        "video_data": video_data,
        "recommended_layering": "Base ambient + mid matrix core + top transient accents (cap at 3 layers on large matrices).",
        "responsible_use": {
            "notice": "Helix creators are not responsible for misuse of training workflows or sequence data.",
            "copyright_warning": "Do not train on licensed third-party sequences or proprietary show files without explicit rights.",
            "build_rule": "During build and tuning, use only assets you own or are licensed to use.",
            "user_context_note": "User-supplied Suno-generated tracks are acceptable when rights are held under your plan.",
        },
    }
