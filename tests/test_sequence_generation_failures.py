from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest

from core import effect_engine
from core import sequence_builder
from core.run_config import RunConfig
from core.run_manager import RunManager


def _wav(path: Path, seconds: float = 0.2) -> None:
    frames = int(8000 * seconds)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * frames)


def _manifests(output_root: Path) -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((output_root / "beta").glob("*/run_manifest.json"))
    ]


def test_xsq_output_is_new_rejects_missing_and_unchanged(tmp_path: Path) -> None:
    missing = tmp_path / "song.xsq"
    assert effect_engine.xsq_output_is_new(missing, None) is False

    existing = tmp_path / "kept.xsq"
    existing.write_text("<xsequence />", encoding="utf-8")
    before = existing.stat()
    assert effect_engine.xsq_output_is_new(existing, before) is False

    existing.write_text("<xsequence>new</xsequence>", encoding="utf-8")
    assert effect_engine.xsq_output_is_new(existing, before) is True
    assert effect_engine.xsq_output_is_new(existing, None) is True


def test_audio_failure_report_records_the_exception(tmp_path: Path) -> None:
    audio = tmp_path / "song.wav"
    _wav(audio)
    out = tmp_path / "out" / "song,v27.3.xsq"
    report = effect_engine.write_audio_failure_report(out, audio, "FAILED: song.wav: RuntimeError('boom')", "traceback")
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["audio"] == "song.wav"
    assert "boom" in payload["error"]
    assert payload["traceback"] == "traceback"
    assert payload["xsq_written"] is False


def test_run_profile_exits_nonzero_when_engine_raises(monkeypatch, tmp_path: Path) -> None:
    out = tmp_path / "out"

    class _Boom:
        def main_for(self, version: str, engine_args: list[str] | None) -> None:
            raise effect_engine.SequenceGenerationError(["FAILED: song.wav: RuntimeError('render failed')"])

    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: type("P", (), {"version": "v27.3", "profile_id": "master"})())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: _Boom())
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: None)

    with pytest.raises(SystemExit) as caught:
        sequence_builder.run_profile(
            "master",
            ["--template", "template.xsq", "--audio", "song.wav", "--output-dir", str(out), "--no-effects-orchestrator"],
        )
    assert caught.value.code == 1
    manifest = _manifests(out)[-1]
    assert manifest["success"] is False
    assert manifest["status"] == "failed"
    assert "render failed" in str(manifest["error_summary"])


def test_run_profile_exits_nonzero_when_no_xsq_is_written(monkeypatch, tmp_path: Path) -> None:
    out = tmp_path / "out"

    class _Silent:
        def main_for(self, version: str, engine_args: list[str] | None) -> None:
            return None

    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: type("P", (), {"version": "v27.3", "profile_id": "master"})())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: _Silent())
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: None)

    with pytest.raises(SystemExit) as caught:
        sequence_builder.run_profile(
            "master",
            ["--no-effects-orchestrator", "--output-dir", str(out)],
        )
    assert caught.value.code == 1
    manifest = _manifests(out)[-1]
    assert manifest["success"] is False
    assert "no new .xsq" in str(manifest["error_summary"])


def test_main_for_turns_a_per_audio_exception_into_a_failed_report(monkeypatch, tmp_path: Path) -> None:
    audio = tmp_path / "clip.wav"
    _wav(audio)
    template = tmp_path / "template.xsq"
    template.write_text("<xsequence />", encoding="utf-8")
    output = tmp_path / "generated"

    def _explode(*args, **kwargs):
        raise RuntimeError("render failed")

    monkeypatch.setattr(effect_engine, "run_variant", _explode)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(effect_engine.SequenceGenerationError) as caught:
        effect_engine.main_for(
            "v27.3",
            [
                "--template",
                str(template),
                "--audio",
                str(audio),
                "--single",
                "--variants",
                "1",
                "--no-prompt",
                "--no-save-settings",
                "--quiet",
                "--output-dir",
                str(output),
            ],
        )
    assert "render failed" in str(caught.value)
    reports = list(output.glob("*.report.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert "render failed" in payload["error"]
    assert "RuntimeError" in payload["traceback"]


def test_main_for_rejects_a_run_that_writes_no_xsq(monkeypatch, tmp_path: Path) -> None:
    audio = tmp_path / "clip.wav"
    _wav(audio)
    template = tmp_path / "template.xsq"
    template.write_text("<xsequence />", encoding="utf-8")
    output = tmp_path / "generated"

    monkeypatch.setattr(effect_engine, "run_variant", lambda *args, **kwargs: {"output_path": str(output / "missing.xsq")})
    monkeypatch.chdir(tmp_path)
    with pytest.raises(effect_engine.SequenceGenerationError) as caught:
        effect_engine.main_for(
            "v27.3",
            [
                "--template",
                str(template),
                "--audio",
                str(audio),
                "--single",
                "--variants",
                "1",
                "--no-prompt",
                "--no-save-settings",
                "--quiet",
                "--output-dir",
                str(output),
            ],
        )
    assert "no new XSQ" in str(caught.value)
    payload = json.loads(next(output.glob("*.report.json")).read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["xsq_written"] is False


def test_run_manager_failure_manifest_shape(tmp_path: Path) -> None:
    config = RunConfig(output_root=tmp_path / "outputs")
    ctx = RunManager(config).start(command=["main.py"], require_existing=False)
    ctx.finalize(success=False, error_summary="FAILED: song.wav: RuntimeError('render failed')")
    manifest = json.loads(ctx.manifest_path.read_text(encoding="utf-8"))
    assert manifest["success"] is False
    assert manifest["status"] == "failed"
    assert "render failed" in manifest["errors"][-1]
