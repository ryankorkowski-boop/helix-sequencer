from __future__ import annotations

from typing import List

from models.helixville4_vocal_phonemes import PHONEME_BY_NAME

# Strict approved phoneme contract
APPROVED_PHONEMES = tuple(sorted(PHONEME_BY_NAME.keys()))
APPROVED_SET = set(APPROVED_PHONEMES)

# Deterministic grapheme buckets
VOWEL_A = {"a"}
VOWEL_E = {"e", "i", "y"}
VOWEL_O = {"o", "u"}
MBP_SET = {"m", "b", "p"}
FV_SET = {"f", "v"}
L_SET = {"l"}


def _map_character(ch: str) -> str:
    c = ch.lower()

    if c in VOWEL_A:
        return "AH"
    if c in VOWEL_E:
        return "EE"
    if c in VOWEL_O:
        return "OH"
    if c in MBP_SET:
        return "MBP"
    if c in FV_SET:
        return "FV"
    if c in L_SET:
        return "L"

    return "REST"


def map_lyric_to_phonemes(text: str) -> List[str]:
    """
    Deterministic grapheme → phoneme mapping.

    Guarantees:
    - Emits only approved phonemes
    - Stable output order
    - No randomness
    """
    if not text or not text.strip():
        return ["REST"]

    phonemes: List[str] = []

    for ch in text:
        if ch.isalpha():
            phoneme = _map_character(ch)
        else:
            phoneme = "REST"

        if phoneme not in APPROVED_SET:
            raise AssertionError(f"Invalid phoneme emitted: {phoneme}")

        phonemes.append(phoneme)

    return phonemes
