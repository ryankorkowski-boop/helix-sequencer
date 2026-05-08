from tools.showcase.hero_dominance import score_hero_dominance


def test_strong_hero_dominance_scores_well():
    report = score_hero_dominance([
        {"name": "intro", "kind": "intro", "start": 0, "end": 12, "intensity": 0.25, "breadth": 0.25, "motion": 0.2, "hero_share": 0.25},
        {"name": "verse", "kind": "verse", "start": 12, "end": 40, "intensity": 0.45, "breadth": 0.55, "motion": 0.4, "hero_share": 0.45},
        {"name": "chorus", "kind": "chorus", "start": 40, "end": 70, "intensity": 0.85, "breadth": 0.8, "motion": 0.75, "hero_share": 0.65},
        {"name": "finale", "kind": "finale", "start": 70, "end": 105, "intensity": 0.95, "breadth": 0.95, "motion": 0.9, "hero_share": 0.75},
    ])

    assert report.section_count == 4
    assert report.focal_clarity_score >= 0.65
    assert report.hero_moment_score >= 0.9
    assert report.visual_mush_penalty == 0.0
    assert report.showcase_hero_score >= 0.75


def test_visual_mush_is_flagged_when_everything_fires_without_focal_point():
    report = score_hero_dominance([
        {"name": "chorus", "kind": "chorus", "start": 0, "end": 30, "intensity": 0.9, "breadth": 0.95, "motion": 0.9, "hero_share": 0.1},
        {"name": "finale", "kind": "finale", "start": 30, "end": 60, "intensity": 0.95, "breadth": 0.95, "motion": 0.95, "hero_share": 0.15},
    ])

    assert report.visual_mush_penalty > 0
    assert any(finding.code == "visual_mush_risk" for finding in report.findings)
    assert any(finding.code == "weak_focal_hierarchy" for finding in report.findings)


def test_weak_hero_moments_are_flagged():
    report = score_hero_dominance([
        {"name": "verse", "kind": "verse", "start": 0, "end": 30, "intensity": 0.4, "breadth": 0.4, "motion": 0.4, "hero_share": 0.3},
        {"name": "chorus", "kind": "chorus", "start": 30, "end": 60, "intensity": 0.85, "breadth": 0.7, "motion": 0.85, "hero_share": 0.2},
    ])

    assert report.hero_moment_score < 0.55
    assert any(finding.code == "weak_hero_moments" for finding in report.findings)


def test_hero_without_support_stage_is_flagged():
    report = score_hero_dominance([
        {"name": "solo", "kind": "solo", "start": 0, "end": 25, "intensity": 0.8, "breadth": 0.2, "motion": 0.7, "hero_share": 0.8},
    ])

    assert any(finding.code == "hero_without_support_stage" for finding in report.findings)


def test_no_sections_returns_zero_score_with_finding():
    report = score_hero_dominance([])

    assert report.section_count == 0
    assert report.showcase_hero_score == 0.0
    assert any(finding.code == "no_sections" for finding in report.findings)
