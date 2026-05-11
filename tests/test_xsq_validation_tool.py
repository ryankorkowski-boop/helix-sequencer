from __future__ import annotations

from pathlib import Path

import pytest

from tools.validate_xsq_structure import ValidationError, validate_xsq


FIXTURE_DIR = Path("fixtures/xsq_validation")



def test_valid_fixture_passes():
    validate_xsq(FIXTURE_DIR / "valid_helix_vocal.xsq")



def test_duplicate_indexes_fail(tmp_path: Path):
    path = tmp_path / "dup.xsq"

    path.write_text(
        """
<xsequence>
  <timingtrack>
    <phoneme index=\"0\" start=\"0.0\" duration=\"1.0\" />
    <phoneme index=\"0\" start=\"1.0\" duration=\"1.0\" />
  </timingtrack>
  <effects />
</xsequence>
""".strip()
    )

    with pytest.raises(ValidationError):
        validate_xsq(path)



def test_negative_start_fails(tmp_path: Path):
    path = tmp_path / "negative.xsq"

    path.write_text(
        """
<xsequence>
  <timingtrack>
    <phoneme index=\"0\" start=\"-1.0\" duration=\"1.0\" />
  </timingtrack>
  <effects />
</xsequence>
""".strip()
    )

    with pytest.raises(ValidationError):
        validate_xsq(path)



def test_non_positive_duration_fails(tmp_path: Path):
    path = tmp_path / "duration.xsq"

    path.write_text(
        """
<xsequence>
  <timingtrack>
    <phoneme index=\"0\" start=\"0.0\" duration=\"0.0\" />
  </timingtrack>
  <effects />
</xsequence>
""".strip()
    )

    with pytest.raises(ValidationError):
        validate_xsq(path)



def test_unordered_timings_fail(tmp_path: Path):
    path = tmp_path / "unordered.xsq"

    path.write_text(
        """
<xsequence>
  <timingtrack>
    <phoneme index=\"0\" start=\"1.0\" duration=\"1.0\" />
    <phoneme index=\"1\" start=\"0.0\" duration=\"1.0\" />
  </timingtrack>
  <effects />
</xsequence>
""".strip()
    )

    with pytest.raises(ValidationError):
        validate_xsq(path)
