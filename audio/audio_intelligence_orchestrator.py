from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams_from_file
from audio.drum_event_fusion import fuse_drum_events
from audio.musical_event_model import MusicalEvent, MusicalEventMap, clamp01
from core.audio_intelligence import AudioAnalysisConfig, build_stem_analysis


@dataclass(frozen=True)
class AudioIntelligenceConfig:
    """Configuration for the renderer-neutral audio intelligence layer."""

    drum_confidence_min: float = 0.45
    stem_confidence_min: float = 0.40
    use_stem_analysis: bool = True
    use_moises: bool = False
    drum_fusion_tolerance_ms: int = 45
    drum_fusion_support_gain: float = 0.22


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
    """Collect existing Helix detectors, normalize them, then fuse drum evidence.

    This is an adapter layer: existing analysis engines remain providers and the
    existing Sequence Plan / XSQ writer remain the downstream consumers.
    """

    path = Path(audio_path)
    result = MusicalEventMap(
        duration_ms=_duration_ms(path),
        providers=[],
    )
    if not path.exists():
        result.diagnostics["error"] = f"audio_not_found:{path}"
        return result

    raw_events: list[MusicalEvent] = []
    streams = detect_drum_event_streams_from_file(
        path,
        DrumDetectionConfig(low_confidence_min=0.0),
    )

    direct_count = 0
    direct_suppressed = 0
    for stream_name, events in streams.items():
        for raw in events:
            confidence = clamp01(float(getattr(raw, "confidence", 0.0)))
            if confidence < config.drum_confidence_min:
                direct_suppressed += 1
                continue
            kind = _drum_type(raw)
            raw_events.append(MusicalEvent(
                time_ms=max(0, int(round(float(getattr(raw, "timestamp", 0.0)) * 1000.0))),
                kind=f"drum_{kind}",
                confidence=confidence,
                strength=clamp01(float(getattr(raw, "velocity", confidence))),
                source="helix.drum_detection",
                instrument=kind,
                metadata={
                    "stream": stream_name,
                    "cluster_id": getattr(raw, "cluster_id", None),
                    "features": dict(getattr(raw, "frequency_band_info", {}) or {}),
                },
            ))
            direct_count += 1
    result.providers.append("helix.drum_detection")

    stem_count = 0
    stem_source = "disabled"
    if config.use_stem_analysis:
        try:
            stem = build_stem_analysis(
                path,
                use_moises=config.use_moises,
                api_key=None,
                cache_dir=path.parent / ".helix_audio_cache",
                config=AudioAnalysisConfig(),
            )
            stem_source = stem.source
            result.providers.append(f"helix.stem_analysis:{stem_source}")

            for kind, times, confidence in (
                ("stem_bass_peak", stem.bass_peaks_ms, 0.72),
                ("stem_vocal_peak", stem.vocal_peaks_ms, 0.58),
            ):
                for time_ms in sorted(set(int(t) for t in times)):
                    result.add(MusicalEvent(
                        time_ms=max(0, time_ms),
                        kind=kind,
                        confidence=confidence,
                        strength=0.62,
                        source="helix.stem_analysis",
                        instrument=kind.removeprefix("stem_"),
                    ))
                    stem_count += 1

            for stream_name, events in (stem.drum_event_streams or {}).items():
                for raw in events:
                    confidence = clamp01(float(getattr(raw, "confidence", 0.0)))
                    if confidence < config.stem_confidence_min:
                        continue
                    kind = _drum_type(raw)
                    raw_events.append(MusicalEvent(
                        time_ms=max(0, int(round(float(getattr(raw, "timestamp", 0.0)) * 1000.0))),
                        kind=f"stem_drum_{kind}",
                        confidence=confidence,
                        strength=clamp01(float(getattr(raw, "velocity", confidence))),
                        source="helix.stem_analysis",
                        instrument=kind,
                        metadata={"stream": stream_name},
                    ))
                    stem_count += 1
        except Exception as exc:
            result.diagnostics["stem_analysis_error"] = str(exc)
            stem_source = "error"

    fused, fusion_diagnostics = fuse_drum_events(
        raw_events,
        config=__import__("audio.drum_event_fusion", fromlist=["DrumFusionConfig"]).DrumFusionConfig(
            time_tolerance_ms=config.drum_fusion_tolerance_ms,
            minimum_confidence=config.drum_confidence_min,
            support_gain=config.drum_fusion_support_gain,
        ),
    )
    for event in fused:
        result.add(event)

    result.diagnostics.update({
        "direct_drum_events_emitted": direct_count,
        "direct_drum_events_suppressed": direct_suppressed,
        "stem_events_emitted": stem_count,
        "stem_source": stem_source,
        "fusion": "confidence_weighted_v2",
        **fusion_diagnostics,
    })
    result.sort()
    return result
