from __future__ import annotations

import argparse
import importlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

import librosa
from core import audio_intelligence as ai
from core import effect_engine as ee
from xlights import xsq_writer as xw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FLAGS_PATH = ROOT / "config" / "core_feature_flags.json"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "core_sandbox"
DEFAULT_AUDIO = ROOT / "2.wav"

TARGET_MODULES = (
    "effect_engine",
    "self_improving_scoring",
    "spatial_mapping_engine",
    "audio_intelligence",
)


@dataclass(frozen=True)
class CoreFlags:
    effect_engine: bool = True
    self_improving_scoring: bool = True
    spatial_mapping_engine: bool = True
    audio_intelligence: bool = True

    def is_enabled(self, module_name: str) -> bool:
        return bool(getattr(self, module_name, True))


def _safe_float(value: float) -> float:
    return float(round(float(value), 6))


def _load_flags(path: Path) -> CoreFlags:
    if not path.exists():
        return CoreFlags()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return CoreFlags()
    return CoreFlags(
        effect_engine=bool(payload.get("effect_engine", True)),
        self_improving_scoring=bool(payload.get("self_improving_scoring", True)),
        spatial_mapping_engine=bool(payload.get("spatial_mapping_engine", True)),
        audio_intelligence=bool(payload.get("audio_intelligence", True)),
    )


def _override_flags(flags: CoreFlags, args: argparse.Namespace) -> CoreFlags:
    data = asdict(flags)
    for module_name in TARGET_MODULES:
        enable_key = f"enable_{module_name}"
        disable_key = f"disable_{module_name}"
        if getattr(args, enable_key, False):
            data[module_name] = True
        if getattr(args, disable_key, False):
            data[module_name] = False
    return CoreFlags(**data)


def _module_import(name: str) -> Any | None:
    try:
        return importlib.import_module(f"core.{name}")
    except Exception:
        return None


def _maybe_preview_frame(path: Path, values: list[float]) -> str | None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None

    width = max(120, len(values) * 12)
    height = 120
    image = Image.new("RGB", (width, height), (12, 20, 32))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, width - 8, height - 8), outline=(120, 160, 200))
    for idx, value in enumerate(values):
        x = 12 + (idx * 10)
        bar_h = int(round(max(0.0, min(1.0, value)) * 88))
        y0 = height - 12
        y1 = y0 - bar_h
        draw.line((x, y0, x, y1), fill=(86, 188, 255), width=6)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return str(path)


def _audio_summary(audio_path: Path) -> tuple[np.ndarray, int, np.ndarray, np.ndarray]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    return y, sr, rms.astype(float), times.astype(float), centroid.astype(float)


def _sample_indices(length: int, count: int) -> list[int]:
    if length <= 0:
        return []
    if length <= count:
        return list(range(length))
    return sorted({int(round(i * (length - 1) / (count - 1))) for i in range(count)})


