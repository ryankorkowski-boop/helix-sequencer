from tools.build_helpers.restraint import RestraintRules, score_restraint


def test_clean_low_density_cues_score_high():
    report = score_restraint([
        {"time": 10.0, "kind": "beat", "intensity": 0.4, "target_groups": ["arches"], "section": "verse"},
        {"time": 14.0, "kind": "downbeat", "intensity": 0.6, "target_groups": ["roofline"], "section": "verse"},
        {"time": 20.0, "kind": "section_peak", "intensity": 0.9, "target_groups": ["mega_tree"], "section": "chorus"},
    ])

    assert report.score == 1.0
    assert report.density_penalty == 0.0
    assert report.findings == ()


def test_flags_whole_house_overuse_by_section():
    cues = [
        {"time": float(index), "kind": "whole_house_hit", "intensity": 0.95, "target_groups": ["whole_layout"], "section": "chorus"}
        for index in range(6)
    ]

    report = score_restraint(cues, RestraintRules(max_whole_house_hits_per_section=4))

    assert report.whole_house_hit_count == 6
    assert report.score < 1.0
    assert any(finding.code == "whole_house_overuse" for finding in report.findings)


def test_flags_major_hits_too_close():
    report = score_restraint([
        {"time": 30.0, "kind": "section_peak", "intensity": 0.95, "target_groups": ["mega_tree"], "section": "chorus"},
        {"time": 30.75, "kind": "major_hit", "intensity": 0.92, "target_groups": ["roofline"], "section": "chorus"},
    ], RestraintRules(min_seconds_between_major_hits=2.0))

    assert any(finding.code == "major_hits_too_close" for finding in report.findings)
    assert report.density_penalty > 0


def test_flags_too_many_dominant_groups():
    report = score_restraint([
        {
            "time": 45.0,
            "kind": "section_peak",
            "intensity": 0.9,
            "target_groups": ["mega_tree", "roofline", "arches", "mini_trees", "snowman_band"],
            "section": "chorus",
        }
    ], RestraintRules(max_simultaneous_dominant_groups=3))

    assert any(finding.code == "too_many_dominant_groups" for finding in report.findings)


def test_flags_strobe_below_required_energy():
    report = score_restraint([
        {"time": 12.0, "kind": "beat", "effect_family": "strobe", "intensity": 0.5, "target_groups": ["strobes"], "section": "verse"}
    ], RestraintRules(strobe_requires_intensity_at_least=0.85))

    assert report.strobe_count == 1
    assert any(finding.code == "strobe_without_peak_energy" for finding in report.findings)


def test_flags_strobe_when_disabled():
    report = score_restraint([
        {"time": 12.0, "kind": "beat", "effect_family": "strobe", "intensity": 0.95, "target_groups": ["strobes"], "section": "verse"}
    ], RestraintRules(allow_strobe=False))

    assert any(finding.code == "strobe_disabled" for finding in report.findings)
