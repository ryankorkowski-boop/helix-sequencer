from __future__ import annotations

import json
from pathlib import Path

from core.effects_orchestrator_bridge import build_seed_graph, run_effects_orchestration


def test_seed_graph_has_canonical_show_sections() -> None:
    graph = build_seed_graph(["--audio", "LightsOutTheme.wav", "--duration", "40"])
    assert len(graph.intents) == 5
    assert graph.ordered_sections() == ("intro", "verse", "build", "chorus", "finale")


def test_effects_orchestrator_runs_all_passes_and_writes_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    report = run_effects_orchestration(
        ["--audio", "LightsOutTheme.wav", "--output-dir", str(output_dir), "--duration", "30"],
        write_report=True,
    )
    assert report.available is True
    assert report.enabled is True
    assert report.invoked is True
    assert report.input_intents == 5
    assert report.final_intents == 5
    assert report.report_path is not None
    pass_names = [item["pass_name"] for item in report.passes]
    assert pass_names == [
        "timeline_orchestration",
        "sequence_memory",
        "emotional_storytelling",
        "visual_cinematography",
        "spatial_choreography",
        "signature_identity",
        "audience_energy",
        "quality_convergence",
        "masterpiece_evaluation",
    ]
    written = Path(report.report_path)
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["invoked"] is True
    assert payload["final_intents"] == 5
