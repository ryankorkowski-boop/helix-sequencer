from tools.build_helpers.output_quality_report import build_output_quality_report


def test_build_output_quality_report_combines_available_reports():
    report = build_output_quality_report(
        options={
            "quality_preset": "showcase",
            "style_preset": "classic_christmas",
        },
        model_names=["mega_tree", "roofline", "snowman_singer"],
        cues=[
            {
                "start": 0.0,
                "end": 1.0,
                "target_groups": ["roofline"],
                "effect_family": "wash",
                "intensity": 0.4,
            }
        ],
        sections=[
            {
                "name": "chorus_1",
                "kind": "chorus",
                "start": 30.0,
                "end": 50.0,
                "target_intensity": 0.85,
                "primary_groups": ["mega_tree"],
                "palette": "classic_christmas_bright",
                "motion_intent": "spiral",
                "density": "high",
                "colors": ["red", "green", "white"],
            }
        ],
        motifs=[
            {
                "name": "chorus_spiral",
                "section_kind": "chorus",
                "family": "spiral",
                "palette": "classic_christmas_bright",
                "primary_groups": ["mega_tree"],
                "intensity_range": [0.8, 0.95],
            }
        ],
        variants=[
            {
                "variant_id": "variant_01",
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
        ],
        baseline_candidate={
            "variant_id": "variant_01",
            "quality_score": 95.0,
            "audit_score": 89.0,
            "rejected_effects": 9000,
        },
    )

    payload = report.as_dict()

    assert payload["report_only"] is True
    assert payload["quality_preset"] == "showcase"
    assert "prop_roles" in payload["reports"]
    assert "density_restraint" in payload["reports"]
    assert "section_identity" in payload["reports"]
    assert "palette_discipline" in payload["reports"]
    assert "motif_memory" in payload["reports"]
    assert "explainable_variants" in payload["reports"]
    assert payload["summary"]["winner"] == "variant_01"


def test_build_output_quality_report_includes_showcase_reports_when_traces_are_provided():
    report = build_output_quality_report(
        showcase_sections=[
            {"name": "intro", "kind": "intro", "start": 0, "end": 12, "intensity": 0.2, "breadth": 0.2, "motion": 0.2, "darkness": 0.4, "hero_share": 0.25},
            {"name": "verse", "kind": "verse", "start": 12, "end": 40, "intensity": 0.35, "breadth": 0.35, "motion": 0.3, "darkness": 0.2, "hero_share": 0.45},
            {"name": "chorus", "kind": "chorus", "start": 40, "end": 70, "intensity": 0.75, "breadth": 0.75, "motion": 0.7, "darkness": 0.0, "hero_share": 0.65},
            {"name": "finale", "kind": "finale", "start": 70, "end": 105, "intensity": 0.95, "breadth": 0.95, "motion": 0.9, "darkness": 0.0, "hero_share": 0.75},
        ],
        showcase_motions=[
            {"name": "intro_sweep", "motion_family": "sweep", "direction": "left_to_right", "intensity": 0.35, "speed": 0.35, "breadth": 0.5, "transition": "blend", "start": 0.0, "end": 10.0},
            {"name": "verse_chase", "motion_family": "chase", "direction": "left_to_right", "intensity": 0.55, "speed": 0.5, "breadth": 0.65, "transition": "wipe", "start": 10.0, "end": 25.0},
            {"name": "chorus_spiral", "motion_family": "spiral", "direction": "inside_out", "intensity": 0.85, "speed": 0.75, "breadth": 0.85, "transition": "crossfade", "start": 25.0, "end": 45.0},
        ],
    )

    payload = report.as_dict()

    assert payload["report_only"] is True
    assert "showcase_energy" in payload["reports"]
    assert "showcase_hero_dominance" in payload["reports"]
    assert "showcase_motion_continuity" in payload["reports"]
    assert payload["reports"]["showcase_energy"]["showcase_energy_score"] > 0.6
    assert payload["reports"]["showcase_hero_dominance"]["showcase_hero_score"] > 0.6
    assert payload["reports"]["showcase_motion_continuity"]["showcase_motion_score"] > 0.6
    assert payload["summary"]["component_scores"]["showcase_energy"] > 0.6
    assert payload["summary"]["component_scores"]["showcase_hero_dominance"] > 0.6
    assert payload["summary"]["component_scores"]["showcase_motion_continuity"] > 0.6


def test_build_output_quality_report_skips_missing_inputs_with_warnings():
    report = build_output_quality_report()

    payload = report.as_dict()

    assert payload["report_only"] is True
    assert payload["reports"] == {}
    assert payload["warnings"]
    assert any("prop_roles skipped" in warning for warning in payload["warnings"])
    assert any("section_identity skipped" in warning for warning in payload["warnings"])


def test_build_output_quality_report_handles_invalid_manual_lock_sidecar():
    report = build_output_quality_report(
        manual_locks={
            "version": "0.1",
            "sequence_id": "song_01",
            "fps": 40,
            "timebase": "ms",
            "locks": [
                {
                    "id": "bad_lock",
                    "label": "Bad",
                    "scope": "time_range",
                    "anchor": {"type": "time_range", "start_ms": 2000, "end_ms": 1000},
                    "selector": {"groups": ["roofline"]},
                }
            ],
        }
    )

    payload = report.as_dict()

    assert "manual_locks" not in payload["reports"]
    assert any("manual_locks skipped" in warning for warning in payload["warnings"])


def test_build_output_quality_report_includes_manual_lock_summary_when_valid():
    report = build_output_quality_report(
        manual_locks={
            "version": "0.1",
            "sequence_id": "song_01",
            "fps": 40,
            "timebase": "ms",
            "locks": [
                {
                    "id": "lock_01",
                    "label": "Protect finale",
                    "scope": "time_range",
                    "anchor": {"type": "time_range", "start_ms": 1000, "end_ms": 2000},
                    "selector": {"groups": ["whole_house"]},
                }
            ],
        }
    )

    payload = report.as_dict()

    assert "manual_locks" in payload["reports"]
    assert payload["reports"]["manual_locks"]["summary"]["enabled"] == 1
