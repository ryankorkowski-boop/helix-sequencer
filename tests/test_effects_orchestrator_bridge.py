from __future__ import annotations

import json
from pathlib import Path

from core.effects_orchestrator_bridge import build_seed_graph, run_effects_orchestration, visual_intents_from_graph


def test_seed_graph_has_canonical_show_sections() -> None:
    graph = build_seed_graph(["--audio", "LightsOutTheme.wav", "--duration", "40"])
    assert len(graph.intents) == 5
    assert graph.ordered_sections() == ("intro", "verse", "build", "chorus", "finale")


def test_final_graph_converts_to_visual_intents() -> None:
    graph = build_seed_graph(["--audio", "LightsOutTheme.wav", "--duration", "40"])
    visual_intents = visual_intents_from_graph(graph)
    assert len(visual_intents) == len(graph.intents)
    assert all(item.id.startswith("orchestrated:") for item in visual_intents)
    assert any("performer" in item.target_roles for item in visual_intents)


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
    assert report.final_visual_intents == 5
    assert report.placement_count > 0
    assert report.effect_contract_placement_count > 0
    assert report.export_driven is True
    assert report.placement_plan_path is not None
    assert report.effect_contract_path is not None
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
    written = Path(report.report_path or "")
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["invoked"] is True
    assert payload["final_intents"] == 5
    assert payload["export_driven"] is True

    placement_payload = json.loads(Path(report.placement_plan_path).read_text(encoding="utf-8"))
    assert placement_payload["schema"] == "helix.placement_plan.v1"
    assert placement_payload["planner_report"]["placement_count"] == report.placement_count

    contract_payload = json.loads(Path(report.effect_contract_path).read_text(encoding="utf-8"))
    assert contract_payload["schema"] == "helix.xlights_effect_contract.v1"
    assert contract_payload["placement_count"] == report.effect_contract_placement_count
