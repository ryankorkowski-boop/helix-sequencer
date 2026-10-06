from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DRUM_STREAM_KEYS = ("kick_events", "snare_events", "tom_events", "hihat_events", "cymbal_events", "drum_bus_events")

@dataclass(frozen=True)
class DrumEvent:
    timestamp: float
    velocity: float
    confidence: float
    frequency_band_info: dict[str, Any]
    cluster_id: int | None
    drum_type: str
    source: str = "drum_detection"
    @property
    def timestamp_ms(self) -> int: return int(round(self.timestamp * 1000.0))
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class DrumClassifierThresholds:
    # Recall is useful for isolated drum stems, but full mixes must reject tonal
    # instrument attacks. HPSS alone is not sufficient: guitar pick attacks can
    # leak into the percussive component and look like sharp drum onsets.
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
    harmonic_contamination_max: float = 0.82
    tonal_flatness_max: float = 0.018
    tonal_spread_max: float = 0.32
    min_percussive_ratio: float = 0.16
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
    """Classify with the historically approved V3 decision order.

    The b27e8d77 oracle behavior is preserved for spectral/transient profiles.
    Newer HPSS evidence is used only as a rejection guard when those fields are
    present, so callers that predate the extra evidence keep their old result.
    """
    low = _clamp(features.get("low_ratio", 0.0))
    mid_low = _clamp(features.get("mid_low_ratio", 0.0))
    mid = _clamp(features.get("mid_ratio", 0.0))
    high = _clamp(features.get("high_ratio", 0.0))
    centroid = float(features.get("centroid_hz", 0.0) or 0.0)
    low_centroid = float(features.get("low_centroid_hz", centroid) or centroid)
    spread = _clamp(features.get("spectral_spread01", 0.0))
    sharp = _clamp(features.get("transient_sharpness", 0.0))
    decay = _clamp(features.get("decay_profile", 0.0))

    has_percussive = "percussive_ratio" in features
    has_flatness = "spectral_flatness" in features
    percussive_ratio = _clamp(features.get("percussive_ratio", 1.0))
    flatness = _clamp(features.get("spectral_flatness", 1.0))
    harmonic_contamination = _clamp(features.get("harmonic_contamination", 1.0 - percussive_ratio))

    if has_percussive and percussive_ratio < thresholds.min_percussive_ratio:
        return "drum_bus", 0.0
    if (
        has_percussive
        and has_flatness
        and harmonic_contamination > thresholds.harmonic_contamination_max
        and flatness < thresholds.tonal_flatness_max
        and spread < thresholds.tonal_spread_max
    ):
        return "drum_bus", 0.0

    # Preserve the known-good b27e8d77 rule order.
    if low >= thresholds.kick_low_ratio_min and low_centroid <= thresholds.kick_low_centroid_max:
        confidence = _clamp(
            (low * 0.55)
            + (0.25 * (1.0 - min(1.0, low_centroid / 700.0)))
            + (sharp * 0.20)
        )
        return "kick", round(confidence, 3)

    if (
        high >= thresholds.hihat_high_ratio_min
        and decay <= thresholds.hihat_decay_max
        and sharp >= thresholds.snare_sharpness_min
    ):
        confidence = _clamp((high * 0.55) + (sharp * 0.30) + ((1.0 - decay) * 0.15))
        return "hihat", round(confidence, 3)

    if high >= thresholds.cymbal_high_ratio_min and decay >= thresholds.cymbal_decay_min:
        confidence = _clamp((high * 0.45) + (decay * 0.35) + (spread * 0.20))
        return "cymbal", round(confidence, 3)

    if (
        mid >= thresholds.snare_mid_ratio_min
        and sharp >= thresholds.snare_sharpness_min
        and high < 0.60
        and mid_low < 0.35
    ):
        confidence = _clamp(
            (mid * 0.48)
            + (sharp * 0.30)
            + (spread * 0.12)
            + ((1.0 - high) * 0.10)
        )
        return "snare", round(confidence, 3)

    if mid_low >= thresholds.tom_mid_low_ratio_min and high < 0.50 and centroid < 2200:
        confidence = _clamp(
            (mid_low * 0.52)
            + (1.0 - min(1.0, abs(centroid - 900.0) / 1800.0)) * 0.20
            + (decay * 0.18)
            + (sharp * 0.10)
        )
        return "tom", round(confidence, 3)

    candidates: list[tuple[str, float]] = [
        ("kick", (low * 0.55) + ((1.0 - min(1.0, low_centroid / 1200.0)) * 0.25) + (sharp * 0.20)),
        ("snare", (mid * 0.42) + (sharp * 0.32) + (spread * 0.18) + (mid_low * 0.08)),
        ("tom", (mid_low * 0.48) + ((1.0 - abs(centroid - 900.0) / 1800.0) * 0.22) + (decay * 0.16) + (sharp * 0.14)),
        ("hihat", (high * 0.56) + (sharp * 0.28) + ((1.0 - decay) * 0.16)),
        ("cymbal", (high * 0.42) + (decay * 0.36) + (spread * 0.22)),
    ]
    drum_type, score = max(candidates, key=lambda item: item[1])

    if drum_type == "kick" and low < thresholds.kick_low_ratio_min:
        score *= 0.78
    if drum_type == "snare" and mid < thresholds.snare_mid_ratio_min:
        score *= 0.78
    if drum_type == "tom" and mid_low < thresholds.tom_mid_low_ratio_min:
        score *= 0.76
    if drum_type == "hihat" and high < thresholds.hihat_high_ratio_min:
        score *= 0.72
    if drum_type == "cymbal" and (high < thresholds.cymbal_high_ratio_min or decay < thresholds.cymbal_decay_min):
        score *= 0.78

    confidence = _clamp(score)
    if confidence < thresholds.low_confidence_min:
        return "drum_bus", round(confidence, 3)
    return drum_type, round(confidence, 3)


def classify_tom_class(features: dict[str, float], thresholds: DrumClassifierThresholds = DrumClassifierThresholds()) -> tuple[str, float]:
    if float(features.get("mid_low_ratio", 0.0) or 0.0) < thresholds.tom_mid_low_ratio_min:
        return "mid", 0.0
    return _tom_class_for_features(features)
