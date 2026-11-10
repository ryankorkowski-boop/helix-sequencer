from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from tools.capture_xlights_validation_evidence import (
    RestProbe,
    build_evidence,
    probe_xlights_rest,
    write_evidence,
)
from tools.export_helix_flow_review_artifacts import export_review_artifacts
from tools.validate_xsq_structure import validate_xsq


DEFAULT_OUTPUT_DIR = Path("test_runs/xlights_review_kit")


@dataclass(frozen=True)
class XlightsReviewKit:
    output_dir: Path
    xsq_path: Path
    mp4_path: Path
    evidence_json: Path
    evidence_markdown: Path
    manual_steps: Path


def manual_steps_markdown(
    *,
    xsq_path: Path,
    mp4_path: Path,
    artifact_run_url: str,
    rest_probes: Sequence[RestProbe],
) -> str:
    probe_lines = "\n".join(
        f"- `{probe.host}:{probe.port}`: {'reachable' if probe.reachable else 'unavailable'} ({probe.detail})"
        for probe in rest_probes
    ) or "- Not probed"
    return (
        "# xLights Manual Review Kit\n\n"
        "This kit is for recording the remaining Issue #76 manual evidence. It does not by itself prove xLights import, visual quality, or controller safety.\n\n"
        "## Inputs\n\n"
        f"- Artifact run: {artifact_run_url}\n"
        f"- XSQ: `{xsq_path}`\n"
        f"- MP4 preview: `{mp4_path}`\n\n"
        "## Local Automation Probe\n\n"
        f"{probe_lines}\n\n"
        "## Manual xLights Pass\n\n"
        "1. Open xLights with the intended show folder/layout.\n"
        "2. Open or import the XSQ listed above.\n"
        "3. Record whether xLights opens the sequence without errors or warnings.\n"
        "4. Inspect timing tracks/effects and note any model-binding warnings.\n"
        "5. Render or preview in xLights and compare against the MP4 preview for obvious timing/order issues.\n"
        "6. Update `xlights_validation_evidence.json` with `imported`, `failed`, or `blocked` status and reviewer notes.\n\n"
        "## Controller/Channel Safety Pass\n\n"
        "1. Use a copied layout/controller setup only.\n"
        "2. Confirm channel ranges do not overlap unexpectedly.\n"
        "3. Confirm controller outputs are not changed unless using a disposable test controller/profile.\n"
        "4. Record `passed`, `failed`, or `blocked` in the evidence file.\n\n"
        "## Close Rule\n\n"
        "Do not check off Issue #76 xLights import, visual review, or controller/channel safety until the evidence file records the completed status and links to reviewable notes or artifacts.\n"
    )


def build_review_kit(
    output_dir: Path,
    *,
    artifact_run_url: str,
    artifact_digest: str | None,
    duration_seconds: float = 20.0,
    step_seconds: float = 1.0,
    bpm: float = 120.0,
    probe_rest: bool = True,
) -> XlightsReviewKit:
    paths = export_review_artifacts(
        output_dir,
        duration_seconds=duration_seconds,
        step_seconds=step_seconds,
        bpm=bpm,
    )
    xsq_path = paths["xsq"]
    mp4_path = paths["mp4"]
    validate_xsq(xsq_path)
    rest_probes = probe_xlights_rest() if probe_rest else ()
    evidence = build_evidence(
        artifact_run_url=artifact_run_url,
        artifact_name="helix-flow-review-artifacts",
        artifact_digest=artifact_digest,
        xsq_filename=xsq_path.name,
        mp4_filename=mp4_path.name,
        xlights_version=None,
        xsq_import_status="not_tested",
        preview_render_status="rendered" if mp4_path.exists() else "failed",
        visual_review_status="not_reviewed",
        controller_status="not_tested",
        reviewer=None,
        notes="Local clean-room review kit generated. xLights GUI import/manual visual review/controller safety still require a human validation pass.",
        rest_probes=rest_probes,
    )
    evidence_paths = write_evidence(evidence, output_dir)
    manual_steps = output_dir / "MANUAL_XLIGHTS_REVIEW.md"
    manual_steps.write_text(
        manual_steps_markdown(
            xsq_path=xsq_path,
            mp4_path=mp4_path,
            artifact_run_url=artifact_run_url,
            rest_probes=rest_probes,
        ),
        encoding="utf-8",
    )
    return XlightsReviewKit(
        output_dir=output_dir,
        xsq_path=xsq_path,
        mp4_path=mp4_path,
        evidence_json=evidence_paths["json"],
        evidence_markdown=evidence_paths["markdown"],
        manual_steps=manual_steps,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local xLights manual review kit from clean-room artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifact-run-url", required=True)
    parser.add_argument("--artifact-digest", default=None)
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--step-seconds", type=float, default=1.0)
    parser.add_argument("--bpm", type=float, default=120.0)
    parser.add_argument("--no-probe-rest", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kit = build_review_kit(
        args.output_dir,
        artifact_run_url=args.artifact_run_url,
        artifact_digest=args.artifact_digest,
        duration_seconds=args.duration_seconds,
        step_seconds=args.step_seconds,
        bpm=args.bpm,
        probe_rest=not args.no_probe_rest,
    )
    print(f"output_dir: {kit.output_dir}")
    print(f"xsq: {kit.xsq_path}")
    print(f"mp4: {kit.mp4_path}")
    print(f"evidence_json: {kit.evidence_json}")
    print(f"evidence_markdown: {kit.evidence_markdown}")
    print(f"manual_steps: {kit.manual_steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
