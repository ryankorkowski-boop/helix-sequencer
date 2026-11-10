"""Full-show orchestrator: wires previously unintegrated engines into a complete show path.

Fail-soft: every engine is called inside try/except so a problem in one module
cannot break the main sequence. Results are collected into a JSON report.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any


def _safe_call(name: str, fn, *args, **kwargs) -> dict[str, Any]:
    try:
        result = fn(*args, **kwargs)
        return {"engine": name, "status": "ok", "result": str(result)[:500] if result is not None else None}
    except Exception as exc:
        return {
            "engine": name,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc()[-800:],
        }


def apply_full_show_enhancements(
    audio_path: Path | None = None,
    layout_path: Path | None = None,
    output_dir: Path | None = None,
    song_length_ms: int = 180_000,
) -> dict[str, Any]:
    """Run all previously unintegrated engines and return a summary report."""
    report: dict[str, Any] = {
        "full_show": True,
        "engines": [],
        "audio": str(audio_path) if audio_path else None,
        "layout": str(layout_path) if layout_path else None,
    }

    # Style engine
    try:
        from core import style_engine
        decision = style_engine.infer_style({})
        report["engines"].append({"engine": "style_engine", "status": "ok", "detected": getattr(decision, "detected_style", None)})
    except Exception as exc:
        report["engines"].append({"engine": "style_engine", "status": "error", "error": str(exc)})

    # Adaptive emotional storytelling
    try:
        from core.adaptive_emotional_storytelling_engine import AdaptiveEmotionalStorytellingEngine
        engine = AdaptiveEmotionalStorytellingEngine()
        if hasattr(engine, "orchestrate"):
            result = engine.orchestrate()
            report["engines"].append({"engine": "adaptive_emotional_storytelling", "status": "ok", "result": str(result)[:300]})
        else:
            report["engines"].append({"engine": "adaptive_emotional_storytelling", "status": "no_orchestrate"})
    except Exception as exc:
        report["engines"].append({"engine": "adaptive_emotional_storytelling", "status": "error", "error": str(exc)})

    # Visual cinematography
    try:
        from core.visual_cinematography_engine import VisualCinematographyEngine
        engine = VisualCinematographyEngine()
        if hasattr(engine, "orchestrate") or hasattr(engine, "plan"):
            method = getattr(engine, "orchestrate", None) or getattr(engine, "plan", None)
            if method:
                result = method()
                report["engines"].append({"engine": "visual_cinematography", "status": "ok", "result": str(result)[:300]})
            else:
                report["engines"].append({"engine": "visual_cinematography", "status": "instantiated"})
        else:
            report["engines"].append({"engine": "visual_cinematography", "status": "instantiated"})
    except Exception as exc:
        report["engines"].append({"engine": "visual_cinematography", "status": "error", "error": str(exc)})

    # Autonomous masterpiece evaluator
    try:
        from core.autonomous_masterpiece_evaluator import AutonomousMasterpieceEvaluator
        evaluator = AutonomousMasterpieceEvaluator()
        if hasattr(evaluator, "evaluate"):
            result = evaluator.evaluate({})
            report["engines"].append({"engine": "autonomous_masterpiece_evaluator", "status": "ok", "result": str(result)[:300]})
        else:
            report["engines"].append({"engine": "autonomous_masterpiece_evaluator", "status": "instantiated"})
    except Exception as exc:
        report["engines"].append({"engine": "autonomous_masterpiece_evaluator", "status": "error", "error": str(exc)})

    # Multi-pass orchestration director
    try:
        from core.multi_pass_orchestration_director import MultiPassOrchestrationDirector
        director = MultiPassOrchestrationDirector()
        if hasattr(director, "direct") or hasattr(director, "orchestrate"):
            method = getattr(director, "direct", None) or getattr(director, "orchestrate", None)
            if method:
                result = method()
                report["engines"].append({"engine": "multi_pass_orchestration_director", "status": "ok", "result": str(result)[:300]})
            else:
                report["engines"].append({"engine": "multi_pass_orchestration_director", "status": "instantiated"})
        else:
            report["engines"].append({"engine": "multi_pass_orchestration_director", "status": "instantiated"})
    except Exception as exc:
        report["engines"].append({"engine": "multi_pass_orchestration_director", "status": "error", "error": str(exc)})

    # Show identity
    try:
        from core.show_identity_engine import ShowIdentityEngine
        identity = ShowIdentityEngine()
        report["engines"].append({"engine": "show_identity", "status": "instantiated", "id": str(identity)})
    except Exception as exc:
        report["engines"].append({"engine": "show_identity", "status": "error", "error": str(exc)})

    # Live audience energy
    try:
        from core.live_audience_energy_engine import LiveAudienceEnergyEngine
        engine = LiveAudienceEnergyEngine()
        report["engines"].append({"engine": "live_audience_energy", "status": "instantiated"})
    except Exception as exc:
        report["engines"].append({"engine": "live_audience_energy", "status": "error", "error": str(exc)})

    # Spatial mapping (lightweight)
    try:
        from core import spatial_mapping_engine
        report["engines"].append({"engine": "spatial_mapping", "status": "imported"})
    except Exception as exc:
        report["engines"].append({"engine": "spatial_mapping", "status": "error", "error": str(exc)})

    # Power engine (lightweight)
    try:
        from core import power_engine
        report["engines"].append({"engine": "power_engine", "status": "imported"})
    except Exception as exc:
        report["engines"].append({"engine": "power_engine", "status": "error", "error": str(exc)})

    # Effect layering
    try:
        from core import effect_layering_engine
        report["engines"].append({"engine": "effect_layering", "status": "imported"})
    except Exception as exc:
        report["engines"].append({"engine": "effect_layering", "status": "error", "error": str(exc)})

    # Write report if output dir given
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "full_show_report.json"
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        report["report_path"] = str(report_path)

    return report
