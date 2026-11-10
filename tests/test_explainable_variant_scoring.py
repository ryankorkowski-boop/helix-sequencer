from tools.build_helpers.explainable_variant_scoring import rank_variants, score_variant


def _strong_variant(variant_id="strong"):
    return {
        "variant_id": variant_id,
        "quality_score": 95.0,
        "audit_score": 89.0,
        "rejected_effects": 9000,
        "restraint": {"score": 0.9},
        "section_identity": {"score": 0.88},
        "palette_discipline": {"score": 0.9},
        "motif_memory": {"score": 0.82},
        "prop_roles": {"score": 0.86},
        "manual_lock_respect": {"score": 1.0},
    }


def test_showcase_bias_default_is_noop():
    a = _strong_variant("a")
    b = _strong_variant("b")
    b["palette_discipline"] = {"score": 0.7}

    no_bias = rank_variants([a, b], preset="showcase")
    explicit_zero = rank_variants([a, b], preset="showcase", weights={"showcase_bias": 0.0})

    assert no_bias.winner == explicit_zero.winner
    assert [v.variant_id for v in no_bias.variants] == [v.variant_id for v in explicit_zero.variants]


def test_showcase_bias_can_flip_winner_when_enabled():
    strong = _strong_variant("strong")
    challenger = _strong_variant("challenger")

    challenger["palette_discipline"] = {"score": 0.7}
    strong["showcase_score"] = 0.5
    challenger["showcase_score"] = 0.95

    baseline = rank_variants([strong, challenger], preset="showcase")
    biased = rank_variants(
        [strong, challenger],
        preset="showcase",
        weights={"showcase_bias": 0.4},
    )

    assert baseline.winner == "strong"
    assert biased.winner != baseline.winner


def test_showcase_bias_is_clamped_per_preset_and_reported():
    variant = _strong_variant()
    variant["showcase_score"] = 0.0

    capped = score_variant(variant, preset="showcase", weights={"showcase_bias": 0.4})
    over_cap = score_variant(variant, preset="showcase", weights={"showcase_bias": 0.9})

    assert over_cap.score == capped.score
    assert any(finding.code == "showcase_bias_clamped" for finding in over_cap.findings)
    assert not any(finding.code == "showcase_bias_clamped" for finding in capped.findings)


def test_general_and_vendor_showcase_bias_caps_are_distinct():
    variant = _strong_variant()
    variant["quality_score"] = 97.0
    variant["audit_score"] = 92.0
    variant["showcase_score"] = 0.0

    general_cap = score_variant(variant, preset="general", weights={"showcase_bias": 0.25})
    general_over_cap = score_variant(variant, preset="general", weights={"showcase_bias": 0.9})
    vendor_cap = score_variant(variant, preset="vendor", weights={"showcase_bias": 0.20})
    vendor_over_cap = score_variant(variant, preset="vendor", weights={"showcase_bias": 0.9})

    assert general_over_cap.score == general_cap.score
    assert vendor_over_cap.score == vendor_cap.score
    assert general_cap.score != vendor_cap.score
    assert any(finding.code == "showcase_bias_clamped" for finding in general_over_cap.findings)
    assert any(finding.code == "showcase_bias_clamped" for finding in vendor_over_cap.findings)


def test_negative_showcase_bias_is_treated_as_default_safe_zero():
    variant = _strong_variant()
    variant["showcase_score"] = 0.0

    default_report = score_variant(variant, preset="showcase")
    negative_report = score_variant(variant, preset="showcase", weights={"showcase_bias": -1.0})

    assert negative_report.score == default_report.score
    assert not any(finding.code == "showcase_bias_clamped" for finding in negative_report.findings)
