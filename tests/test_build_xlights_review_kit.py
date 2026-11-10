from __future__ import annotations

from pathlib import Path

from tools.build_xlights_review_kit import manual_steps_markdown
from tools.capture_xlights_validation_evidence import RestProbe


def test_manual_steps_markdown_names_artifacts_and_boundaries(tmp_path: Path) -> None:
    xsq = tmp_path / "helix_flow_demo.xsq"
    mp4 = tmp_path / "helix_flow_demo.mp4"

    text = manual_steps_markdown(
        xsq_path=xsq,
        mp4_path=mp4,
        artifact_run_url="https://github.com/example/repo/actions/runs/123",
        rest_probes=(RestProbe("127.0.0.1", 49913, False, "connection refused"),),
    )

    assert "helix_flow_demo.xsq" in text
    assert "helix_flow_demo.mp4" in text
    assert "does not by itself prove xLights import" in text
    assert "127.0.0.1:49913" in text
    assert "Do not check off Issue #76" in text


def test_manual_steps_markdown_handles_unprobed_rest(tmp_path: Path) -> None:
    text = manual_steps_markdown(
        xsq_path=tmp_path / "demo.xsq",
        mp4_path=tmp_path / "demo.mp4",
        artifact_run_url="https://github.com/example/repo/actions/runs/123",
        rest_probes=(),
    )

    assert "- Not probed" in text
    assert "Controller/Channel Safety Pass" in text
