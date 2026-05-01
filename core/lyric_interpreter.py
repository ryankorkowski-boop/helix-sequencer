from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any


_WORD_RE = re.compile(r"[A-Za-z']+")

_TRIGGER_LEXICON: dict[str, set[str]] = {
    "impact": {"bang", "boom", "drop", "hit", "crash", "explode", "fire"},
    "motion_up": {"up", "rise", "higher", "fly", "lift", "climb", "ascend"},
    "motion_down": {"down", "fall", "lower", "sink", "drop"},
    "light_bright": {"light", "shine", "glow", "sun", "gold", "bright", "spark"},
    "dark_shadow": {"dark", "night", "shadow", "black", "cold", "moon"},
    "energy_hype": {"dance", "party", "jump", "run", "wild", "loud", "ignite"},
    "calm_soft": {"slow", "calm", "quiet", "still", "soft", "breathe", "gentle"},
}

_POSITIVE_WORDS = {
    "love",
    "alive",
    "good",
    "great",
    "joy",
    "happy",
    "hope",
    "free",
    "light",
    "shine",
    "smile",
}
_NEGATIVE_WORDS = {
    "hate",
    "pain",
    "dark",
    "fear",
    "lost",
    "alone",
    "cold",
    "sad",
    "broken",
    "cry",
    "tears",
}
_HIGH_ENERGY_WORDS = {
    "fire",
    "burn",
    "run",
    "jump",
    "wild",
    "loud",
    "fight",
    "bang",
    "boom",
    "drop",
}
_CALM_WORDS = {
    "calm",
    "still",
    "breathe",
    "slow",
    "quiet",
    "soft",
    "gentle",
    "peace",
}

_AUDIO_MOOD_FALLBACK = {
    "uplifting": "uplifting",
    "brooding": "brooding",
    "calm": "calm",
    "aggressive": "aggressive",
    "neutral": "neutral",
    "balanced": "neutral",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_lexicon_path() -> Path:
    return _repo_root() / "config" / "lyric_trigger_lexicon.json"


def _coerce_word_set(values: object) -> set[str]:
    out: set[str] = set()
    if isinstance(values, list):
        for value in values:
            token = str(value or "").strip().lower()
            if token:
                out.add(token)
    return out


def load_trigger_lexicon(config_path: str | Path | None = None) -> dict[str, set[str]]:
    """
    Load trigger lexicon from JSON config file.

    Accepted JSON shapes:
    1) {"trigger_lexicon": {"impact": ["boom", ...], ...}}
    2) {"impact": ["boom", ...], ...}
    """
    lexicon: dict[str, set[str]] = {key: set(values) for key, values in _TRIGGER_LEXICON.items()}
    candidate: Path | None = None
    if config_path:
        candidate = Path(config_path)
    else:
        env_path = str(os.environ.get("HELIX_LYRIC_LEXICON_FILE", "") or "").strip()
        candidate = Path(env_path) if env_path else _default_lexicon_path()

    if not candidate or not candidate.exists():
        return lexicon

    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return lexicon

    candidate_map = payload.get("trigger_lexicon") if isinstance(payload, dict) else None
    if isinstance(candidate_map, dict):
        source_map = candidate_map
    elif isinstance(payload, dict):
        source_map = payload
    else:
        return lexicon

    loaded: dict[str, set[str]] = {}
    for key, values in source_map.items():
        category = str(key or "").strip().lower()
        if not category:
            continue
        words = _coerce_word_set(values)
        if words:
            loaded[category] = words

    if loaded:
        return loaded
    return lexicon


def _event_start_ms(event: Any) -> int:
    try:
        return max(0, int(getattr(event, "start_ms", 0)))
    except Exception:
        return 0


def _event_text(event: Any) -> str:
    return str(getattr(event, "text", "") or "").strip()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _WORD_RE.findall(text)]


def _classify_lyric_mood(
    *,
    positive_count: int,
    negative_count: int,
    high_energy_count: int,
    calm_count: int,
    audio_mood_hint: str,
) -> tuple[str, dict[str, int]]:
    energy_score = high_energy_count - calm_count
    sentiment_score = positive_count - negative_count

    if energy_score >= 2 and sentiment_score >= 0:
        mood = "uplifting"
    elif energy_score >= 2 and sentiment_score < 0:
        mood = "aggressive"
    elif calm_count >= 2 and sentiment_score >= 0:
        mood = "calm"
    elif negative_count >= 2 and sentiment_score <= 0:
        mood = "brooding"
    elif abs(energy_score) <= 1 and abs(sentiment_score) <= 1:
        mood = _AUDIO_MOOD_FALLBACK.get(audio_mood_hint.strip().lower(), "neutral")
    elif sentiment_score > 0:
        mood = "uplifting"
    elif sentiment_score < 0:
        mood = "brooding"
    else:
        mood = "neutral"

    return mood, {
        "positive": int(positive_count),
        "negative": int(negative_count),
        "high_energy": int(high_energy_count),
        "calm": int(calm_count),
        "energy_score": int(energy_score),
        "sentiment_score": int(sentiment_score),
    }


