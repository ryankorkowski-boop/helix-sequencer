from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from core import spatial_scene


CAMERA_MODES = ("orbit", "fly_through", "focus", "wide_shot", "chase")


@dataclass(frozen=True)
class CameraState:
    timestamp_ms: int
    position: tuple[float, float, float]
    target: tuple[float, float, float]
    velocity: tuple[float, float, float]
    fov: float
    zoom: float
    roll: float
    tilt: float
    mode: str
    target_label: str
    energy_level: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CameraTarget:
    label: str
    position: tuple[float, float, float]
    confidence: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _lerp(a: float, b: float, t: float) -> float:
    return float(a) + (float(b) - float(a)) * t


def _lerp3(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t), _lerp(a[2], b[2], t))


def ease_in_out(t: float) -> float:
    t = _clamp(t)
    return t * t * (3.0 - (2.0 * t))


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


def _scene_center(scene: spatial_scene.SpatialScene) -> tuple[float, float, float]:
    nodes = list(scene.nodes.values()) or list(scene.group_nodes.values())
    if not nodes:
        return (0.0, 0.0, 0.0)
    return (
        sum(node.center_xyz[0] for node in nodes) / len(nodes),
        sum(node.center_xyz[1] for node in nodes) / len(nodes),
        sum(node.center_xyz[2] for node in nodes) / len(nodes),
    )


def _scene_radius(scene: spatial_scene.SpatialScene) -> float:
    report = scene.capability_report
    return max(30.0, report.horizontal_span * 0.62, report.vertical_span * 0.72, report.depth_span * 1.1)


def _target_for_names(scene: spatial_scene.SpatialScene, names: Iterable[str], label: str, source: str) -> CameraTarget | None:
    coords: list[tuple[float, float, float]] = []
    for name in names:
        node = scene.node_for(str(name))
        if node is not None:
            coords.append(node.center_xyz)
    if not coords:
        return None
    pos = (
        sum(item[0] for item in coords) / len(coords),
        sum(item[1] for item in coords) / len(coords),
        sum(item[2] for item in coords) / len(coords),
    )
    return CameraTarget(label=label, position=pos, confidence=min(1.0, 0.45 + len(coords) * 0.12), source=source)


def build_camera_targets(
    scene: spatial_scene.SpatialScene,
    *,
    snowman_payload: Mapping[str, Any] | None = None,
    active_models: Iterable[str] = (),
) -> dict[str, CameraTarget]:
    payload = snowman_payload or {}
    layout_mapping = dict(payload.get("layout_mapping", {}) or {})
    targets: dict[str, CameraTarget] = {}
    role_aliases = {
        "lead_singer": ("lead_singer", "singer"),
        "drummer": ("drummer",),
        "guitarist": ("guitarist",),
        "bassist": ("bassist",),
    }
    for payload_key, labels in role_aliases.items():
        names = list((layout_mapping.get(payload_key, {}) or {}).get("targets", []) or [])
        target = _target_for_names(scene, names, labels[0], "snowman_layout_mapping")
        if target is not None:
            for label in labels:
                targets[label] = target
    active_target = _target_for_names(scene, active_models, "spatial_energy_cluster", "active_model_cluster")
    if active_target is not None:
        targets["spatial_energy_cluster"] = active_target
    targets.setdefault("wide", CameraTarget("wide", _scene_center(scene), 0.65, "scene_center"))
    return targets


def _segment_value(segment: Mapping[str, Any], key: str, default: Any) -> Any:
    return segment.get(key, default)


def _mode_for_segment(segment: Mapping[str, Any]) -> str:
    section = str(_segment_value(segment, "section_type", "") or "").lower()
    energy = float(_segment_value(segment, "energy_level", 0.4) or 0.4)
    density = str(_segment_value(segment, "density_level", "") or "").lower()
    if section in {"intro", "outro"}:
        return "wide_shot" if section == "outro" else "orbit"
    if section in {"drop", "breakdown"} and energy >= 0.72:
        return "chase"
    if section in {"chorus", "post_chorus"}:
        return "fly_through"
    if "busy" in density and energy >= 0.62:
        return "chase"
    return "focus" if section in {"verse", "bridge"} else "orbit"


def _focus_label(segment: Mapping[str, Any], performer_focus: Iterable[Mapping[str, Any]], start_ms: int) -> str:
    for focus in performer_focus:
        f_start = int(focus.get("start_ms", 0) or 0)
        f_end = int(focus.get("end_ms", f_start) or f_start)
        if f_start <= start_ms < f_end:
            primary = str(focus.get("primary_focus", "") or "")
            return {"singer": "lead_singer", "environment": "spatial_energy_cluster"}.get(primary, primary)
    dominant = [str(item) for item in list(segment.get("dominant_features", []) or [])]
    if "vocals" in dominant:
        return "lead_singer"
    if "drums" in dominant:
        return "drummer"
    if "guitar" in dominant:
        return "guitarist"
    if "bass" in dominant:
        return "bassist"
    return "wide"


