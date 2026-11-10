from tools.build_helpers.explainable_shortlist_adapter import (
    adapt_variant_entry,
    attach_explainable_shortlist_report,
    build_explainable_shortlist_report,
)


def _entry(label, quality, audit, rejected, advisory=None):
    return {
        "label": label,
        "quality": {
            "score": quality,
            "component_scores": {
                "structure": 85.0,
                "coverage": 82.0,
                "detail": 80.0,
                "family_diversity": 78.0,
                "dominance": 84.0,
            },
        },
        "audit": {
            "final": {
                "score": audit,
                "musical_coherence": 90.0,
                "section_coverage": 0.88,
                "overlap_ratio": 0.02,
                "clutter_ratio": 0.06,
            }
        },
        "validation": {
            "rejected_effects_count": rejected,
        },
        "self_improving_scoring": {
            "total_score": 0.91,
        },
        "polish": {
            "score": 90.0,
            "hook_enhancements": 3,
            "breathing_fades": 2,
            "palette_swaps": 1,
        },
        "advisory": advisory or {},
    }


def test_adapt_variant_entry_extracts_expected_metrics():
    adapted = adapt_variant_entry(
        _entry(
            "signature",
            95.0,
            89.0,
            9000,
            advisory={
                "motif_memory": {"score": 0.84},
                "palette_discipline": {"score": 0.9},
            },
        )
    )

    assert adapted["variant_id"] == "signature"
    assert adapted["quality_score"] == 95.0
    assert adapted["audit_score"] == 89.0
    assert adapted["rejected_effects"] == 9000
    assert adapted["motif_memory"]["score"] == 0.84


def test_build_explainable_shortlist_report_agreement():
    entries = [
        _entry("strong", 96.0, 90.0, 7000),
        _entry("weak", 88.0, 78.0, 25000),
    ]

    report = build_explainable_shortlist_report(entries, preset="showcase")

    payload = report.as_dict()

    assert payload["agreement"] is True
    assert payload["legacy_winner"] == "strong"
    assert payload["explainable_winner"] == "strong"
    assert payload["warnings"] == []


def test_build_explainable_shortlist_report_warns_on_divergence():
    entries = [
        _entry(
            "legacy_favored",
            96.0,
            90.0,
            7000,
            advisory={
                "motif_memory": {"score": 0.2},
                "palette_discipline": {"score": 0.2},
                "section_identity": {"score": 0.2},
            },
        ),
        _entry(
            "explainable_favored",
            94.0,
            89.0,
            9000,
            advisory={
                "motif_memory": {"score": 0.95},
                "palette_discipline": {"score": 0.95},
                "section_identity": {"score": 0.95},
            },
        ),
    ]

    report = build_explainable_shortlist_report(entries, preset="showcase")

    payload = report.as_dict()

    assert payload["agreement"] is False
    assert payload["legacy_winner"] == "legacy_favored"
    assert payload["explainable_winner"] == "explainable_favored"
    assert any("did not change selection" in warning for warning in payload["warnings"])


def test_attach_explainable_shortlist_report_returns_copy():
    payload = {"existing": True}
    entries = [
        _entry("strong", 96.0, 90.0, 7000),
    ]

    updated = attach_explainable_shortlist_report(payload, entries)

    assert updated is not payload
    assert updated["existing"] is True
    assert "explainable_shortlist" in updated
    assert "explainable_shortlist" not in payload


def test_empty_entries_generate_warning():
    report = build_explainable_shortlist_report([], preset="showcase")

    payload = report.as_dict()

    assert payload["legacy_winner"] is None
    assert payload["explainable_winner"] is None
    assert any("no entries provided" in warning for warning in payload["warnings"])
