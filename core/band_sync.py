from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


PERFORMERS = ("singer", "drummer", "guitarist", "bassist", "environment")
STATE_NAMES = ("idle", "build", "groove", "chorus", "breakdown", "climax")


@dataclass(frozen=True)
class TimelineSegment:
    start_ms: int
    end_ms: int
    energy_level: float
    section_type: str
    density_level: str
    dominant_features: list[str]
    phrase_id: str
    repetition_signature: str


@dataclass(frozen=True)
class BandStateFrame:
    start_ms: int
    end_ms: int
    state: str
    performer_intensity: dict[str, float]
    effect_density: float
    motion_amplitude: float
    lighting_style: str
    primary_focus: str


@dataclass(frozen=True)
class EnergyDistribution:
    start_ms: int
    end_ms: int
    total_budget: float
    allocations: dict[str, float]
    dominant_features: list[str]
    focus: str


@dataclass(frozen=True)
class ConflictRule:
    start_ms: int
    end_ms: int
    rule: str
    severity: float
    recommendation: str
    affected_performers: list[str]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _start_ms(obj: Any) -> int:
    return int(getattr(obj, "start_ms", getattr(obj, "start", 0)) or 0)


def _end_ms(obj: Any) -> int:
    start = _start_ms(obj)
    return max(start + 1, int(getattr(obj, "end_ms", getattr(obj, "end", start + 1)) or (start + 1)))


def _label(obj: Any) -> str:
    return str(getattr(obj, "name", getattr(obj, "label", "verse")) or "verse").lower().replace(" ", "_").replace("-", "_")


def _energy(obj: Any) -> float:
    return _clamp(float(getattr(obj, "energy_level", getattr(obj, "energy", 0.5)) or 0.5))


def _marks_in(start_ms: int, end_ms: int, marks: Iterable[int]) -> int:
    return sum(1 for mark in marks if start_ms <= int(mark) < end_ms)


def _events_in(start_ms: int, end_ms: int, events: Iterable[Any]) -> int:
    return sum(1 for event in events if start_ms <= _start_ms(event) < end_ms)


def _flatten_drum_events(streams: Mapping[str, Iterable[Any]] | None) -> list[Any]:
    out: list[Any] = []
    for events in (streams or {}).values():
        out.extend(list(events or []))
    return out


def _density_label(value: float) -> str:
    if value >= 0.72:
        return "busy"
    if value >= 0.34:
        return "medium"
    return "sparse"


def _state_for(section: str, energy: float, density: str, dominant: list[str]) -> str:
    section = section.lower()
    if section in {"chorus", "post_chorus"}:
        return "climax" if energy >= 0.86 else "chorus"
    if section in {"drop"}:
        return "climax"
    if section in {"breakdown"}:
        return "breakdown"
    if section in {"pre_chorus", "build"} or (energy >= 0.68 and density != "sparse"):
        return "build"
    if energy <= 0.18 and density == "sparse":
        return "idle"
    return "groove"


def _dominant_features(
    start_ms: int,
    end_ms: int,
    *,
    vocal_peaks: Iterable[int],
    bass_peaks: Iterable[int],
    drum_events: Iterable[Any],
    note_events: Iterable[Any],
    background_vocals: Iterable[Any],
) -> list[str]:
    span_s = max(0.25, (end_ms - start_ms) / 1000.0)
    scores = {
        "vocals": _marks_in(start_ms, end_ms, vocal_peaks) / span_s,
        "bass": _marks_in(start_ms, end_ms, bass_peaks) / span_s,
        "drums": _events_in(start_ms, end_ms, drum_events) / span_s,
        "guitar": _events_in(start_ms, end_ms, note_events) / span_s,
        "harmony": _events_in(start_ms, end_ms, background_vocals) / span_s,
    }
    ranked = sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)
    selected = [name for name, score in ranked if score > 0.01][:3]
    return selected or ["environment"]


