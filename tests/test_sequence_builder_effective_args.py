from __future__ import annotations

import json
from types import SimpleNamespace

from core import sequence_builder
from core.run_config import RunConfig


class _FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str] | None]] = []

    def main_for(self, version: str, engine_args: list[str] | None) -> None:
        self.calls.append((version, list(engine_args or [])))


def test_run_profile_records_stripped_engine_args(monkeypatch, tmp_path) -> None:
    fake_engine = _FakeEngine()
    monkeypatch.setattr(
        sequence_builder.engine_profiles,
        "resolve_profile",
        lambda profile_id: SimpleNamespace(version="v27.3", profile_id="master"),
    )
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(
        sequence_builder,
        "run_effects_orchestration",
        lambda engine_args: SimpleNamespace(
            invoked=True,
            passes=(object(),),
            report_path=str(tmp_path / "song.effects_orchestration.json"),
            error=None,
            xsq_written=True,
            orchestrated_xsq_path=str(tmp_path / "song.orchestrated.xsq"),
            placement_plan_path=None,
            effect_contract_path=None,
            xsq_render_report_path=None,
        ),
    )

    output = tmp_path / "outputs"
    sequence_builder.run_profile(
        "master",
        ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", str(output), "--birdsong"],
    )

    assert fake_engine.calls
    effective = fake_engine.calls[0][1]
    assert "--snap-grid" not in effective
    assert "--birdsong" in effective
    assert "--birdsong-issue2-demo" not in effective
    manifests = list((output / "beta").glob("*/run_manifest.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["effective_engine_args"] == effective
    assert "--snap-grid" in payload["command"]
    note = (manifests[0].parent / "effective_engine_args.txt").read_text(encoding="utf-8")
    assert "--snap-grid" not in note


def test_birdsong_flag_does_not_write_synthetic_manifest(tmp_path) -> None:
    class Ctx:
        def record_warning(self, message: str) -> None:
            raise AssertionError(message)

        def record_artifact(self, kind: str, path) -> None:
            raise AssertionError(kind)

    sequence_builder._run_birdsong_hook(
        RunConfig(output_root=tmp_path),
        ["--birdsong", "--birdsong-profile", "canopy"],
        Ctx(),
    )
    assert not (tmp_path / "birdsong_runtime_manifest.json").exists()


def test_issue2_demo_flag_writes_synthetic_manifest_only(tmp_path) -> None:
    artifacts: list[tuple[str, object]] = []

    class Ctx:
        def record_warning(self, message: str) -> None:
            return None

        def record_artifact(self, kind: str, path) -> None:
            artifacts.append((kind, path))

    sequence_builder._run_birdsong_hook(
        RunConfig(output_root=tmp_path),
        ["--birdsong-issue2-demo"],
        Ctx(),
    )
    manifest = tmp_path / "birdsong_runtime_manifest.json"
    assert manifest.exists()
    assert artifacts and artifacts[0][0] == "birdsong_runtime_manifest"
