from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from core import sequence_builder


class _FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str] | None]] = []

    def main_for(self, version: str, engine_args: list[str] | None) -> None:
        self.calls.append((version, engine_args))
        args = list(engine_args or [])
        folder = Path("outputs")
        if "--output-dir" in args:
            folder = Path(args[args.index("--output-dir") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "generated.xsq").write_text("<xsequence />", encoding="utf-8")


def _profile() -> SimpleNamespace:
    return SimpleNamespace(version="v27.3")


def _report(*, invoked: bool = True, xsq_written: bool = True, path: str | None = "out/song.orchestrated.xsq") -> SimpleNamespace:
    return SimpleNamespace(
        invoked=invoked,
        passes=(object(), object()),
        report_path="out/song.effects_orchestration.json",
        error=None,
        xsq_written=xsq_written,
        orchestrated_xsq_path=path,
    )


def test_run_profile_keeps_orchestrated_xsq_as_sidecar_by_default(monkeypatch, tmp_path: Path) -> None:
    fake_engine = _FakeEngine()
    out = tmp_path / "out"
    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: _report())

    sequence_builder.run_profile(
        "master",
        ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", str(out)],
    )

    assert fake_engine.calls == [
        (
            "v27.3",
            ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", str(out)],
        )
    ]


def test_run_profile_promotes_orchestrated_xsq_as_next_template_when_requested(monkeypatch, tmp_path: Path) -> None:
    fake_engine = _FakeEngine()
    out = tmp_path / "out"
    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: _report())

    sequence_builder.run_profile(
        "master",
        [
            "--template",
            "template.xsq",
            "--audio",
            "song.mp3",
            "--output-dir",
            str(out),
            "--promote-orchestrated-template",
        ],
    )

    assert fake_engine.calls == [
        (
            "v27.3",
            ["--template", "out/song.orchestrated.xsq", "--audio", "song.mp3", "--output-dir", str(out)],
        )
    ]


def test_run_profile_can_force_orchestrated_xsq_sidecar_only(monkeypatch, tmp_path: Path) -> None:
    fake_engine = _FakeEngine()
    out = tmp_path / "out"
    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: _report())

    sequence_builder.run_profile(
        "master",
        [
            "--template",
            "template.xsq",
            "--audio",
            "song.mp3",
            "--output-dir",
            str(out),
            "--no-orchestrator-template-promotion",
        ],
    )

    assert fake_engine.calls == [
        ("v27.3", ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", str(out)]),
    ]


def test_run_profile_no_effects_orchestrator_skips_orchestration_and_strips_flag(monkeypatch, tmp_path: Path) -> None:
    fake_engine = _FakeEngine()
    called = False

    def _unexpected_orchestration(engine_args: list[str] | None) -> SimpleNamespace:
        nonlocal called
        called = True
        return _report()

    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", _unexpected_orchestration)

    out = tmp_path / "out"
    sequence_builder.run_profile(
        "master",
        ["--template", "template.xsq", "--no-effects-orchestrator", "--audio", "song.mp3", "--output-dir", str(out)],
    )

    assert called is False
    assert fake_engine.calls == [
        ("v27.3", ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", str(out)]),
    ]
