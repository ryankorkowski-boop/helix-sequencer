from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from core.beat_aligner import align_to_beat_grid
from core.energy_scaler import scale_section_intensity
from core.lyric_section_scheduler import schedule_lyric_section
from core.xsq_emitter import emit_xsq_sequence
from tools.validate_xsq_structure import validate_xsq


DEMO_LINES = [
    "Audio in",
    "Lights out",
]


def build_demo_xsq_text(
    *,
    section_energy: float = 0.85,
    beat_interval: float = 0.5,
    grid_division: int = 2,
) -> str:
    timings = schedule_lyric_section(
        performer="singer",
        lines=DEMO_LINES,
        section_start=0.0,
        section_duration=4.0,
        intensity=1.0,
    )
    timings = scale_section_intensity(timings, section_energy)
    timings = align_to_beat_grid(timings, beat_interval=beat_interval, grid_division=grid_division)

    sequence = emit_xsq_sequence(
        timings=timings,
        sequence_name="HelixDemoVocal",
        model_name="HX_SNOWMAN_SINGER",
    )
    return sequence.xml_text


def export_demo_xsq(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_demo_xsq_text(), encoding="utf-8")
    validate_xsq(path)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a deterministic Helix demo XSQ artifact.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("test_runs/helix_demo_xsq/helix_demo_vocal.xsq"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = export_demo_xsq(args.output)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
