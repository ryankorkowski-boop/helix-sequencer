from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PropPowerMeta:
    prop_id: str
    pixels: int
    voltage: float
    watts_per_pixel_full_white: float
    circuit_id: str
    priority: str = "background"


@dataclass(frozen=True)
class CircuitMeta:
    circuit_id: str
    breaker_limit_amps: float
    safe_utilization: float = 0.8
    voltage: float = 120.0

    @property
    def safe_amps(self) -> float:
        return max(0.0, float(self.breaker_limit_amps) * float(self.safe_utilization))


@dataclass(frozen=True)
class FramePropState:
    prop_id: str
    active_pixel_fraction: float
    intensity_fraction: float
    is_accent: bool = False
    effect_family: str = "generic"


@dataclass(frozen=True)
class FrameInput:
    timestamp_ms: int
    props: list[FramePropState]


@dataclass
class CorrectionEvent:
    timestamp_ms: int
    circuit_id: str
    overload_amps: float
    action: str
    affected_props: list[str] = field(default_factory=list)


@dataclass
class PowerEngineReport:
    max_amps_by_circuit: dict[str, float]
    overload_events: list[dict[str, Any]]
    corrections_applied: list[dict[str, Any]]
    frames_adjusted: int
    safe_after_processing: bool
    near_limit_events: list[dict[str, Any]] = field(default_factory=list)
    residual_overload_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_amps_by_circuit": dict(self.max_amps_by_circuit),
            "overload_events": list(self.overload_events),
            "corrections_applied": list(self.corrections_applied),
            "frames_adjusted": int(self.frames_adjusted),
            "safe_after_processing": bool(self.safe_after_processing),
            "near_limit_events": list(self.near_limit_events),
            "residual_overload_events": list(self.residual_overload_events),
        }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _state_map_from_frame(frame: FrameInput) -> dict[str, dict[str, Any]]:
    state_map: dict[str, dict[str, Any]] = {}
    for state in frame.props:
        state_map[state.prop_id] = {
            "active_pixel_fraction": _clamp(state.active_pixel_fraction),
            "intensity_fraction": _clamp(state.intensity_fraction),
            "is_accent": bool(state.is_accent),
            "effect_family": str(state.effect_family or "generic").strip().lower(),
        }
    return state_map


def _estimate_frame_from_state_map(
    *,
    timestamp_ms: int,
    state_map: dict[str, dict[str, Any]],
    props_by_id: dict[str, PropPowerMeta],
    circuits_by_id: dict[str, CircuitMeta],
) -> dict[str, Any]:
    watts_by_prop: dict[str, float] = {}
    watts_by_circuit: dict[str, float] = {cid: 0.0 for cid in circuits_by_id.keys()}
    amps_by_circuit: dict[str, float] = {cid: 0.0 for cid in circuits_by_id.keys()}
    overload_events: list[dict[str, Any]] = []
    intensity_by_prop: dict[str, float] = {}

    for prop_id, entry in state_map.items():
        meta = props_by_id.get(prop_id)
        if meta is None:
            continue
        active = _clamp(entry.get("active_pixel_fraction", 0.0))
        intensity = _clamp(entry.get("intensity_fraction", 0.0))
        watts = estimate_prop_watts(meta, active, intensity)
        watts_by_prop[prop_id] = watts
        intensity_by_prop[prop_id] = intensity
        watts_by_circuit[meta.circuit_id] = watts_by_circuit.get(meta.circuit_id, 0.0) + watts

    for circuit_id, watts in watts_by_circuit.items():
        circuit = circuits_by_id.get(circuit_id)
        if circuit is None:
            continue
        amps = watts / max(1e-6, float(circuit.voltage))
        amps_by_circuit[circuit_id] = amps
        overload = amps - circuit.safe_amps
        if overload > 1e-6:
            overload_events.append(
                {
                    "timestamp_ms": int(timestamp_ms),
                    "circuit_id": circuit_id,
                    "amps": round(float(amps), 6),
                    "safe_amps": round(float(circuit.safe_amps), 6),
                    "overload_amps": round(float(overload), 6),
                }
            )

    return {
        "timestamp_ms": int(timestamp_ms),
        "watts_by_prop": watts_by_prop,
        "watts_by_circuit": watts_by_circuit,
        "amps_by_circuit": amps_by_circuit,
        "safe_amps_by_circuit": {cid: circuits_by_id[cid].safe_amps for cid in circuits_by_id.keys()},
        "overload_events": overload_events,
        "intensity_by_prop": intensity_by_prop,
    }


