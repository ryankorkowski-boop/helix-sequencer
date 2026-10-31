"""Typed, lazy facade over the existing engine and its BeatGrid adapter.

Argument order and exceptions belong to the existing parsers. Keep the raw
argument tuple lossless rather than round-tripping it through a second parser.
This module performs no audio, preview or experimental imports at startup.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.engine_profiles import ACTIVE_STYLE_VERSION
from core.stage_metrics import StageMetrics, capture_metrics, profile_run

if TYPE_CHECKING:
    from core.effect_engine import RuntimeTuning, VariantStyle
    from xlights.xsq_writer import UserProfile


@dataclass(frozen=True)
class SequenceJobConfig:
    version: str = ACTIVE_STYLE_VERSION
    engine_args: tuple[str, ...] = ()
    metrics_output: Path | None = None


@dataclass(frozen=True)
class SequenceJobResult:
    version: str
    success: bool
    metrics: StageMetrics | None = None


def run_sequence_job(config: SequenceJobConfig) -> SequenceJobResult:
    """Run unchanged BeatGrid/controller processing; propagate engine failures.

    Explicit metrics_output captures direct API calls. The compatibility CLI
    entry also honors HELIX_PROFILE_OUTPUT. No error or success is invented
    from the existence of an old output file.
    """
    from core import effect_engine_beat_grid

    if config.metrics_output is not None:
        with capture_metrics(config.metrics_output) as metrics:
            effect_engine_beat_grid.main_for(config.version, list(config.engine_args))
        return SequenceJobResult(config.version, True, metrics)
    effect_engine_beat_grid.main_for(config.version, list(config.engine_args))
    return SequenceJobResult(config.version, True)


@profile_run
def main_for(version: str, argv: list[str] | None = None) -> None:
    """Compatibility entry for sequence_builder (and its CLI/GUI callers)."""
    run_sequence_job(SequenceJobConfig(version, tuple(argv or ())))


@profile_run
def run_variant(
    style: VariantStyle,
    template_xsq: Path,
    audio_path: Path,
    out_path: Path,
    profile: UserProfile,
    tuning: RuntimeTuning | None = None,
    analysis_cache: Any = None,
) -> dict[str, object]:
    """Lossless entry for existing multi-layout rendering tools."""
    from core import effect_engine

    return effect_engine.run_variant(
        style, template_xsq, audio_path, out_path, profile,
        tuning=tuning, analysis_cache=analysis_cache,
    )
