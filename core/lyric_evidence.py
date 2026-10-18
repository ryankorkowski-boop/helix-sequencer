"""Evidence-preserving transcript adapter; no synthetic words on vocal peaks.

CMU pronunciation/viseme rules are recovered from tools.align_snowman_lyrics.
Word timing and phoneme timing are separate claims. Dictionary phone boundaries
remain estimates unless an aligner supplied explicit timed phonemes.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from core import vocal_timeline as vt


def value(item: Any, name: str, default: Any = None) -> Any:
    return item.get(name, default) if isinstance(item, Mapping) else getattr(item, name, default)


def number(raw: Any, default: float = 0.0) -> float:
    try:
        result = float(raw)
        return result if math.isfinite(result) else default
    except (ValueError, TypeError):
        return default


def probability(raw: Any) -> float:
    return max(0.0, min(1.0, number(raw)))


def whisper_events(payload: Mapping[str, Any], *, minimum_confidence: float = .65) -> list[dict]:
    """Accept measured words; retain unintelligible spans without their text."""
    events = []
    for segment in payload.get('segments', []):
        no_speech = probability(segment.get('no_speech_prob', 0))
        unreliable = (no_speech > .6 or number(segment.get('avg_logprob', 0)) < -1
                      or number(segment.get('compression_ratio', 0)) > 2.4)
        words = segment.get('words') or [dict(start=segment.get('start'), end=segment.get('end'),
                                            word=segment.get('text', ''), probability=0)]
        for word in words:
            start, end = number(word.get('start'), -1), number(word.get('end'), -1)
            if start < 0 or end <= start:
                continue
            conf = probability(word.get('probability', word.get('confidence', 0)))
            text = str(word.get('word', '')).strip()
            accepted = bool(text and not unreliable and conf >= minimum_confidence)
            events.append(dict(start_ms=round(start * 1000), end_ms=round(end * 1000),
                               text=text if accepted else '', confidence=conf,
                               source='whisper_word_timestamp', timing_level='word',
                               intelligible=accepted, reason='' if accepted else 'uncertain_transcription'))
    return events


def load_corrections(path: Path, audio_path: Path) -> list[dict]:
    """Only explicitly timed, source-bound corrections can drive a mouth."""
    payload = json.loads(path.read_text(encoding='utf-8'))
    digest = hashlib.sha256(audio_path.read_bytes()).hexdigest()
    if payload.get('audio_sha256') != digest:
        raise ValueError('Lyric corrections belong to a different audio source')
    events = payload.get('events')
    if not isinstance(events, list):
        raise ValueError('Corrections require a list of timed events')
    out = []
    for event in events:
        start, end = number(event.get('start_ms'), -1), number(event.get('end_ms'), -1)
        text = str(event.get('text', '')).strip()
        if start < 0 or end <= start or not text:
            raise ValueError('Each correction requires text and valid millisecond boundaries')
        level = event.get('timing_level', 'phrase')
        if level not in ('word', 'phrase') or (level == 'word' and len(text.split()) != 1):
            raise ValueError('Word timing requires one word; use phrase for untimed lyrics')
        out.append({**event, 'start_ms':round(start), 'end_ms':round(end), 'text':text,
                    'source':'user_timed_correction', 'confidence':1.0, 'timing_level':level})
    return out


def build_timeline(events: Iterable[Any], *, minimum_confidence: float = .65,
                   phrase_gap_ms: int = 650) -> vt.LyricTimeline:
    words, lines, phones, unknown = [], [], [], []
    pending = []

    def flush():
        if pending:
            lines.append(vt.LyricLine(list(pending), pending[0].start_time,
                                     pending[-1].end_time, min(w.confidence for w in pending)))
            pending.clear()

    for event in sorted(events, key=lambda e: number(value(e, 'start_ms'), -1)):
        start, end = number(value(event, 'start_ms'), -1), number(value(event, 'end_ms'), -1)
        text = str(value(event, 'text', '') or '').strip()
        confidence = probability(value(event, 'confidence', 0))
        source = str(value(event, 'source', 'supplied_timed_lyrics'))
        if start < 0 or end <= start:
            continue
        tokens = text.split()
        if (not tokens or confidence < minimum_confidence or not value(event, 'intelligible', True)
                or text.lower() in ('vocal_hit', '[inaudible]', '[unintelligible]', '[music]')):
            flush()
            unknown.append(dict(start_ms=round(start), end_ms=round(end), confidence=confidence,
                                reason='unintelligible_or_low_confidence', source=source))
            continue
        level = value(event, 'timing_level', 'word' if len(tokens) == 1 else 'phrase')
        if len(tokens) > 1 or level != 'word':
            # A phrase is usable for meaning, never advertised as aligned words.
            flush()
            phrase = vt.LyricWord(text, start/1000, end/1000, confidence,
                                  source=source, timing_level='phrase')
            lines.append(vt.LyricLine([phrase], start/1000, end/1000, confidence))
            continue
        if pending and (start - pending[-1].end_ms > phrase_gap_ms
                        or start < pending[-1].end_ms):
            flush()
        word = vt.LyricWord(text, start/1000, end/1000, confidence, source=source, timing_level='word')
        supplied = value(event, 'phonemes', []) or []
        if supplied:
            previous_end = start
            for phone in supplied:
                a, b = number(value(phone, 'start_ms'), -1), number(value(phone, 'end_ms'), -1)
                shape = str(value(phone, 'phoneme', '')).upper()
                if not (start <= a < b <= end and a >= previous_end and shape in vt.MOUTH_BY_PHONEME):
                    raise ValueError('Aligned phonemes must be ordered and contained in their word')
                previous_end = b
                mouth = vt.phoneme_to_mouth_shape(shape)
                word.phonemes.append(vt.PhonemeEvent(shape, mouth, mouth, a/1000, b/1000,
                    min(confidence, probability(value(phone, 'confidence', 0))), text,
                    str(value(phone, 'source', 'supplied_phone_alignment'))))
        else:
            # Reuse the stronger recovered dictionary pronunciation, with an
            # explicit distinction between pronunciation and measured alignment.
            from core.lyric_pronunciation import pronunciation
            try:
                import cmudict
                dictionary = _dictionary()
            except ImportError:
                dictionary = {}
            shapes, method = pronunciation(text, dictionary)
            span = end - start
            for index, shape in enumerate(shapes):
                a, b = start + span*index/len(shapes), start + span*(index+1)/len(shapes)
                mouth = vt.phoneme_to_mouth_shape(shape)
                word.phonemes.append(vt.PhonemeEvent(shape, mouth, mouth, a/1000, b/1000,
                    min(confidence, .45), text, method + ':estimated_within_word'))
        words.append(word); phones.extend(word.phonemes); pending.append(word)
        if re.search(r'[.!?;:]\s*$', text):
            flush()
    flush()
    return vt.LyricTimeline(lines, words, phones, {
        'source':'evidence_aware_lyrics', 'word_count':len(words), 'line_count':len(lines),
        'phoneme_count':len(phones), 'average_confidence':sum(w.confidence for w in words)/max(1,len(words)),
        'unintelligible_spans':unknown, 'word_alignment':'only_source_timed_words',
        'phoneme_alignment':'source_supplied_or_explicitly_estimated',
    })


from functools import lru_cache


@lru_cache(maxsize=1)
def _dictionary():
    import cmudict
    return cmudict.dict()
