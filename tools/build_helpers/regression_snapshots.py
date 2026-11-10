"""Quality-report regression snapshot helpers for Helix.

Slice 9 is advisory/test-infrastructure only. This module compares compact quality
report snapshots with tolerances. It does not render effects, write XSQ content,
mutate layouts, or require proprietary/vendor sequence files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


DEFAULT_TOLERANCES: dict[str, float] = {
    "quality_score": 0.5,
    "audit_score": 0.5,
    "explainable_score": 0.02,
    "restraint_score": 0.03,
    "section_identity_score": 0.03,
    "palette_discipline_score": 0.03,
    "motif_memory_score": 0.03,
    "manual_lock_respect_score": 0.03,
    "rejected_effects": 500.0,
}

DEFAULT_REQUIRED_KEYS = (
    "quality_score",
    "audit_score",
    "rejected_effects",
)


@dataclass(frozen=True)
class SnapshotFinding:
    """One snapshot comparison finding."""

    code: str
    severity: str
    message: str
    key: str | None = None
    expected: object | None = None
    actual: object | None = None
    tolerance: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "tolerance": self.tolerance,
        }


@dataclass(frozen=True)
class SnapshotComparisonReport:
    """Result of comparing a current compact report to a baseline snapshot."""

    passed: bool
    checked_keys: tuple[str, ...]
    findings: tuple[SnapshotFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "checked_keys": list(self.checked_keys),
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _as_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_quality_snapshot(raw_report: Mapping[str, object]) -> dict[str, object]:
    """Extract stable quality fields from a larger report-like mapping.

    This intentionally avoids snapshotting full exported sequences or volatile
    formatting-heavy artifacts. Callers can store the returned dictionary as JSON.
    """

    snapshot: dict[str, object] = {}
    for key in DEFAULT_TOLERANCES:
        if key in raw_report:
            snapshot[key] = raw_report[key]

    variant_id = raw_report.get("variant_id", raw_report.get("id"))
    if variant_id is not None:
        snapshot["variant_id"] = str(variant_id)

    preset = raw_report.get("preset")
    if preset is not None:
        snapshot["preset"] = str(preset)

    return snapshot


def compare_quality_snapshot(
    expected: Mapping[str, object],
    actual: Mapping[str, object],
    tolerances: Mapping[str, float] | None = None,
    required_keys: Iterable[str] = DEFAULT_REQUIRED_KEYS,
) -> SnapshotComparisonReport:
    """Compare compact quality snapshots using per-field tolerances."""

    active_tolerances = dict(DEFAULT_TOLERANCES)
    if tolerances:
        active_tolerances.update({key: float(value) for key, value in tolerances.items()})

    findings: list[SnapshotFinding] = []
    checked_keys: list[str] = []

    for key in required_keys:
        if key not in expected:
            findings.append(
                SnapshotFinding(
                    code="missing_expected_key",
                    severity="error",
                    key=key,
                    message=f"Expected snapshot is missing required key '{key}'.",
                )
            )
        if key not in actual:
            findings.append(
                SnapshotFinding(
                    code="missing_actual_key",
                    severity="error",
                    key=key,
                    message=f"Actual snapshot is missing required key '{key}'.",
                )
            )

    for key, expected_value in expected.items():
        if key not in active_tolerances:
            continue
        if key not in actual:
            findings.append(
                SnapshotFinding(
                    code="missing_actual_metric",
                    severity="error",
                    key=key,
                    expected=expected_value,
                    message=f"Actual snapshot is missing metric '{key}'.",
                )
            )
            continue

        checked_keys.append(key)
        actual_value = actual[key]
        expected_float = _as_float(expected_value)
        actual_float = _as_float(actual_value)
        tolerance = active_tolerances[key]
        if expected_float is None or actual_float is None:
            findings.append(
                SnapshotFinding(
                    code="non_numeric_metric",
                    severity="error",
                    key=key,
                    expected=expected_value,
                    actual=actual_value,
                    tolerance=tolerance,
                    message=f"Metric '{key}' must be numeric for tolerant comparison.",
                )
            )
            continue

        delta = actual_float - expected_float
        if abs(delta) > tolerance:
            severity = "warning" if delta > 0 else "error"
            findings.append(
                SnapshotFinding(
                    code="metric_outside_tolerance",
                    severity=severity,
                    key=key,
                    expected=expected_float,
                    actual=actual_float,
                    tolerance=tolerance,
                    message=(
                        f"Metric '{key}' changed by {delta:.4f}, outside tolerance ±{tolerance:.4f}."
                    ),
                )
            )

    passed = not any(finding.severity == "error" for finding in findings)
    return SnapshotComparisonReport(
        passed=passed,
        checked_keys=tuple(checked_keys),
        findings=tuple(findings),
    )


def assert_quality_snapshot_within_tolerance(
    expected: Mapping[str, object],
    actual: Mapping[str, object],
    tolerances: Mapping[str, float] | None = None,
    required_keys: Iterable[str] = DEFAULT_REQUIRED_KEYS,
) -> None:
    """Raise AssertionError when a quality snapshot regresses beyond tolerance."""

    report = compare_quality_snapshot(
        expected,
        actual,
        tolerances=tolerances,
        required_keys=required_keys,
    )
    if not report.passed:
        details = "\n".join(finding.message for finding in report.findings)
        raise AssertionError(f"Quality snapshot comparison failed:\n{details}")
