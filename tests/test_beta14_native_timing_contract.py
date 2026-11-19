"""Regression coverage for unified native and independent vocal timing."""
from pathlib import Path
import pytest
from tools.validate_xsq_structure import ValidationError, validate_xsq


def check(tmp_path: Path, body: str):
    path = tmp_path / "timing.xsq"
    path.write_text("<xsequence>" + body + "</xsequence>", encoding="utf-8")
    validate_xsq(path)


def track(start="0", duration="0.1"):
    return f'<timingtrack><phoneme index="0" start="{start}" duration="{duration}"/></timingtrack>'


def test_independent_tracks_restart_index_and_clock(tmp_path):
    check(tmp_path, track("2") + track("0") + '<ElementEffects><Element name="Lead"/></ElementEffects>')


@pytest.mark.parametrize("start,duration", [("nan","1"), ("inf","1"), ("0","nan"), ("0","inf")])
def test_reject_nonfinite_phonemes(tmp_path, start, duration):
    with pytest.raises(ValidationError):
        check(tmp_path, track(start, duration) + '<ElementEffects><Element name="Lead"/></ElementEffects>')


@pytest.mark.parametrize("name,effect,valid", [("Lead", '<Effect startTime="0" endTime="50"/>', True), ("Lead", "", False), ("Harmony", '<Effect startTime="0" endTime="50"/>', False)])
def test_native_timing_requires_matching_populated_row(tmp_path, name, effect, valid):
    body = f'<DisplayElements><Element type="timing" name="Lead"/></DisplayElements><ElementEffects><Element type="timing" name="{name}"><EffectLayer>{effect}</EffectLayer></Element></ElementEffects>'
    if valid:
        check(tmp_path, body)
    else:
        with pytest.raises(ValidationError):
            check(tmp_path, body)


@pytest.mark.parametrize("start,end", [("nan","50"), ("0","inf"), ("-1","50"), ("50","50"), ("100","50"), ("bad","50")])
@pytest.mark.parametrize("legacy", [False, True])
def test_invalid_native_intervals_rejected_even_with_legacy_track(tmp_path, start, end, legacy):
    body = f'<DisplayElements><Element type="timing" name="Lead"/></DisplayElements><ElementEffects><Element type="timing" name="Lead"><EffectLayer><Effect startTime="{start}" endTime="{end}"/></EffectLayer></Element></ElementEffects>'
    with pytest.raises(ValidationError):
        check(tmp_path, (track() if legacy else "") + body)