def _is_focal_priority(priority: str) -> bool:
    text = (priority or "").strip().lower()
    return any(key in text for key in ("focal", "vocal", "lead", "primary"))


def _is_support_priority(priority: str) -> bool:
    text = (priority or "").strip().lower()
    return any(key in text for key in ("support", "mid", "secondary"))


def _is_transition_priority(priority: str) -> bool:
    text = (priority or "").strip().lower()
    return any(key in text for key in ("transition", "phrase"))


def _reduction_rank(meta: PropPowerMeta, state: dict[str, Any]) -> float:
    rank = 0.0
    effect_family = str(state.get("effect_family", "")).lower()
    priority = str(meta.priority or "").lower()
    if "wash" in effect_family:
        rank += 2.0
    if bool(state.get("is_accent", False)):
        rank -= 4.0
    if _is_focal_priority(priority):
        rank -= 2.0
    elif _is_transition_priority(priority):
        rank -= 1.0
    elif _is_support_priority(priority):
        rank += 1.0
    else:
        rank += 2.0
    return rank


def _intensity_floor(meta: PropPowerMeta, state: dict[str, Any]) -> float:
    if bool(state.get("is_accent", False)):
        return 0.75
    if _is_focal_priority(meta.priority):
        return 0.6
    if _is_transition_priority(meta.priority):
        return 0.5
    if _is_support_priority(meta.priority):
        return 0.25
    return 0.0


def _reduce_overload_for_circuit(
    *,
    timestamp_ms: int,
    circuit_id: str,
    circuit: CircuitMeta,
    state_map: dict[str, dict[str, Any]],
    props_by_id: dict[str, PropPowerMeta],
    watts_by_prop: dict[str, float],
    watts_by_circuit: dict[str, float],
) -> list[dict[str, Any]]:
    safe_watts = max(0.0, float(circuit.safe_amps) * float(circuit.voltage))
    current_watts = float(watts_by_circuit.get(circuit_id, 0.0))
    excess_watts = current_watts - safe_watts
    if excess_watts <= 1e-9:
        return []

    candidates: list[tuple[float, float, str]] = []
    for prop_id, entry in state_map.items():
        meta = props_by_id.get(prop_id)
        if meta is None or meta.circuit_id != circuit_id:
            continue
        watts = float(watts_by_prop.get(prop_id, 0.0))
        if watts <= 0.0:
            continue
        candidates.append((_reduction_rank(meta, entry), watts, prop_id))
    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)

    corrections: list[dict[str, Any]] = []
    remaining_watts = excess_watts
    for _, _, prop_id in candidates:
        if remaining_watts <= 1e-9:
            break
        meta = props_by_id.get(prop_id)
        if meta is None:
            continue
        entry = state_map.get(prop_id)
        if entry is None:
            continue
        active_fraction = _clamp(entry.get("active_pixel_fraction", 0.0))
        intensity = _clamp(entry.get("intensity_fraction", 0.0))
        base_watts = estimate_prop_watts(meta, active_fraction, 1.0)
        if base_watts <= 1e-9:
            continue
        min_intensity = _intensity_floor(meta, entry)
        max_intensity_drop = max(0.0, intensity - min_intensity)
        max_watts_drop = max_intensity_drop * base_watts
        if max_watts_drop <= 1e-9:
            continue
        watts_drop = min(remaining_watts, max_watts_drop)
        new_intensity = _clamp(intensity - (watts_drop / base_watts))
        entry["intensity_fraction"] = new_intensity
        remaining_watts -= watts_drop
        corrections.append(
            {
                "timestamp_ms": int(timestamp_ms),
                "circuit_id": circuit_id,
                "prop_id": prop_id,
                "action": "compress_intensity",
                "old_intensity": round(float(intensity), 6),
                "new_intensity": round(float(new_intensity), 6),
                "watts_reduced": round(float(watts_drop), 6),
            }
        )

    return corrections


