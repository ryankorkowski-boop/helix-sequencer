from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random
from typing import Callable


@dataclass(frozen=True)
class BirdPhrase:
    species: str
    source: str
    part: str
    start_ms: int
    end_ms: int
    confidence: float


@dataclass
class BirdsongResult:
    enabled: bool
    confidence: float
    profile: str
    calls: int
    echos: int
    sweeps: int
    species_counts: dict[str, int]
    timing_spans: list[tuple[str, int, int]]
    reason: str = ""


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def _as_float_sequence(raw: object) -> list[float]:
    if raw is None:
        return []
    out: list[float] = []
    try:
        for value in raw:  # type: ignore[assignment]
            try:
                fv = float(value)
            except Exception:
                continue
            if math.isfinite(fv):
                out.append(fv)
    except Exception:
        return out
    return out


def _event_midis(event: object) -> list[int]:
    notes = getattr(event, "notes", []) or []
    out: list[int] = []
    for note in notes:
        try:
            midi = int(note[0])
        except Exception:
            continue
        out.append(midi)
    return out


def _event_part(event: object) -> str:
    return str(getattr(event, "part", "VERSE") or "VERSE").upper()


def _species_for_event(source: str, event: object | None, part: str) -> str:
    if source == "vocal" or part in {"CHORUS", "BRIDGE"}:
        return "nightingale"
    mids = _event_midis(event) if event is not None else []
    avg = (sum(mids) / len(mids)) if mids else 64.0
    if avg >= 78:
        return "warbler"
    if avg >= 68:
        return "sparrow"
    if avg >= 58:
        return "finch"
    return "thrush"


def estimate_birdsong_confidence(
    *,
    audio: object,
    hats: list[int],
    vocal_peaks: list[int],
    note_events: list[object],
) -> float:
    duration_s = max(1.0, float(getattr(audio, "dur_s", 0.0) or 0.0))
    centroid = _as_float_sequence(getattr(audio, "centroid", []))
    pitch_hz = _as_float_sequence(getattr(audio, "pitch_hz", []))

    high_centroid_ratio = 0.0
    if centroid:
        high_centroid_ratio = sum(1 for value in centroid if value >= 3000.0) / float(len(centroid))

    pitch_motion_ratio = 0.0
    if len(pitch_hz) >= 2:
        motions = 0
        checks = 0
        prev = None
        for hz in pitch_hz:
            if hz <= 0:
                continue
            if prev is not None and prev > 0:
                checks += 1
                if abs(math.log2(hz / prev)) >= 0.10:
                    motions += 1
            prev = hz
        if checks > 0:
            pitch_motion_ratio = motions / float(checks)

    hat_density = clamp(len(hats) / (duration_s * 2.8), 0.0, 1.0)
    vocal_density = clamp(len(vocal_peaks) / (duration_s * 1.5), 0.0, 1.0)
    note_density = clamp(len(note_events) / (duration_s * 2.2), 0.0, 1.0)

    confidence = (
        0.08
        + (0.36 * high_centroid_ratio)
        + (0.24 * pitch_motion_ratio)
        + (0.17 * hat_density)
        + (0.10 * vocal_density)
        + (0.13 * note_density)
    )
    return clamp(confidence, 0.0, 1.0)


def _compress_times(times_ms: list[int], min_gap_ms: int) -> list[int]:
    out: list[int] = []
    last = -10**9
    gap = max(1, int(min_gap_ms))
    for value in sorted(set(int(t) for t in times_ms if t >= 0)):
        if value - last >= gap:
            out.append(value)
            last = value
    return out


def _pools_by_category(pools: list[object], categories: tuple[str, ...]) -> list[object]:
    wanted = {c.lower() for c in categories}
    selected: list[object] = []
    for pool in pools:
        category = str(getattr(pool, "category", "") or "").lower()
        models = list(getattr(pool, "models", []) or [])
        if category in wanted and models:
            selected.append(pool)
    return selected


def _cycle_model(pool: object, state: dict[str, int]) -> str | None:
    models = list(getattr(pool, "models", []) or [])
    if not models:
        return None
    key = str(getattr(pool, "name", "pool"))
    index = state.get(key, 0) % len(models)
    state[key] = index + 1
    return str(models[index])


