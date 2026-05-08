from tools.showcase.impact_model import score_impact_model


def test_strong_impact_sequence_scores_well():
    report = score_impact_model([
        {
            "name": "chorus_drop",
            "kind": "drop",
            "start": 30.0,
            "end": 32.0,
            "intensity": 0.9,
            "breadth": 0.85,
            "darkness_before": 0.75,
            "density_before": 0.2,
            "surprise": 0.55,
            "beat_alignment": 0.95,
        },
        {
            "name": "finale_climax",
            "kind": "finale",
            "start": 90.0,
            "end": 100.0,
            "intensity": 1.0,
            "breadth": 1.0,
            "darkness_before": 0.35,
            "density_before": 0.35,
            "surprise": 0.4,
            "beat_alignment": 0.95,
        },
    ])

    assert report.impact_count == 2
    assert report.anticipation_score >= 0.6
    assert report.drop_punch_score >= 0.7
    assert report.finale_payoff_score >= 0.7
    assert report.showcase_impact_score >= 0.65


def test_weak_anticipation_and_drop_punch_are_flagged():
    report = score_impact_model([
        {
            "name": "flat_drop",
            "kind": "drop",
            "start": 10.0,
            "end": 12.0,
            "intensity": 0.45,
            "breadth": 0.35,
            "darkness_before": 0.0,
            "density_before": 0.95,
            "surprise": 0.0,
            "beat_alignment": 0.4,
        }
    ])

    assert any(finding.code == "weak_anticipation" for finding in report.findings)
    assert any(finding.code == "weak_drop_punch" for finding in report.findings)


def test_peak_spam_is_flagged():
    report = score_impact_model([
        {
            "name": f"peak_{index}",
            "kind": "hit",
            "start": float(index * 2),
            "end": float(index * 2 + 1),
            "intensity": 1.0,
            "breadth": 1.0,
            "darkness_before": 0.2,
            "density_before": 0.2,
            "surprise": 0.4,
            "beat_alignment": 0.95,
        }
        for index in range(5)
    ])

    assert any(finding.code == "peak_spam_risk" for finding in report.findings)


def test_weak_finale_payoff_is_flagged():
    report = score_impact_model([
        {
            "name": "early_peak",
            "kind": "drop",
            "start": 10.0,
            "end": 12.0,
            "intensity": 1.0,
            "breadth": 1.0,
            "darkness_before": 0.8,
            "density_before": 0.1,
            "surprise": 0.5,
            "beat_alignment": 0.95,
        },
        {
            "name": "soft_finale",
            "kind": "finale",
            "start": 90.0,
            "end": 100.0,
            "intensity": 0.45,
            "breadth": 0.4,
            "darkness_before": 0.1,
            "density_before": 0.7,
            "surprise": 0.0,
            "beat_alignment": 0.5,
        },
    ])

    assert any(finding.code == "weak_finale_payoff" for finding in report.findings)


def test_no_impacts_returns_zero_score_with_finding():
    report = score_impact_model([])

    assert report.impact_count == 0
    assert report.showcase_impact_score == 0.0
    assert any(finding.code == "no_impacts" for finding in report.findings)
