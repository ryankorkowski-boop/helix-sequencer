from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DRUM_STREAM_KEYS = ("kick_events", "snare_events", "tom_events", "hihat_events", "cymbal_events", "drum_bus_events")

@dataclass(frozen=True)
class DrumEvent:
    timestamp: float
    velocity: float
    confidence: float
    frequency_band_info: dict[str, float]
    cluster_id: int | None
    drum_type: str
    source: str = "drum_detection"
    @property
    def timestamp_ms(self) -> int: return int(round(self.timestamp * 1000.0))
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class DrumClassifierThresholds:
    low_confidence_min: float = 0.34
    kick_low_ratio_min: float = 0.24
    kick_low_centroid_max: float = 700.0
    snare_mid_ratio_min: float = 0.20
    snare_sharpness_min: float = 0.08
    tom_mid_low_ratio_min: float = 0.22
    tom_high_centroid_min: float = 520.0
    tom_mid_centroid_min: float = 760.0
    tom_floor_centroid_max: float = 520.0
    hihat_high_ratio_min: float = 0.38
    hihat_decay_max: float = 0.42
    cymbal_high_ratio_min: float = 0.32
    cymbal_decay_min: float = 0.42
    cymbal_percussive_ratio_min: float = 0.28
    cymbal_flatness_min: float = 0.035
    hihat_percussive_ratio_min: float = 0.22
    harmonic_contamination_max: float = 0.55
    ambiguous_margin_min: float = 0.08

def empty_drum_streams() -> dict[str, list[DrumEvent]]: return {key: [] for key in DRUM_STREAM_KEYS}

def stream_key_for_type(drum_type: str) -> str:
    return {"kick":"kick_events","snare":"snare_events","tom":"tom_events","hihat":"hihat_events","cymbal":"cymbal_events"}.get(str(drum_type), "drum_bus_events")

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float: return max(low, min(high, float(value)))

def _tom_class_for_features(features: dict[str, float]) -> tuple[str, float]:
    """Return high/mid/floor plus confidence from the detected tom spectral center."""
    centroid = float(features.get("centroid_hz", 0.0) or 0.0)
    low_centroid = float(features.get("low_centroid_hz", centroid) or centroid)
    mid_low = _clamp(features.get("mid_low_ratio", 0.0))
    candidates = [
        ("floor", max(0.0, 1.0 - abs(low_centroid - 380.0) / 700.0) * 0.55 + max(0.0, 1.0 - abs(centroid - 480.0) / 1200.0) * 0.25 + mid_low * 0.20),
        ("high", max(0.0, 1.0 - abs(low_centroid - 650.0) / 900.0) * 0.45 + max(0.0, 1.0 - abs(centroid - 900.0) / 1600.0) * 0.35 + mid_low * 0.20),
        ("mid", max(0.0, 1.0 - abs(low_centroid - 900.0) / 1100.0) * 0.45 + max(0.0, 1.0 - abs(centroid - 1300.0) / 1800.0) * 0.35 + mid_low * 0.20),
    ]
    ranked = sorted(candidates, key=lambda item: item[1], reverse=True)
    return ranked[0][0], _clamp(ranked[0][1] - ranked[1][1] + 0.55)

def classify_drum_hit(features: dict[str, float], thresholds: DrumClassifierThresholds = DrumClassifierThresholds()) -> tuple[str, float]:
    low=_clamp(features.get("low_ratio",0)); mid_low=_clamp(features.get("mid_low_ratio",0)); mid=_clamp(features.get("mid_ratio",0)); high=_clamp(features.get("high_ratio",0))
    centroid=float(features.get("centroid_hz",0) or 0); low_centroid=float(features.get("low_centroid_hz",centroid) or centroid)
    spread=_clamp(features.get("spectral_spread01",0)); sharp=_clamp(features.get("transient_sharpness",0)); decay=_clamp(features.get("decay_profile",0)); percussive_ratio=_clamp(features.get("percussive_ratio",0)); flatness=_clamp(features.get("spectral_flatness",0))
    harmonic_ratio=1.0-percussive_ratio
    if harmonic_ratio > thresholds.harmonic_contamination_max and high < thresholds.hihat_high_ratio_min:
        return "drum_bus", 0.0
    candidates=[
        ("kick",(low*.55)+((1-min(1,low_centroid/1200))*.25)+(sharp*.20)),
        ("snare",(mid*.42)+(sharp*.32)+(spread*.18)+(mid_low*.08)),
        ("tom",(mid_low*.48)+(max(0,1-abs(centroid-900)/1800)*.22)+(decay*.16)+(sharp*.14)),
        ("hihat",(high*.48)+(sharp*.24)+((1-decay)*.14)+(percussive_ratio*.14)),
        ("cymbal",(high*.34)+(decay*.24)+(spread*.12)+(percussive_ratio*.20)+(flatness*.10)),
    ]
    ranked=sorted(candidates,key=lambda item:item[1],reverse=True)
    best, score=ranked[0]; runner=ranked[1][1]
    if best=="kick" and low < thresholds.kick_low_ratio_min: score*=.78
    if best=="snare" and mid < thresholds.snare_mid_ratio_min: score*=.78
    if best=="tom" and mid_low < thresholds.tom_mid_low_ratio_min: score*=.76
    if best=="hihat" and high < thresholds.hihat_high_ratio_min: score*=.72
    if best=="cymbal" and (high<thresholds.cymbal_high_ratio_min or decay<thresholds.cymbal_decay_min or percussive_ratio<thresholds.cymbal_percussive_ratio_min or flatness<thresholds.cymbal_flatness_min): score*=.60
    score=_clamp(score)
    if score < thresholds.low_confidence_min or (score-runner) < thresholds.ambiguous_margin_min:
        return "drum_bus", round(score,3)
    return best, round(score,3)


def classify_tom_class(features: dict[str, float], thresholds: DrumClassifierThresholds = DrumClassifierThresholds()) -> tuple[str, float]:
    """Classify an already-detected tom as high, mid, or floor using its spectral center."""
    if float(features.get("mid_low_ratio", 0.0) or 0.0) < thresholds.tom_mid_low_ratio_min:
        return "mid", 0.0
    return _tom_class_for_features(features)
