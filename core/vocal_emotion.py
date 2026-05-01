from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from core import vocal_timeline as vt


EMOTION_TYPES = (
    "happy",
    "sad",
    "aggressive",
    "calm",
    "energetic",
    "melancholic",
    "triumphant",
    "mysterious",
    "neutral",
)

EMOTION_PALETTES = {
    "happy": {"palette": "warm_gold", "primary": "#ffd166", "accent": "#ff9f1c", "motion_style": "bouncy"},
    "sad": {"palette": "cool_blue", "primary": "#6aa6ff", "accent": "#8ecae6", "motion_style": "slow_fade"},
    "aggressive": {"palette": "hot_red_white", "primary": "#ff2d2d", "accent": "#ffffff", "motion_style": "sharp_punch"},
    "calm": {"palette": "soft_aqua", "primary": "#86e3ce", "accent": "#d0f4de", "motion_style": "breathing"},
    "energetic": {"palette": "electric_pop", "primary": "#faff00", "accent": "#00bbf9", "motion_style": "quick_pulse"},
    "melancholic": {"palette": "blue_violet", "primary": "#7b68ee", "accent": "#80bfff", "motion_style": "drift"},
    "triumphant": {"palette": "gold_white", "primary": "#ffd700", "accent": "#ffffff", "motion_style": "wide_lift"},
    "mysterious": {"palette": "deep_teal_magenta", "primary": "#2ec4b6", "accent": "#9b5de5", "motion_style": "slow_orbit"},
    "neutral": {"palette": "balanced_white", "primary": "#f8f9fa", "accent": "#adb5bd", "motion_style": "steady"},
}

POSITIVE_WORDS = {
    "alive",
    "beautiful",
    "bright",
    "celebrate",
    "dance",
    "dream",
    "free",
    "glad",
    "happy",
    "heart",
    "joy",
    "light",
    "love",
    "shine",
    "smile",
    "summer",
    "sweet",
}
NEGATIVE_WORDS = {
    "alone",
    "blue",
    "broken",
    "cold",
    "cry",
    "dark",
    "down",
    "fall",
    "gone",
    "hurt",
    "lost",
    "never",
    "pain",
    "rain",
    "sad",
    "tears",
}
AGGRESSIVE_WORDS = {
    "battle",
    "burn",
    "fight",
    "fire",
    "hard",
    "rage",
    "riot",
    "run",
    "scream",
    "shout",
    "strike",
    "thunder",
}
CALM_WORDS = {
    "breathe",
    "calm",
    "dream",
    "float",
    "gentle",
    "home",
    "moon",
    "peace",
    "quiet",
    "sleep",
    "snow",
    "soft",
    "still",
}
TRIUMPH_WORDS = {"rise", "king", "queen", "victory", "win", "glory", "higher", "together", "forever"}
MYSTERY_WORDS = {"ghost", "hidden", "midnight", "mist", "mystery", "secret", "shadow", "whisper"}


@dataclass(frozen=True)
class VocalEmotionEvent:
    start_ms: int
    end_ms: int
    emotion_type: str
    intensity: float
    confidence: float
    lyric_text: str
    section: str
    source_reason: str

    @property
    def timestamp(self) -> int:
        return self.start_ms

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp
        return data


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z']+", text or "")]


def _count(tokens: Iterable[str], lexicon: set[str]) -> int:
    return sum(1 for token in tokens if token in lexicon)


def _section_at(song_parts: Iterable[Any], target_ms: int) -> str:
    target_s = target_ms / 1000.0
    for part in song_parts:
        start_s = float(getattr(part, "start_time", getattr(part, "start_ms", 0) / 1000.0) or 0.0)
        end_s = float(getattr(part, "end_time", getattr(part, "end_ms", 0) / 1000.0) or 0.0)
        if start_s <= target_s < end_s:
            return str(getattr(part, "name", getattr(part, "label", "section")) or "section").lower()
    return "section"


def _marks_in(start_ms: int, end_ms: int, marks: Iterable[int]) -> int:
    return sum(1 for mark in marks if start_ms <= int(mark) < end_ms)


