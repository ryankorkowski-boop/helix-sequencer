from __future__ import annotations

from types import SimpleNamespace

from core import sequence_builder


class _FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str] | None]] = []

    def main_for(self, version: str, engine_args: list[str] | None) -> None:
        self.calls.append((version, engine_args))


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


def test_run_profile_promotes_orchestrated_xsq_as_next_template(monkeypatch) -> None:
    fake_engine = _FakeEngine()
    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", lambda engine_args: _report())

    sequence_builder.run_profile(
        "master",
        ["--template", "template.xsq", "--audio", "song.mp3", "--output-dir", "out"],
    )

    assert fake_engine.calls == [
        (
            "v27.3",
            ["--template", "out/song.orchestrated.xsq", "--audio", "song.mp3", "--output-dir", "out"],
        )
    ]


def test_run_profile_can_keep_orchestrated_xsq_as_sidecar_only(monkeypatch) -> None:
    fake_engine = _FakeEngine()
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
            "--no-orchestrator-template-promotion",
        ],
    )

    assert fake_engine.calls == [
        ("v27.3", ["--template", "template.xsq", "--audio", "song.mp3"]),
    ]


def test_run_profile_no_effects_orchestrator_skips_orchestration_and_strips_flag(monkeypatch) -> None:
    fake_engine = _FakeEngine()
    called = False

    def _unexpected_orchestration(engine_args: list[str] | None) -> SimpleNamespace:
        nonlocal called
        called = True
        return _report()

    monkeypatch.setattr(sequence_builder.engine_profiles, "resolve_profile", lambda profile_id: _profile())
    monkeypatch.setattr(sequence_builder, "_effect_engine", lambda: fake_engine)
    monkeypatch.setattr(sequence_builder, "run_effects_orchestration", _unexpected_orchestration)

    sequence_builder.run_profile(
        "master",
        ["--template", "template.xsq", "--no-effects-orchestrator", "--audio", "song.mp3"],
    )

    assert called is False
    assert fake_engine.calls == [
        ("v27.3", ["--template", "template.xsq", "--audio", "song.mp3"]),
    ]
