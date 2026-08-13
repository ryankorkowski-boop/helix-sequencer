from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DRUM_STREAM_KEYS = (
    "kick_events",
    "snare_events",
    "tom_events",
    "hihat_events",
    "cymbal_events",
    "drum_bus_events",
)


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
    def timestamp_ms(self) -> int:
        return int(round(self.timestamp * 1000.0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DrumClassifierThresholds:
    low_confidence_min: float = 0.34
    kick_low_ratio_min: float = 0.24
    kick_low_centroid_max: float = 700.0
    snare_mid_ratio_min: float = 0.20
    snare_sharpness_min: float = 0.08
    tom_mid_low_ratio_min: float = 0.22
    hihat_high_ratio_min: float = 0.38
    hihat_decay_max: float = 0.42
    cymbal_high_ratio_min: float = 0.32
    cymbal_decay_min: float = 0.42


def empty_drum_streams() -> dict[str, list[DrumEvent]]:
    return {key: [] for key in DRUM_STREAM_KEYS}


def stream_key_for_type(drum_type: str) -> str:
    return {
        "kick": "kick_events",
        "snare": "snare_events",
        "tom": "tom_events",
        "hihat": "hihat_events",
        "cymbal": "cymbal_events",
    }.get(str(drum_type), "drum_bus_events")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def classify_drum_hit(
    features: dict[str, float],
    thresholds: DrumClassifierThresholds = DrumClassifierThresholds(),
) -> tuple[str, float]:
    low = _clamp(features.get("low_ratio", 0.0))
    mid_low = _clamp(features.get("mid_low_ratio", 0.0))
    mid = _clamp(features.get("mid_ratio", 0.0))
    high = _clamp(features.get("high_ratio", 0.0))
    centroid = float(features.get("centroid_hz", 0.0) or 0.0)
    low_centroid = float(features.get("low_centroid_hz", centroid) or centroid)
    spread = _clamp(features.get("spectral_spread01", 0.0))
    sharp = _clamp(features.get("transient_sharpness", 0.0))
    decay = _clamp(features.get("decay_profile", 0.0))

    # Evaluate kick from the low-frequency energy itself. A full-spectrum
    # centroid is intentionally not used here because a real kick can share
    # the onset with snare/cymbal energy and therefore have a high overall
    # centroid even when its low-end component is unmistakable.
    if low >= thresholds.kick_low_ratio_min and low_centroid <= thresholds.kick_low_centroid_max:
        confidence = _clamp(
            (low * 0.55)
            + (0.25 * (1.0 - min(1.0, low_centroid / 700.0)))
            + (sharp * 0.20)
        )
        return "kick", round(confidence, 3)

    # Short, high-frequency transients are normally hats; sustained high
    # frequency energy is handled as cymbal below.
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