def _pick_pool(candidates: list[object], rng: Random) -> object | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    return candidates[rng.randrange(len(candidates))]


def build_bird_phrases(
    *,
    note_events: list[object],
    hats: list[int],
    vocal_peaks: list[int],
    song_length_ms: int,
    intensity: float,
    confidence: float,
) -> list[BirdPhrase]:
    intensity = clamp(intensity, 0.2, 2.2)
    seed_events: list[tuple[int, str, object | None, str]] = []

    for value in hats:
        seed_events.append((int(value), "hat", None, "VERSE"))
    for value in vocal_peaks:
        seed_events.append((int(value), "vocal", None, "CHORUS"))
    for event in note_events:
        start_ms = int(getattr(event, "start_ms", -1))
        if start_ms < 0:
            continue
        seed_events.append((start_ms, "note", event, _event_part(event)))

    seed_events.sort(key=lambda item: item[0])
    min_gap = max(70, int(round(165 - (38 * intensity))))
    compressed_times = _compress_times([item[0] for item in seed_events], min_gap)
    if not compressed_times:
        return []

    event_lookup: dict[int, tuple[str, object | None, str]] = {}
    for when, source, event, part in seed_events:
        event_lookup.setdefault(when, (source, event, part))

    max_phrases = max(12, int((song_length_ms / 1000.0) * (0.9 + (0.85 * intensity) + (0.35 * confidence))))
    phrases: list[BirdPhrase] = []
    for when in compressed_times[:max_phrases]:
        source, event, part = event_lookup.get(when, ("note", None, "VERSE"))
        species = _species_for_event(source, event, part)
        base_dur = {
            "warbler": 150,
            "nightingale": 210,
            "sparrow": 130,
            "finch": 115,
            "thrush": 165,
        }.get(species, 140)
        if part in {"CHORUS", "BRIDGE"}:
            base_dur = int(base_dur * 1.18)
        dur = max(75, int(round(base_dur * (0.70 + (0.45 * intensity)))))
        end_ms = min(song_length_ms, when + dur)
        if end_ms - when < 55:
            continue
        phrases.append(
            BirdPhrase(
                species=species,
                source=source,
                part=part,
                start_ms=when,
                end_ms=end_ms,
                confidence=confidence,
            )
        )
    return phrases


