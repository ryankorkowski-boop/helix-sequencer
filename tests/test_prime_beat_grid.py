from pathlib import Path

from core.beat_grid import BeatGrid
from core.beat_grid_bpm import bpm_from_payload, resolve_bpm
from core.drummer_beat_grid import classify_drum_event, quantize_drum_event
from core.prime_beat_grid import decide_prime_beat_grid, prime_beat_grid_args


def test_prime_defaults_enable_sixteenth_grid_for_master():
    decision = decide_prime_beat_grid(profile_id_or_version="master", engine_args=[])

    assert decision.enabled is True
    assert decision.beat_grid is not None
    assert decision.beat_grid.subdivision == 16
    assert decision.beat_grid.mode == "musical"


def test_prime_respects_explicit_no_snap():
    decision = decide_prime_beat_grid(profile_id_or_version="master", engine_args=["--no-snap"])

    assert decision.enabled is False
    assert decision.source == "explicit_no_snap"


def test_prime_explicit_runtime_flags_win():
    decision = decide_prime_beat_grid(
        profile_id_or_version="master",
        engine_args=["--snap-grid", "8", "--snap-bpm", "140"],
    )

    assert decision.enabled is True
    assert decision.source == "explicit_runtime_flags"
    assert decision.beat_grid is not None
    assert decision.beat_grid.bpm == 140
    assert decision.beat_grid.subdivision == 8


def test_prime_beat_grid_args_emit_canonical_defaults():
    args = prime_beat_grid_args(profile_id_or_version="prime", engine_args=[])

    assert args[:2] == ["--snap-grid", "16"]
    assert "--snap-bpm" in args


def test_bpm_from_payload_prefers_advanced_audio():
    payload = {"advanced_audio": {"tempo_bpm": 132.5}, "other": {"bpm": 88}}

    assert bpm_from_payload(payload) == 132.5


def test_resolve_bpm_uses_payload_median_before_fallback():
    payloads = [{"analysis": {"tempo_bpm": 100}}, {"analysis": {"tempo_bpm": 120}}, {"analysis": {"tempo_bpm": 140}}]

    assert resolve_bpm(None, payloads, fallback_bpm=90) == 120


def test_drummer_classifies_crash_and_quantizes_to_strong_beat():
    event = {"label": "right crash cymbal", "start_ms": 560, "end_ms": 700}
    grid = BeatGrid(bpm=120, subdivision=16, max_shift_ms=40)

    changed, kind = quantize_drum_event(event, grid, duration_ms=2000)

    assert kind == "crash"
    assert event["raw_start_ms"] == 560
    assert event["snapped_start_ms"] == 500
    assert event["start_ms"] == 500
    assert changed is True


def test_drummer_keeps_fill_on_fine_grid():
    event = {"label": "tom fill roll", "start_ms": 126, "end_ms": 200}
    grid = BeatGrid(bpm=120, subdivision=8, max_shift_ms=40)

    changed, kind = quantize_drum_event(event, grid, duration_ms=1000)

    assert kind == "fill"
    assert event["snapped_start_ms"] == 125
    assert changed is True