def _effect_engine_snapshot(
    audio_path: Path,
    y: np.ndarray,
    sr: int,
    rms: np.ndarray,
    times_s: np.ndarray,
    centroid: np.ndarray,
) -> dict[str, Any]:
    rng = random.Random(7331)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=False)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    beat_tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    events: list[ee.NoteEvent] = []
    for idx, onset in enumerate(onset_times[:10]):
        start_ms = int(round(float(onset) * 1000.0))
        end_ms = start_ms + 220
        note = 48 + (idx % 12)
        events.append(
            ee.NoteEvent(
                start_ms=start_ms,
                end_ms=end_ms,
                notes=[(note, 0.65), (note + 7, 0.4)],
                part="CHORUS" if (idx % 2 == 0) else "VERSE",
                section="chorus" if (idx % 2 == 0) else "verse",
            )
        )

    kicks = [int(round(value * 1000.0)) for value in onset_times[::3][:16]]
    snares = [int(round(value * 1000.0)) for value in onset_times[1::3][:16]]
    hats = [int(round(value * 1000.0)) for value in onset_times[2::3][:16]]
    bass_peaks = [int(round(value * 1000.0)) for value in beat_times[:16]]
    vocal_peaks = [int(round(value * 1000.0)) for value in onset_times[::2][:16]]

    timeline = []
    for event in events:
        cue = ee.reactive_cue_for_event(
            event,
            kicks=kicks,
            snares=snares,
            hats=hats,
            bass_peaks=bass_peaks,
            vocal_peaks=vocal_peaks,
            default="phrase",
        )
        timeline.append({"start_ms": event.start_ms, "end_ms": event.end_ms, "cue": cue})

    sample_idx = _sample_indices(len(rms), 12)
    rms_values = [float(rms[i]) for i in sample_idx]
    rms_norm = np.asarray(xw.norm01(np.asarray(rms_values, dtype=float)), dtype=float)
    audio_obj = xw.Audio(
        sr=sr,
        y=y[: max(1, min(len(y), sr * 4))],
        dur_s=float(len(y) / max(1, sr)),
        onset_ms=[int(round(v * 1000.0)) for v in onset_times[:128]],
        beat_ms=[int(round(v * 1000.0)) for v in beat_times[:128]],
        times_s=np.asarray([times_s[i] for i in sample_idx], dtype=float),
        centroid=np.asarray([centroid[min(i, len(centroid) - 1)] for i in sample_idx], dtype=float),
        rms01=rms_norm,
        bass01=np.zeros_like(rms_norm),
        vocal01=np.zeros_like(rms_norm),
        pitch_hz=np.zeros_like(rms_norm),
    )
    states = []
    build_marks = [item["start_ms"] for item in timeline[::3]]
    release_marks = [item["start_ms"] for item in timeline[1::3]]
    for i, idx in enumerate(sample_idx):
        t_ms = int(round(times_s[idx] * 1000.0))
        state = ee.macro_intensity_state(
            t_ms,
            audio=audio_obj,
            build_lifts=build_marks,
            releases=release_marks,
            quiet_windows=[],
        )
        states.append({"time_ms": t_ms, "rms01": _safe_float(rms_norm[i]), "state": state})

    palettes = [
        "C_BUTTON_Palette1=#FF0000,C_BUTTON_Palette2=#00FF00,C_BUTTON_Palette3=#0000FF",
        "C_BUTTON_Palette1=#FFD700,C_BUTTON_Palette2=#FFA500,C_BUTTON_Palette3=#FF69B4",
        "C_BUTTON_Palette1=#00FFFF,C_BUTTON_Palette2=#39FF14,C_BUTTON_Palette3=#FF00FF",
    ]
    color_distribution = {"red": 0, "green": 0, "blue": 0}
    for i in range(9):
        picked = ee.pick_palette_for_effect(
            mode="random",
            template_palette=palettes[0],
            template_pool=palettes,
            history_pool=palettes[1:],
            rng=rng,
            effect_index=i,
        ) or ""
        for code in ee.extract_palette_hexes(picked):
            code_l = code.lower()
            if code_l.startswith("#ff"):
                color_distribution["red"] += 1
            elif code_l[3:5] == "ff":
                color_distribution["green"] += 1
            elif code_l.endswith("ff"):
                color_distribution["blue"] += 1

    coords = {"A": (0.0, 0.8), "B": (0.6, 0.4), "C": (0.4, 0.1), "D": (0.9, 0.7)}
    spatial_order = ee.spatial_ordered_models(["A", "B", "C", "D"], coords, rng, path_style="top_to_bottom")

    return {
        "module": "core.effect_engine",
        "status": "ok",
        "effect_timeline": timeline,
        "intensity_map": states,
        "color_distribution": color_distribution,
        "spatial_coordinates": {"ordered_models": spatial_order, "coords": coords},
        "tempo_bpm": _safe_float(float(np.asarray(beat_tempo).reshape(-1)[0] if np.asarray(beat_tempo).size else 0.0)),
    }