def place_birdsong_engine(
    *,
    audio: object,
    note_events: list[object],
    hats: list[int],
    vocal_peaks: list[int],
    pools: list[object],
    add_model: Callable[..., None],
    in_blackout: Callable[[int], bool],
    rng: Random,
    enabled: bool,
    auto_enable: bool,
    intensity: float,
    min_confidence: float,
    profile: str,
) -> BirdsongResult:
    profile_key = (profile or "wild").strip().lower()
    profile_gain = {
        "wild": 1.00,
        "canopy": 1.18,
        "ambient": 0.75,
        "dawn": 0.92,
    }.get(profile_key, 1.00)

    confidence = estimate_birdsong_confidence(
        audio=audio,
        hats=hats,
        vocal_peaks=vocal_peaks,
        note_events=note_events,
    )
    active = bool(enabled) or (bool(auto_enable) and confidence >= clamp(min_confidence, 0.0, 1.0))
    if not active:
        return BirdsongResult(
            enabled=False,
            confidence=confidence,
            profile=profile_key,
            calls=0,
            echos=0,
            sweeps=0,
            species_counts={},
            timing_spans=[],
            reason="disabled",
        )

    song_length_ms = max(1000, int(round(float(getattr(audio, "dur_s", 0.0) or 0.0) * 1000.0)))
    effective_intensity = clamp(float(intensity) * profile_gain, 0.2, 2.4)
    phrases = build_bird_phrases(
        note_events=note_events,
        hats=hats,
        vocal_peaks=vocal_peaks,
        song_length_ms=song_length_ms,
        intensity=effective_intensity,
        confidence=confidence,
    )
    if not phrases:
        return BirdsongResult(
            enabled=False,
            confidence=confidence,
            profile=profile_key,
            calls=0,
            echos=0,
            sweeps=0,
            species_counts={},
            timing_spans=[],
            reason="no_phrases",
        )

    call_candidates = _pools_by_category(pools, ("stars", "snowflakes", "talking_heads", "matrix", "line"))
    echo_candidates = _pools_by_category(pools, ("line", "arch", "matrix", "mega", "tree"))
    sweep_candidates = _pools_by_category(pools, ("mega", "line", "arch", "canes_combo", "gt", "tree"))

    if not call_candidates:
        return BirdsongResult(
            enabled=False,
            confidence=confidence,
            profile=profile_key,
            calls=0,
            echos=0,
            sweeps=0,
            species_counts={},
            timing_spans=[],
            reason="no_targets",
        )

    call_effect_map = {
        "warbler": "Butterfly",
        "nightingale": "Shimmer",
        "sparrow": "Twinkle",
        "finch": "On",
        "thrush": "Wave",
    }

    state: dict[str, int] = {}
    spans: list[tuple[str, int, int]] = []
    species_counts: dict[str, int] = {}
    calls = 0
    echos = 0
    sweeps = 0

    sweep_interval = max(6, int(round(12 - (2.5 * effective_intensity))))
    for index, phrase in enumerate(phrases):
        if in_blackout(phrase.start_ms):
            continue

        call_pool = _pick_pool(call_candidates, rng)
        if call_pool is None:
            continue
        call_target = _cycle_model(call_pool, state)
        if call_target is None:
            continue

        call_effect = call_effect_map.get(phrase.species, "On")
        stem_key = "vocals" if phrase.source == "vocal" else "other"
        add_model(call_target, phrase.start_ms, phrase.end_ms, "birdsong_call", eff=call_effect, stem=stem_key)
        spans.append((f"{phrase.species.upper()}_CALL", phrase.start_ms, phrase.end_ms))
        species_counts[phrase.species] = species_counts.get(phrase.species, 0) + 1
        calls += 1

        echo_probability = clamp((0.42 + (0.20 * effective_intensity) + (0.18 * confidence)), 0.15, 0.92)
        if echo_candidates and rng.random() <= echo_probability:
            echo_pool = _pick_pool(echo_candidates, rng)
            echo_target = _cycle_model(echo_pool, state) if echo_pool is not None else None
            if echo_target and echo_target != call_target:
                echo_start = min(song_length_ms, phrase.start_ms + int(round(40 + (20 * effective_intensity))))
                echo_end = min(song_length_ms, echo_start + max(65, int(round((phrase.end_ms - phrase.start_ms) * 0.78))))
                if echo_end > echo_start and not in_blackout(echo_start):
                    add_model(echo_target, echo_start, echo_end, "birdsong_echo", eff="On", stem="other")
                    spans.append((f"{phrase.species.upper()}_ECHO", echo_start, echo_end))
                    echos += 1

        if sweep_candidates and index > 0 and (index % sweep_interval) == 0:
            sweep_pool = _pick_pool(sweep_candidates, rng)
            models = list(getattr(sweep_pool, "models", []) or []) if sweep_pool is not None else []
            if models:
                sweep_len = min(5, len(models))
                start = max(0, phrase.start_ms - 70)
                step = max(24, int(round(36 / max(0.6, effective_intensity))))
                for step_idx in range(sweep_len):
                    model = models[(state.get(str(getattr(sweep_pool, "name", "sweep")), 0) + step_idx) % len(models)]
                    seg_st = start + (step_idx * step)
                    seg_en = min(song_length_ms, seg_st + max(75, int(round(95 * effective_intensity))))
                    if seg_en <= seg_st or in_blackout(seg_st):
                        continue
                    add_model(str(model), seg_st, seg_en, "birdsong_sweep", eff="Wave", stem="other")
                spans.append(("FLOCK_SWEEP", start, min(song_length_ms, start + sweep_len * step + 110)))
                sweeps += 1

    return BirdsongResult(
        enabled=(calls > 0),
        confidence=confidence,
        profile=profile_key,
        calls=calls,
        echos=echos,
        sweeps=sweeps,
        species_counts=species_counts,
        timing_spans=spans,
        reason="ok" if calls > 0 else "no_successful_placements",
    )
