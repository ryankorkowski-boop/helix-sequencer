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
    hihat_high_ratio_min: float = 0.38
    hihat_decay_max: float = 0.42
    cymbal_high_ratio_min: float = 0.32
    cymbal_decay_min: float = 0.68
    cymbal_percussive_ratio_min: float = 0.28
    cymbal_flatness_min: float = 0.035
    hihat_percussive_ratio_min: float = 0.22
    harmonic_contamination_max: float = 0.55
    ambiguous_margin_min: float = 0.08

def empty_drum_streams() -> dict[str, list[DrumEvent]]: return {key: [] for key in DRUM_STREAM_KEYS}

def stream_key_for_type(drum_type: str) -> str:
    return {"kick":"kick_events","snare":"snare_events","tom":"tom_events","hihat":"hihat_events","cymbal":"cymbal_events"}.get(str(drum_type), "drum_bus_events")

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float: return max(low, min(high, float(value)))

def score_drum_hit_families(
    features: dict[str, float],
    thresholds: DrumClassifierThresholds = DrumClassifierThresholds(),
) -> dict[str, float]:
    """Return independent confidence scores for each supported drum family.

    Unlike :func:`classify_drum_hit`, this does not force a single winner.
    Callers that can represent simultaneous hits (for example kick + crash)
    can preserve multiple well-supported families from the same onset.
    """
    low = _clamp(features.get("low_ratio", 0))
    mid_low = _clamp(features.get("mid_low_ratio", 0))
    mid = _clamp(features.get("mid_ratio", 0))
    high = _clamp(features.get("high_ratio", 0))
    centroid = float(features.get("centroid_hz", 0) or 0)
    low_centroid = float(features.get("low_centroid_hz", centroid) or centroid)
    low_flux_peak = float(features.get("low_flux_peak_hz", 0.0) or 0.0)
    has_band_flux = "low_flux_strength" in features or "mid_low_flux_strength" in features
    has_high_flux = "high_flux_strength" in features
    low_flux_strength = _clamp(features.get("low_flux_strength", 0.0))
    mid_low_flux_strength = _clamp(features.get("mid_low_flux_strength", 0.0))
    high_flux_strength = _clamp(features.get("high_flux_strength", 0.0))
    band_flux_strength = max(low_flux_strength, mid_low_flux_strength)
    spread = _clamp(features.get("spectral_spread01", 0))
    sharp = _clamp(features.get("transient_sharpness", 0))
    decay = _clamp(features.get("decay_profile", 0))

    # Older/direct callers may not provide these newer features. Treat missing
    # values as neutral instead of automatically declaring harmonic pollution,
    # and do not apply the richer snare evidence bonuses unless the caller
    # actually supplied those measurements.
    has_snare_detail = any(
        key in features
        for key in ("percussive_ratio", "spectral_flatness", "high_flux_strength")
    )
    percussive_ratio = _clamp(features.get("percussive_ratio", 1.0))
    flatness = _clamp(features.get("spectral_flatness", thresholds.cymbal_flatness_min))
    harmonic_ratio = 1.0 - percussive_ratio

    names = ("kick", "snare", "tom", "hihat", "cymbal")
    strong_low_support = (
        low >= (thresholds.kick_low_ratio_min * 0.65)
        or mid_low >= (thresholds.tom_mid_low_ratio_min * 0.65)
    )
    # HPSS can place the ringing body of tonal drums (especially kick/toms)
    # in the harmonic component. Only reject harmonic contamination when there
    # is no meaningful low-frequency drum evidence.
    if (
        harmonic_ratio > thresholds.harmonic_contamination_max
        and high < thresholds.hihat_high_ratio_min
        and not strong_low_support
    ):
        return {name: 0.0 for name in names}

    kick_peak_support = 0.0
    tom_peak_support = 0.0
    if low_flux_peak > 0.0:
        if 35.0 <= low_flux_peak <= 75.0:
            kick_peak_support = 1.0
        elif 75.0 < low_flux_peak < 130.0:
            kick_peak_support = max(0.0, 1.0 - ((low_flux_peak - 75.0) / 55.0))
        if 82.0 <= low_flux_peak <= 230.0:
            tom_peak_support = 1.0
        else:
            tom_peak_support = max(0.0, 1.0 - (abs(low_flux_peak - 150.0) / 120.0))

    medium_decay = max(0.0, 1.0 - (abs(decay - 0.55) / 0.50))

    scores = {
        "kick": (
            (low * .55)
            + ((1 - min(1, low_centroid / 1200)) * .25)
            + (sharp * .20)
            + (kick_peak_support * .18)
            + (low_flux_strength * .25)
        ),
        "snare": (
            (mid * .42)
            + (sharp * .32)
            + (spread * .18)
            + (mid_low * .08)
            + (
                (flatness * .12)
                + (percussive_ratio * .08)
                + (high * .06)
                + (medium_decay * .20)
                + (high_flux_strength * .26)
                if has_snare_detail
                else 0.0
            )
        ),
        "tom": (
            (mid_low * .48)
            + (max(0, 1 - abs(centroid - 900) / 1800) * .22)
            + (decay * .16)
            + (sharp * .14)
            + (tom_peak_support * .28)
            + (band_flux_strength * .22)
        ),
        "hihat": (high * .48) + (sharp * .24) + ((1 - decay) * .14) + (percussive_ratio * .14),
        "cymbal": (high * .34) + (decay * .24) + (spread * .12) + (percussive_ratio * .20) + (flatness * .10),
    }

    if low < thresholds.kick_low_ratio_min and not (
        35.0 <= low_flux_peak <= 75.0 and low_flux_strength >= 0.20
    ):
        scores["kick"] *= .78
    if low_flux_peak > 78.0:
        scores["kick"] *= .55
    if mid < thresholds.snare_mid_ratio_min:
        scores["snare"] *= .78
    if mid_low < thresholds.tom_mid_low_ratio_min:
        scores["tom"] *= .76
    if 0.0 < low_flux_peak < 75.0:
        scores["tom"] *= .65
    if has_band_flux and band_flux_strength < 0.30:
        scores["tom"] *= .40
    if high < thresholds.hihat_high_ratio_min:
        scores["hihat"] *= .72
    if decay > thresholds.hihat_decay_max:
        scores["hihat"] *= .62
    if (
        high < thresholds.cymbal_high_ratio_min
        or decay < thresholds.cymbal_decay_min
        or percussive_ratio < thresholds.cymbal_percussive_ratio_min
        or flatness < thresholds.cymbal_flatness_min
    ):
        scores["cymbal"] *= .60
    if has_high_flux and high_flux_strength < 0.40:
        scores["cymbal"] *= .48

    return {name: round(_clamp(score), 3) for name, score in scores.items()}


def classify_drum_hit(
    features: dict[str, float],
    thresholds: DrumClassifierThresholds = DrumClassifierThresholds(),
) -> tuple[str, float]:
    """Backward-compatible single-label classifier.

    The richer detector uses :func:`score_drum_hit_families` directly so
    simultaneous compatible families are not discarded. This function keeps
    the legacy confidence/margin gate for callers that require one label.
    """
    scores = score_drum_hit_families(features, thresholds)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best, score = ranked[0]
    runner = ranked[1][1]
    if score < thresholds.low_confidence_min or (score - runner) < thresholds.ambiguous_margin_min:
        return "drum_bus", round(score, 3)
    return best, round(score, 3)