def _audio_intelligence_snapshot(
    audio_path: Path,
    y: np.ndarray,
    sr: int,
    rms: np.ndarray,
    times_s: np.ndarray,
    centroid: np.ndarray,
) -> dict[str, Any]:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=False)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    marks = [int(round(v * 1000.0)) for v in onset_times[:40]]

    sample_idx = _sample_indices(len(rms), 12)
    intensity_map = []
    for idx in sample_idx:
        t_ms = int(round(times_s[idx] * 1000.0))
        confidence = ai.proximity_confidence(t_ms, marks, window_ms=220, floor=0.0)
        intensity_map.append(
            {
                "time_ms": t_ms,
                "rms": _safe_float(rms[idx]),
                "onset_confidence": _safe_float(confidence),
            }
        )

    timeline = []
    for t_ms in marks[:10]:
        distance = ai.nearest_mark_distance_ms(t_ms, marks)
        timeline.append(
            {
                "time_ms": t_ms,
                "nearest_mark_ms": int(distance or 0),
                "confidence": _safe_float(ai.proximity_confidence(t_ms, marks, window_ms=120)),
            }
        )

    color_distribution = {"warm": 0, "neutral": 0, "cool": 0}
    for idx in sample_idx:
        c = float(centroid[min(idx, len(centroid) - 1)])
        if c >= 3200.0:
            color_distribution["cool"] += 1
        elif c >= 1800.0:
            color_distribution["neutral"] += 1
        else:
            color_distribution["warm"] += 1

    layout_path = ROOT / "xlights_rgbeffects.xml"
    coords = {}
    ordered = []
    if layout_path.exists():
        names = ["HOUSE", "MEGA TREE", "LEFT TREE", "RIGHT TREE", "ARCH", "MATRIX"]
        coords = ai.parse_layout_coordinates(layout_path, names)
        if coords:
            ordered = ai.ordered_spatial_path(list(coords.keys()), coords, "left_to_right", rng=random.Random(11))

    return {
        "module": "core.audio_intelligence",
        "status": "ok",
        "effect_timeline": timeline,
        "intensity_map": intensity_map,
        "color_distribution": color_distribution,
        "spatial_coordinates": {"ordered_models": ordered, "coords": coords},
    }


def _missing_or_disabled(module_name: str, state: str, detail: str) -> dict[str, Any]:
    return {
        "module": f"core.{module_name}",
        "status": state,
        "detail": detail,
        "effect_timeline": [],
        "intensity_map": [],
        "color_distribution": {},
        "spatial_coordinates": {},
    }


def _self_improving_scoring_snapshot() -> dict[str, Any]:
    module_name = "self_improving_scoring"
    module = _module_import(module_name)
    if module is None:
        return _missing_or_disabled(module_name, "missing", "module not present on current branch")

    payload = {
        "version": "sandbox",
        "placement_mode": "isolated",
        "runtime_tuning": {"chase_style": "left_to_right", "palette_mode": "template"},
        "quality": {"coverage_ratio": 0.52, "dominant_family_ratio": 0.33, "component_scores": {"coverage": 74, "density": 71, "structure": 78, "validation": 81, "family_diversity": 67, "dominance": 62}},
        "audit": {"final": {"musical_coherence": 78, "intensity_balance": 73, "section_coverage": 0.56, "clutter_ratio": 0.21}},
        "advanced_audio": {"mood_hint": "neutral"},
        "profile": {"darkness": 1.0},
        "placements": {"tree": 18, "arch": 10, "matrix": 12},
        "watermark": {"version": "dream-sequence-weaver-signature-v1", "signature": "sandbox"},
        "responsible_use": {"helix_generated_only": True},
    }
    score = module.score_sequence(payload).as_dict()
    ranked = module.rank_sequence_payloads([{"label": "A", "payload": payload}, {"label": "B", "payload": payload}])
    return {
        "module": "core.self_improving_scoring",
        "status": "ok",
        "effect_timeline": [{"label": item["label"], "rank": item["rank"], "total_score": item["total_score"]} for item in ranked],
        "intensity_map": [{"metric": key, "value": _safe_float(value)} for key, value in score["metrics"].items()],
        "color_distribution": {},
        "spatial_coordinates": {},
    }


