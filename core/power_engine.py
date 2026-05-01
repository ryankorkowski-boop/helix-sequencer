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

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_amps_by_circuit": dict(self.max_amps_by_circuit),
            "overload_events": list(self.overload_events),
            "corrections_applied": list(self.corrections_applied),
            "frames_adjusted": int(self.frames_adjusted),
            "safe_after_processing": bool(self.safe_after_processing),
        }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


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
    watts_by_prop: dict[str, float] = {}
    watts_by_circuit: dict[str, float] = {cid: 0.0 for cid in circuits_by_id.keys()}
    amps_by_circuit: dict[str, float] = {cid: 0.0 for cid in circuits_by_id.keys()}
    overload_events: list[dict[str, Any]] = []

    for state in frame.props:
        meta = props_by_id.get(state.prop_id)
        if meta is None:
            continue
        watts = estimate_prop_watts(meta, state.active_pixel_fraction, state.intensity_fraction)
        watts_by_prop[state.prop_id] = watts
        watts_by_circuit[meta.circuit_id] = watts_by_circuit.get(meta.circuit_id, 0.0) + watts

    for circuit_id, watts in watts_by_circuit.items():
        circuit = circuits_by_id.get(circuit_id)
        if circuit is None:
            continue
        amps = watts / max(1e-6, float(circuit.voltage))
        amps_by_circuit[circuit_id] = amps
        overload = amps - circuit.safe_amps
        if overload > 0.0:
            overload_events.append(
                {
                    "timestamp_ms": int(frame.timestamp_ms),
                    "circuit_id": circuit_id,
                    "amps": round(float(amps), 6),
                    "safe_amps": round(float(circuit.safe_amps), 6),
                    "overload_amps": round(float(overload), 6),
                }
            )

    return {
        "timestamp_ms": int(frame.timestamp_ms),
        "watts_by_prop": watts_by_prop,
        "watts_by_circuit": watts_by_circuit,
        "amps_by_circuit": amps_by_circuit,
        "safe_amps_by_circuit": {cid: circuits_by_id[cid].safe_amps for cid in circuits_by_id.keys()},
        "overload_events": overload_events,
    }


def analyze_power(
    *,
    frames: list[FrameInput],
    props: list[PropPowerMeta],
    circuits: list[CircuitMeta],
) -> tuple[list[dict[str, Any]], PowerEngineReport]:
    """Scaffold pass: compute frame-level estimates and overloads without correction."""
    props_by_id = {item.prop_id: item for item in props}
    circuits_by_id = {item.circuit_id: item for item in circuits}
    frame_logs: list[dict[str, Any]] = []
    max_amps_by_circuit: dict[str, float] = {item.circuit_id: 0.0 for item in circuits}
    overload_events: list[dict[str, Any]] = []

    for frame in frames:
        row = estimate_frame(frame, props_by_id, circuits_by_id)
        frame_logs.append(row)
        for circuit_id, amps in (row.get("amps_by_circuit") or {}).items():
            max_amps_by_circuit[circuit_id] = max(float(max_amps_by_circuit.get(circuit_id, 0.0)), float(amps))
        overload_events.extend(list(row.get("overload_events") or []))

    report = PowerEngineReport(
        max_amps_by_circuit={key: round(float(value), 6) for key, value in max_amps_by_circuit.items()},
        overload_events=overload_events,
        corrections_applied=[],
        frames_adjusted=0,
        safe_after_processing=(len(overload_events) == 0),
    )
    return frame_logs, report