def _curve_mean(multiband: Any, attr: str, start_ms: int, end_ms: int) -> float:
    values = getattr(multiband, attr, None)
    times = getattr(multiband, "frame_times_s", None)
    if values is None:
        return 0.0
    try:
        seq = list(values)
    except TypeError:
        return 0.0
    if not seq:
        return 0.0
    if times is None:
        return float(sum(float(v) for v in seq) / max(1, len(seq)))
    try:
        time_seq = list(times)
    except TypeError:
        return 0.0
    selected = [
        float(value)
        for value, time_s in zip(seq, time_seq)
        if start_ms <= int(round(float(time_s) * 1000.0)) < end_ms
    ]
    if not selected:
        return 0.0
    return float(sum(selected) / len(selected))


def _lyric_scores(text: str) -> dict[str, float]:
    words = _tokens(text)
    total = max(1, len(words))
    pos = _count(words, POSITIVE_WORDS) / total
    neg = _count(words, NEGATIVE_WORDS) / total
    aggro = _count(words, AGGRESSIVE_WORDS) / total
    calm = _count(words, CALM_WORDS) / total
    triumph = _count(words, TRIUMPH_WORDS) / total
    mystery = _count(words, MYSTERY_WORDS) / total
    return {
        "happy": pos * 1.2,
        "sad": neg,
        "aggressive": aggro * 1.25,
        "calm": calm,
        "energetic": (pos + aggro) * 0.65,
        "melancholic": neg * 0.8 + calm * 0.35,
        "triumphant": triumph * 1.3 + pos * 0.35,
        "mysterious": mystery * 1.2,
        "neutral": 0.08 if words else 0.22,
    }


def _tone_scores(
    *,
    start_ms: int,
    end_ms: int,
    vocal_peaks_ms: Iterable[int],
    multiband: Any,
    section: str,
) -> dict[str, float]:
    span_s = max(0.25, (end_ms - start_ms) / 1000.0)
    peak_density = _clamp(_marks_in(start_ms, end_ms, vocal_peaks_ms) / max(1.0, span_s * 2.5))
    brightness = _clamp(_curve_mean(multiband, "spectral_centroid01", start_ms, end_ms))
    motion = _clamp(_curve_mean(multiband, "mfcc_motion01", start_ms, end_ms))
    pitch_motion = _clamp(_curve_mean(multiband, "pitch_motion01", start_ms, end_ms))
    section_energy = {
        "chorus": 0.22,
        "post_chorus": 0.2,
        "drop": 0.26,
        "build": 0.2,
        "pre_chorus": 0.18,
        "bridge": 0.02,
        "breakdown": -0.08,
        "intro": -0.06,
        "outro": -0.08,
    }.get(section, 0.0)
    energy = _clamp((peak_density * 0.48) + (brightness * 0.22) + (motion * 0.22) + 0.2 + section_energy)
    return {
        "energetic": energy * 0.8 + motion * 0.18,
        "aggressive": max(0.0, energy - 0.52) * 0.7 + brightness * 0.14,
        "triumphant": max(0.0, energy - 0.48) * 0.55 + (0.16 if section in {"chorus", "drop"} else 0.0),
        "calm": max(0.0, 0.55 - energy) * 0.75,
        "mysterious": max(0.0, 0.44 - brightness) * 0.4 + max(0.0, 0.38 - motion) * 0.25,
        "melancholic": max(0.0, 0.5 - energy) * 0.35,
        "happy": max(0.0, energy - 0.42) * 0.25 + max(0.0, pitch_motion - 0.45) * 0.15,
        "sad": max(0.0, 0.42 - energy) * 0.35,
        "neutral": 0.08,
    }


def _choose_emotion(scores: Mapping[str, float], previous: str | None) -> str:
    ranked = sorted(EMOTION_TYPES, key=lambda name: (scores.get(name, 0.0), name), reverse=True)
    best = ranked[0] if ranked else "neutral"
    if previous and previous != best:
        previous_score = float(scores.get(previous, 0.0))
        best_score = float(scores.get(best, 0.0))
        if best_score - previous_score < 0.16:
            return previous
    return best


