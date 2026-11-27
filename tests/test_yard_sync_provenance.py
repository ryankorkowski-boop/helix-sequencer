"""Regression: one common roof clock must not drive the entire yard."""
import xml.etree.ElementTree as ET

import pytest

from tools.yard_sync_provenance import analyze_yard_sync, assert_yard_sync_safe


def _sequence(clocks):
    root = ET.Element("xsequence")
    rows = ET.SubElement(root, "ElementEffects")
    for name, starts in clocks.items():
        row = ET.SubElement(rows, "Element", type="model", name=name)
        layer = ET.SubElement(row, "EffectLayer")
        for start in starts:
            ET.SubElement(layer, "Effect", name="Bars", startTime=str(start),
                          endTime=str(start + 150),
                          sourceMethod="layout_prime_placement")
    return root


def test_rejected_beat_clock_repeated_across_unrelated_yard_props():
    names = ("HOME_ROOF", "WINDOW_1", "ARCH_1", "MEGATREE_1",
             "MATRIX_1", "CANDY_CANE_1", "SNOWFLAKE_1", "SPINNER_1")
    root = _sequence({name: (100, 500, 900, 1300, 1700) for name in names})
    audit = analyze_yard_sync(root)
    assert audit["eligible_models"] == 8
    assert audit["broad_common_clock_count"] == 1
    assert audit["native_fseq_verified"] is False
    with pytest.raises(ValueError, match="Broad repeated yard onset clock"):
        assert_yard_sync_safe(audit)


def test_independently_timed_props_are_not_rejected():
    names = ("HOME_ROOF", "WINDOW_1", "ARCH_1", "MEGATREE_1",
             "MATRIX_1", "CANDY_CANE_1", "SNOWFLAKE_1", "SPINNER_1")
    clocks = {name: tuple(100 + index * 35 + offset
                           for offset in (0, 400, 800, 1200, 1600))
              for index, name in enumerate(names)}
    audit = analyze_yard_sync(_sequence(clocks))
    assert audit["broad_common_clock_count"] == 0
    assert_yard_sync_safe(audit)


def test_symmetric_fixture_pairs_are_allowed_but_not_the_whole_yard():
    root = _sequence({"ARCH_LEFT": (100, 500, 900, 1300),
                      "ARCH_RIGHT": (100, 500, 900, 1300),
                      "TREE_LEFT": (200, 600, 1000, 1400),
                      "TREE_RIGHT": (200, 600, 1000, 1400)})
    audit = analyze_yard_sync(root)
    assert audit["eligible_models"] == 4
    assert_yard_sync_safe(audit)


def test_untagged_and_performer_effects_do_not_create_false_clock():
    root = _sequence({name: (100, 500, 900, 1300) for name in
                      ("HOME_ROOF", "ARCH_1", "TREE_1", "MATRIX_1",
                       "CANE_1", "SPINNER_1")})
    for row in root.findall("./ElementEffects/Element"):
        for effect in row.findall(".//Effect"):
            effect.attrib.pop("sourceMethod")
    assert analyze_yard_sync(root)["eligible_models"] == 0
