"""No-model tests for automatic RoFormer review wiring and safety."""
from pathlib import Path

import pytest

from tools.automatic_roformer_review import select_model_outputs


def test_select_karaoke_outputs_from_actual_separator_naming(tmp_path: Path):
    lead = tmp_path / "vocals_(Vocals)_mel_band_roformer.wav"
    backing = tmp_path / "vocals_(Instrumental)_mel_band_roformer.wav"
    lead.touch()
    backing.touch()
    assert select_model_outputs(tmp_path) == (lead, backing)


def test_missing_or_ambiguous_model_outputs_fail_closed(tmp_path: Path):
    (tmp_path / "vocals_(Vocals)_model.wav").touch()
    with pytest.raises(ValueError, match="exactly one"):
        select_model_outputs(tmp_path)
    (tmp_path / "vocals_(Instrumental)_model.wav").touch()
    (tmp_path / "vocals_(Vocals)_duplicate.wav").touch()
    with pytest.raises(ValueError, match="exactly one"):
        select_model_outputs(tmp_path)


def test_no_reuse_of_existing_review_outputs(tmp_path: Path):
    from tools.automatic_roformer_review import prepare
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"not decoded in this preflight")
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(FileExistsError):
        prepare(audio, output, vocals=audio)
