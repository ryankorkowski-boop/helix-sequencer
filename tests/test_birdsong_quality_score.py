from __future__ import annotations

from core.birdsong_quality_score import score_birdsong_manifest
from tools.export_birdsong_demo_manifest import build_birdsong_demo_intents
from core.birdsong_intent_manifest import build_intent_manifest


def test_score_empty_manifest_is_zero() -> None:
    report = score_birdsong_manifest({"intents": []})

    assert report.score == 0.0
    assert report.intent_count == 0
    assert report.musicality == 0.0
    assert report.spatial_coherence == 0.0
    assert report.layering == 0.0
    assert report.novelty == 0.0
    assert report.emotion == 0.0


def test_score_birdsong_manifest_uses_issue_two_weighting_formula() -> None:
    manifest = {
        "intents": [
            {
                "effect_name": "Bars",
                "motif": "wave_sweep",
                "direction": "left_to_right",
                "start_time": 0.0,
                "duration": 1.0,
                "strength": 0.8,
                "score": 0.9,
            },
            {
                "effect_name": "Twinkle",
                "motif": "sparkle_field",
                "direction": "top_down",
                "start_time": 1.0,
                "duration": 1.0,
                "strength": 0.6,
                "score": 0.7,
            },
        ]
    }

    report = score_birdsong_manifest(manifest)
    expected = round(
        report.musicality * 0.30
        + report.spatial_coherence * 0.25
        + report.layering * 0.20
        + report.novelty * 0.15
        + report.emotion * 0.10,
        6,
    )

    assert report.score == expected
    assert report.intent_count == 2
    assert 0.0 <= report.score <= 1.0


def test_score_demo_manifest_is_deterministic() -> None:
    intents = build_birdsong_demo_intents(duration_seconds=20.0, step_seconds=1.0, bpm=120.0)
    manifest = build_intent_manifest(intents)

    first = score_birdsong_manifest(manifest)
    second = score_birdsong_manifest(manifest)

    assert first == second
    assert first.intent_count == len(intents)
    assert first.score > 0.0


def test_report_serializes_to_dict() -> None:
    report = score_birdsong_manifest({"intents": []})

    assert report.as_dict() == {
        "score": 0.0,
        "musicality": 0.0,
        "spatial_coherence": 0.0,
        "layering": 0.0,
        "novelty": 0.0,
        "emotion": 0.0,
        "intent_count": 0,
    }
