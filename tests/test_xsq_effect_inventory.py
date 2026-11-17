from core.xsq_effect_inventory import inventory_xsq_outputs


def test_counts_effect_elements_in_changed_xsq_only(tmp_path):
    xsq = tmp_path / "generated.xsq"
    xsq.write_text(
        '<xsequence><ElementEffects><Element><EffectLayer>'
        '<Effect name="On"/><Effect name="Bars"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>', encoding="utf-8"
    )
    other = tmp_path / "input_template.xml"
    other.write_text('<Effect name="On"/>', encoding="utf-8")
    inventory = inventory_xsq_outputs([xsq, other])
    assert inventory["total_effect_elements"] == 2
    assert len(inventory["outputs"]) == 1
    assert inventory["all_parsed"] is True
    assert inventory["engine_attribution_verified"] is False
    assert inventory["native_fseq_verified"] is False


def test_bad_xml_does_not_claim_effect_count(tmp_path):
    xsq = tmp_path / "broken.xsq"
    xsq.write_text("<xsequence><Effect>", encoding="utf-8")
    inventory = inventory_xsq_outputs([xsq])
    assert inventory["all_parsed"] is False
    assert inventory["outputs"][0]["effect_element_count"] is None


def test_no_changed_xsq_means_no_export_proof():
    inventory = inventory_xsq_outputs([])
    assert inventory["outputs"] == []
    assert inventory["total_effect_elements"] == 0
    assert not inventory["native_fseq_verified"]


def test_tagged_orchestrator_effects_are_counted_without_native_claim(tmp_path):
    xsq = tmp_path / "output.xsq"
    xsq.write_text(
        '<xsequence><ElementEffects><Element><EffectLayer>'
        '<Effect source="HelixOrchestrator" sourceVisualIntentId="intent:1"/>'
        '<Effect source="HelixOrchestrator" sourceVisualIntentId="intent:1"/>'
        '<Effect source="HelixOrchestrator" sourceVisualIntentId="intent:2"/>'
        '<Effect name="Bars"/>'
        '</EffectLayer></Element></ElementEffects></xsequence>', encoding="utf-8",
    )
    inventory = inventory_xsq_outputs([xsq])
    row = inventory["outputs"][0]
    assert row["effect_element_count"] == 4
    assert row["orchestrator_tagged_effects"] == 3
    assert row["distinct_tagged_visual_intents"] == 2
    assert row["other_or_untagged_effects"] == 1
    assert inventory["orchestrator_tag_provenance_observed"] is True
    assert inventory["engine_attribution_verified"] is False
    assert inventory["native_fseq_verified"] is False


def test_invalid_xml_cannot_claim_partial_tagged_counts(tmp_path):
    xsq = tmp_path / "broken.xsq"
    xsq.write_text('<xsequence><Effect source="HelixOrchestrator">', encoding="utf-8")
    row = inventory_xsq_outputs([xsq])["outputs"][0]
    assert row["orchestrator_tagged_effects"] is None
    assert row["distinct_tagged_visual_intents"] is None
