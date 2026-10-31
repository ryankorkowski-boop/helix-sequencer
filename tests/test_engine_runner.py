"""Public-boundary contracts: preserve argument order, results and failures."""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import core
from core import engine_runner


def test_facade_import_does_not_load_engine_or_optional_stacks():
    code = '''import sys
from core import engine_runner
assert not any(name in sys.modules for name in (
    "core.effect_engine", "core.effect_engine_beat_grid", "librosa", "numpy",
    "whisper", "PIL", "moderngl"))
'''
    subprocess.run([sys.executable, "-c", code], check=True)


def test_typed_job_forwards_lossless_args_and_captures_metrics(monkeypatch, tmp_path):
    calls = []
    fake = SimpleNamespace(main_for=lambda version, args: calls.append((version, args)))
    monkeypatch.setitem(sys.modules, "core.effect_engine_beat_grid", fake)
    monkeypatch.setattr(core, "effect_engine_beat_grid", fake, raising=False)
    args = ("--snap-grid", "1/16", "--audio=a song.mp3", "--density", "0.7")
    metrics_path = tmp_path / "stages.json"
    result = engine_runner.run_sequence_job(engine_runner.SequenceJobConfig(
        "v27.3", args, metrics_path))
    assert result.success and result.version == "v27.3"
    assert calls == [("v27.3", list(args))]
    assert json.loads(metrics_path.read_text())["success"] is True


@pytest.mark.parametrize("error", [RuntimeError("failed"), SystemExit(2), KeyboardInterrupt()])
def test_facade_keeps_original_errors(monkeypatch, tmp_path, error):
    def fail(*args):
        raise error
    monkeypatch.setitem(sys.modules, "core.effect_engine_beat_grid", SimpleNamespace(main_for=fail))
    monkeypatch.setattr(core, "effect_engine_beat_grid", sys.modules["core.effect_engine_beat_grid"], raising=False)
    path = tmp_path / "failed.json"
    with pytest.raises(type(error)) as caught:
        engine_runner.run_sequence_job(engine_runner.SequenceJobConfig(metrics_output=path))
    assert caught.value is error
    assert json.loads(path.read_text())["success"] is False


def test_compatibility_entry_preserves_none_return(monkeypatch):
    calls = []
    monkeypatch.setattr(engine_runner, "run_sequence_job", lambda config: calls.append(config))
    assert engine_runner.main_for("v27.3", ["--no-snap"]) is None
    assert calls == [engine_runner.SequenceJobConfig("v27.3", ("--no-snap",))]


def test_variant_facade_preserves_return_and_cache(monkeypatch):
    from core import effect_engine
    calls = []
    expected = {"report_path": "out.report.json"}
    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return expected
    monkeypatch.setattr(effect_engine, "run_variant", run)
    style, profile, tuning, cache = object(), object(), object(), object()
    paths = (Path("template.xsq"), Path("audio.wav"), Path("out.xsq"))
    assert engine_runner.run_variant(style, *paths, profile, tuning=tuning, analysis_cache=cache) is expected
    assert calls == [((style, *paths, profile), {"tuning": tuning, "analysis_cache": cache})]
