from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core import audit as sequence_audit
from core import effect_engine
from core import model_parser as xmp
from core import polish as sequence_polish
from tools.build_helpers import build_neighbor_graph


def _model(name: str, *, model_type: str, x: float) -> xmp.Model:
    return xmp.Model(
        name=name,
        display_as=model_type,
        type=model_type,
        strings=8,
        nodes_per_string=25,
        total_pixels=200,
        start_channel=None,
        coordinates=(x, 0.0, 0.0),
        end_coordinates=(x + 4.0, 18.0, 0.0),
        orientation="horizontal",
        wiring=None,
        string_type="RGB Nodes",
        color_family="rgb",
    )


def _timeline_entry(layer_name: str, start_ms: int, end_ms: int, priority: int) -> tuple[str, effect_engine.TimelineEntry]:
    layer = ET.Element(layer_name)
    effect = ET.SubElement(layer, "Effect", startTime=str(start_ms), endTime=str(end_ms), name="On")
    return (
        layer_name,
        effect_engine.TimelineEntry(
            start=start_ms,
            end=end_ms,
            effect_name="On",
            priority=priority,
            xml_layer=layer,
            xml_effect=effect,
        ),
    )


class AuditAndPolishTests(unittest.TestCase):
    def test_super_audit_trims_lower_priority_overlap(self) -> None:
        timeline = effect_engine.EffectTimeline()
        base_layer, base_entry = _timeline_entry("base", 0, 600, 1)
        accent_layer, accent_entry = _timeline_entry("accent", 400, 900, 3)
        timeline.add(base_layer, base_entry)
        timeline.add(accent_layer, accent_entry)

        result = sequence_audit.run_super_audit(
            timelines={"Mega 1": timeline},
            parts=[
                effect_engine.SongPart("VERSE", 0, 700, 0.4),
                effect_engine.SongPart("CHORUS", 700, 1200, 0.9),
            ],
            placements={"vocal_hook": 4, "drop_focus": 2},
            min_effect_ms=50,
            auto_fix=True,
        )

        self.assertGreater(result.fixes_applied, 0)
        self.assertLessEqual(base_entry.end, accent_entry.start)
        self.assertLess(result.overlap_ratio, 0.05)

    def test_polish_pass_adds_breathing_and_hook_enhancements(self) -> None:
        timeline = effect_engine.EffectTimeline()
        base_layer, base_entry = _timeline_entry("base", 130, 250, 1)
        motion_layer, motion_entry = _timeline_entry("motion", 180, 340, 2)
        timeline.add(base_layer, base_entry)
        timeline.add(motion_layer, motion_entry)

        layout = xmp.ParsedLayout(
            path=Path("layout.xml"),
            models={
                "Mega 1": _model("Mega 1", model_type="tree", x=0.0),
                "Mega 2": _model("Mega 2", model_type="tree", x=15.0),
                "Mega 3": _model("Mega 3", model_type="tree", x=30.0),
            },
            groups={},
            aliases={},
        )
        graph = build_neighbor_graph(layout, available_names=list(layout.models.keys()))
        placements: list[tuple[str, int, int, str, str, str]] = []

        def add_model(
            model_name: str,
            start_ms: int,
            end_ms: int,
            label: str,
            eff: str = "On",
            tpl=None,
            cd_key=None,
            cd_ms: int = 0,
            stem: str = "other",
        ) -> None:
            placements.append((model_name, start_ms, end_ms, label, eff, stem))

        result = sequence_polish.apply_polish_pass(
            timelines={"Mega 1": timeline},
            parts=[
                effect_engine.SongPart("VERSE", 0, 900, 0.4),
                effect_engine.SongPart("CHORUS", 900, 1800, 0.95),
            ],
            quiet_windows=[(420, 560)],
            add_model=add_model,
            min_effect_ms=50,
            used_root_models={"Mega 1", "Mega 2"},
            neighbor_graph=graph,
            template_palette_pool=["Color1", "Color2"],
            vocal_peaks=[100],
            bass_peaks=[],
            drum_peaks=[],
        )

        self.assertGreater(result.overlap_repairs, 0)
        self.assertGreater(result.breathing_fades, 0)
        self.assertGreater(result.hook_enhancements, 0)
        self.assertGreater(result.retimed_entries, 0)
        self.assertEqual(base_entry.start, 100)
        labels = [entry[3] for entry in placements]
        self.assertIn("polish_breathing_fade", labels)
        self.assertIn("polish_hook_enhancement", labels)

    def test_section_transition_windows_wrap_boundaries(self) -> None:
        windows = sequence_polish.section_transition_windows(
            [
                effect_engine.SongPart("INTRO", 0, 500, 0.2),
                effect_engine.SongPart("VERSE", 500, 1200, 0.5),
                effect_engine.SongPart("CHORUS", 1200, 1800, 0.9),
            ],
            padding_ms=100,
        )
        self.assertEqual(windows, [(400, 600), (1100, 1300)])


if __name__ == "__main__":
    unittest.main()
