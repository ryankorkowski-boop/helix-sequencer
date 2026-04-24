from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping


MOUTH_BY_PHONEME: dict[str, str] = {
    "A": "mouth_A",
    "AH": "mouth_A",
    "AA": "mouth_A",
    "AE": "mouth_A",
    "E": "mouth_E",
    "EH": "mouth_E",
    "EE": "mouth_E",
    "I": "mouth_I",
    "IH": "mouth_I",
    "Y": "mouth_I",
    "O": "mouth_O",
    "OH": "mouth_O",
    "OW": "mouth_O",
    "U": "mouth_U",
    "UW": "mouth_U",
    "M": "mouth_MBP",
    "B": "mouth_MBP",
    "P": "mouth_MBP",
    "MBP": "mouth_MBP",
}

MOUTH_PRIORITY = ("MBP", "AH", "EH", "IH", "OH", "UW")


@dataclass
class PhonemeEvent:
    phoneme: str
    mouth_shape: str
    mouth_submodel: str
    start_time: float
    end_time: float
    confidence: float
    word_text: str = ""
    source: str = "rule_word_timing"

    @property
    def start_ms(self) -> int:
        return int(round(self.start_time * 1000.0))

    @property
    def end_ms(self) -> int:
        return int(round(self.end_time * 1000.0))


@dataclass
class LyricWord:
    text: str
    start_time: float
    end_time: float
    confidence: float = 0.75
    phonemes: list[PhonemeEvent] = field(default_factory=list)

    @property
    def start_ms(self) -> int:
        return int(round(self.start_time * 1000.0))

    @property
    def end_ms(self) -> int:
        return int(round(self.end_time * 1000.0))


@dataclass
class LyricLine:
    words: list[LyricWord]
    start_time: float
    end_time: float
    confidence: float = 0.75

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words).strip()


@dataclass
class LyricTimeline:
    lines: list[LyricLine]
    words: list[LyricWord]
    phoneme_events: list[PhonemeEvent]
    confidence_summary: dict[str, float | int | str]


@dataclass
class SongPart:
    name: str
    start_time: float
    end_time: float
    confidence: float
    energy_level: float
    dominant_sources: list[str]
    repetition_signature: str

    @property
    def start_ms(self) -> int:
        return int(round(self.start_time * 1000.0))

    @property
    def end_ms(self) -> int:
        return int(round(self.end_time * 1000.0))


@dataclass
class PartHit:
    timestamp: float
    part_name: str
    hit_type: str
    strength: float
    confidence: float
    source_reason: str

    @property
    def start_ms(self) -> int:
        return int(round(self.timestamp * 1000.0))


@dataclass(frozen=True)
class VocalRoutingConfig:
    background_vocal_confidence_min: float = 0.42
    background_vocal_energy_min: float = 0.35
    background_vocal_chorus_boost: float = 0.18
    background_face_max_intensity: float = 0.46
    background_face_min_duration: float = 0.10


def _event_start_ms(event: Any) -> int:
    return int(getattr(event, "start_ms", getattr(event, "start", 0)) or 0)


def _event_end_ms(event: Any, fallback_ms: int = 180) -> int:
    start_ms = _event_start_ms(event)
    end_ms = int(getattr(event, "end_ms", getattr(event, "end", start_ms + fallback_ms)) or (start_ms + fallback_ms))
    return max(start_ms + 1, end_ms)


def _event_text(event: Any) -> str:
    return str(getattr(event, "text", "") or "").strip()


def _confidence(event: Any, default: float = 0.75) -> float:
    try:
        return max(0.0, min(1.0, float(getattr(event, "confidence", default))))
    except Exception:
        return default


