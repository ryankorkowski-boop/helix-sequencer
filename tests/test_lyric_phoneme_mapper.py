from __future__ import annotations

from core.lyric_phoneme_mapper import map_lyric_to_phonemes
from models.helixville4_vocal_phonemes import PHONEME_BY_NAME

APPROVED = set(PHONEME_BY_NAME.keys())


def test_empty_string_maps_to_rest() -> None:
    assert map_lyric_to_phonemes("") == ["REST"]
    assert map_lyric_to_phonemes("   ") == ["REST"]


def test_mapping_is_deterministic() -> None:
    text = "Hello"
    first = map_lyric_to_phonemes(text)
    second = map_lyric_to_phonemes(text)
    assert first == second


def test_all_outputs_within_contract() -> None:
    text = "Amplify love"
    phonemes = map_lyric_to_phonemes(text)
    assert set(phonemes).issubset(APPROVED)


def test_non_alpha_characters_become_rest() -> None:
    phonemes = map_lyric_to_phonemes("Hi!")
    assert phonemes[-1] == "REST"
