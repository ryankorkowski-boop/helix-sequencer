from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.capture_xlights_validation_evidence import (
    RestProbe,
    build_evidence,
    evidence_markdown,
    write_evidence,
)


def test_build_evidence_records_artifact_and_manual_statuses() -> None:
    evidence = build_evidence(
        artifact_run_url="https://github.com/example/repo/actions/runs/123",
        artifact_name="helix-flow-review-artifacts",
        artifact_digest="sha256:abc",
        xsq_filename="helix_flow_demo.xsq",
        mp4_filename="helix_flow_demo.mp4",
        xlights_version="2024.9",
        xsq_import_status="imported",
        preview_render_status="rendered",
        visual_review_status="passed",
        controller_status="not_tested",
        reviewer="tester",
        notes="Imported cleanly; controller proof still pending.",
        rest_probes=(RestProbe("127.0.0.1", 49913, False, "connection refused"),),
    )

    assert evidence.schema == "helix.xlights_validation_evidence.v1"
    assert evidence.artifact_digest == "sha256:abc"
    assert evidence.xsq_import_status == "imported"
    assert evidence.preview_render_status == "rendered"
    assert evidence.visual_review_status == "passed"
    assert evidence.controller_status == "not_tested"
    assert evidence.rest_probes[0].port == 49913


def test_build_evidence_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="xsq_import_status must be one of"):
        build_evidence(
            artifact_run_url="https://github.com/example/repo/actions/runs/123",
            artifact_name="helix-flow-review-artifacts",
            artifact_digest=None,
            xsq_filename="helix_flow_demo.xsq",
            mp4_filename="helix_flow_demo.mp4",
            xlights_version=None,
            xsq_import_status="maybe",
            preview_render_status="not_tested",
            visual_review_status="not_reviewed",
            controller_status="not_tested",
            reviewer=None,
            notes="",
        )


def test_write_evidence_outputs_json_and_markdown(tmp_path: Path) -> None:
    evidence = build_evidence(
        artifact_run_url="https://github.com/example/repo/actions/runs/123",
        artifact_name="helix-flow-review-artifacts",
        artifact_digest="sha256:abc",
        xsq_filename="helix_flow_demo.xsq",
        mp4_filename="helix_flow_demo.mp4",
        xlights_version=None,
        xsq_import_status="blocked",
        preview_render_status="not_tested",
        visual_review_status="blocked",
        controller_status="blocked",
        reviewer=None,
        notes="xLights REST automation was not active.",
    )

    paths = write_evidence(evidence, tmp_path)

    assert set(paths) == {"json", "markdown"}
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["xsq_import_status"] == "blocked"
    assert payload["controller_status"] == "blocked"
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert "# xLights Validation Evidence" in markdown
    assert "xLights REST automation was not active." in markdown


def test_evidence_markdown_preserves_controller_boundary() -> None:
    evidence = build_evidence(
        artifact_run_url="https://github.com/example/repo/actions/runs/123",
        artifact_name="helix-flow-review-artifacts",
        artifact_digest=None,
        xsq_filename="helix_flow_demo.xsq",
        mp4_filename="helix_flow_demo.mp4",
        xlights_version=None,
        xsq_import_status="not_tested",
        preview_render_status="rendered",
        visual_review_status="not_reviewed",
        controller_status="not_tested",
        reviewer=None,
        notes="",
    )

    markdown = evidence_markdown(evidence)

    assert "- Controller/channel safety: `not_tested`" in markdown
    assert "- Not probed" in markdown