def _spatial_mapping_snapshot() -> dict[str, Any]:
    module_name = "spatial_mapping_engine"
    module = _module_import(module_name)
    if module is None:
        return _missing_or_disabled(module_name, "missing", "module not present on current branch")
    scene_module = _module_import("spatial_scene")
    parser_module = _module_import("model_parser")
    if scene_module is None or parser_module is None:
        return _missing_or_disabled(module_name, "missing", "required spatial dependencies not present")

    layout_path = ROOT / "xlights_rgbeffects.xml"
    if not layout_path.exists():
        return _missing_or_disabled(module_name, "missing", "layout file missing")
    parsed = parser_module.parse_layout(layout_path)
    scene = scene_module.build_scene(parsed)
    plan = module.build_mapping_plan(
        scene,
        points=[(0.1, 0.2, 0.0, 0.7), (0.8, 0.7, 0.3, 0.9)],
        trajectories=[{"name": "line", "points": [(0.2, 0.3, 0.1, 0.7), (0.7, 0.6, 0.4, 0.8)], "start_ms": 0, "end_ms": 900}],
    ).to_dict()
    return {
        "module": "core.spatial_mapping_engine",
        "status": "ok",
        "effect_timeline": [{"model": effect["model"], "start_ms": effect["start_ms"], "end_ms": effect["end_ms"]} for effect in plan["effects"][:16]],
        "intensity_map": [{"model": effect["model"], "intensity": _safe_float(effect["intensity"])} for effect in plan["effects"][:16]],
        "color_distribution": {},
        "spatial_coordinates": {"coverage": plan["coverage_visualization"]},
    }


def run_core_sandbox(
    *,
    audio_path: Path,
    output_dir: Path,
    flags: CoreFlags,
    preview_frames: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio input not found: {audio_path}")

    y, sr, rms, times_s, centroid = _audio_summary(audio_path)
    modules: dict[str, dict[str, Any]] = {}

    if flags.effect_engine:
        modules["effect_engine"] = _effect_engine_snapshot(audio_path, y, sr, rms, times_s, centroid)
    else:
        modules["effect_engine"] = _missing_or_disabled("effect_engine", "disabled", "disabled by feature flag")

    if flags.audio_intelligence:
        modules["audio_intelligence"] = _audio_intelligence_snapshot(audio_path, y, sr, rms, times_s, centroid)
    else:
        modules["audio_intelligence"] = _missing_or_disabled("audio_intelligence", "disabled", "disabled by feature flag")

    if flags.self_improving_scoring:
        modules["self_improving_scoring"] = _self_improving_scoring_snapshot()
    else:
        modules["self_improving_scoring"] = _missing_or_disabled("self_improving_scoring", "disabled", "disabled by feature flag")

    if flags.spatial_mapping_engine:
        modules["spatial_mapping_engine"] = _spatial_mapping_snapshot()
    else:
        modules["spatial_mapping_engine"] = _missing_or_disabled("spatial_mapping_engine", "disabled", "disabled by feature flag")

    previews: dict[str, str] = {}
    if preview_frames:
        for name, payload in modules.items():
            values = [float(item.get("rms01", item.get("rms", item.get("onset_confidence", 0.0)))) for item in payload.get("intensity_map", [])]
            if not values:
                continue
            frame_path = output_dir / "frames" / f"{name}_intensity.png"
            saved = _maybe_preview_frame(frame_path, values)
            if saved:
                previews[name] = saved

    report = {
        "audio_file": str(audio_path.resolve()),
        "feature_flags": asdict(flags),
        "modules": modules,
        "preview_frames": previews,
    }
    out_path = output_dir / "core_sandbox_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run core modules in isolation and write deterministic debug artifacts.")
    parser.add_argument("--audio", default=str(DEFAULT_AUDIO), help="Input audio file. Defaults to 2.wav when available.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output folder for JSON artifacts.")
    parser.add_argument("--flags-config", default=str(DEFAULT_FLAGS_PATH), help="Feature flag config JSON path.")
    parser.add_argument("--preview-frames", action="store_true", help="Write optional preview frames for intensity maps.")
    for module_name in TARGET_MODULES:
        parser.add_argument(f"--enable-{module_name.replace('_', '-')}", dest=f"enable_{module_name}", action="store_true", help=f"Enable {module_name}.")
        parser.add_argument(f"--disable-{module_name.replace('_', '-')}", dest=f"disable_{module_name}", action="store_true", help=f"Disable {module_name}.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    flags = _override_flags(_load_flags(Path(args.flags_config)), args)
    report = run_core_sandbox(
        audio_path=Path(args.audio).resolve(),
        output_dir=Path(args.output_dir).resolve(),
        flags=flags,
        preview_frames=bool(args.preview_frames),
    )
    print(json.dumps({"report": str((Path(args.output_dir).resolve() / "core_sandbox_report.json")), "flags": report["feature_flags"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
