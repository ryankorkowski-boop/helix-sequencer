from tools.showcase.palette_arc import score_palette_arc


def test_smooth_palette_progression_scores_well():
    report = score_palette_arc([
        {"name": "intro", "start": 0, "end": 10, "colors": ["blue"], "palette": "cool_intro", "contrast_level": 0.3},
        {"name": "verse", "start": 10, "end": 30, "colors": ["blue", "green"], "palette": "cool_intro", "contrast_level": 0.5},
        {"name": "chorus", "start": 30, "end": 50, "colors": ["purple", "pink"], "palette": "warm_peak", "contrast_level": 0.9},
    ])

    assert report.section_count == 3
    assert report.warm_cool_flow_score >= 0.4
    assert report.palette_continuity_score >= 0.5
    assert report.showcase_palette_score >= 0.5


def test_abrupt_palette_shift_is_flagged():
    report = score_palette_arc([
        {"name": "cool", "start": 0, "end": 10, "colors": ["blue"], "palette": "cool", "contrast_level": 0.4},
        {"name": "hot", "start": 10, "end": 20, "colors": ["red"], "palette": "hot", "contrast_level": 0.9},
    ])

    assert report.abrupt_palette_shift_penalty > 0
    assert any(f.code == "abrupt_palette_shift" for f in report.findings)


def test_no_sections_returns_zero_score():
    report = score_palette_arc([])

    assert report.section_count == 0
    assert report.showcase_palette_score == 0.0
    assert any(f.code == "no_palette_sections" for f in report.findings)
