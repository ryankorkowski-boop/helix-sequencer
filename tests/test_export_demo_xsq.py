from __future__ import annotations

from pathlib import Path

from tools.export_demo_xsq import build_demo_xsq_text, export_demo_xsq



def test_generated_demo_is_deterministic():
    first = build_demo_xsq_text()
    second = build_demo_xsq_text()

    assert first == second



def test_export_writes_valid_xsq(tmp_path: Path):
    output = tmp_path / "demo.xsq"

    export_demo_xsq(output)

    assert output.exists()

    xml = output.read_text(encoding="utf-8")

    assert "<xsequence" in xml
    assert "<timingtrack" in xml
    assert "<effects" in xml
    assert "phoneme" in xml
