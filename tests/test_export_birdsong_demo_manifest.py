from __future__ import annotations

import json
from pathlib import Path

from core.birdsong_intent_manifest import SCHEMA
from tools.export_birdsong_demo_manifest import (
    build_birdsong_demo_intents,
    export_birdsong_demo_manifest,
    export_birdsong_demo_quality_report,
    export_birdsong_demo_xsq,
    export_helix_flow_baseline_report,
)
from tools.validate_xsq_structure import validate_xsq


def test_build_birdsong_demo_intents_is_deterministic() -> None:
    first = build_birdsong_demo_intents(duration_seconds=20.0, step_seconds=1.0, bpm=120.0)
    second = build_birdsong_demo_intents(duration_seconds=20.0, step_seconds=1.0, bpm=120.0)

    assert first == second
    assert first
    assert all(0.0 <= intent.start_time < 20.0 for intent in first)


def test_export_birdsong_demo_manifest_writes_20_second_artifact(tmp_path: Path) -> None:
    output = export_birdsong_demo_manifest(tmp_path / "helix_flow_intents.json", duration_seconds=20.0)

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))

    assert data["schema"] == SCHEMA
    assert data["title"] == "HelixFlowDemo20s"
    assert data["intent_count"] > 0
    assert data["intent_count"] == len(data["intents"])
    assert max(item["start_time"] for item in data["intents"]) < 20.0


def test_export_birdsong_demo_manifest_is_deterministic(tmp_path: Path) -> None:
    first = export_birdsong_demo_manifest(tmp_path / "first.json")
    second = export_birdsong_demo_manifest(tmp_path / "second.json")

    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_export_birdsong_demo_quality_report_writes_score_json(tmp_path: Path) -> None:
    manifest = export_birdsong_demo_manifest(tmp_path / "helix_flow_intents.json", duration_seconds=20.0)
    report = export_birdsong_demo_quality_report(manifest, tmp_path / "helix_flow_quality_report.json")

    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))

    assert data["intent_count"] > 0
    assert 0.0 <= data["score"] <= 1.0
    assert data["public_engine_name"] == "Helix Flow Engine"
    assert data["public_engine_slug"] == "helix_flow"
    assert set(data) == {
        "score",
        "musicality",
        "spatial_coherence",
        "layering",
        "novelty",
        "emotion",
        "intent_count",
        "public_engine_name",
        "public_engine_slug",
    }


def test_export_helix_flow_baseline_report_writes_comparison_json(tmp_path: Path) -> None:
    manifest = export_birdsong_demo_manifest(tmp_path / "helix_flow_intents.json", duration_seconds=20.0)
    quality = export_birdsong_demo_quality_report(manifest, tmp_path / "helix_flow_quality_report.json")
    baseline = export_helix_flow_baseline_report(quality, tmp_path / "helix_flow_baseline_report.json")

    assert baseline.exists()
    data = json.loads(baseline.read_text(encoding="utf-8"))

    assert data["public_engine_name"] == "Helix Flow Engine"
    assert data["public_engine_slug"] == "helix_flow"
    assert "recommended_next_adjustment" in data
    assert "weakest_category" in data
    assert "deltas" in data
    assert 0.0 <= data["score"] <= 1.0


def test_export_birdsong_demo_xsq_writes_valid_xsq(tmp_path: Path) -> None:
    xsq = export_birdsong_demo_xsq(tmp_path / "helix_flow_demo.xsq", duration_seconds=20.0)

    assert xsq.exists()
    validate_xsq(xsq)
    xml = xsq.read_text(encoding="utf-8")
    assert "ElementEffects" in xml
    assert "BirdsongIntentTrack" in xml
    assert "HelixFlowDemo20s" in xml


def test_build_birdsong_demo_rejects_invalid_inputs() -> None:
    for kwargs in (
        {"duration_seconds": 0.0},
        {"step_seconds": 0.0},
    ):
        try:
            build_birdsong_demo_intents(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {kwargs}")
