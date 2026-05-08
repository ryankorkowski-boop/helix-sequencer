from tools.showcase.showcase_score import score_showcase_report


def _reports():
    return {
        "showcase_energy": {"showcase_energy_score": 0.8},
        "showcase_hero_dominance": {"showcase_hero_score": 0.75},
        "showcase_motion_continuity": {"showcase_motion_score": 0.7},
        "showcase_palette_arc": {"showcase_palette_score": 0.65},
        "showcase_impact_model": {"showcase_impact_score": 0.85},
    }


def test_full_showcase_report_scores_expected_range():
    report = score_showcase_report(_reports())

    assert report.score >= 0.7
    assert set(report.available_components) == set(_reports())
    assert report.missing_components == ()
    assert "showcase_energy" in report.weighted_components
    assert any(finding.code == "showcase_component_contribution" for finding in report.findings)


def test_missing_components_are_reported_but_available_scores_still_work():
    report = score_showcase_report({
        "showcase_energy": {"showcase_energy_score": 0.8},
    })

    assert report.score == 0.8
    assert report.available_components == ("showcase_energy",)
    assert "showcase_impact_model" in report.missing_components
    assert any(finding.code == "missing_showcase_component" for finding in report.findings)


def test_weak_component_is_flagged():
    reports = _reports()
    reports["showcase_palette_arc"] = {"showcase_palette_score": 0.3}

    report = score_showcase_report(reports)

    assert any(
        finding.code == "weak_showcase_component" and finding.component == "showcase_palette_arc"
        for finding in report.findings
    )


def test_empty_reports_return_zero_with_finding():
    report = score_showcase_report({})

    assert report.score == 0.0
    assert report.available_components == ()
    assert any(finding.code == "no_showcase_components" for finding in report.findings)


def test_custom_weights_change_score():
    reports = _reports()
    default_report = score_showcase_report(reports)
    custom_report = score_showcase_report(
        reports,
        weights={
            "showcase_energy": 1.0,
            "showcase_hero_dominance": 0.0,
            "showcase_motion_continuity": 0.0,
            "showcase_palette_arc": 0.0,
            "showcase_impact_model": 0.0,
        },
    )

    assert custom_report.score == 0.8
    assert custom_report.score != default_report.score
