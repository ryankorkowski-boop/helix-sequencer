from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from core import audio_intelligence, effect_engine
from tools.build_helpers.variants import build_runtime_candidates
from xlights import xsq_writer


def test_variant_default_is_signature_only() -> None:
    style = SimpleNamespace(version="v27.3", title="Helix Prime")
    args = effect_engine.parse_args(style, ["--no-prompt"])

    assert args.variant_count == 1
    assert args.auto_shortlist is False
    assert args.use_demucs is False
    assert effect_engine.RuntimeTuning().variant_count == 1
    assert effect_engine.RuntimeTuning().use_demucs is False

    tuning = SimpleNamespace()
    candidates = build_runtime_candidates(style, tuning, args.variant_count)
    assert len(candidates) == 1
    assert candidates[0].label == "signature"
    assert candidates[0].style is style
    assert candidates[0].tuning is tuning


def test_shortlist_flag_still_requests_alternates() -> None:
    style = SimpleNamespace(version="v27.3", title="Helix Prime")
    args = effect_engine.parse_args(style, ["--variants", "3", "--auto-shortlist", "--use-demucs"])

    assert args.variant_count == 3
    assert args.auto_shortlist is True
    assert args.use_demucs is True


def test_resolve_shared_audio_does_not_decode_twice() -> None:
    sentinel = SimpleNamespace(dur_s=12.5)
    with patch.object(effect_engine.base, "analyze") as analyze:
        reused = effect_engine.resolve_shared_audio(Path("song.wav"), sentinel)
    assert reused is sentinel
    analyze.assert_not_called()


def test_analysis_hop_preserves_frame_period() -> None:
    assert xsq_writer.analysis_hop_length(44100, 22050, 512) == 256
    assert xsq_writer.analysis_hop_length(48000, 22050, 512) == 235
    assert xsq_writer.ANALYSIS_TARGET_SR == 22050


def test_fast_pitch_matches_frame_loop() -> None:
    pitches = np.array([[0.0, 10.0, 0.0], [440.0, 0.0, 0.0], [100.0, 50.0, 20.0]], dtype=float)
    magnitudes = np.array([[0.1, 0.2, 0.4], [0.9, 0.1, 0.2], [0.3, 0.8, 0.3]], dtype=float)
    expected = []
    for frame in range(pitches.shape[1]):
        index = int(np.argmax(magnitudes[:, frame]))
        pitch = float(pitches[index, frame])
        expected.append(pitch if pitch > 0 else np.nan)
    got = xsq_writer.fast_pitch_hz(pitches, magnitudes)
    assert np.allclose(got, np.asarray(expected), equal_nan=True)


def test_load_analysis_audio_uses_target_rate_and_native_duration(tmp_path: Path) -> None:
    audio = tmp_path / "tone.wav"
    audio.write_bytes(b"unused")
    samples = np.ones(22050, dtype=np.float32)
    with patch.object(xsq_writer, "_native_audio_info", return_value=(44100, 2.5)), patch.object(
        xsq_writer.librosa, "load", return_value=(samples, 22050)
    ) as load:
        y, sr, dur, hop = xsq_writer.load_analysis_audio(audio)
    assert load.call_args.kwargs["sr"] == 22050
    assert load.call_args.kwargs["mono"] is True
    assert sr == 22050
    assert dur == 2.5
    assert hop == 256
    assert y is samples


def _silence_stem_readers() -> tuple[object, ...]:
    return (
        patch.object(audio_intelligence, "_analyze_drum_events", return_value=([], [], [])),
        patch.object(audio_intelligence.drum_intel, "detect_drum_event_streams_from_file", return_value={}),
        patch.object(audio_intelligence, "_analyze_peak_events", return_value=[]),
        patch.object(audio_intelligence, "_classify_background_vocals", return_value=[]),
        patch.object(audio_intelligence, "_summarize_stem_file", return_value={"confidence": 0.2}),
    )


def test_stem_cache_skips_demucs_and_local_split(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"RIFFfake")
    stem_dir = tmp_path / "cache" / "song"
    stem_dir.mkdir(parents=True)
    stems = {}
    for name in audio_intelligence._STEM_NAMES:
        path = stem_dir / f"song.{name}.wav"
        path.write_bytes(b"wav-bytes")
        stems[name] = path
    audio_intelligence._write_stem_cache_meta(audio, stem_dir, stems, "local")

    readers = _silence_stem_readers()
    with readers[0], readers[1], readers[2], readers[3], readers[4], patch.object(
        audio_intelligence, "_try_demucs_stem_separation"
    ) as demucs, patch.object(audio_intelligence, "_local_stem_separation") as local, patch.object(
        audio_intelligence, "_try_moises_stem_separation"
    ) as moises:
        result = audio_intelligence.build_stem_analysis(
            audio_path=audio,
            use_moises=False,
            api_key=None,
            cache_dir=tmp_path / "cache",
            use_demucs=True,
        )
    assert result.source == "cache"
    assert set(result.stems) == set(audio_intelligence._STEM_NAMES)
    demucs.assert_not_called()
    local.assert_not_called()
    moises.assert_not_called()


def test_changed_audio_invalidates_stem_cache(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"first")
    stem_dir = tmp_path / "cache" / "song"
    stem_dir.mkdir(parents=True)
    stems = {name: stem_dir / f"{name}.wav" for name in audio_intelligence._STEM_NAMES}
    for path in stems.values():
        path.write_bytes(b"wav")
    audio_intelligence._write_stem_cache_meta(audio, stem_dir, stems, "local")
    audio.write_bytes(b"first-plus")

    assert audio_intelligence._load_cached_stems(audio, stem_dir) is None


def test_demucs_runs_only_when_requested(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not-audio")
    produced = {name: tmp_path / f"{name}.wav" for name in audio_intelligence._STEM_NAMES}
    for path in produced.values():
        path.write_bytes(b"wav")

    readers = _silence_stem_readers()
    with readers[0], readers[1], readers[2], readers[3], readers[4], patch.object(
        audio_intelligence, "_try_demucs_stem_separation", return_value=produced
    ) as demucs, patch.object(audio_intelligence, "_local_stem_separation", return_value=produced) as local:
        skipped = audio_intelligence.build_stem_analysis(
            audio_path=audio,
            use_moises=False,
            api_key=None,
            cache_dir=tmp_path / "off",
            use_demucs=False,
        )
    demucs.assert_not_called()
    local.assert_called_once()
    assert skipped.source == "local"

    readers = _silence_stem_readers()
    with readers[0], readers[1], readers[2], readers[3], readers[4], patch.object(
        audio_intelligence, "_try_demucs_stem_separation", return_value=produced
    ) as demucs, patch.object(audio_intelligence, "_local_stem_separation", return_value=produced) as local:
        chosen = audio_intelligence.build_stem_analysis(
            audio_path=audio,
            use_moises=False,
            api_key=None,
            cache_dir=tmp_path / "on",
            use_demucs=True,
        )
    demucs.assert_called_once()
    local.assert_not_called()
    assert chosen.source == "demucs"
    assert (tmp_path / "on" / "song" / "helix_stem_cache.json").exists()
