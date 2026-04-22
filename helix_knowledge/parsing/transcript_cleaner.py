from __future__ import annotations

import re

_TIMECODE_PATTERNS = [
    re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b"),
    re.compile(r"\b\d{1,2}:\d{2}\b"),
    re.compile(r"<\d{1,2}:\d{2}(?::\d{2})?>"),
]


def clean_transcript(text: str, *, max_chars: int = 24000) -> str:
    cleaned = text or ""
    cleaned = cleaned.replace("\ufeff", "")
    for pattern in _TIMECODE_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)

    cleaned = re.sub(r"\[(music|applause|laughter)\]", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(music|applause|laughter\)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bSpeaker\s*\d+\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\r", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = cleaned.strip()

    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + " ..."
    return cleaned