def _apply_peak_smoothing(
    *,
    frames: list[FrameInput],
    frame_state_maps: list[dict[str, dict[str, Any]]],
    props_by_id: dict[str, PropPowerMeta],
    smoothing_window_ms: int,
    spike_ratio: float,
) -> list[dict[str, Any]]:
    if len(frames) < 3:
        return []
    corrections: list[dict[str, Any]] = []
    window_ms = max(0, int(smoothing_window_ms))
    ratio = max(1.0, float(spike_ratio))

    for i in range(1, len(frames) - 1):
        prev_ts = int(frames[i - 1].timestamp_ms)
        curr_ts = int(frames[i].timestamp_ms)
        next_ts = int(frames[i + 1].timestamp_ms)
        if window_ms > 0:
            if (curr_ts - prev_ts) > window_ms or (next_ts - curr_ts) > window_ms:
                continue
        current_states = frame_state_maps[i]
        prev_states = frame_state_maps[i - 1]
        next_states = frame_state_maps[i + 1]

        for prop_id, state in current_states.items():
            meta = props_by_id.get(prop_id)
            if meta is None:
                continue
            if bool(state.get("is_accent", False)) or _is_focal_priority(meta.priority):
                continue
            prev_state = prev_states.get(prop_id)
            next_state = next_states.get(prop_id)
            if prev_state is None or next_state is None:
                continue

            current_intensity = _clamp(state.get("intensity_fraction", 0.0))
            neighbor_mean = 0.5 * (
                _clamp(prev_state.get("intensity_fraction", 0.0))
                + _clamp(next_state.get("intensity_fraction", 0.0))
            )
            if neighbor_mean <= 1e-9:
                continue
            cap = neighbor_mean * ratio
            if current_intensity <= cap:
                continue
            new_intensity = _clamp(cap)
            state["intensity_fraction"] = new_intensity
            corrections.append(
                {
                    "timestamp_ms": curr_ts,
                    "circuit_id": meta.circuit_id,
                    "prop_id": prop_id,
                    "action": "peak_smoothing",
                    "old_intensity": round(float(current_intensity), 6),
                    "new_intensity": round(float(new_intensity), 6),
                }
            )

    return corrections


def estimate_prop_watts(prop: PropPowerMeta, active_pixel_fraction: float, intensity_fraction: float) -> float:
    return (
        _clamp(active_pixel_fraction)
        * _clamp(intensity_fraction)
        * max(0, int(prop.pixels))
        * max(0.0, float(prop.watts_per_pixel_full_white))
    )


def estimate_frame(
    frame: FrameInput,
    props_by_id: dict[str, PropPowerMeta],
    circuits_by_id: dict[str, CircuitMeta],
) -> dict[str, Any]:
    return _estimate_frame_from_state_map(
        timestamp_ms=frame.timestamp_ms,
        state_map=_state_map_from_frame(frame),
        props_by_id=props_by_id,
        circuits_by_id=circuits_by_id,
    )


