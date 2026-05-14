from __future__ import annotations

import json
import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import numpy as np

from core import effect_engine
from xlights import xsq_writer


class EffectEngineTests(unittest.TestCase):
    def _empty_layout(self) -> xsq_writer.Layout:
        return xsq_writer.Layout(
            house=None,
            garage=None,
            all_white=None,
            all_red=None,
            all_green=None,
            all_notes=None,
            blvd=[],
            blvd_all=None,
            perim=[],
            perim_all=None,
            snowflakes=[],
            stars=[],
            arches={},
            mega_group=None,
            mega_models=[],
            line_all=None,
            line_models=[],
            red_models=[],
            green_models=[],
            white_models=[],
            cane_g_n=None,
            cane_g_s=None,
            notes_main=None,
            notes_mirror=None,
            north_canes=[],
            south_canes=[],
        )

    def _write_layout(
        self,
        root: ET.Element,
    ) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        layout_path = Path(tmpdir.name) / "xlights_rgbeffects.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        return layout_path

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

    def test_choose_player_piano_pool_prefers_notes_group(self) -> None:
        pools = [
            effect_engine.SequentialPool("mega_tree_rgb", "mega", ["m1", "m2", "m3", "m4", "m5", "m6"]),
            effect_engine.SequentialPool("notes_1_16", "notes", ["n1", "n2", "n3", "n4", "n5", "n6"]),
        ]
        selected = effect_engine.choose_player_piano_pool(pools)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.name, "notes_1_16")

    def test_place_player_piano_sequence_maps_notes_to_sequential_pool(self) -> None:
        style = replace(effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION], polyphony=2)
        pools = [
            effect_engine.SequentialPool("notes_1_16", "notes", [f"n{i}" for i in range(1, 9)]),
            effect_engine.SequentialPool("mega_tree_rgb", "mega", [f"m{i}" for i in range(1, 9)]),
        ]
        event = effect_engine.NoteEvent(
            start_ms=1000,
            end_ms=1180,
            notes=[(48, 0.8), (72, 0.7)],
            part="CHORUS",
            section="chorus",
        )
        placements: list[tuple[str, int, int, str, str | None, str]] = []
        keyboard_track: list[tuple[str, int, int]] = []

        def add_model(
            model: str,
            start_ms: int,
            end_ms: int,
            label: str,
            eff: str = "On",
            tpl=None,
            cd_key=None,
            cd_ms: int = 0,
            stem: str = "other",
        ) -> None:
            placements.append((model, start_ms, end_ms, label, eff, stem))

        placed = effect_engine.place_player_piano_sequence(
            style=style,
            note_events=[event],
            pools=pools,
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[],
            keyboard_mix=1.0,
            ramp_ok=False,
            ramp_tpl=xsq_writer.EffectTemplate(settings="", palette=""),
            add_model=add_model,
            in_blackout=lambda _t: False,
            keyboard_track=keyboard_track,
        )

        self.assertEqual(placed, 2)
        self.assertEqual([entry[0] for entry in placements], ["n2", "n5"])
        self.assertTrue(all(entry[3] == "player_piano_notes" for entry in placements))
        self.assertEqual(keyboard_track[0][0], "player_piano:notes_1_16:phrase:C3+C5")

    def test_player_piano_sequence_uses_energy_curve_for_note_density(self) -> None:
        style = replace(effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION], polyphony=2)
        pools = [
            effect_engine.SequentialPool("notes_1_16", "notes", [f"n{i}" for i in range(1, 9)]),
        ]
        event = effect_engine.NoteEvent(
            start_ms=1000,
            end_ms=1180,
            notes=[(48, 0.8), (60, 0.7), (72, 0.7)],
            part="CHORUS",
            section="chorus",
        )

        def run_with_energy(value: float) -> list[tuple[str, int, int, str]]:
            placements: list[tuple[str, int, int, str]] = []

            def add_model(model: str, start_ms: int, end_ms: int, label: str, **_kwargs) -> None:
                placements.append((model, start_ms, end_ms, label))

            effect_engine.place_player_piano_sequence(
                style=style,
                note_events=[event],
                pools=pools,
                kicks=[],
                snares=[],
                hats=[],
                bass_peaks=[],
                vocal_peaks=[],
                keyboard_mix=1.0,
                ramp_ok=False,
                ramp_tpl=xsq_writer.EffectTemplate(settings="", palette=""),
                add_model=add_model,
                in_blackout=lambda _t: False,
                keyboard_track=[],
                energy_curve=SimpleNamespace(sample=lambda _t: value),
            )
            return placements

        low_energy = run_with_energy(0.1)
        high_energy = run_with_energy(0.9)

        self.assertLess(len(low_energy), len(high_energy))
        self.assertGreater(high_energy[-1][2] - high_energy[-1][1], low_energy[0][2] - low_energy[0][1])

    def test_place_player_piano_sequence_uses_helixualizer_support_spread_for_canes(self) -> None:
        style = replace(effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION], polyphony=1)
        pools = [
            effect_engine.SequentialPool("north_canes", "north_canes", [f"c{i}" for i in range(1, 9)]),
        ]
        event = effect_engine.NoteEvent(
            start_ms=1000,
            end_ms=1180,
            notes=[(60, 0.9)],
            part="CHORUS",
            section="chorus",
        )
        placements: list[tuple[str, int, int, str, str | None, str]] = []
        keyboard_track: list[tuple[str, int, int]] = []
        helix_payload = {
            "frame_times_s": [0.0, 0.5, 1.0, 1.5],
            "transport": {"arrival_curve": [0.1, 0.45, 0.9, 0.2]},
            "xlights_projection": {
                "candy_cane_bar_curve": [0.1, 0.35, 0.92, 0.15],
                "piano_lane_groups": {
                    "low": [0.1, 0.2, 0.7, 0.1],
                    "mid": [0.1, 0.3, 0.8, 0.1],
                    "high": [0.1, 0.2, 0.6, 0.1],
                },
            },
        }

        def add_model(
            model: str,
            start_ms: int,
            end_ms: int,
            label: str,
            eff: str = "On",
            tpl=None,
            cd_key=None,
            cd_ms: int = 0,
            stem: str = "other",
        ) -> None:
            placements.append((model, start_ms, end_ms, label, eff, stem))

        placed = effect_engine.place_player_piano_sequence(
            style=style,
            note_events=[event],
            pools=pools,
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[],
            keyboard_mix=1.0,
            ramp_ok=False,
            ramp_tpl=xsq_writer.EffectTemplate(settings="", palette=""),
            add_model=add_model,
            in_blackout=lambda _t: False,
            keyboard_track=keyboard_track,
            helixualizer_payload=helix_payload,
        )

        self.assertEqual(placed, 5)
        self.assertEqual(placements[0][3], "player_piano_north_canes")
        self.assertTrue(any(entry[3] == "player_piano_north_canes_support" for entry in placements))
        self.assertEqual(keyboard_track[0][0], "player_piano:north_canes:phrase:C4")

    def test_discover_sequential_pools_adds_nested_perimeter_group_lane(self) -> None:
        root = ET.Element("xrgb")
        models_el = ET.SubElement(root, "models")
        groups_el = ET.SubElement(root, "modelGroups")

        for idx, name in enumerate(
            (
                "Left Tree White",
                "Left Blvd White",
                "Center Blvd White",
                "Right Blvd White",
                "Right Linden White",
            ),
            start=1,
        ):
            ET.SubElement(
                models_el,
                "model",
                {
                    "name": name,
                    "DisplayAs": "Single Line",
                    "StringType": "Single Color White",
                    "WorldPosX": str(idx * 10),
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "0",
                    "Y2": "10",
                    "Z2": "0",
                    "parm1": "1",
                    "parm2": "1",
                    "parm3": "1",
                    "StartChannel": str(idx),
                },
            )

        group_specs = {
            "LEFT_TREE": ["Left Tree White"],
            "BLVD_LEFT": ["Left Blvd White"],
            "BLVD_CENTER": ["Center Blvd White"],
            "BLVD_RIGHT": ["Right Blvd White"],
            "RIGHT_LINDEN": ["Right Linden White"],
            "13_PERIMETER_ALL": ["LEFT_TREE", "BLVD_LEFT", "BLVD_CENTER", "BLVD_RIGHT", "RIGHT_LINDEN"],
        }
        for group_name, members in group_specs.items():
            ET.SubElement(groups_el, "modelGroup", {"name": group_name, "models": ",".join(members)})

        parsed_layout = effect_engine.xmp.parse_layout(self._write_layout(root))
        names = [
            "Left Tree White",
            "Left Blvd White",
            "Center Blvd White",
            "Right Blvd White",
            "Right Linden White",
            "LEFT_TREE",
            "BLVD_LEFT",
            "BLVD_CENTER",
            "BLVD_RIGHT",
            "RIGHT_LINDEN",
            "13_PERIMETER_ALL",
        ]

        pools = effect_engine.discover_sequential_pools(names, self._empty_layout(), parsed_layout)
        perimeter = next((pool for pool in pools if pool.name == "13_PERIMETER_ALL"), None)
        self.assertIsNotNone(perimeter)
        assert perimeter is not None
        self.assertEqual(perimeter.category, "line")
        self.assertEqual(perimeter.models, ["LEFT_TREE", "BLVD_LEFT", "BLVD_CENTER", "BLVD_RIGHT", "RIGHT_LINDEN"])

    def test_discover_sequential_pools_skips_huge_catchall_groups(self) -> None:
        root = ET.Element("xrgb")
        models_el = ET.SubElement(root, "models")
        groups_el = ET.SubElement(root, "modelGroups")

        member_names: list[str] = []
        for idx in range(1, 27):
            name = f"Line Tree {idx}"
            member_names.append(name)
            ET.SubElement(
                models_el,
                "model",
                {
                    "name": name,
                    "DisplayAs": "Single Line",
                    "StringType": "Single Color White",
                    "WorldPosX": str(idx),
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "0",
                    "Y2": "10",
                    "Z2": "0",
                    "parm1": "1",
                    "parm2": "1",
                    "parm3": "1",
                    "StartChannel": str(idx),
                },
            )
        ET.SubElement(groups_el, "modelGroup", {"name": "01_ALL", "models": ",".join(member_names)})

        parsed_layout = effect_engine.xmp.parse_layout(self._write_layout(root))
        names = member_names + ["01_ALL"]
        pools = effect_engine.discover_sequential_pools(names, self._empty_layout(), parsed_layout)
        self.assertFalse(any(pool.name == "01_ALL" for pool in pools))

    def test_discover_sequential_pools_skips_three_color_stack_groups(self) -> None:
        root = ET.Element("xrgb")
        models_el = ET.SubElement(root, "models")
        groups_el = ET.SubElement(root, "modelGroups")

        for idx, name in enumerate(
            ("Mega Tree Red 1", "Mega Tree Green 1", "Mega Tree White 1"),
            start=1,
        ):
            ET.SubElement(
                models_el,
                "model",
                {
                    "name": name,
                    "DisplayAs": "Single Line",
                    "StringType": "Single Color White",
                    "WorldPosX": str(idx),
                    "WorldPosY": "0",
                    "WorldPosZ": "0",
                    "X2": "0",
                    "Y2": "10",
                    "Z2": "0",
                    "parm1": "1",
                    "parm2": "1",
                    "parm3": "1",
                    "StartChannel": str(idx),
                },
            )
        ET.SubElement(
            groups_el,
            "modelGroup",
            {"name": "mega tree 1", "models": "Mega Tree Red 1,Mega Tree Green 1,Mega Tree White 1"},
        )

        parsed_layout = effect_engine.xmp.parse_layout(self._write_layout(root))
        names = ["Mega Tree Red 1", "Mega Tree Green 1", "Mega Tree White 1", "mega tree 1"]
        pools = effect_engine.discover_sequential_pools(names, self._empty_layout(), parsed_layout)
        self.assertFalse(any(pool.name == "mega tree 1" for pool in pools))

    def test_map_notes_to_models_spreads_pitch_across_group_count(self) -> None:
        style = replace(
            effect_engine.VARIANTS[effect_engine.ACTIVE_STYLE_VERSION],
            pool_mode="rotating",
            call_response=False,
            piano_echo=False,
        )
        pool = effect_engine.SequentialPool(
            "13_PERIMETER_ALL",
            "line",
            ["LEFT_TREE", "BLVD_LEFT", "BLVD_CENTER", "BLVD_RIGHT", "RIGHT_LINDEN"],
        )
        event = effect_engine.NoteEvent(
            start_ms=1000,
            end_ms=1180,
            notes=[(48, 0.9), (66, 0.7), (84, 0.8)],
            part="CHORUS",
            section="chorus",
        )
        mapped = effect_engine.map_notes_to_models(pool, event, {}, style, random.Random(0))
        self.assertEqual(mapped, ["LEFT_TREE", "BLVD_CENTER", "RIGHT_LINDEN"])

    def test_showcase_signature_sweep_plan_reduces_build_sweeps(self) -> None:
        pool = effect_engine.SequentialPool("sig", "mega", ["m1", "m2", "m3", "m4", "m5"])
        tuned_pool, span_scale, hit_scale = effect_engine.showcase_signature_sweep_plan(pool, "build", "CHORUS")
        self.assertIsNotNone(tuned_pool)
        self.assertEqual(len(tuned_pool.models), 2)
        self.assertLess(span_scale, 1.0)
        self.assertLess(hit_scale, 1.0)

    def test_pixel_phrase_prefers_motion_for_chorus_phrase(self) -> None:
        self.assertTrue(effect_engine.pixel_phrase_prefers_motion("CHORUS", "phrase"))
        self.assertFalse(effect_engine.pixel_phrase_prefers_motion("VERSE", "phrase"))
        self.assertFalse(effect_engine.pixel_phrase_prefers_motion("CHORUS", "hat"))

    def test_cue_duration_scale_supports_player_piano_mode(self) -> None:
        build_scale = effect_engine.cue_duration_scale("build", placement_mode="player_piano", part_label="CHORUS")
        hat_scale = effect_engine.cue_duration_scale("hat", placement_mode="player_piano", part_label="CHORUS")
        self.assertGreater(build_scale, hat_scale)

    def test_cinematic_helpers_map_roles_and_expression_palette(self) -> None:
        self.assertEqual(effect_engine.cinematic_layer_role_to_stem("focus"), "vocals")
        self.assertEqual(effect_engine.cinematic_layer_role_to_stem("motion"), "drums")
        self.assertEqual(effect_engine.cinematic_layer_role_to_stem("support"), "bass")

        template = effect_engine.cinematic_palette_template({"palette": ["#ffd166", "#06d6a0", "#ffffff"]})

        self.assertIsNotNone(template)
        self.assertEqual(template.palette, "#ffd166,#06d6a0,#ffffff")
        self.assertEqual(template.settings, "")

    def test_spatial_route_order_style_prefers_directional_styles_only_when_awareness_is_high(self) -> None:
        self.assertEqual(effect_engine.spatial_route_order_style("top_to_bottom", 0.75), "top_to_bottom")
        self.assertEqual(effect_engine.spatial_route_order_style("wave", 0.75), "left_to_right")
        self.assertEqual(effect_engine.spatial_route_order_style("top_to_bottom", 0.10), "left_to_right")

    def test_scaled_spatial_route_stride_reduces_stride_with_awareness(self) -> None:
        self.assertEqual(effect_engine.scaled_spatial_route_stride(4, awareness=0.0, dramatic=False), 4)
        self.assertLess(effect_engine.scaled_spatial_route_stride(4, awareness=1.0, dramatic=False), 4)
        self.assertLessEqual(
            effect_engine.scaled_spatial_route_stride(4, awareness=1.0, dramatic=True),
            effect_engine.scaled_spatial_route_stride(4, awareness=1.0, dramatic=False),
        )

    def test_spatial_ordered_models_respects_path_style(self) -> None:
        models = ["m1", "m2", "m3"]
        coords = {"m1": (2.0, 9.0), "m2": (1.0, 1.0), "m3": (3.0, 4.0)}
        ordered = effect_engine.spatial_ordered_models(models, coords, random.Random(0), path_style="top_to_bottom")
        self.assertEqual(ordered, ["m2", "m3", "m1"])

    def test_hit_class_for_time_detects_clap_when_snare_and_hat_overlap(self) -> None:
        hit = effect_engine.hit_class_for_time(1000, kicks=[1200], snares=[995], hats=[1008])
        self.assertEqual(hit, "clap")

    def test_rhythm_complexity_by_part_scores_busy_section_higher(self) -> None:
        parts = [
            effect_engine.SongPart(label="VERSE", start_ms=0, end_ms=1000, energy=0.4),
            effect_engine.SongPart(label="CHORUS", start_ms=1000, end_ms=2000, energy=0.8),
        ]
        beat_ms = [0, 500, 1000, 1500]
        onset_ms = [50, 1020, 1080, 1140, 1210, 1300, 1380, 1450, 1530, 1610, 1700, 1800, 1900]
        complexity = effect_engine.rhythm_complexity_by_part(parts, onset_ms=onset_ms, beat_ms=beat_ms)
        self.assertLess(complexity["VERSE"], complexity["CHORUS"])

    def test_macro_intensity_state_handles_build_drop_and_quiet(self) -> None:
        times = np.asarray([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
        audio = xsq_writer.Audio(
            sr=44100,
            y=np.zeros(22050, dtype=np.float32),
            dur_s=2.0,
            onset_ms=[],
            beat_ms=[],
            times_s=times,
            centroid=np.zeros_like(times),
            rms01=np.asarray([0.15, 0.35, 0.82, 0.38, 0.08], dtype=float),
            bass01=np.zeros_like(times),
            vocal01=np.zeros_like(times),
            pitch_hz=np.zeros_like(times),
        )
        self.assertEqual(
            effect_engine.macro_intensity_state(
                1000,
                audio=audio,
                build_lifts=[1000],
                releases=[1500],
                quiet_windows=[(1800, 2100)],
            ),
            "build",
        )
        self.assertEqual(
            effect_engine.macro_intensity_state(
                1500,
                audio=audio,
                build_lifts=[],
                releases=[1500],
                quiet_windows=[],
            ),
            "drop",
        )
        self.assertEqual(
            effect_engine.macro_intensity_state(
                1900,
                audio=audio,
                build_lifts=[],
                releases=[],
                quiet_windows=[(1800, 2100)],
            ),
            "quiet",
        )

    def test_dominant_band_at_time_prefers_dominance_marks(self) -> None:
        analysis = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[],
            bass_marks=[],
            mid_marks=[],
            high_marks=[],
            spectral_flux_marks=[],
            loud_marks=[],
            quiet_windows=[],
            dominance_marks={"sub_bass": [], "bass": [1000], "mid": [], "high": []},
        )
        self.assertEqual(effect_engine.dominant_band_at_time(1025, analysis), "bass")

    def test_audio_reactive_beat_timeline_uses_audio_features(self) -> None:
        audio = xsq_writer.Audio(
            sr=44100,
            y=np.zeros(44100, dtype=np.float32),
            dur_s=2.0,
            onset_ms=[0, 500, 1000],
            beat_ms=[0, 500, 1000, 1500],
            times_s=np.asarray([0.0, 0.5, 1.0, 1.5], dtype=float),
            centroid=np.asarray([100.0, 4000.0, 6000.0, 2000.0], dtype=float),
            rms01=np.asarray([0.1, 0.5, 0.9, 0.3], dtype=float),
            bass01=np.asarray([0.2, 0.7, 0.8, 0.1], dtype=float),
            vocal01=np.asarray([0.1, 0.4, 0.3, 0.2], dtype=float),
            pitch_hz=np.zeros(4, dtype=float),
        )

        timeline = effect_engine.build_audio_reactive_beat_timeline(
            audio=audio,
            beat_ms=[0, 500, 1000, 1500],
            onset_ms=[0, 500, 1000],
            bar_ms=[0, 1000],
        )

        self.assertEqual(len(timeline), 4)
        self.assertTrue(timeline[0]["downbeat"])
        self.assertTrue(timeline[2]["downbeat"])
        self.assertGreater(timeline[2]["energy_smooth"], timeline[0]["energy_smooth"])
        self.assertGreater(timeline[1]["low"], timeline[0]["low"])

    def test_place_audio_reactive_actions_maps_catalog_to_pools(self) -> None:
        pools = [
            effect_engine.SequentialPool("Mega", "mega", ["Mega 1", "Mega 2", "Mega 3"]),
            effect_engine.SequentialPool("Stars", "stars", ["Star 1", "Star 2"]),
        ]
        placements: list[tuple[str, int, int, str, str, str]] = []

        def add_model(model, start_ms, end_ms, label, eff="On", tpl=None, cd_key=None, cd_ms=0, stem="other"):
            placements.append((model, start_ms, end_ms, label, eff, stem))

        track: list[tuple[str, int, int]] = []
        placed = effect_engine.place_audio_reactive_actions(
            actions=[
                {"time_ms": 1000, "effect": "bass_pulse", "target_hint": "large_props", "density": 0.5},
                {"time_ms": 1500, "effect": "treble_sparkle", "target_hint": "stars_snowflakes", "density": 0.4},
            ],
            pools=pools,
            pool_state={},
            ramp_ok=True,
            ramp_tpl=xsq_writer.EffectTemplate(settings="ramp", palette=None),
            add_model=add_model,
            in_blackout=lambda _t: False,
            reactive_track=track,
        )

        self.assertGreaterEqual(placed, 2)
        self.assertTrue(any(entry[3] == "audio_reactive_bass_pulse" for entry in placements))
        self.assertTrue(any(entry[0].startswith("Star") for entry in placements))
        self.assertEqual(len(track), 2)

    def test_place_audio_reactive_actions_respects_intensity(self) -> None:
        pools = [effect_engine.SequentialPool("Mega", "mega", ["Mega 1", "Mega 2", "Mega 3", "Mega 4"])]
        actions = [
            {"time_ms": idx * 500, "effect": "bass_pulse", "target_hint": "large_props", "density": 0.5}
            for idx in range(8)
        ]

        def run(intensity: float) -> tuple[int, list[tuple[str, int, int]]]:
            track: list[tuple[str, int, int]] = []
            placements: list[tuple[str, int, int, str]] = []

            def add_model(model, start_ms, end_ms, label, **_kwargs):
                placements.append((model, start_ms, end_ms, label))

            placed = effect_engine.place_audio_reactive_actions(
                actions=actions,
                pools=pools,
                pool_state={},
                ramp_ok=False,
                ramp_tpl=xsq_writer.EffectTemplate(settings="", palette=""),
                add_model=add_model,
                in_blackout=lambda _t: False,
                reactive_track=track,
                max_actions=4,
                intensity=intensity,
            )
            return placed, track

        off_placed, off_track = run(0.0)
        low_placed, low_track = run(0.5)
        high_placed, high_track = run(2.0)

        self.assertEqual(off_placed, 0)
        self.assertEqual(off_track, [])
        self.assertLess(len(low_track), len(high_track))
        self.assertLess(low_placed, high_placed)

    def test_place_audio_reactive_actions_caps_flash_like_fanout(self) -> None:
        pools = [effect_engine.SequentialPool("Mega", "mega", ["Mega 1", "Mega 2", "Mega 3", "Mega 4", "Mega 5"])]
        placements: list[tuple[str, int, int, str]] = []

        def add_model(model, start_ms, end_ms, label, **_kwargs):
            placements.append((model, start_ms, end_ms, label))

        placed = effect_engine.place_audio_reactive_actions(
            actions=[
                {"time_ms": 1000, "effect": "drop_burst", "target_hint": "whole_house", "density": 1.0},
                {"time_ms": 1400, "effect": "energy_wave", "target_hint": "all_models", "density": 1.0},
            ],
            pools=pools,
            pool_state={},
            ramp_ok=True,
            ramp_tpl=xsq_writer.EffectTemplate(settings="ramp", palette=""),
            add_model=add_model,
            in_blackout=lambda _t: False,
            reactive_track=[],
            max_actions=2,
            intensity=2.0,
        )

        drop_count = sum(1 for _model, _start, _end, label in placements if label == "audio_reactive_drop_burst")
        wave_count = sum(1 for _model, _start, _end, label in placements if label == "audio_reactive_energy_wave")
        self.assertEqual(placed, len(placements))
        self.assertLessEqual(drop_count, 2)
        self.assertGreater(wave_count, drop_count)

    def test_audio_reactive_profiles_resolve_to_intensity(self) -> None:
        self.assertEqual(effect_engine.resolve_audio_reactive_tuning(None, None), ("balanced", 1.0))
        self.assertEqual(effect_engine.resolve_audio_reactive_tuning("showcase", None), ("showcase", 1.6))
        self.assertEqual(effect_engine.resolve_audio_reactive_tuning("not-real", None), ("balanced", 1.0))
        self.assertEqual(effect_engine.resolve_audio_reactive_tuning("subtle", 2.8), ("custom", 2.0))

    def test_classify_mir_genre_detects_edm_signature(self) -> None:
        genre = effect_engine.classify_mir_genre(
            {
                "bass_density": 66.0,
                "sub_bass_density": 54.0,
                "high_density": 42.0,
                "flux_density": 72.0,
                "contrast_mean": 0.52,
                "flatness_mean": 0.44,
                "mfcc_motion_mean": 0.46,
                "chroma_stability_mean": 0.41,
                "tonnetz_motion_mean": 0.52,
            },
            tempo_bpm=132.0,
            rms_mean=0.68,
        )
        self.assertEqual(genre, "edm")

    def test_derive_section_mir_profiles_returns_scene_modes(self) -> None:
        times = np.asarray([0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
        audio = xsq_writer.Audio(
            sr=44100,
            y=np.zeros(22050, dtype=np.float32),
            dur_s=2.0,
            onset_ms=[100, 260, 410, 610, 790, 1010, 1120, 1250, 1370, 1490, 1630, 1760],
            beat_ms=[0, 500, 1000, 1500],
            times_s=times,
            centroid=np.zeros_like(times),
            rms01=np.asarray([0.18, 0.22, 0.76, 0.74, 0.70], dtype=float),
            bass01=np.zeros_like(times),
            vocal01=np.zeros_like(times),
            pitch_hz=np.zeros_like(times),
        )
        analysis = effect_engine.MultiBandAnalysis(
            sub_bass_marks=[1050, 1200],
            bass_marks=[1080, 1290],
            mid_marks=[1110, 1320],
            high_marks=[1140, 1350],
            spectral_flux_marks=[1030, 1210, 1380],
            loud_marks=[1100],
            quiet_windows=[],
            dominance_marks={"sub_bass": [], "bass": [1100], "mid": [], "high": []},
            frame_times_s=times,
            spectral_centroid01=np.asarray([0.2, 0.3, 0.6, 0.7, 0.8], dtype=float),
            spectral_contrast01=np.asarray([0.2, 0.2, 0.6, 0.6, 0.7], dtype=float),
            spectral_flatness01=np.asarray([0.1, 0.1, 0.4, 0.5, 0.5], dtype=float),
            spectral_flux01=np.asarray([0.1, 0.2, 0.7, 0.8, 0.6], dtype=float),
        )
        parts = [
            effect_engine.SongPart(label="VERSE", start_ms=0, end_ms=1000, energy=0.35),
            effect_engine.SongPart(label="CHORUS", start_ms=1000, end_ms=2000, energy=0.86),
        ]
        profiles = effect_engine.derive_section_mir_profiles(
            parts=parts,
            audio=audio,
            analysis=analysis,
            onset_ms=audio.onset_ms,
            beat_ms=audio.beat_ms,
            vocal_peaks=[1150, 1400],
        )
        self.assertEqual(profiles["VERSE"]["scene_mode"], "tight_minimal")
        self.assertEqual(profiles["CHORUS"]["scene_mode"], "wide_bright")

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

    def test_validate_report_payload_requires_nonzero_final_audit(self) -> None:
        with self.assertRaises(ValueError):
            effect_engine.validate_report_payload({"audit": {"final": {"score": 0.0}}})
        effect_engine.validate_report_payload({"audit": {"final": {"score": 84.5}}})

    def test_quality_score_rewards_top_show_aggregate_density(self) -> None:
        payload = {
            "version": "v27.3",
            "duration_seconds": 60,
            "effects_total": 5400,
            "placements": {
                "showcase_scene_arrival": 300,
                "showcase_phrase_pickup": 340,
                "showcase_transition": 220,
                "audio_reactive_drop_burst": 80,
                "audio_reactive_downbeat_flash": 34,
                "player_piano_notes": 900,
                "polyphonic_keyboard": 850,
                "spatial_keyboard_arch_flow": 700,
                "treble_sparkle": 420,
                "mid_sweep": 360,
                "energy_wave": 320,
                "bass_pulse": 280,
            },
            "validation": {"rejected_effects_count": 0, "auto_fixes": 0, "issues": []},
            "parsed_layout": {
                "root_model_count": 100,
                "submodel_count": 20,
                "available_family_count": 10,
            },
            "used_targets": {
                "root_models": 84,
                "submodels": 8,
                "family_count": 9,
            },
            "audio_reactive": {
                "action_count": 192,
                "timing_track_events": 180,
            },
            "audit": {"final": {"score": 92.0}},
        }

        quality = effect_engine.compute_quality_score(payload)
        benchmark = quality["top_show_benchmark"]

        self.assertGreaterEqual(benchmark["aggregate_changes_per_second"], 35.0)
        self.assertGreaterEqual(benchmark["component_scores"]["technical_density"], 90.0)
        self.assertGreaterEqual(quality["component_scores"]["top_show_benchmark"], 80.0)

    def test_quality_score_penalizes_unsafe_flash_like_density(self) -> None:
        safe_payload = {
            "version": "v27.3",
            "duration_seconds": 60,
            "effects_total": 4200,
            "placements": {
                "showcase_scene_arrival": 260,
                "showcase_transition": 220,
                "audio_reactive_drop_burst": 40,
                "audio_reactive_downbeat_flash": 28,
                "player_piano_notes": 900,
                "polyphonic_keyboard": 760,
                "spatial_keyboard_arch_flow": 620,
                "treble_sparkle": 360,
                "mid_sweep": 330,
                "energy_wave": 300,
            },
            "validation": {"rejected_effects_count": 0, "auto_fixes": 0, "issues": []},
            "parsed_layout": {"root_model_count": 100, "submodel_count": 20, "available_family_count": 10},
            "used_targets": {"root_models": 80, "submodels": 8, "family_count": 9},
            "audio_reactive": {"action_count": 160, "timing_track_events": 150},
            "audit": {"final": {"score": 92.0}},
        }
        unsafe_payload = json.loads(json.dumps(safe_payload))
        unsafe_payload["placements"]["strobe_flash"] = 420

        safe = effect_engine.compute_quality_score(safe_payload)["top_show_benchmark"]
        unsafe = effect_engine.compute_quality_score(unsafe_payload)["top_show_benchmark"]

        self.assertGreater(safe["component_scores"]["flash_safety"], unsafe["component_scores"]["flash_safety"])
        self.assertLess(unsafe["score"], safe["score"])

    def test_validate_report_payload_blocks_unsafe_power_report(self) -> None:
        payload = {
            "audit": {"final": {"score": 84.5}},
            "power": {
                "enabled": True,
                "safe_after_processing": False,
                "unknown_circuit_events": [{"prop_id": "orphan", "circuit_id": "MISSING"}],
            },
        }

        with self.assertRaisesRegex(ValueError, "missing circuit metadata"):
            effect_engine.validate_report_payload(payload)

    def test_validate_report_payload_allows_disabled_power_report(self) -> None:
        effect_engine.validate_report_payload(
            {
                "audit": {"final": {"score": 84.5}},
                "power": {"enabled": False, "safe_after_processing": False},
            }
        )

    def test_load_power_metadata_payload_reports_unknown_circuit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "power.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "helix.power.metadata.v1",
                        "circuits": [{"circuit_id": "A", "breaker_limit_amps": 15}],
                        "props": [
                            {
                                "prop_id": "roof",
                                "pixels": 100,
                                "voltage": 12,
                                "watts_per_pixel_full_white": 0.3,
                                "circuit_id": "MISSING",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = effect_engine.load_power_metadata_payload(path)

        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["analysis_status"], "metadata_only")
        self.assertFalse(payload["safe_after_processing"])
        self.assertEqual(payload["unknown_circuit_events"][0]["prop_id"], "roof")

    def test_validate_report_payload_allows_non_enforced_power_metadata(self) -> None:
        effect_engine.validate_report_payload(
            {
                "audit": {"final": {"score": 84.5}},
                "power": {
                    "enabled": True,
                    "enforce": False,
                    "safe_after_processing": False,
                    "unknown_circuit_events": [{"prop_id": "roof"}],
                },
            }
        )


if __name__ == "__main__":
    unittest.main()
