from tools.build_helpers.palette_discipline import score_palette_discipline


def test_classic_christmas_palette_plan_scores_high():
    report = score_palette_discipline([
        {"name": "intro", "kind": "intro", "start": 0.0, "palette": "classic_christmas", "colors": ["red", "green", "warm_white"]},
        {"name": "verse", "kind": "verse", "start": 12.0, "palette": "classic_christmas", "colors": ["red", "green", "warm_white"]},
        {"name": "chorus", "kind": "chorus", "start": 45.0, "palette": "classic_christmas_bright", "colors": ["red", "green", "white", "gold"]},
        {"name": "finale", "kind": "finale", "start": 150.0, "palette": "classic_christmas_finale", "colors": ["red", "green", "white", "gold"]},
    ], style="classic_christmas")

    assert report.section_count == 4
    assert report.score >= 0.8
    assert report.style_alignment_score == 1.0


def test_palette_style_mismatch_is_flagged():
    report = score_palette_discipline([
        {"name": "verse", "kind": "verse", "start": 0.0, "palette": "spooky"},
        {"name": "chorus", "kind": "chorus", "start": 30.0, "palette": "spooky"},
    ], style="classic_christmas")

    assert report.style_alignment_score == 0.0
    assert any(finding.code == "palette_style_mismatch" for finding in report.findings)


def test_abrupt_color_churn_is_flagged_for_showcase():
    report = score_palette_discipline([
        {"name": "intro", "kind": "intro", "start": 0.0, "colors": ["red", "green"]},
        {"name": "verse", "kind": "verse", "start": 20.0, "colors": ["blue", "cyan"]},
        {"name": "chorus", "kind": "chorus", "start": 50.0, "colors": ["orange", "purple"]},
    ], style="showcase")

    assert report.color_churn_score < 1.0
    assert any(finding.code == "abrupt_color_family_change" for finding in report.findings)


def test_edm_style_tolerates_more_color_churn():
    report = score_palette_discipline([
        {"name": "intro", "kind": "intro", "start": 0.0, "colors": ["red", "green"]},
        {"name": "drop", "kind": "drop", "start": 20.0, "colors": ["blue", "cyan"]},
        {"name": "drop_2", "kind": "drop", "start": 50.0, "colors": ["magenta", "purple"]},
    ], style="edm")

    assert report.color_churn_score >= 0.85
    assert not any(finding.code == "abrupt_color_family_change" for finding in report.findings)


def test_repeated_chorus_palette_motif_scores_high():
    report = score_palette_discipline([
        {"name": "chorus_1", "kind": "chorus", "start": 30.0, "colors": ["red", "green", "white"]},
        {"name": "verse", "kind": "verse", "start": 60.0, "colors": ["blue", "white"]},
        {"name": "chorus_2", "kind": "chorus", "start": 90.0, "colors": ["red", "green", "white"]},
    ], style="showcase")

    assert report.motif_reuse_score == 1.0


def test_weak_recurring_section_palette_motif_is_flagged():
    report = score_palette_discipline([
        {"name": "chorus_1", "kind": "chorus", "start": 30.0, "colors": ["red", "green"]},
        {"name": "chorus_2", "kind": "chorus", "start": 90.0, "colors": ["blue", "cyan"]},
    ], style="showcase")

    assert report.motif_reuse_score < 0.35
    assert any(finding.code == "weak_recurring_section_palette_motif" for finding in report.findings)


def test_missing_palette_intent_is_flagged():
    report = score_palette_discipline([
        {"name": "unknown", "kind": "unknown", "start": 0.0},
    ])

    assert report.palette_consistency_score < 1.0
    assert any(finding.code == "missing_palette_intent" for finding in report.findings)


def test_no_sections_returns_zero_score_with_finding():
    report = score_palette_discipline([])

    assert report.section_count == 0
    assert report.score == 0.0
    assert any(finding.code == "no_sections" for finding in report.findings)
