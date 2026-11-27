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


def test_source_bound_estimated_review_pipeline_with_stubbed_models(tmp_path, monkeypatch):
    """Exercise the actual orchestration without downloading either model."""
    import json
    from tools import automatic_roformer_review as mod

    original = tmp_path / "real_source.wav"
    original.write_bytes(b"test source bytes")
    vocals = tmp_path / "combined_vocals.wav"
    vocals.write_bytes(b"test separated vocals")
    commands = []

    def fake_run(cmd, *, check):
        assert check
        commands.append(cmd)
        if cmd[0] == "separator":
            root = Path(cmd[cmd.index("--output_dir") + 1])
            (root / "combined_vocals_(Vocals)_model.wav").write_bytes(b"lead estimate")
            (root / "combined_vocals_(Instrumental)_model.wav").write_bytes(b"backing estimate")

    def fake_manifest(source, lead, backing, output, **kwargs):
        assert source == original.resolve()
        assert lead != backing
        assert kwargs["combined_vocals"] == vocals.resolve()
        output.write_text('{"source_sha256": "test"}')
        return output

    def fake_fixture(audio, manifest, output):
        output.mkdir()
        (output / "diagnostic.json").write_text(json.dumps({
            "audio_sha256": mod.sha256(audio),
            "verification_state": "ESTIMATED_REVIEW",
            "independent_backing_verified": False,
        }))
        return output

    monkeypatch.setattr(mod.shutil, "which", lambda _: "separator")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    monkeypatch.setattr(mod, "write_manifest", fake_manifest)
    monkeypatch.setattr(mod, "build_review_fixture", fake_fixture)
    output = tmp_path / "reviews" / "run"
    fixture = mod.prepare(original, output, vocals=vocals)
    assert fixture == output / "vocal-fixture"
    assert json.loads((output / "review_origin.json").read_text())[
        "independent_singer_identity_verified"
    ] is False
    assert [cmd[0] for cmd in commands] == ["separator", "ffmpeg", "ffmpeg"]
