from __future__ import annotations

from pathlib import Path

from tools.export_helix_flow_review_artifacts import export_review_artifacts
from tools.validate_xsq_structure import validate_xsq


def test_export_review_artifacts_writes_all_expected_files(tmp_path: Path) -> None:
    paths = export_review_artifacts(tmp_path, duration_seconds=3.0, step_seconds=1.0, bpm=120.0)

    assert set(paths) == {
        "manifest",
        "quality",
        "baseline",
        "iteration",
        "xsq",
        "mp4",
        "acceptance_summary",
    }
    for path in paths.values():
        assert path.exists(), path

    validate_xsq(paths["xsq"])
    assert paths["mp4"].suffix == ".mp4"
    assert paths["mp4"].stat().st_size > 0


def test_export_review_artifacts_acceptance_summary_marks_mp4_present(tmp_path: Path) -> None:
    paths = export_review_artifacts(tmp_path, duration_seconds=3.0, step_seconds=1.0, bpm=120.0)

    text = paths["acceptance_summary"].read_text(encoding="utf-8")

    assert "Helix Flow Issue #2 Acceptance Summary" in text
    assert "- [x] XSQ generated" in text
    assert "- [x] MP4 preview generated" in text


def test_export_review_artifacts_is_deterministic_for_text_artifacts(tmp_path: Path) -> None:
    first = export_review_artifacts(tmp_path / "first", duration_seconds=3.0, step_seconds=1.0, bpm=120.0)
    second = export_review_artifacts(tmp_path / "second", duration_seconds=3.0, step_seconds=1.0, bpm=120.0)

    for key in ("manifest", "quality", "baseline", "iteration", "xsq", "acceptance_summary"):
        assert first[key].read_text(encoding="utf-8") == second[key].read_text(encoding="utf-8")