def _desired_state(
    *,
    scene: spatial_scene.SpatialScene,
    segment: Mapping[str, Any],
    targets: Mapping[str, CameraTarget],
    performer_focus: Iterable[Mapping[str, Any]],
    target_ms: int,
    index: int,
) -> CameraState:
    start_ms = int(segment.get("start_ms", 0) or 0)
    end_ms = max(start_ms + 1, int(segment.get("end_ms", start_ms + 1000) or (start_ms + 1000)))
    local = ease_in_out((target_ms - start_ms) / max(1, end_ms - start_ms))
    energy = _clamp(float(segment.get("energy_level", 0.4) or 0.4))
    mode = _mode_for_segment(segment)
    focus_label = _focus_label(segment, performer_focus, start_ms)
    target = targets.get(focus_label) or targets.get("wide") or CameraTarget("wide", _scene_center(scene), 0.4, "fallback")
    center = _scene_center(scene)
    radius = _scene_radius(scene)
    depth_boost = max(20.0, scene.capability_report.depth_span * 0.55)
    angle = (index * 0.85) + (local * math.pi * (0.7 + energy))
    if mode == "orbit":
        position = (
            center[0] + math.cos(angle) * radius,
            center[1] + radius * (0.34 + energy * 0.18),
            center[2] + math.sin(angle) * (radius * 0.62 + depth_boost),
        )
        fov = 48.0 - energy * 5.0
        roll = math.sin(angle) * 1.8
    elif mode == "fly_through":
        position = (
            _lerp(center[0] - radius * 0.8, center[0] + radius * 0.72, local),
            center[1] + radius * (0.22 + energy * 0.18),
            _lerp(center[2] - radius * 0.72 - depth_boost, center[2] + radius * 0.46, local),
        )
        fov = 54.0 - energy * 7.0
        roll = math.sin(local * math.pi * 2.0) * 2.2
    elif mode == "chase":
        shake = math.sin(target_ms * 0.021) * energy * 5.0
        position = (
            target.position[0] - radius * (0.42 - energy * 0.12),
            target.position[1] + radius * (0.2 + energy * 0.15) + shake,
            target.position[2] - radius * (0.5 + energy * 0.26),
        )
        fov = 50.0 - energy * 12.0
        roll = math.sin(target_ms * 0.033) * energy * 4.5
    elif mode == "focus":
        side = -1.0 if index % 2 else 1.0
        drift = math.sin(local * math.pi * 2.0) * radius * 0.08
        position = (
            target.position[0] + side * radius * 0.34 + drift,
            target.position[1] + radius * 0.26 + (math.sin(local * math.pi) * radius * 0.04),
            target.position[2] - radius * 0.58 + (drift * 0.35),
        )
        fov = 42.0 - energy * 4.0
        roll = side * 0.8
    else:
        pull = 1.0 + local * 0.35
        position = (
            center[0],
            center[1] + radius * 0.46,
            center[2] - radius * pull - depth_boost,
        )
        fov = 58.0 + local * 5.0
        roll = 0.0
    look_at = _lerp3(center, target.position, 0.74 if mode in {"focus", "chase"} else 0.38)
    tilt = math.degrees(math.atan2(look_at[1] - position[1], max(1.0, abs(look_at[2] - position[2]))))
    return CameraState(
        timestamp_ms=target_ms,
        position=tuple(round(v, 3) for v in position),
        target=tuple(round(v, 3) for v in look_at),
        velocity=(0.0, 0.0, 0.0),
        fov=round(max(28.0, min(72.0, fov)), 3),
        zoom=round(60.0 / max(1.0, fov), 3),
        roll=round(roll, 3),
        tilt=round(tilt, 3),
        mode=mode,
        target_label=target.label,
        energy_level=round(energy, 3),
    )


def smooth_camera_states(states: Iterable[CameraState], smoothing: float = 0.34) -> list[CameraState]:
    sorted_states = sorted(states, key=lambda state: state.timestamp_ms)
    if not sorted_states:
        return []
    alpha = _clamp(smoothing, 0.0, 0.9)
    out: list[CameraState] = []
    prev = sorted_states[0]
    out.append(prev)
    for state in sorted_states[1:]:
        dt_s = max(0.001, (state.timestamp_ms - prev.timestamp_ms) / 1000.0)
        position = _lerp3(state.position, prev.position, alpha)
        target = _lerp3(state.target, prev.target, alpha * 0.72)
        velocity = tuple((position[idx] - prev.position[idx]) / dt_s for idx in range(3))
        smoothed = CameraState(
            timestamp_ms=state.timestamp_ms,
            position=tuple(round(v, 3) for v in position),
            target=tuple(round(v, 3) for v in target),
            velocity=tuple(round(v, 3) for v in velocity),
            fov=round(_lerp(state.fov, prev.fov, alpha * 0.6), 3),
            zoom=round(_lerp(state.zoom, prev.zoom, alpha * 0.6), 3),
            roll=round(_lerp(state.roll, prev.roll, alpha * 0.7), 3),
            tilt=round(_lerp(state.tilt, prev.tilt, alpha * 0.5), 3),
            mode=state.mode,
            target_label=state.target_label,
            energy_level=state.energy_level,
        )
        out.append(smoothed)
        prev = smoothed
    return out


