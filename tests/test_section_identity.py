from tools.build_helpers.section_identity import score_section_identity


def test_strong_section_plan_scores_high():
    report = score_section_identity([
        {
            "name": "intro",
            "kind": "intro",
            "start": 0.0,
            "end": 12.0,
            "target_intensity": 0.3,
            "primary_groups": ["roofline"],
            "secondary_groups": ["mini_trees"],
            "palette": "winter_soft",
            "motion_intent": "gentle_reveal",
            "density": "low",
        },
        {
            "name": "verse",
            "kind": "verse",
            "start": 12.0,
            "end": 45.0,
            "target_intensity": 0.5,
            "primary_groups": ["arches"],
            "secondary_groups": ["roofline"],
            "palette": "winter_soft",
            "motion_intent": "rhythmic_support",
            "density": "medium",
        },
        {
            "name": "chorus",
            "kind": "chorus",
            "start": 45.0,
            "end": 72.0,
            "target_intensity": 0.86,
            "primary_groups": ["mega_tree", "roofline"],
            "secondary_groups": ["arches", "snowman_band"],
            "palette": "classic_christmas_bright",
            "motion_intent": "wide_sweeps_and_spirals",
            "density": "high",
        },
        {
            "name": "finale",
            "kind": "finale",
            "start": 150.0,
            "end": 180.0,
            "target_intensity": 0.97,
            "primary_groups": ["whole_layout"],
            "secondary_groups": ["mega_tree", "snowman_band", "arches"],
            "palette": "classic_christmas_finale",
            "motion_intent": "layered_bursts_and_cascades",
            "density": "peak",
        },
    ])

    assert report.section_count == 4
    assert report.score >= 0.8
    assert report.finale_strength_score == 1.0


def test_flat_adjacent_sections_are_flagged():
    report = score_section_identity([
        {
            "name": "verse_1",
            "kind": "verse",
            "start": 0.0,
            "end": 30.0,
            "target_intensity": 0.5,
            "primary_groups": ["roofline"],
            "palette": "red_green",
            "motion_intent": "sweep",
            "density": "medium",
        },
        {
            "name": "chorus_1",
            "kind": "chorus",
            "start": 30.0,
            "end": 60.0,
            "target_intensity": 0.52,
            "primary_groups": ["roofline"],
            "palette": "red_green",
            "motion_intent": "sweep",
            "density": "medium",
        },
    ])

    assert report.contrast_score < 0.5
    assert any(finding.code == "weak_adjacent_section_contrast" for finding in report.findings)


def test_missing_section_data_lowers_coverage():
    report = score_section_identity([
        {
            "name": "unknown_section",
            "kind": "unknown",
            "start": 10.0,
            "end": 10.0,
            "target_intensity": 0.5,
        }
    ])

    assert report.coverage_score < 1.0
    assert any(finding.code == "invalid_section_duration" for finding in report.findings)
    assert any(finding.code == "section_missing_groups" for finding in report.findings)
    assert any(finding.code == "section_missing_palette" for finding in report.findings)


def test_weak_finale_is_flagged():
    report = score_section_identity([
        {
            "name": "intro",
            "kind": "intro",
            "start": 0.0,
            "end": 20.0,
            "target_intensity": 0.3,
            "primary_groups": ["roofline"],
            "palette": "soft",
            "motion_intent": "reveal",
            "density": "low",
        },
        {
            "name": "finale",
            "kind": "finale",
            "start": 100.0,
            "end": 120.0,
            "target_intensity": 0.6,
            "primary_groups": ["mini_trees"],
            "palette": "soft",
            "motion_intent": "small_sparkles",
            "density": "medium",
        },
    ])

    assert report.finale_strength_score < 1.0
    assert any(finding.code == "weak_finale_intensity" for finding in report.findings)
    assert any(finding.code == "weak_finale_density" for finding in report.findings)
    assert any(finding.code == "narrow_finale_coverage" for finding in report.findings)


def test_no_sections_returns_zero_score_with_finding():
    report = score_section_identity([])

    assert report.section_count == 0
    assert report.score == 0.0
    assert any(finding.code == "no_sections" for finding in report.findings)