def _clean_word(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9']+", "", text).strip("'").lower()


def word_to_phonemes(text: str) -> list[str]:
    """Small rule-based grapheme fallback for xLights-style singing faces."""
    word = _clean_word(text)
    if not word:
        return ["AH"]
    phonemes: list[str] = []
    idx = 0
    while idx < len(word):
        pair = word[idx : idx + 2]
        ch = word[idx]
        if ch in "mbp":
            phonemes.append("MBP")
        elif pair in {"ee", "ea", "ey"}:
            phonemes.append("EH")
            idx += 1
        elif pair in {"oo", "ou"}:
            phonemes.append("UW")
            idx += 1
        elif pair in {"oh", "ow"}:
            phonemes.append("OH")
            idx += 1
        elif ch == "a":
            phonemes.append("AH")
        elif ch == "e":
            phonemes.append("EH")
        elif ch in {"i", "y"}:
            phonemes.append("IH")
        elif ch == "o":
            phonemes.append("OH")
        elif ch == "u":
            phonemes.append("UW")
        idx += 1
    if not phonemes:
        phonemes = ["MBP"] if any(ch in word for ch in "mbp") else ["AH"]
    compact: list[str] = []
    for phoneme in phonemes:
        if not compact or compact[-1] != phoneme:
            compact.append(phoneme)
    return compact[:6]


def phoneme_to_mouth_shape(phoneme: str) -> str:
    return MOUTH_BY_PHONEME.get(str(phoneme).upper(), "mouth_A")


def build_phoneme_events_for_word(word: LyricWord) -> list[PhonemeEvent]:
    phonemes = word_to_phonemes(word.text)
    duration = max(0.04, word.end_time - word.start_time)
    step = duration / max(1, len(phonemes))
    events: list[PhonemeEvent] = []
    for idx, phoneme in enumerate(phonemes):
        start = word.start_time + idx * step
        end = word.end_time if idx == len(phonemes) - 1 else min(word.end_time, start + step)
        mouth = phoneme_to_mouth_shape(phoneme)
        events.append(
            PhonemeEvent(
                phoneme=phoneme,
                mouth_shape=mouth,
                mouth_submodel=mouth,
                start_time=round(start, 3),
                end_time=round(max(start + 0.035, end), 3),
                confidence=word.confidence,
                word_text=word.text,
            )
        )
    return events


def build_lyric_timeline(lyric_events: Iterable[Any], vocal_peaks_ms: Iterable[int] | None = None) -> LyricTimeline:
    words: list[LyricWord] = []
    lines: list[LyricLine] = []
    phoneme_events: list[PhonemeEvent] = []
    for event in lyric_events:
        text = _event_text(event)
        if not text:
            continue
        start_ms = _event_start_ms(event)
        end_ms = _event_end_ms(event)
        raw_words = [token for token in re.split(r"\s+", text) if _clean_word(token)]
        if not raw_words:
            continue
        span = max(1, end_ms - start_ms)
        event_words: list[LyricWord] = []
        for idx, token in enumerate(raw_words):
            st = start_ms + int(round(span * idx / len(raw_words)))
            en = start_ms + int(round(span * (idx + 1) / len(raw_words)))
            word = LyricWord(
                text=_clean_word(token) or token.strip(),
                start_time=round(st / 1000.0, 3),
                end_time=round(max(st + 40, en) / 1000.0, 3),
                confidence=_confidence(event),
            )
            word.phonemes = build_phoneme_events_for_word(word)
            event_words.append(word)
            words.append(word)
            phoneme_events.extend(word.phonemes)
        lines.append(
            LyricLine(
                words=event_words,
                start_time=round(start_ms / 1000.0, 3),
                end_time=round(end_ms / 1000.0, 3),
                confidence=sum(word.confidence for word in event_words) / max(1, len(event_words)),
            )
        )
    source = "lyrics"
    peaks = list(vocal_peaks_ms or [])
    if not words and peaks:
        source = "vocal_energy_fallback"
        for idx, peak_ms in enumerate(peaks):
            word = LyricWord(
                text="vocal_hit",
                start_time=round(int(peak_ms) / 1000.0, 3),
                end_time=round((int(peak_ms) + 140) / 1000.0, 3),
                confidence=0.32,
            )
            word.phonemes = [PhonemeEvent("AH", "mouth_A", "mouth_A", word.start_time, word.end_time, 0.32, word.text, source)]
            words.append(word)
            phoneme_events.extend(word.phonemes)
            lines.append(LyricLine([word], word.start_time, word.end_time, 0.32))
    avg_conf = sum(word.confidence for word in words) / max(1, len(words))
    return LyricTimeline(
        lines=lines,
        words=words,
        phoneme_events=phoneme_events,
        confidence_summary={
            "source": source,
            "word_count": len(words),
            "line_count": len(lines),
            "phoneme_count": len(phoneme_events),
            "average_confidence": round(avg_conf, 3) if words else 0.0,
        },
    )


def _part_label(part: Any) -> str:
    raw = str(getattr(part, "name", getattr(part, "label", "verse")) or "verse")
    norm = raw.lower().replace("-", "_").replace(" ", "_")
    aliases = {"prechorus": "pre_chorus", "postchorus": "post_chorus"}
    return aliases.get(norm, norm)


def build_song_parts(parts: Iterable[Any], vocal_peaks_ms: Iterable[int] = (), bass_peaks_ms: Iterable[int] = (), drum_hits_ms: Iterable[int] = ()) -> list[SongPart]:
    raw = list(parts)
    if not raw:
        return []
    vocals = list(vocal_peaks_ms)
    bass = list(bass_peaks_ms)
    drums = list(drum_hits_ms)
    out: list[SongPart] = []
    seen: dict[str, int] = {}
    for part in raw:
        start_ms = int(getattr(part, "start_ms", 0) or 0)
        end_ms = int(getattr(part, "end_ms", start_ms + 1) or (start_ms + 1))
        label = _part_label(part)
        energy = float(getattr(part, "energy", getattr(part, "energy_level", 0.5)) or 0.5)
        sources = []
        for name, marks in (("vocals", vocals), ("bass", bass), ("drums", drums)):
            if any(start_ms <= int(mark) < end_ms for mark in marks):
                sources.append(name)
        if not sources:
            sources = ["heuristic"]
        seen[label] = seen.get(label, 0) + 1
        confidence = 0.78 if label in {"intro", "verse", "pre_chorus", "chorus", "post_chorus", "bridge", "breakdown", "solo", "drop", "outro"} else 0.48
        if "heuristic" in sources:
            confidence = min(confidence, 0.56)
        out.append(
            SongPart(
                name=label,
                start_time=round(start_ms / 1000.0, 3),
                end_time=round(max(start_ms + 1, end_ms) / 1000.0, 3),
                confidence=confidence,
                energy_level=round(max(0.0, min(1.0, energy)), 3),
                dominant_sources=sources,
                repetition_signature=f"{label}_{seen[label]}",
            )
        )
    return out


def detect_part_hits(
    song_parts: list[SongPart],
    lyric_timeline: LyricTimeline,
    *,
    vocal_peaks_ms: Iterable[int] = (),
    build_lifts_ms: Iterable[int] = (),
    releases_ms: Iterable[int] = (),
) -> list[PartHit]:
    hits: list[PartHit] = []
    important = {
        "chorus": "chorus_start",
        "drop": "drop_hit",
        "breakdown": "breakdown_start",
        "bridge": "bridge_enter",
        "solo": "solo_enter",
        "outro": "outro_fade",
    }
    for idx, part in enumerate(song_parts):
        if idx == 0 and part.name not in {"drop", "chorus"}:
            continue
        hit_type = important.get(part.name, f"{part.name}_start")
        strength = min(1.0, 0.45 + part.energy_level * 0.45 + (0.1 if part.name in important else 0.0))
        hits.append(PartHit(part.start_time, part.name, hit_type, round(strength, 3), part.confidence, "song_part_boundary"))
    for line in lyric_timeline.lines:
        if not line.words:
            continue
        part_name = part_name_at(song_parts, line.start_time)
        confidence = min(0.9, max(0.35, line.confidence))
        hits.append(PartHit(line.start_time, part_name, "lyric_phrase_hit", 0.55, confidence, "lyric_line_start"))
    for ms in list(build_lifts_ms or []) + list(releases_ms or []):
        part_name = part_name_at(song_parts, int(ms) / 1000.0)
        hits.append(PartHit(int(ms) / 1000.0, part_name, "energy_swell_peak", 0.72, 0.62, "energy_release_or_build"))
    hits.sort(key=lambda hit: (hit.timestamp, hit.hit_type))
    compact: list[PartHit] = []
    for hit in hits:
        if compact and abs(compact[-1].timestamp - hit.timestamp) < 0.035 and compact[-1].hit_type == hit.hit_type:
            continue
        compact.append(hit)
    return compact


def part_name_at(parts: list[SongPart], timestamp: float) -> str:
    for part in parts:
        if part.start_time <= timestamp < part.end_time:
            return part.name
    return parts[-1].name if parts else "verse"


def detect_background_vocal_windows(
    lyric_timeline: LyricTimeline,
    song_parts: list[SongPart],
    vocal_peaks_ms: Iterable[int],
    config: VocalRoutingConfig = VocalRoutingConfig(),
    classifier_events: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for idx, event in enumerate(classifier_events or []):
        start_ms = int(getattr(event, "start_ms", 0) or 0)
        end_ms = int(getattr(event, "end_ms", start_ms + 160) or (start_ms + 160))
        confidence = float(getattr(event, "confidence", 0.0) or 0.0)
        energy = float(getattr(event, "energy", 0.0) or 0.0)
        if confidence < config.background_vocal_confidence_min or energy < config.background_vocal_energy_min:
            continue
        role = str(getattr(event, "role", "harmony") or "harmony")
        hint = str(getattr(event, "performer_hint", "") or "")
        if "all" in hint or role == "group_chant":
            performer = "group"
        elif "bass" in hint and "guitar" not in hint:
            performer = "bassist"
        else:
            performer = "guitarist" if idx % 2 else "bassist"
        windows.append(
            {
                "performer": performer,
                "start_time": round(start_ms / 1000.0, 3),
                "end_time": round(max(start_ms + int(config.background_face_min_duration * 1000), end_ms) / 1000.0, 3),
                "part_name": part_name_at(song_parts, start_ms / 1000.0),
                "confidence": round(min(0.96, confidence), 3),
                "role": "group_chant" if performer == "group" else "background_vocal",
                "source_reason": str(getattr(event, "source_reason", "background_vocal_classifier") or "background_vocal_classifier"),
                "classifier_role": role,
                "energy": round(max(0.0, min(1.0, energy)), 3),
            }
        )
    if windows:
        return windows
    lead_word_starts = [word.start_ms for word in lyric_timeline.words]
    for idx, peak_ms in enumerate(sorted(set(int(v) for v in vocal_peaks_ms))):
        part = part_name_at(song_parts, peak_ms / 1000.0)
        nearest = min((abs(peak_ms - start) for start in lead_word_starts), default=999999)
        energy_conf = 0.45 if nearest > 160 else 0.25
        if part in {"chorus", "post_chorus", "drop"}:
            energy_conf += config.background_vocal_chorus_boost
        if energy_conf < config.background_vocal_confidence_min:
            continue
        performer = "guitarist" if idx % 2 else "bassist"
        duration = max(config.background_face_min_duration, 0.16)
        windows.append(
            {
                "performer": performer,
                "start_time": round(peak_ms / 1000.0, 3),
                "end_time": round((peak_ms / 1000.0) + duration, 3),
                "part_name": part,
                "confidence": round(min(0.88, energy_conf), 3),
                "role": "background_vocal",
                "source_reason": "chorus_vocal_energy_not_explained_by_lead" if nearest > 160 else "chorus_harmony_lock",
            }
        )
    return windows


def as_plain_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: as_plain_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): as_plain_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_plain_dict(item) for item in value]
    return value
