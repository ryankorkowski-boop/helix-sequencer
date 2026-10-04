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
    # These are deliberately recall-oriented for mixed real music. HPSS is already
    # used upstream, so requiring a clean isolated percussive signal here caused
    # real snare/tom hits to collapse into drum_bus.
    low_confidence_min: float = 0.27
    kick_low_ratio_min: float = 0.18
    kick_low_centroid_max: float = 800.0
    snare_mid_ratio_min: float = 0.14
    snare_sharpness_min: float = 0.04
    tom_mid_low_ratio_min: float = 0.16
    tom_high_centroid_min: float = 520.0
    tom_mid_centroid_min: float = 760.0
    tom_floor_centroid_max: float = 520.0
    hihat_high_ratio_min: float = 0.28
    hihat_decay_max: float = 0.50
    cymbal_high_ratio_min: float = 0.25
    cymbal_decay_min: float = 0.35
    cymbal_percussive_ratio_min: float = 0.18
    cymbal_flatness_min: float = 0.025
    hihat_percussive_ratio_min: float = 0.14
    harmonic_contamination_max: float = 0.85
    ambiguous_margin_min: float = 0.035

def empty_drum_streams() -> dict[str, list[DrumEvent]]: return {key: [] for key in DRUM_STREAM_KEYS}

def stream_key_for_type(drum_type: str) -> str:
    return {"kick":"kick_events","snare":"snare_events","tom":"tom_events","hihat":"hihat_events","cymbal":"cymbal_events"}.get(str(drum_type), "drum_bus_events")

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float: return max(low, min(high, float(value)))

def _tom_class_for_features(features: dict[str, float]) -> tuple[str, float]:
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

    candidates=[
        ("kick", (low*.58) + ((1-min(1,low_centroid/1400))*.22) + (sharp*.20)),
        ("snare", (mid*.44) + (sharp*.28) + (spread*.18) + (high*.06) + (mid_low*.04)),
        ("tom", (mid_low*.46) + (max(0,1-abs(centroid-950)/1900)*.22) + (decay*.18) + (sharp*.10) + (low*.04)),
        ("hihat", (high*.48) + (sharp*.20) + ((1-decay)*.16) + (percussive_ratio*.16)),
        ("cymbal", (high*.34) + (decay*.24) + (spread*.14) + (percussive_ratio*.18) + (flatness*.10)),
    ]
    ranked=sorted(candidates,key=lambda item:item[1],reverse=True)
    best, score=ranked[0]; runner=ranked[1][1]
    if best=="kick" and low < thresholds.kick_low_ratio_min: score*=.78
    if best=="snare" and mid < thresholds.snare_mid_ratio_min: score*=.80
    if best=="tom" and mid_low < thresholds.tom_mid_low_ratio_min: score*=.80
    if best=="hihat" and high < thresholds.hihat_high_ratio_min: score*=.78
    if best=="cymbal" and (high<thresholds.cymbal_high_ratio_min or decay<thresholds.cymbal_decay_min): score*=.70
    score=_clamp(score)

    # drum_bus is now a last-resort label, not the normal outcome for a mixed track.
    # Only use it when there is genuinely too little discriminating information.
    discriminating_energy = max(low, mid_low, mid, high)
    if discriminating_energy < 0.055 or score < thresholds.low_confidence_min or (score-runner) < thresholds.ambiguous_margin_min:
        # Preserve a useful typed hit when the winner is materially stronger than
        # the others even if the absolute score is modest.
        if score >= 0.22 and (score-runner) >= 0.075:
            return best, round(score,3)
        return "drum_bus", round(score,3)
    return best, round(score,3)


def classify_tom_class(features: dict[str, float], thresholds: DrumClassifierThresholds = DrumClassifierThresholds()) -> tuple[str, float]:
    if float(features.get("mid_low_ratio", 0.0) or 0.0) < thresholds.tom_mid_low_ratio_min:
        return "mid", 0.0
    return _tom_class_for_features(features)
