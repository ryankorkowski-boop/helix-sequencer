from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from audio.drum_detection import DrumDetectionConfig, detect_drum_event_streams_from_file
from audio.drum_event_fusion import DrumFusionConfig, fuse_drum_events
from audio.musical_event_model import MusicalEvent, MusicalEventMap, clamp01
from audio.instrument_detection import derive_bass_events, derive_guitar_events
from audio.musical_intelligence import (
    MusicalIntelligenceConfig,
    annotate_importance,
    build_adaptive_timing_events,
    detect_chord_groups,
    summarize as summarize_musical_intelligence,
)
from core.audio_intelligence import AudioAnalysisConfig, analyze_audio_file, build_stem_analysis


@dataclass(frozen=True)
class AudioIntelligenceConfig:
    """Configuration for the renderer-neutral audio intelligence layer."""

    drum_confidence_min: float = 0.45
    stem_confidence_min: float = 0.40
    use_stem_analysis: bool = True
    use_moises: bool = False
    drum_fusion_tolerance_ms: int = 45
    drum_fusion_support_gain: float = 0.22
    adaptive_timing: bool = True
    chord_grouping: bool = True
    timing_min_gap_ms: int = 45
    chord_window_ms: int = 85
    import_note_events: bool = True
    import_timing_map: bool = True


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
    beat_ms: list[int] = []
    note_event_count = 0
    timing_event_count = 0

    # Reuse the canonical Helix analysis provider for pitch and timing when
    # available. These events remain renderer-neutral and are additive to the
    # existing drum/stem providers. Failures are intentionally non-fatal so
    # legacy stem-only operation remains available.
    if config.import_note_events or config.import_timing_map:
        try:
            analysis = analyze_audio_file(
                path,
                enable_lyrics=False,
                config=AudioAnalysisConfig(),
            )
            if config.import_timing_map:
                beat_ms = [int(event.time_ms) for event in analysis.beat_events]
                for event in analysis.beat_events:
                    result.add(MusicalEvent(
                        time_ms=max(0, int(event.time_ms)),
                        kind="beat_downbeat" if event.metadata.get("downbeat") else "beat",
                        confidence=clamp01(event.confidence),
                        strength=clamp01(event.strength),
                        source="helix.audio_analysis",
                        metadata={"downbeat": bool(event.metadata.get("downbeat")), "label": event.label},
                    ))
                    timing_event_count += 1
                result.providers.append("helix.audio_analysis:timing")
            if config.import_note_events:
                for note in analysis.note_events:
                    result.add(MusicalEvent(
                        time_ms=max(0, int(note.timestamp_ms)),
                        kind="note_event",
                        confidence=clamp01(note.confidence),
                        strength=clamp01(note.velocity),
                        source="helix.audio_analysis",
                        instrument=note.source_stem,
                        duration_ms=max(0, int(note.duration_ms)),
                        pitch_midi=float(note.midi_note),
                        metadata={
                            "pitch_hz": float(note.pitch_hz),
                            "note_name": note.note_name,
                            "velocity": float(note.velocity),
                            "source_stem": note.source_stem,
                        },
                    ))
                    note_event_count += 1
                result.providers.append("helix.audio_analysis:pitch")
        except Exception as exc:
            result.diagnostics["canonical_audio_analysis_error"] = str(exc)
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
    instrument_count = 0
    instrument_diagnostics: dict[str, Any] = {}
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

            # Keep bass and guitar on the same normalized event bus as drums.
            # Guitar uses provider note events when available; this adapter
            # deliberately remains renderer-neutral.
            bass_events, bass_diag = derive_bass_events(
                stem.bass_peaks_ms,
                (),
                beat_ms=[],
            )
            guitar_onsets: list[int] = []
            for stem_name, details in stem.stem_features.items():
                if stem_name in {"bass", "vocals", "drums"} or not isinstance(details, dict):
                    continue
                for onset in details.get("onset_events", []) or []:
                    if isinstance(onset, dict) and "time_ms" in onset:
                        guitar_onsets.append(int(onset["time_ms"]))
            guitar_events, guitar_diag = derive_guitar_events(
                [SimpleNamespace(start_ms=mark, end_ms=mark + 160, notes=[], velocity=0.62)
                 for mark in sorted(set(guitar_onsets))],
                onset_ms=guitar_onsets,
                beat_ms=[],
            )
            for event in bass_events:
                result.add(MusicalEvent(
                    time_ms=event.start_ms,
                    kind=f"instrument_{event.event_type}",
                    confidence=clamp01(event.confidence),
                    strength=clamp01(event.intensity),
                    source=event.source,
                    instrument=event.performer,
                    duration_ms=max(0, event.end_ms - event.start_ms),
                    pitch_midi=event.pitch_midi,
                    metadata={
                        "performer": event.performer,
                        "reason": event.reason,
                        "note_count": event.note_count,
                    },
                ))
                instrument_count += 1
            for event in guitar_events:
                result.add(MusicalEvent(
                    time_ms=event.start_ms,
                    kind=f"instrument_{event.event_type}",
                    confidence=clamp01(event.confidence),
                    strength=clamp01(event.intensity),
                    source=event.source,
                    instrument=event.performer,
                    duration_ms=max(0, event.end_ms - event.start_ms),
                    pitch_midi=event.pitch_midi,
                    metadata={
                        "performer": event.performer,
                        "reason": event.reason,
                        "note_count": event.note_count,
                    },
                ))
                instrument_count += 1
            instrument_diagnostics = {
                "bass": dict(bass_diag),
                "guitar": dict(guitar_diag),
            }

            # Vocal timing stays renderer-neutral so singer/face mapping can
            # consume the same normalized event stream later.
            for time_ms in sorted(set(int(t) for t in stem.vocal_peaks_ms)):
                result.add(MusicalEvent(
                    time_ms=max(0, time_ms),
                    kind="vocal_onset",
                    confidence=0.58,
                    strength=0.62,
                    source="helix.stem_analysis",
                    instrument="singer",
                    metadata={"performer": "singer", "reason": "vocal_energy_peak"},
                ))
                instrument_count += 1

            for vocal in stem.background_vocal_events or []:
                result.add(MusicalEvent(
                    time_ms=max(0, int(vocal.start_ms)),
                    kind="vocal_harmony",
                    confidence=clamp01(vocal.confidence),
                    strength=clamp01(vocal.energy),
                    source="helix.background_vocal_classifier",
                    instrument="singer",
                    duration_ms=max(0, int(vocal.end_ms - vocal.start_ms)),
                    metadata={
                        "role": vocal.role,
                        "performer_hint": vocal.performer_hint,
                        "reason": vocal.source_reason,
                    },
                ))
                instrument_count += 1

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
        config=DrumFusionConfig(
            time_tolerance_ms=config.drum_fusion_tolerance_ms,
            minimum_confidence=config.drum_confidence_min,
            support_gain=config.drum_fusion_support_gain,
        ),
    )
    for event in fused:
        result.add(event)

    intelligence_config = MusicalIntelligenceConfig(
        timing_min_gap_ms=max(1, config.timing_min_gap_ms),
        chord_window_ms=max(1, config.chord_window_ms),
    )
    downbeats_ms = [
        event.time_ms for event in result.events
        if bool(event.metadata.get("downbeat"))
    ]
    result.events = annotate_importance(
        result.events,
        downbeats_ms=downbeats_ms,
        config=intelligence_config,
    )

    if config.chord_grouping:
        chord_events = detect_chord_groups(
            result.events,
            window_ms=intelligence_config.chord_window_ms,
        )
        result.events.extend(chord_events)

    adaptive_timing_events: list[MusicalEvent] = []
    if config.adaptive_timing:
        adaptive_timing_events = build_adaptive_timing_events(
            result.events,
            beat_ms=[],
            config=intelligence_config,
        )
        result.events.extend(adaptive_timing_events)

    result.diagnostics.update({
        "direct_drum_events_emitted": direct_count,
        "direct_drum_events_suppressed": direct_suppressed,
        "stem_events_emitted": stem_count,
        "instrument_events_emitted": instrument_count,
        "instrument_mapping": instrument_diagnostics,
        "stem_source": stem_source,
        "fusion": "confidence_weighted_v2",
        "musical_intelligence": summarize_musical_intelligence(result.events),
        "adaptive_timing_events": len(adaptive_timing_events),
        "canonical_timing_events_imported": timing_event_count,
        "canonical_note_events_imported": note_event_count,
        "beat_map_available": bool(beat_ms),
        "chord_events": sum(1 for event in result.events if event.kind == "harmony_chord"),
        **fusion_diagnostics,
    })
    result.sort()
    return result
