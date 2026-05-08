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


# ... existing tests unchanged above ...


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
        weights={"showcase_bias": 0.5},
    )

    assert baseline.winner == "strong"
    assert biased.winner != baseline.winner