def interpret_lyric_events(
    lyric_events: list[Any],
    *,
    audio_mood_hint: str = "neutral",
    max_trigger_hits: int = 300,
    max_repeat_phrases: int = 24,
    lexicon_path: str | Path | None = None,
) -> dict[str, Any]:
    """Rule-based lyric interpreter for trigger cues, mood, and repeats."""
    trigger_lexicon = load_trigger_lexicon(lexicon_path)
    if not lyric_events:
        return {
            "enabled": False,
            "overall_mood": _AUDIO_MOOD_FALLBACK.get(audio_mood_hint.strip().lower(), "neutral"),
            "trigger_hits": [],
            "trigger_counts": {},
            "repeated_phrases": [],
            "token_count": 0,
            "line_count": 0,
            "mood_signals": {
                "positive": 0,
                "negative": 0,
                "high_energy": 0,
                "calm": 0,
                "energy_score": 0,
                "sentiment_score": 0,
            },
        }

    trigger_hits: list[dict[str, Any]] = []
    trigger_counts: Counter[str] = Counter()
    line_counter: Counter[str] = Counter()
    phrase_counter: Counter[str] = Counter()

    positive_count = 0
    negative_count = 0
    high_energy_count = 0
    calm_count = 0
    token_count = 0
    seen_trigger_markers: set[tuple[int, str, str]] = set()

    for event in lyric_events:
        start_ms = _event_start_ms(event)
        text = _event_text(event)
        if not text:
            continue
        normalized_line = " ".join(_tokenize(text))
        if normalized_line:
            line_counter[normalized_line] += 1
        tokens = _tokenize(text)
        if not tokens:
            continue
        token_count += len(tokens)

        for token in tokens:
            if token in _POSITIVE_WORDS:
                positive_count += 1
            if token in _NEGATIVE_WORDS:
                negative_count += 1
            if token in _HIGH_ENERGY_WORDS:
                high_energy_count += 1
            if token in _CALM_WORDS:
                calm_count += 1

            for trigger_type, vocab in trigger_lexicon.items():
                if token not in vocab:
                    continue
                marker = (start_ms, token, trigger_type)
                if marker in seen_trigger_markers:
                    continue
                seen_trigger_markers.add(marker)
                trigger_counts[trigger_type] += 1
                if len(trigger_hits) < max_trigger_hits:
                    trigger_hits.append(
                        {
                            "start_ms": start_ms,
                            "word": token,
                            "trigger_type": trigger_type,
                            "line_excerpt": text[:64],
                        }
                    )

        for n in (2, 3):
            if len(tokens) < n:
                continue
            for idx in range(0, len(tokens) - n + 1):
                phrase = " ".join(tokens[idx : idx + n])
                phrase_counter[phrase] += 1

    repeated_phrases: list[dict[str, Any]] = []
    for line, count in line_counter.items():
        if count >= 2:
            repeated_phrases.append({"phrase": line, "count": int(count), "kind": "line"})
    for phrase, count in phrase_counter.items():
        if count >= 2:
            repeated_phrases.append({"phrase": phrase, "count": int(count), "kind": "ngram"})
    repeated_phrases.sort(key=lambda item: (-int(item["count"]), -len(str(item["phrase"])), str(item["phrase"])))
    repeated_phrases = repeated_phrases[:max_repeat_phrases]

    overall_mood, mood_signals = _classify_lyric_mood(
        positive_count=positive_count,
        negative_count=negative_count,
        high_energy_count=high_energy_count,
        calm_count=calm_count,
        audio_mood_hint=audio_mood_hint,
    )

    return {
        "enabled": True,
        "overall_mood": overall_mood,
        "trigger_hits": trigger_hits,
        "trigger_counts": dict(sorted(trigger_counts.items())),
        "repeated_phrases": repeated_phrases,
        "token_count": int(token_count),
        "line_count": int(sum(1 for event in lyric_events if _event_text(event))),
        "mood_signals": mood_signals,
    }
