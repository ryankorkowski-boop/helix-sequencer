from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from core.band_intent_adapter import BandIntentAdapter
from core.band_performance_timeline import BandPerformanceTimelineCompiler
from core.band_vocal_face_export import BandVocalFaceExportCompiler, build_demo_vocal_face_timings
from core.band_xlights_export import BandXLightsExportCompiler
from core.choreography_intent import (
    ChoreographyIntent,
    ChoreographyTarget,
    IntentLayerRole,
    MotionVocabulary,
)
from core.intent_layer_expander import IntentLayerExpander
from models.helixville4_performer_runtime import build_performer_runtime_catalog


DEMO_INTENTS = (
    ChoreographyIntent(
        start=0.0,
        duration=4.0,
        section="intro",
        event_type="build",
        style="helixville4",
        emotional_energy=0.55,
        intensity=0.65,
        focal_region="center_stage",
        target_families=(ChoreographyTarget.PERFORMER,),
        motion_vocabulary=(MotionVocabulary.PULSE, MotionVocabulary.SHIMMER),
        layer_roles=(IntentLayerRole.BASE, IntentLayerRole.MOTION),
        source="band_manifest_exporter",
    ),
    ChoreographyIntent(
        start=4.0,
        duration=6.0,
        section="chorus",
        event_type="impact",
        style="helixville4",
        emotional_energy=0.95,
        intensity=1.0,
        focal_region="front_stage",
        target_families=(ChoreographyTarget.PERFORMER,),
        motion_vocabulary=(MotionVocabulary.IMPACT, MotionVocabulary.BLOOM),
        layer_roles=(IntentLayerRole.EVENT, IntentLayerRole.ACCENT),
        source="band_manifest_exporter",
    ),
)

ARTIFACT_FILENAMES = {
    "combined": "helixville4_band_demo_manifest.json",
    "runtime_catalog": "helixville4_band_runtime_catalog.json",
    "xlights_export": "helixville4_band_xlights_export.json",
    "vocal_face_export": "helixville4_band_vocal_face_export.json",
    "summary": "HELIXVILLE4_BAND_SUMMARY.txt",
}


def build_demo_manifest() -> dict:
    expanded = IntentLayerExpander().expand_many(DEMO_INTENTS)
    adapted = BandIntentAdapter().adapt_many(expanded)
    timeline = BandPerformanceTimelineCompiler().compile_many(adapted)
    export_manifest = BandXLightsExportCompiler().build_manifest(timeline)
    vocal_face_manifest = BandVocalFaceExportCompiler().build_manifest(build_demo_vocal_face_timings())

    return {
        "schema": "helixville4.band_demo_manifest.v1",
        "runtime_catalog": build_performer_runtime_catalog(),
        "intent_count": len(DEMO_INTENTS),
        "expanded_event_count": len(expanded),
        "adapted_event_count": len(adapted),
        "timeline_event_count": len(timeline),
        "xlights_export": export_manifest,
        "vocal_face_export": vocal_face_manifest,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_demo_manifest(output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = build_demo_manifest()

    manifest_path = out_dir / ARTIFACT_FILENAMES["combined"]
    _write_json(manifest_path, payload)
    _write_json(out_dir / ARTIFACT_FILENAMES["runtime_catalog"], payload["runtime_catalog"])
    _write_json(out_dir / ARTIFACT_FILENAMES["xlights_export"], payload["xlights_export"])
    _write_json(out_dir / ARTIFACT_FILENAMES["vocal_face_export"], payload["vocal_face_export"])

    summary_path = out_dir / ARTIFACT_FILENAMES["summary"]
    summary_path.write_text(
        "Helixville4 deterministic performer pipeline export generated.\n"
        "Includes all five runtime performers, compiled timeline events,\n"
        "xLights-oriented submodel effect instructions, and vocal face instructions.\n"
        "Standalone JSON artifacts are written for runtime catalog, submodel effects,\n"
        "and vocal face effects for downstream import/testing.\n",
        encoding="utf-8",
    )

    return manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export deterministic Helixville4 band performance manifests.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_runs/helixville4_band_manifest"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = export_demo_manifest(args.output_dir)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
