from __future__ import annotations

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from core import effect_engine
from xlights import xsq_writer


class EffectEngineTests(unittest.TestCase):
    def test_effect_family_groups_known_effects(self) -> None:
        self.assertEqual(effect_engine.effect_family("Ramp"), "ramp")
        self.assertEqual(effect_engine.effect_family("Bars"), "vu")

    def test_variant_output_name_uses_version_suffix(self) -> None:
        output = effect_engine.variant_output_name(Path("demo.wav"), Path("outputs"), effect_engine.ACTIVE_STYLE_VERSION)
        self.assertEqual(output.name, f"demo,{effect_engine.ACTIVE_STYLE_VERSION}.xsq")

    def test_active_style_proxy_matches_lazy_variant_catalog(self) -> None:
        active_variant = effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION]
        self.assertEqual(effect_engine.ACTIVE_STYLE.version, active_variant.version)
        self.assertEqual(effect_engine.ACTIVE_STYLE.title, active_variant.title)

    def test_piano_lights_prefers_vocal_cues_over_percussion(self) -> None:
        event = effect_engine.NoteEvent(
            start_ms=1000,
            end_ms=1180,
            notes=[(72, 0.9), (76, 0.7), (79, 0.6)],
            part="CHORUS",
            section="chorus",
        )
        cue = effect_engine.piano_lights_cue_for_event(
            event,
            kicks=[995],
            snares=[1005],
            hats=[1010],
            bass_peaks=[990],
            vocal_peaks=[1020],
        )
        self.assertEqual(cue, "vocal")

    def test_piano_lights_pool_choice_follows_cue_preferences(self) -> None:
        pools = [
            effect_engine.SequentialPool("arch", "arch", ["a1", "a2", "a3", "a4", "a5", "a6"]),
            effect_engine.SequentialPool("matrix", "matrix", ["m1", "m2", "m3", "m4", "m5", "m6"]),
            effect_engine.SequentialPool("spinner", "spinner", ["s1", "s2", "s3", "s4", "s5", "s6"]),
        ]
        self.assertEqual(effect_engine.choose_piano_lights_pool(pools, "vocal", 0).category, "matrix")
        self.assertEqual(effect_engine.choose_piano_lights_pool(pools, "kick", 0).category, "spinner")

    def test_choose_cue_preferred_pool_uses_signature_context(self) -> None:
        candidates = [
            effect_engine.SequentialPool("impact", "mega", ["g1", "g2", "g3"]),
            effect_engine.SequentialPool("lead", "talking_heads", ["h1", "h2", "h3"]),
            effect_engine.SequentialPool("motion", "line", ["l1", "l2", "l3"]),
        ]
        selected = effect_engine.choose_cue_preferred_pool(candidates, "vocal", 0, context="signature")
        self.assertIsNotNone(selected)
        self.assertEqual(selected.category, "talking_heads")

    def test_reactive_cue_for_event_promotes_dramatic_dense_events_to_build(self) -> None:
        event = effect_engine.NoteEvent(
            start_ms=2500,
            end_ms=2700,
            notes=[(60, 0.8), (64, 0.7), (67, 0.6)],
            part="PRECHORUS",
            section="prechorus",
        )
        cue = effect_engine.reactive_cue_for_event(
            event,
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[],
            default="phrase",
        )
        self.assertEqual(cue, "build")

    def test_cue_duration_scale_varies_by_mode_and_cue(self) -> None:
        build_scale = effect_engine.cue_duration_scale("build", placement_mode="pixel_reactive", part_label="CHORUS")
        hat_scale = effect_engine.cue_duration_scale("hat", placement_mode="pixel_reactive", part_label="CHORUS")
        self.assertGreater(build_scale, hat_scale)

    def test_cue_target_count_boosts_dramatic_builds(self) -> None:
        boosted = effect_engine.cue_target_count(
            1,
            "build",
            placement_mode="showcase_signature",
            part_label="CHORUS",
            maximum=3,
        )
        restrained = effect_engine.cue_target_count(
            2,
            "hat",
            placement_mode="pixel_reactive",
            part_label="VERSE",
            maximum=3,
        )
        self.assertGreaterEqual(boosted, 2)
        self.assertLessEqual(restrained, 2)

    def test_xsq_writer_timing_facade_round_trips_marks(self) -> None:
        root = ET.Element("Sequence")
        xsq_writer.write_timing_track(root, "AUTO Test", [("Intro", 0, 100), ("Verse", 250, 500)], active=False)
        self.assertIsNotNone(xsq_writer.find_root_child(root, "DisplayElements"))
        self.assertIsNotNone(xsq_writer.find_root_child(root, "ElementEffects"))

        marks_root = ET.Element("Sequence")
        layer = xsq_writer.ensure_timing_effect_track(marks_root, "AUTO Marks")
        for start_ms, end_ms in ((0, 100), (250, 500)):
            effect = ET.Element("Effect")
            effect.attrib["startTime"] = str(start_ms)
            effect.attrib["endTime"] = str(end_ms)
            layer.append(effect)
        self.assertEqual(xsq_writer.read_timing_track_marks_ms(marks_root, "AUTO Marks"), [0, 250])


if __name__ == "__main__":
    unittest.main()
