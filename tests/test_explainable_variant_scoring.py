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


def test_strong_showcase_variant_passes():
    report = score_variant(_strong_variant(), preset="showcase")

    assert report.passed is True
    assert report.score >= 0.78
    assert report.findings == ()


def test_quality_below_preset_is_explained():
    variant = _strong_variant()
    variant["quality_score"] = 90.0

    report = score_variant(variant, preset="showcase")

    assert report.passed is False
    assert any(finding.code == "quality_below_preset" for finding in report.findings)


def test_rejected_effects_above_preset_is_explained():
    variant = _strong_variant()
    variant["rejected_effects"] = 30000

    report = score_variant(variant, preset="showcase")

    assert report.passed is False
    assert any(finding.code == "too_many_rejected_effects" for finding in report.findings)


def test_weak_component_scores_are_explained():
    variant = _strong_variant()
    variant["palette_discipline"] = {"score": 0.4}
    variant["motif_memory"] = {"score": 0.5}

    report = score_variant(variant, preset="showcase")

    assert any(finding.code == "weak_palette_discipline" for finding in report.findings)
    assert any(finding.code == "weak_motif_memory" for finding in report.findings)


def test_vendor_preset_is_stricter_than_showcase():
    variant = _strong_variant()

    showcase = score_variant(variant, preset="showcase")
    vendor = score_variant(variant, preset="vendor")

    assert showcase.passed is True
    assert vendor.passed is False
    assert any(finding.code == "quality_below_preset" for finding in vendor.findings)


def test_rank_variants_prefers_passing_high_score():
    weak = _strong_variant("weak")
    weak["quality_score"] = 89.0
    weak["audit_score"] = 79.0

    strong = _strong_variant("strong")
    middle = _strong_variant("middle")
    middle["palette_discipline"] = {"score": 0.68}
    middle["motif_memory"] = {"score": 0.7}

    shortlist = rank_variants([weak, middle, strong], preset="showcase")

    assert shortlist.winner == "strong"
    assert shortlist.variants[0].variant_id == "strong"
    assert shortlist.variants[-1].variant_id == "weak"


def test_empty_rank_variants_has_no_winner():
    shortlist = rank_variants([], preset="showcase")

    assert shortlist.winner is None
    assert shortlist.variants == ()
