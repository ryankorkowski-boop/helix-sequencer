import pytest

from tools.build_helpers.regression_snapshots import (
    assert_quality_snapshot_within_tolerance,
    compact_quality_snapshot,
    compare_quality_snapshot,
)


def test_compact_quality_snapshot_extracts_stable_fields():
    snapshot = compact_quality_snapshot({
        "variant_id": "variant_01",
        "preset": "showcase",
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
        "volatile_render_path": "test_runs/tmp/output.xsq",
    })

    assert snapshot == {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
        "variant_id": "variant_01",
        "preset": "showcase",
    }


def test_compare_quality_snapshot_passes_within_tolerance():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
        "palette_discipline_score": 0.9,
    }
    actual = {
        "quality_score": 93.8,
        "audit_score": 87.8,
        "rejected_effects": 10400,
        "palette_discipline_score": 0.88,
    }

    report = compare_quality_snapshot(expected, actual)

    assert report.passed is True
    assert report.checked_keys == (
        "quality_score",
        "audit_score",
        "rejected_effects",
        "palette_discipline_score",
    )


def test_compare_quality_snapshot_fails_on_quality_regression():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }
    actual = {
        "quality_score": 92.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }

    report = compare_quality_snapshot(expected, actual)

    assert report.passed is False
    assert any(
        finding.code == "metric_outside_tolerance" and finding.key == "quality_score" and finding.severity == "error"
        for finding in report.findings
    )


def test_metric_improvement_outside_tolerance_is_warning_not_failure():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }
    actual = {
        "quality_score": 96.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }

    report = compare_quality_snapshot(expected, actual)

    assert report.passed is True
    assert any(
        finding.code == "metric_outside_tolerance" and finding.key == "quality_score" and finding.severity == "warning"
        for finding in report.findings
    )


def test_missing_required_actual_key_fails():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }
    actual = {
        "quality_score": 94.0,
        "audit_score": 88.0,
    }

    report = compare_quality_snapshot(expected, actual)

    assert report.passed is False
    assert any(finding.code == "missing_actual_key" for finding in report.findings)


def test_assert_quality_snapshot_within_tolerance_raises_on_regression():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }
    actual = {
        "quality_score": 92.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }

    with pytest.raises(AssertionError, match="Quality snapshot comparison failed"):
        assert_quality_snapshot_within_tolerance(expected, actual)


def test_custom_tolerance_can_allow_known_variance():
    expected = {
        "quality_score": 94.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }
    actual = {
        "quality_score": 93.0,
        "audit_score": 88.0,
        "rejected_effects": 10000,
    }

    report = compare_quality_snapshot(expected, actual, tolerances={"quality_score": 1.5})

    assert report.passed is True
