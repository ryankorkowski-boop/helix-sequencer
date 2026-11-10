from tools.build_helpers.motif_memory import score_motif_memory


def test_strong_recurring_chorus_motif_scores_high():
    report = score_motif_memory([
        {
            "name": "chorus_spiral_1",
            "section": "chorus_1",
            "section_kind": "chorus",
            "family": "spiral",
            "palette": "classic_christmas_bright",
            "primary_groups": ["mega_tree"],
            "intensity_range": [0.72, 0.88],
            "variation": "base",
            "start": 30.0,
            "end": 45.0,
        },
        {
            "name": "chorus_spiral_2",
            "section": "chorus_2",
            "section_kind": "chorus",
            "family": "spiral",
            "palette": "classic_christmas_bright",
            "primary_groups": ["mega_tree", "roofline"],
            "intensity_range": [0.82, 0.96],
            "variation": "expanded",
            "start": 90.0,
            "end": 110.0,
        },
        {
            "name": "verse_sweep",
            "section": "verse_1",
            "section_kind": "verse",
            "family": "sweep",
            "palette": "winter_soft",
            "primary_groups": ["roofline"],
            "intensity_range": [0.35, 0.55],
            "variation": "support",
            "start": 12.0,
            "end": 28.0,
        },
    ])

    assert report.motif_count == 3
    assert report.identity_reuse_score >= 0.6
    assert report.variation_score >= 0.7
    assert report.score >= 0.65


def test_weak_motif_reuse_is_flagged_for_repeated_section_kind():
    report = score_motif_memory([
        {
            "name": "chorus_spiral",
            "section_kind": "chorus",
            "family": "spiral",
            "palette": "classic_christmas_bright",
            "primary_groups": ["mega_tree"],
            "intensity_range": [0.7, 0.9],
        },
        {
            "name": "chorus_strobe",
            "section_kind": "chorus",
            "family": "strobe",
            "palette": "edm_neon",
            "primary_groups": ["strobes"],
            "intensity_range": [0.95, 1.0],
        },
    ])

    assert report.identity_reuse_score < 0.45
    assert any(finding.code == "weak_motif_reuse" for finding in report.findings)


def test_repeated_motif_without_variation_is_flagged():
    report = score_motif_memory([
        {
            "name": "chorus_1",
            "section_kind": "chorus",
            "family": "spiral",
            "palette": "classic_christmas",
            "primary_groups": ["mega_tree"],
            "intensity_range": [0.75, 0.9],
        },
        {
            "name": "chorus_2",
            "section_kind": "chorus",
            "family": "spiral",
            "palette": "classic_christmas",
            "primary_groups": ["mega_tree"],
            "intensity_range": [0.75, 0.9],
        },
    ])

    assert report.variation_score < 0.55
    assert any(finding.code == "motif_repeats_without_variation" for finding in report.findings)


def test_overfragmented_motifs_are_flagged():
    report = score_motif_memory([
        {"name": "m1", "section_kind": "intro", "family": "sweep", "palette": "winter_soft", "primary_groups": ["roofline"]},
        {"name": "m2", "section_kind": "verse", "family": "pulse", "palette": "rock", "primary_groups": ["arches"]},
        {"name": "m3", "section_kind": "chorus", "family": "spiral", "palette": "classic_christmas", "primary_groups": ["mega_tree"]},
        {"name": "m4", "section_kind": "bridge", "family": "sparkle", "palette": "warm_elegant", "primary_groups": ["mini_trees"]},
        {"name": "m5", "section_kind": "finale", "family": "burst", "palette": "classic_christmas_finale", "primary_groups": ["whole_layout"]},
    ])

    assert report.overfragmentation_score < 0.5
    assert any(finding.code == "motif_overfragmentation" for finding in report.findings)


def test_missing_motif_fields_lower_coverage():
    report = score_motif_memory([
        {"name": "unknown_motif"},
    ])

    assert report.coverage_score < 1.0
    assert any(finding.code == "motif_missing_section_kind" for finding in report.findings)
    assert any(finding.code == "motif_missing_groups" for finding in report.findings)


def test_no_motifs_returns_zero_score_with_finding():
    report = score_motif_memory([])

    assert report.motif_count == 0
    assert report.score == 0.0
    assert any(finding.code == "no_motifs" for finding in report.findings)
