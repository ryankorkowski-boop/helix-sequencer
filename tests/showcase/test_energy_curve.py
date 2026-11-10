from tools.showcase.energy_curve import score_showcase_energy
from tools.showcase.trace import normalize_section_trace


def test_section_trace_visual_energy_clamps_and_combines_components():
    trace = normalize_section_trace({
        "name": "chorus",
        "kind": "chorus",
        "intensity": 1.5,
        "breadth": 1.0,
        "motion": 0.8,
        "darkness": 0.0,
    })

    assert trace.intensity == 1.0
    assert 0.9 <= trace.visual_energy <= 1.0


def test_showcase_energy_rewards_restrained_build_and_finale_peak():
    report = score_showcase_energy([
        {"name": "intro", "kind": "intro", "start": 0, "end": 12, "intensity": 0.2, "breadth": 0.2, "motion": 0.2, "darkness": 0.4},
        {"name": "verse", "kind": "verse", "start": 12, "end": 40, "intensity": 0.35, "breadth": 0.35, "motion": 0.3, "darkness": 0.2},
        {"name": "chorus", "kind": "chorus", "start": 40, "end": 70, "intensity": 0.75, "breadth": 0.75, "motion": 0.7, "darkness": 0.0, "hero_share": 0.65},
        {"name": "bridge", "kind": "bridge", "start": 70, "end": 95, "intensity": 0.42, "breadth": 0.35, "motion": 0.35, "darkness": 0.45},
        {"name": "finale", "kind": "finale", "start": 95, "end": 125, "intensity": 0.95, "breadth": 0.95, "motion": 0.9, "darkness": 0.0, "hero_share": 0.8},
    ])

    assert report.section_count == 5
    assert report.energy_curve_score >= 0.75
    assert report.chorus_contrast_delta >= 0.7
    assert report.finale_escalation_index >= 0.7
    assert report.showcase_energy_score >= 0.65


def test_flat_energy_curve_is_flagged():
    report = score_showcase_energy([
        {"name": "intro", "kind": "intro", "start": 0, "end": 10, "intensity": 0.5, "breadth": 0.5, "motion": 0.5},
        {"name": "verse", "kind": "verse", "start": 10, "end": 30, "intensity": 0.52, "breadth": 0.5, "motion": 0.5},
        {"name": "chorus", "kind": "chorus", "start": 30, "end": 60, "intensity": 0.53, "breadth": 0.5, "motion": 0.5},
        {"name": "finale", "kind": "finale", "start": 60, "end": 80, "intensity": 0.51, "breadth": 0.5, "motion": 0.5},
    ])

    assert any(finding.code == "flat_energy_curve" for finding in report.findings)
    assert any(finding.code == "weak_chorus_lift" for finding in report.findings)


def test_weak_finale_escalation_is_flagged():
    report = score_showcase_energy([
        {"name": "intro", "kind": "intro", "start": 0, "end": 12, "intensity": 0.3, "breadth": 0.3, "motion": 0.3},
        {"name": "chorus", "kind": "chorus", "start": 12, "end": 45, "intensity": 0.95, "breadth": 0.9, "motion": 0.9, "hero_share": 0.8},
        {"name": "finale", "kind": "finale", "start": 45, "end": 70, "intensity": 0.4, "breadth": 0.4, "motion": 0.3, "hero_share": 0.2},
    ])

    assert any(finding.code == "weak_finale_escalation" for finding in report.findings)
    assert any(finding.code == "finale_not_near_peak" for finding in report.findings)


def test_no_sections_returns_zero_score_with_finding():
    report = score_showcase_energy([])

    assert report.section_count == 0
    assert report.showcase_energy_score == 0.0
    assert any(finding.code == "no_sections" for finding in report.findings)