def _timeline_segments(band_sync_payload: Mapping[str, Any] | None, song_length_ms: int) -> list[Mapping[str, Any]]:
    timeline = list((band_sync_payload or {}).get("timeline", []) or [])
    if timeline:
        return sorted(timeline, key=lambda item: int(item.get("start_ms", 0) or 0))
    frames = list((band_sync_payload or {}).get("state_frames", []) or [])
    if frames:
        return [
            {
                "start_ms": int(frame.get("start_ms", 0) or 0),
                "end_ms": int(frame.get("end_ms", 0) or 0),
                "energy_level": max(dict(frame.get("performer_intensity", {}) or {}).values() or [0.35]),
                "section_type": str(frame.get("state", "groove") or "groove"),
                "density_level": "busy" if float(frame.get("effect_density", 0.4) or 0.4) > 0.66 else "medium",
                "dominant_features": [str(frame.get("primary_focus", "environment") or "environment")],
            }
            for frame in frames
        ]
    return [{"start_ms": 0, "end_ms": max(1000, song_length_ms), "energy_level": 0.35, "section_type": "wide", "density_level": "medium", "dominant_features": ["environment"]}]


def build_camera_path(
    scene: spatial_scene.SpatialScene,
    *,
    band_sync_payload: Mapping[str, Any] | None = None,
    snowman_payload: Mapping[str, Any] | None = None,
    active_models: Iterable[str] = (),
    song_length_ms: int = 0,
    sample_step_ms: int = 500,
) -> dict[str, Any]:
    targets = build_camera_targets(scene, snowman_payload=snowman_payload, active_models=active_models)
    segments = _timeline_segments(band_sync_payload, song_length_ms)
    focus_frames = list((band_sync_payload or {}).get("performer_focus", []) or [])
    desired: list[CameraState] = []
    for idx, segment in enumerate(segments):
        start_ms = int(segment.get("start_ms", 0) or 0)
        end_ms = max(start_ms + sample_step_ms, int(segment.get("end_ms", start_ms + sample_step_ms) or (start_ms + sample_step_ms)))
        marks = list(range(start_ms, end_ms, max(120, int(sample_step_ms))))
        if not marks or marks[-1] != end_ms:
            marks.append(end_ms)
        for mark in marks:
            desired.append(_desired_state(scene=scene, segment=segment, targets=targets, performer_focus=focus_frames, target_ms=mark, index=idx))
    states = smooth_camera_states(desired)
    speeds = [round(_distance((0.0, 0.0, 0.0), state.velocity), 3) for state in states]
    preview = [
        {
            "timestamp_ms": state.timestamp_ms,
            "screen_hint": {
                "x": round((state.target[0] - state.position[0]) / max(1.0, _scene_radius(scene)), 3),
                "y": round((state.target[1] - state.position[1]) / max(1.0, _scene_radius(scene)), 3),
                "depth": round(state.position[2], 3),
            },
            "mode": state.mode,
            "target": state.target_label,
        }
        for state in states
    ]
    return {
        "schema": "helix.camera_path.v1",
        "camera_model": {
            "state_fields": ["position", "target", "velocity", "fov", "zoom", "roll", "tilt"],
            "coordinate_space": "layout_world_xyz",
            "capability": scene.capability,
        },
        "path": [state.to_dict() for state in states],
        "targets": {label: target.to_dict() for label, target in targets.items()},
        "preview": {
            "type": "camera_path_samples",
            "sample_step_ms": int(sample_step_ms),
            "states": preview,
            "demo_video_hint": "Use these camera states to drive a 3D preview renderer or overlay camera HUD in the projected MP4 preview.",
        },
        "export": {
            "format": "json",
            "attach_to_sequence_payload_key": "camera_path",
            "modes": list(CAMERA_MODES),
        },
        "debug": {
            "camera_path_timeline": [
                f"{state.timestamp_ms}ms {state.mode} -> {state.target_label} pos={state.position} fov={state.fov}"
                for state in states[:400]
            ],
            "position_logs": [state.to_dict() for state in states[:400]],
            "speed_graph": speeds[:400],
            "max_speed": max(speeds) if speeds else 0.0,
            "state_count": len(states),
            "smoothing": "ease_in_out segment sampling plus exponential position/target smoothing",
        },
    }