def build_global_music_timeline(
    *,
    parts: list[Any],
    beat_ms: list[int],
    onset_ms: list[int],
    vocal_peaks: list[int],
    bass_peaks: list[int],
    drum_event_streams: Mapping[str, Iterable[Any]] | None = None,
    note_events: list[Any] | None = None,
    background_vocal_events: list[Any] | None = None,
    song_length_ms: int | None = None,
) -> list[TimelineSegment]:
    drum_events = _flatten_drum_events(drum_event_streams)
    notes = list(note_events or [])
    bg = list(background_vocal_events or [])
    raw_parts = list(parts or [])
    if not raw_parts:
        end = song_length_ms or max([0, *beat_ms, *onset_ms, *vocal_peaks, *bass_peaks]) + 1000
        raw_parts = [type("Part", (), {"label": "verse", "start_ms": 0, "end_ms": end, "energy": 0.5})()]
    segments: list[TimelineSegment] = []
    seen_section: dict[str, int] = {}
    for idx, part in enumerate(raw_parts):
        start = _start_ms(part)
        end = _end_ms(part)
        section = _label(part)
        energy = _energy(part)
        span_s = max(0.25, (end - start) / 1000.0)
        event_density = (
            _marks_in(start, end, onset_ms)
            + _events_in(start, end, drum_events)
            + _events_in(start, end, notes)
            + _marks_in(start, end, vocal_peaks)
        ) / max(1.0, span_s * 5.0)
        density = _density_label(_clamp(event_density))
        dominant = _dominant_features(
            start,
            end,
            vocal_peaks=vocal_peaks,
            bass_peaks=bass_peaks,
            drum_events=drum_events,
            note_events=notes,
            background_vocals=bg,
        )
        seen_section[section] = seen_section.get(section, 0) + 1
        phrase_id = f"phrase_{idx + 1:02d}"
        repetition = f"{section}_{seen_section[section]}"
        segments.append(TimelineSegment(start, end, energy, section, density, dominant, phrase_id, repetition))
    return segments


def primary_focus_for_segment(segment: TimelineSegment) -> str:
    dominant = segment.dominant_features
    if "vocals" in dominant or "harmony" in dominant:
        return "singer"
    if "drums" in dominant or segment.section_type in {"drop", "breakdown"}:
        return "drummer"
    if "bass" in dominant and "guitar" not in dominant:
        return "bassist"
    if "guitar" in dominant:
        return "guitarist"
    return "environment"


def distribute_energy(segment: TimelineSegment, focus: str | None = None) -> EnergyDistribution:
    focus = focus or primary_focus_for_segment(segment)
    budget = _clamp(0.18 + segment.energy_level * 0.74 + (0.08 if segment.density_level == "busy" else 0.0))
    base = {name: 0.10 for name in PERFORMERS}
    for feature in segment.dominant_features:
        if feature == "vocals":
            base["singer"] += 0.28
        elif feature == "harmony":
            base["guitarist"] += 0.12
            base["bassist"] += 0.12
            base["singer"] += 0.12
        elif feature == "drums":
            base["drummer"] += 0.30
        elif feature == "bass":
            base["bassist"] += 0.24
        elif feature == "guitar":
            base["guitarist"] += 0.22
    base[focus] = base.get(focus, 0.0) + 0.22
    if segment.section_type in {"chorus", "drop", "post_chorus"}:
        base["environment"] += 0.16
    total = sum(base.values()) or 1.0
    allocations = {name: round(_clamp((value / total) * budget, 0.03, 0.82), 3) for name, value in base.items()}
    if sum(1 for value in allocations.values() if value > 0.55) > 2:
        for name in allocations:
            if name != focus:
                allocations[name] = round(allocations[name] * 0.82, 3)
    return EnergyDistribution(segment.start_ms, segment.end_ms, round(budget, 3), allocations, segment.dominant_features, focus)


def build_band_state_frames(timeline: list[TimelineSegment]) -> list[BandStateFrame]:
    frames: list[BandStateFrame] = []
    for segment in timeline:
        focus = primary_focus_for_segment(segment)
        distribution = distribute_energy(segment, focus)
        state = _state_for(segment.section_type, segment.energy_level, segment.density_level, segment.dominant_features)
        style = {
            "idle": "dim_hold",
            "groove": "locked_rhythm",
            "build": "rising_motion",
            "chorus": "wide_bright",
            "breakdown": "percussive_sparse",
            "climax": "full_band_peak",
        }[state]
        frames.append(
            BandStateFrame(
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                state=state,
                performer_intensity=distribution.allocations,
                effect_density=round(_clamp(distribution.total_budget * (1.0 if segment.density_level == "busy" else 0.78)), 3),
                motion_amplitude=round(_clamp(segment.energy_level * (1.15 if state in {"build", "climax"} else 0.86)), 3),
                lighting_style=style,
                primary_focus=focus,
            )
        )
    return frames


def build_phrase_motifs(timeline: list[TimelineSegment]) -> list[dict[str, Any]]:
    motifs: list[dict[str, Any]] = []
    section_counts: dict[str, int] = {}
    for segment in timeline:
        section_counts[segment.section_type] = section_counts.get(segment.section_type, 0) + 1
        occurrence = section_counts[segment.section_type]
        motif = {
            "phrase_id": segment.phrase_id,
            "section_type": segment.section_type,
            "repetition_signature": segment.repetition_signature,
            "motif_family": f"{segment.section_type}_language",
            "variation": "intensified" if occurrence > 1 and segment.section_type in {"chorus", "drop"} else "base" if occurrence == 1 else "variation",
            "reuse_hint": "reuse core direction/palette; vary density and accent timing",
        }
        motifs.append(motif)
    return motifs


