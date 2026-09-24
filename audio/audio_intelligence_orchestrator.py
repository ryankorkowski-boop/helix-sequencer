from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams_from_file
from audio.musical_event_model import MusicalEvent, MusicalEventMap, clamp01


@dataclass(frozen=True)
class AudioIntelligenceConfig:
    """Conservative first-pass configuration for the normalized event layer."""

    drum_confidence_min: float = 0.45
    beat_confidence_min: float = 0.55


def _duration_ms(path: Path) -> int:
    try:
        import librosa

        return int(round(float(librosa.get_duration(path=str(path))) * 1000.0))
    except Exception:
        return 0


def _drum_type(event: Any) -> str:
    value = getattr(event, "drum_type", None)
    if value is None:
        value = getattr(event, "kind", "drum_hit")
    return str(value).lower().replace(" ", "_")


def build_musical_event_map(
    audio_path: Path,
    *,
    config: AudioIntelligenceConfig = AudioIntelligenceConfig(),
) -> MusicalEventMap:
    """Build the first normalized musical-event layer without changing XSQ generation.

    This deliberately consumes existing Helix drum analysis rather than replacing it.
    Additional providers can be attached later without changing downstream consumers.
    """

    path = Path(audio_path)
    result = MusicalEventMap(
        duration_ms=_duration_ms(path),
        providers=["helix.drum_detection"],
    )

    if not path.exists():
        result.diagnostics["error"] = f"audio_not_found:{path}"
        return result

    streams = detect_drum_event_streams_from_file(
        path,
        DrumDetectionConfig(low_confidence_min=0.0),
    )

    count = 0
    suppressed = 0
    for stream_name, events in streams.items():
        for raw in events:
            confidence = clamp01(float(getattr(raw, "confidence", 0.0)))
            if confidence < config.drum_confidence_min:
                suppressed += 1
                continue
            timestamp = float(getattr(raw, "timestamp", 0.0))
            strength = clamp01(float(getattr(raw, "velocity", confidence)))
            kind = _drum_type(raw)
            result.add(
                MusicalEvent(
                    time_ms=max(0, int(round(timestamp * 1000.0))),
                    kind=f"drum_{kind}",
                    confidence=confidence,
                    strength=strength,
                    source="helix.drum_detection",
                    instrument=kind,
                    metadata={
                        "stream": stream_name,
                        "cluster_id": getattr(raw, "cluster_id", None),
                        "features": dict(getattr(raw, "frequency_band_info", {}) or {}),
                    },
                )
            )
            count += 1

    result.diagnostics.update(
        {
            "drum_events_emitted": count,
            "drum_events_suppressed": suppressed,
            "confidence_threshold": config.drum_confidence_min,
        }
    )
    result.sort()
    return result
