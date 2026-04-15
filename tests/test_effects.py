from __future__ import annotations

import random
import unittest
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

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


if __name__ == "__main__":
    unittest.main()
