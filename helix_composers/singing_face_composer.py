from __future__ import annotations


def compose_singing_face(*, has_lyrics: bool) -> dict[str, object]:
    if not has_lyrics:
        return {"composer": "singing_face", "mode": "fallback_vowel_energy", "mouth_strategy": "vowel_approximation"}
    return {"composer": "singing_face", "mode": "lyric_sync", "mouth_strategy": "phoneme_timing"}