def _smooth_events(events: list[VocalEmotionEvent], *, min_hold_ms: int = 420) -> list[VocalEmotionEvent]:
    if not events:
        return []
    out: list[VocalEmotionEvent] = []
    previous = events[0]
    for event in events[1:]:
        if event.emotion_type != previous.emotion_type and event.start_ms - previous.start_ms < min_hold_ms:
            blended = VocalEmotionEvent(
                start_ms=event.start_ms,
                end_ms=event.end_ms,
                emotion_type=previous.emotion_type,
                intensity=round((previous.intensity * 0.45) + (event.intensity * 0.55), 3),
                confidence=round(min(previous.confidence, event.confidence) * 0.92, 3),
                lyric_text=event.lyric_text,
                section=event.section,
                source_reason=f"smoothed_from_{event.emotion_type}",
            )
            out.append(previous)
            previous = blended
            continue
        out.append(previous)
        previous = event
    out.append(previous)
    return out


def build_vocal_emotion_timeline(
    *,
    lyric_timeline: vt.LyricTimeline,
    song_parts: Iterable[Any],
    vocal_peaks_ms: Iterable[int] = (),
    multiband: Any = None,
) -> dict[str, Any]:
    raw_events: list[VocalEmotionEvent] = []
    previous: str | None = None
    lines = list(lyric_timeline.lines)
    if not lines and lyric_timeline.words:
        lines = [vt.LyricLine(words=[word], start_time=word.start_time, end_time=word.end_time, confidence=word.confidence) for word in lyric_timeline.words]
    for line in lines:
        start_ms = int(round(line.start_time * 1000.0))
        end_ms = max(start_ms + 120, int(round(line.end_time * 1000.0)))
        section = _section_at(song_parts, start_ms)
        lyric_scores = _lyric_scores(line.text)
        tone_scores = _tone_scores(
            start_ms=start_ms,
            end_ms=end_ms,
            vocal_peaks_ms=vocal_peaks_ms,
            multiband=multiband,
            section=section,
        )
        combined = {
            emotion: (lyric_scores.get(emotion, 0.0) * 0.62) + (tone_scores.get(emotion, 0.0) * 0.38)
            for emotion in EMOTION_TYPES
        }
        emotion = _choose_emotion(combined, previous)
        previous = emotion
        score = _clamp(combined.get(emotion, 0.0))
        tone_energy = max(tone_scores.get("energetic", 0.0), tone_scores.get("aggressive", 0.0), tone_scores.get("triumphant", 0.0))
        intensity = _clamp(0.22 + (score * 0.72) + (tone_energy * 0.22))
        confidence = _clamp((float(line.confidence) * 0.52) + (min(1.0, score + 0.25) * 0.34) + (0.14 if line.text.strip() else 0.0))
        raw_events.append(
            VocalEmotionEvent(
                start_ms=start_ms,
                end_ms=end_ms,
                emotion_type=emotion,
                intensity=round(intensity, 3),
                confidence=round(confidence, 3),
                lyric_text=line.text,
                section=section,
                source_reason="lyric_sentiment_tone_section",
            )
        )
    events = _smooth_events(raw_events)
    return {
        "schema": "helix.vocal_emotion.v1",
        "events": [event.to_dict() for event in events],
        "raw_events": [event.to_dict() for event in raw_events],
        "palettes": EMOTION_PALETTES,
        "debug": {
            "event_count": len(events),
            "raw_event_count": len(raw_events),
            "smoothing_window_ms": 420,
            "sources": ["lyrics", "vocal_peaks", "pitch_or_brightness_curves", "song_section_context"],
            "fallback": "rule_based_lexicon_and_energy_heuristics",
        },
    }


def emotion_at(events: Iterable[Mapping[str, Any]], target_ms: int) -> Mapping[str, Any]:
    best: Mapping[str, Any] | None = None
    best_distance: int | None = None
    for event in events:
        start_ms = int(event.get("start_ms", 0) or 0)
        end_ms = int(event.get("end_ms", start_ms) or start_ms)
        if start_ms <= target_ms < end_ms:
            return event
        distance = min(abs(target_ms - start_ms), abs(target_ms - end_ms))
        if best_distance is None or distance < best_distance:
            best = event
            best_distance = distance
    return best or {"emotion_type": "neutral", "intensity": 0.2, "confidence": 0.25}


