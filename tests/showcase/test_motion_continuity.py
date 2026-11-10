from tools.showcase.motion_continuity import score_motion_continuity


def test_smooth_motion_sequence_scores_well():
    report = score_motion_continuity([
        {
            "name": "intro_sweep",
            "motion_family": "sweep",
            "direction": "left_to_right",
            "intensity": 0.35,
            "speed": 0.35,
            "breadth": 0.5,
            "transition": "blend",
            "start": 0.0,
            "end": 10.0,
        },
        {
            "name": "verse_chase",
            "motion_family": "chase",
            "direction": "left_to_right",
            "intensity": 0.55,
            "speed": 0.5,
            "breadth": 0.65,
            "transition": "wipe",
            "start": 10.0,
            "end": 25.0,
        },
        {
            "name": "chorus_spiral",
            "motion_family": "spiral",
            "direction": "inside_out",
            "intensity": 0.85,
            "speed": 0.75,
            "breadth": 0.85,
            "transition": "crossfade",
            "start": 25.0,
            "end": 45.0,
        },
    ])

    assert report.motion_count == 3
    assert report.direction_coherence_score >= 0.6
    assert report.family_continuity_score >= 0.5
    assert report.transition_smoothness_score >= 0.85
    assert report.hard_cut_penalty == 0.0
    assert report.showcase_motion_score >= 0.65


def test_abrupt_direction_flip_is_flagged():
    report = score_motion_continuity([
        {
            "name": "left_sweep",
            "motion_family": "sweep",
            "direction": "left_to_right",
            "intensity": 0.7,
            "speed": 0.6,
            "transition": "blend",
            "start": 0.0,
            "end": 10.0,
        },
        {
            "name": "right_sweep",
            "motion_family": "sweep",
            "direction": "right_to_left",
            "intensity": 0.7,
            "speed": 0.6,
            "transition": "blend",
            "start": 10.0,
            "end": 20.0,
        },
    ])

    assert report.direction_coherence_score < 1.0
    assert any(finding.code == "abrupt_direction_flip" for finding in report.findings)


def test_unrelated_high_energy_motion_jump_is_flagged():
    report = score_motion_continuity([
        {
            "name": "spiral_peak",
            "motion_family": "spiral",
            "direction": "inside_out",
            "intensity": 0.9,
            "speed": 0.8,
            "transition": "crossfade",
            "start": 0.0,
            "end": 10.0,
        },
        {
            "name": "random_strobe",
            "motion_family": "strobe",
            "direction": "random",
            "intensity": 0.9,
            "speed": 0.9,
            "transition": "cut",
            "start": 10.0,
            "end": 15.0,
        },
    ])

    assert report.family_continuity_score < 1.0
    assert any(finding.code == "unrelated_high_energy_motion_jump" for finding in report.findings)


def test_hard_cut_risk_is_flagged():
    report = score_motion_continuity([
        {
            "name": "slow_wash",
            "motion_family": "wash",
            "direction": "center",
            "intensity": 0.3,
            "speed": 0.2,
            "transition": "blend",
            "start": 0.0,
            "end": 10.0,
        },
        {
            "name": "hard_peak",
            "motion_family": "burst",
            "direction": "inside_out",
            "intensity": 0.9,
            "speed": 0.9,
            "transition": "hard_cut",
            "start": 10.0,
            "end": 12.0,
        },
    ])

    assert report.hard_cut_penalty > 0.0
    assert any(finding.code == "hard_cut_risk" for finding in report.findings)
    assert any(finding.code == "high_energy_hard_transition" for finding in report.findings)


def test_no_motion_traces_returns_zero_score_with_finding():
    report = score_motion_continuity([])

    assert report.motion_count == 0
    assert report.showcase_motion_score == 0.0
    assert any(finding.code == "no_motion_traces" for finding in report.findings)