def analyze_power(
    *,
    frames: list[FrameInput],
    props: list[PropPowerMeta],
    circuits: list[CircuitMeta],
    apply_corrections: bool = True,
    enable_peak_smoothing: bool = True,
    smoothing_window_ms: int = 100,
    near_limit_ratio: float = 0.95,
    spike_ratio: float = 1.35,
) -> tuple[list[dict[str, Any]], PowerEngineReport]:
    """Analyze power and apply optional post-process correction in an isolated module."""
    props_by_id = {item.prop_id: item for item in props}
    circuits_by_id = {item.circuit_id: item for item in circuits}
    frame_state_maps = [_state_map_from_frame(frame) for frame in frames]
    frame_logs: list[dict[str, Any]] = []
    max_amps_by_circuit: dict[str, float] = {item.circuit_id: 0.0 for item in circuits}
    overload_events: list[dict[str, Any]] = []
    residual_overload_events: list[dict[str, Any]] = []
    near_limit_events: list[dict[str, Any]] = []
    corrections_applied: list[dict[str, Any]] = []
    frames_adjusted = 0
    adjusted_timestamps: set[int] = set()

    if enable_peak_smoothing:
        smoothing_corrections = _apply_peak_smoothing(
            frames=frames,
            frame_state_maps=frame_state_maps,
            props_by_id=props_by_id,
            smoothing_window_ms=smoothing_window_ms,
            spike_ratio=spike_ratio,
        )
        corrections_applied.extend(smoothing_corrections)
        adjusted_timestamps.update(int(item["timestamp_ms"]) for item in smoothing_corrections)

    for index, frame in enumerate(frames):
        state_map = frame_state_maps[index]
        row_pre = _estimate_frame_from_state_map(
            timestamp_ms=frame.timestamp_ms,
            state_map=state_map,
            props_by_id=props_by_id,
            circuits_by_id=circuits_by_id,
        )
        overload_events.extend(list(row_pre.get("overload_events") or []))

        if apply_corrections:
            loop_guard = 0
            while True:
                loop_guard += 1
                if loop_guard > 6:
                    break
                row = _estimate_frame_from_state_map(
                    timestamp_ms=frame.timestamp_ms,
                    state_map=state_map,
                    props_by_id=props_by_id,
                    circuits_by_id=circuits_by_id,
                )
                overloaded = [event for event in row.get("overload_events", [])]
                if not overloaded:
                    break
                frame_had_change = False
                for event in overloaded:
                    circuit_id = str(event.get("circuit_id", ""))
                    circuit = circuits_by_id.get(circuit_id)
                    if circuit is None:
                        continue
                    circuit_corrections = _reduce_overload_for_circuit(
                        timestamp_ms=frame.timestamp_ms,
                        circuit_id=circuit_id,
                        circuit=circuit,
                        state_map=state_map,
                        props_by_id=props_by_id,
                        watts_by_prop=dict(row.get("watts_by_prop") or {}),
                        watts_by_circuit=dict(row.get("watts_by_circuit") or {}),
                    )
                    if circuit_corrections:
                        frame_had_change = True
                        corrections_applied.extend(circuit_corrections)
                        adjusted_timestamps.add(int(frame.timestamp_ms))
                if not frame_had_change:
                    break

        row_post = _estimate_frame_from_state_map(
            timestamp_ms=frame.timestamp_ms,
            state_map=state_map,
            props_by_id=props_by_id,
            circuits_by_id=circuits_by_id,
        )
        if row_post.get("overload_events"):
            residual_overload_events.extend(list(row_post.get("overload_events") or []))
        row_post["detected_overload_events"] = list(row_pre.get("overload_events") or [])
        row_post["near_limit_events"] = []

        ratio = max(0.0, float(near_limit_ratio))
        for circuit_id, amps in (row_post.get("amps_by_circuit") or {}).items():
            safe_amps = float(row_post.get("safe_amps_by_circuit", {}).get(circuit_id, 0.0))
            if safe_amps <= 1e-9:
                continue
            if float(amps) >= (safe_amps * ratio):
                event = {
                    "timestamp_ms": int(frame.timestamp_ms),
                    "circuit_id": circuit_id,
                    "amps": round(float(amps), 6),
                    "safe_amps": round(float(safe_amps), 6),
                    "ratio": round(float(amps) / safe_amps, 6),
                }
                near_limit_events.append(event)
                row_post["near_limit_events"].append(event)

        frame_logs.append(row_post)
        for circuit_id, amps in (row_post.get("amps_by_circuit") or {}).items():
            max_amps_by_circuit[circuit_id] = max(float(max_amps_by_circuit.get(circuit_id, 0.0)), float(amps))
    frames_adjusted = len(adjusted_timestamps)
    report = PowerEngineReport(
        max_amps_by_circuit={key: round(float(value), 6) for key, value in max_amps_by_circuit.items()},
        overload_events=overload_events,
        corrections_applied=corrections_applied,
        frames_adjusted=frames_adjusted,
        safe_after_processing=(len(residual_overload_events) == 0),
        near_limit_events=near_limit_events,
        residual_overload_events=residual_overload_events,
    )
    return frame_logs, report

