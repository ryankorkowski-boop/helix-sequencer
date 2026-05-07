from tools.build_helpers.prop_roles import infer_prop_role, summarize_roles


def test_infers_centerpiece_for_mega_tree():
    hint = infer_prop_role("Mega Tree")

    assert hint.role == "centerpiece"
    assert "spirals" in hint.best_for
    assert hint.energy_capacity == "high"
    assert hint.confidence > 0.6


def test_infers_singer_for_snowman_singer():
    hint = infer_prop_role("Snowman Singer Face")

    assert hint.role == "singer"
    assert "vocals" in hint.best_for
    assert hint.confidence > 0.6


def test_infers_percussion_for_drummer():
    hint = infer_prop_role("Snowman Drummer")

    assert hint.role == "percussion"
    assert "drum_hits" in hint.best_for


def test_unknown_models_fall_back_to_fill():
    hint = infer_prop_role("Random Pixel Thing")

    assert hint.role == "fill"
    assert hint.energy_capacity == "low"
    assert hint.confidence < 0.5


def test_summarize_roles_groups_hints_by_role():
    summary = summarize_roles([
        "Mega Tree",
        "Roofline Left",
        "Snowman Singer",
        "Snowman Drummer",
        "Mini Tree 1",
    ])

    assert "centerpiece" in summary
    assert "outline" in summary
    assert "singer" in summary
    assert "percussion" in summary
    assert "accent" in summary