def face_expression_for(
    performer: str,
    emotion: Mapping[str, Any],
    base_intensity: float,
) -> dict[str, Any]:
    emotion_type = str(emotion.get("emotion_type", "neutral") or "neutral")
    intensity = _clamp(float(emotion.get("intensity", 0.2) or 0.2))
    confidence = _clamp(float(emotion.get("confidence", 0.25) or 0.25))
    if performer == "lead_singer":
        amplitude = 1.0
        transition = "expressive"
    elif performer in {"guitarist", "bassist"}:
        amplitude = 0.48
        transition = "smooth"
    elif performer == "drummer":
        amplitude = 0.24 if intensity >= 0.72 else 0.0
        transition = "spike_only"
    else:
        amplitude = 0.38
        transition = "smooth"
    palette = EMOTION_PALETTES.get(emotion_type, EMOTION_PALETTES["neutral"])
    scaled = _clamp(base_intensity * (0.74 + intensity * 0.72 * amplitude))
    if performer in {"guitarist", "bassist"}:
        scaled = min(0.46, scaled)
    elif performer == "drummer":
        scaled = min(0.4, scaled)
    brightness = _clamp((0.16 + intensity * 0.78) * amplitude + (0.12 if performer == "lead_singer" else 0.0))
    mouth_scale = _clamp(0.7 + intensity * 0.62 * amplitude, 0.42, 1.4)
    motion_amplitude = _clamp(intensity * amplitude)
    return {
        "emotion_type": emotion_type,
        "emotion_intensity": round(intensity, 3),
        "emotion_confidence": round(confidence, 3),
        "intensity": round(scaled, 3),
        "mouth_intensity_scale": round(mouth_scale, 3),
        "brightness": round(brightness, 3),
        "palette": palette["palette"],
        "primary_color": palette["primary"],
        "accent_color": palette["accent"],
        "motion_style": palette["motion_style"],
        "motion_amplitude": round(motion_amplitude, 3),
        "transition_style": transition,
        "eye_glow": bool(performer == "lead_singer" and intensity >= 0.48),
        "body_micro_motion": round(_clamp(0.08 + motion_amplitude * 0.42), 3),
    }


def apply_emotion_to_face_cues(face_cues: Iterable[Mapping[str, Any]], emotion_payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events = list(emotion_payload.get("events", []) or [])
    out: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    for cue in face_cues:
        item = dict(cue)
        start_ms = int(item.get("start_ms", 0) or 0)
        performer = str(item.get("performer", "lead_singer") or "lead_singer")
        base_intensity = float(item.get("intensity", item.get("strength", 0.6)) or 0.6)
        emotion = emotion_at(events, start_ms)
        expression = face_expression_for(performer, emotion, base_intensity)
        item["intensity"] = expression["intensity"]
        item["emotion"] = expression
        item["mouth_intensity_scale"] = expression["mouth_intensity_scale"]
        item["brightness"] = expression["brightness"]
        item["palette"] = expression["palette"]
        item["effect_scoring_hint"] = {
            "emotion_type": expression["emotion_type"],
            "brightness": expression["brightness"],
            "motion_style": expression["motion_style"],
            "avoid_conflict": "limit simultaneous bright face effects when confidence is low",
        }
        item["spatial_emotion_hint"] = {
            "enabled": expression["emotion_confidence"] >= 0.42,
            "family": "face_centered_glow" if performer == "lead_singer" else "support_face_wash",
            "strength": round(expression["brightness"] * expression["emotion_confidence"], 3),
        }
        out.append(item)
        logs.append(
            {
                "start_ms": start_ms,
                "performer": performer,
                "emotion_type": expression["emotion_type"],
                "base_intensity": round(base_intensity, 3),
                "mapped_intensity": expression["intensity"],
                "mouth_intensity_scale": expression["mouth_intensity_scale"],
                "palette": expression["palette"],
            }
        )
    return out, logs