def resolve_effect_conflicts(frames: list[BandStateFrame]) -> list[ConflictRule]:
    rules: list[ConflictRule] = []
    for frame in frames:
        high = [name for name, value in frame.performer_intensity.items() if value >= 0.42]
        if len(high) >= 4 and frame.state != "climax":
            rules.append(
                ConflictRule(
                    frame.start_ms,
                    frame.end_ms,
                    "too_many_bright_performers",
                    0.72,
                    f"Keep {frame.primary_focus} primary; dim support performers by 15-30 percent.",
                    high,
                )
            )
        if frame.effect_density >= 0.82 and frame.motion_amplitude >= 0.78 and frame.state not in {"climax", "build"}:
            rules.append(
                ConflictRule(
                    frame.start_ms,
                    frame.end_ms,
                    "motion_density_collision",
                    0.64,
                    "Stagger motion effects by 40-120ms and prefer one spatial direction.",
                    list(frame.performer_intensity),
                )
            )
    return rules


def build_spatial_coherence(frames: list[BandStateFrame]) -> list[dict[str, Any]]:
    directions = ("left_to_right", "center_out", "right_to_left", "bottom_to_top")
    out: list[dict[str, Any]] = []
    for idx, frame in enumerate(frames):
        if frame.state in {"chorus", "climax"}:
            direction = "center_out"
            origin = frame.primary_focus
        elif frame.state == "breakdown":
            direction = "bottom_to_top"
            origin = "drummer"
        else:
            direction = directions[idx % len(directions)]
            origin = frame.primary_focus
        out.append(
            {
                "start_ms": frame.start_ms,
                "end_ms": frame.end_ms,
                "direction": direction,
                "origin": origin,
                "rule": "all moving effects in this window should honor direction/origin unless explicitly scored as counterpoint",
            }
        )
    return out


def debug_payload(timeline: list[TimelineSegment], frames: list[BandStateFrame], distributions: list[EnergyDistribution]) -> dict[str, Any]:
    return {
        "timeline_state_log": [
            f"{frame.start_ms}-{frame.end_ms} {frame.state} focus={frame.primary_focus} style={frame.lighting_style}"
            for frame in frames
        ],
        "performer_intensity_over_time": [
            {"start_ms": frame.start_ms, "end_ms": frame.end_ms, **frame.performer_intensity}
            for frame in frames
        ],
        "energy_distribution_graph": [
            f"{dist.start_ms}-{dist.end_ms} budget={dist.total_budget:.2f} "
            + " ".join(f"{name}:{value:.2f}" for name, value in dist.allocations.items())
            for dist in distributions
        ],
        "detected_sections": [
            {
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "section_type": segment.section_type,
                "energy_level": segment.energy_level,
                "density_level": segment.density_level,
                "dominant_features": segment.dominant_features,
            }
            for segment in timeline
        ],
    }


def build_band_sync_plan(
    *,
    parts: list[Any],
    beat_ms: list[int],
    onset_ms: list[int],
    vocal_peaks: list[int],
    bass_peaks: list[int],
    note_events: list[Any] | None = None,
    background_vocal_events: list[Any] | None = None,
    drum_event_streams: Mapping[str, Iterable[Any]] | None = None,
    song_length_ms: int | None = None,
) -> dict[str, Any]:
    timeline = build_global_music_timeline(
        parts=parts,
        beat_ms=beat_ms,
        onset_ms=onset_ms,
        vocal_peaks=vocal_peaks,
        bass_peaks=bass_peaks,
        drum_event_streams=drum_event_streams,
        note_events=note_events,
        background_vocal_events=background_vocal_events,
        song_length_ms=song_length_ms,
    )
    frames = build_band_state_frames(timeline)
    distributions = [distribute_energy(segment, frame.primary_focus) for segment, frame in zip(timeline, frames)]
    conflicts = resolve_effect_conflicts(frames)
    spatial = build_spatial_coherence(frames)
    motifs = build_phrase_motifs(timeline)
    return {
        "schema": "helix.band_sync.v1",
        "timeline": [asdict(segment) for segment in timeline],
        "state_frames": [asdict(frame) for frame in frames],
        "energy_distributions": [asdict(item) for item in distributions],
        "phrase_motifs": motifs,
        "performer_focus": [
            {"start_ms": frame.start_ms, "end_ms": frame.end_ms, "primary_focus": frame.primary_focus, "state": frame.state}
            for frame in frames
        ],
        "conflict_rules": [asdict(rule) for rule in conflicts],
        "spatial_coherence": spatial,
        "debug": debug_payload(timeline, frames, distributions),
    }
