from __future__ import annotations

import unittest
from types import SimpleNamespace

from core import audio_intelligence
from core import snowman_band
from core import vocal_timeline
from audio.drum_classification import DrumEvent


class SnowmanBandTests(unittest.TestCase):
    def test_preferred_face_routing_prioritizes_helix_mascot(self) -> None:
        routing = snowman_band.preferred_face_routing(
            [
                "NBH_RIGHT_SINGING_FACE_01_PANEL",
                "NBH_RIGHT_SINGING_FACE_02_PANEL",
                "NBH_RIGHT_HELIXMASCOT_CUSTOM",
                "NBH_LEFT_MATRIX_01",
            ]
        )
        self.assertEqual(routing["preferred_lead"], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertTrue(routing["lead_cycle"])
        self.assertEqual(routing["lead_cycle"][0], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertIn("NBH_LEFT_MATRIX_01", routing["lyric_surfaces"])

    def test_build_snowman_band_plan_creates_performer_cues(self) -> None:
        parsed_layout = SimpleNamespace(
            models={
                "NBH_RIGHT_HELIXMASCOT_CUSTOM": object(),
                "NBH_RIGHT_SINGING_FACE_01_PANEL": object(),
            }
        )
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=1200),
            SimpleNamespace(label="CHORUS", start_ms=1200, end_ms=2600),
        ]
        lyric_events = [SimpleNamespace(start_ms=1300, end_ms=1500, text="hello world")]
        note_events = [
            SimpleNamespace(start_ms=220, end_ms=420, notes=[(43, 0.8), (55, 0.3)]),
            SimpleNamespace(start_ms=1320, end_ms=1560, notes=[(50, 0.5), (67, 0.9)]),
        ]
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=parsed_layout,
            parts=parts,
            lyric_events=lyric_events,
            note_events=note_events,
            beat_ms=[0, 500, 1000, 1500, 2000],
            kicks=[500, 1500],
            snares=[750, 1750],
            hats=[250, 1000, 1800],
            bass_peaks=[260, 1480],
            vocal_peaks=[1360],
            build_lifts=[1180],
            releases=[1600],
            chronoflow_payload={"debug": {"event_count": 12}},
            band_sync_payload={
                "schema": "helix.band_sync.v1",
                "state_frames": [{"start_ms": 0, "end_ms": 2600, "state": "chorus"}],
                "performer_focus": [{"start_ms": 0, "end_ms": 2600, "primary_focus": "singer"}],
                "energy_distributions": [],
            },
            multiband=SimpleNamespace(tempo_bpm=128.0),
            enable_lyrics=True,
        )

        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["face_routing"]["preferred_lead"], "NBH_RIGHT_HELIXMASCOT_CUSTOM")
        self.assertTrue(payload["cues"]["lead_singer"])
        self.assertTrue(payload["cues"]["bassist"])
        self.assertTrue(payload["cues"]["guitarist"])
        self.assertTrue(payload["cues"]["drummer"])
        self.assertIn("kick", payload["kit"]["components"])
        self.assertEqual(payload["debug"]["chronoflow_event_count"], 12)
        self.assertEqual(payload["debug"]["band_sync_frames"], 1)
        self.assertEqual(payload["band_sync"]["schema"], "helix.band_sync.v1")

    def test_build_timing_track_labels_core_performers(self) -> None:
        payload = {
            "cues": {
                "lead_singer": [{"start_ms": 100, "end_ms": 180, "viseme": "AH"}],
                "bassist": [{"start_ms": 200, "end_ms": 320, "string_index": 3}],
                "guitarist": [{"start_ms": 250, "end_ms": 380, "neck_position": 2}],
                "drummer": [{"start_ms": 300, "end_ms": 360, "kind": "snare"}],
                "background_vocals": [{"start_ms": 400, "end_ms": 520, "performer": "guitarist"}],
            }
        }
        track = snowman_band.build_timing_track(payload)
        labels = [label for label, _, _ in track]
        self.assertEqual(labels[:5], ["vox:AH", "bass:s3", "gtr:n2", "drm:snare", "bgv:gtr"])

    def test_word_to_phoneme_and_mouth_shape_mapping(self) -> None:
        phonemes = vocal_timeline.word_to_phonemes("boom")
        self.assertIn("MBP", phonemes)
        self.assertIn("UW", phonemes)
        self.assertEqual(vocal_timeline.phoneme_to_mouth_shape("AH"), "mouth_A")
        self.assertEqual(vocal_timeline.phoneme_to_mouth_shape("P"), "mouth_MBP")

    def test_lyric_timeline_builds_words_and_phoneme_events(self) -> None:
        timeline = vocal_timeline.build_lyric_timeline(
            [SimpleNamespace(start_ms=1000, end_ms=1600, text="bright moon", confidence=0.81)]
        )
        self.assertEqual([word.text for word in timeline.words], ["bright", "moon"])
        self.assertTrue(timeline.phoneme_events)
        self.assertTrue(all(event.mouth_submodel.startswith("mouth_") for event in timeline.phoneme_events))
        self.assertAlmostEqual(float(timeline.confidence_summary["average_confidence"]), 0.81, places=2)

    def test_song_part_detection_fallback_and_part_hits(self) -> None:
        parts = vocal_timeline.build_song_parts(
            [
                SimpleNamespace(label="INTRO", start_ms=0, end_ms=1000, energy=0.2),
                SimpleNamespace(label="CHORUS", start_ms=1000, end_ms=2600, energy=0.9),
            ],
            vocal_peaks_ms=[1200],
            drum_hits_ms=[1000],
        )
        timeline = vocal_timeline.build_lyric_timeline(
            [SimpleNamespace(start_ms=1100, end_ms=1500, text="shine now", confidence=0.7)]
        )
        hits = vocal_timeline.detect_part_hits(parts, timeline, releases_ms=[1800])
        self.assertEqual(parts[0].name, "intro")
        self.assertTrue(any(hit.hit_type == "chorus_start" for hit in hits))
        self.assertTrue(any(hit.hit_type == "lyric_phrase_hit" for hit in hits))
        self.assertTrue(any(hit.hit_type == "energy_swell_peak" for hit in hits))

    def test_missing_lyric_fallback_uses_vocal_energy(self) -> None:
        timeline = vocal_timeline.build_lyric_timeline([], vocal_peaks_ms=[500, 900])
        self.assertEqual(timeline.confidence_summary["source"], "vocal_energy_fallback")
        self.assertEqual(len(timeline.words), 2)
        self.assertEqual(timeline.phoneme_events[0].mouth_shape, "mouth_A")

    def test_demo_timeline_routes_lead_background_and_drummer_reactions(self) -> None:
        parsed_layout = SimpleNamespace(
            models={
                "NBH_RIGHT_HELIXMASCOT_CUSTOM": object(),
                "NBH_RIGHT_SINGING_FACE_01_PANEL": object(),
                "NBH_LEFT_MATRIX_01": object(),
            }
        )
        parts = [
            SimpleNamespace(label="VERSE", start_ms=0, end_ms=2000, energy=0.35),
            SimpleNamespace(label="CHORUS", start_ms=2000, end_ms=4200, energy=0.92),
            SimpleNamespace(label="DROP", start_ms=4200, end_ms=5200, energy=0.98),
        ]
        lyric_events = [
            SimpleNamespace(start_ms=400, end_ms=1100, text="walking through snow", confidence=0.8),
            SimpleNamespace(start_ms=2100, end_ms=2700, text="shine shine", confidence=0.86),
        ]
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=parsed_layout,
            parts=parts,
            lyric_events=lyric_events,
            note_events=[SimpleNamespace(start_ms=2050, end_ms=2450, notes=[(64, 0.8)])],
            beat_ms=[0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500],
            kicks=[2000, 4200],
            snares=[2250, 4450],
            hats=[2100, 2300, 4300],
            bass_peaks=[2200, 2600],
            vocal_peaks=[2360, 2820, 3300],
            build_lifts=[1900],
            releases=[4200],
            chronoflow_payload={"debug": {"event_count": 4}},
            multiband=SimpleNamespace(tempo_bpm=120.0),
            enable_lyrics=True,
        )
        self.assertTrue(payload["global_timeline"]["lyric_words"])
        self.assertTrue(payload["global_timeline"]["phoneme_events"])
        self.assertTrue(payload["global_timeline"]["song_parts"])
        self.assertTrue(payload["global_timeline"]["part_hits"])
        self.assertEqual(payload["timing_intelligence"]["schema"], "helix.snowman_band.timing_intelligence.v1")
        self.assertTrue(payload["timing_intelligence"]["lyric_timing_track"])
        self.assertTrue(payload["timing_intelligence"]["word_timing_track"])
        self.assertTrue(payload["timing_intelligence"]["phoneme_timing_track"])
        self.assertIn("lead_singer", payload["timing_intelligence"]["face_definitions"])
        self.assertTrue(payload["timing_intelligence"]["faces_effect_instructions"])
        self.assertEqual(
            payload["xlights_translation"]["faces_effect_placements"],
            payload["timing_intelligence"]["faces_effect_instructions"],
        )
        self.assertTrue(payload["cues"]["lead_face_activations"])
        bg_performers = {cue["performer"] for cue in payload["cues"]["background_face_activations"]}
        self.assertIn("guitarist", bg_performers)
        self.assertIn("bassist", bg_performers)
        self.assertTrue(any(cue.get("performer") == "drummer" and cue.get("kind") == "cheer_face" for cue in payload["cues"]["part_hit_reactions"]))
        self.assertLessEqual(max(cue["intensity"] for cue in payload["cues"]["background_face_activations"]), 0.46)
        self.assertTrue(payload["debug_timeline"]["vocal_routing_log"])
        self.assertTrue(payload["xlights_translation"]["faces_effect_placements"])
        sequence_instructions = payload["xlights_translation"]["sequence_effect_instructions"]
        self.assertTrue(sequence_instructions)
        self.assertTrue(all(instruction["target_model"] for instruction in sequence_instructions))
        self.assertTrue(any(instruction["effect"] == "Faces" for instruction in sequence_instructions))
        self.assertTrue(any(instruction["timing_track"] == "phoneme" for instruction in sequence_instructions))

    def test_classifier_background_events_drive_background_faces(self) -> None:
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=SimpleNamespace(models={"NBH_RIGHT_HELIXMASCOT_CUSTOM": object()}),
            parts=[
                SimpleNamespace(label="VERSE", start_ms=0, end_ms=1000, energy=0.3),
                SimpleNamespace(label="CHORUS", start_ms=1000, end_ms=3000, energy=0.9),
            ],
            lyric_events=[SimpleNamespace(start_ms=1050, end_ms=1500, text="lead line", confidence=0.8)],
            note_events=[],
            beat_ms=[0, 500, 1000, 1500, 2000, 2500],
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[1100],
            build_lifts=[],
            releases=[],
            chronoflow_payload={},
            multiband=SimpleNamespace(tempo_bpm=100.0),
            enable_lyrics=True,
            background_vocal_events=[
                audio_intelligence.BackgroundVocalEvent(
                    start_ms=1800,
                    end_ms=2200,
                    confidence=0.82,
                    role="group_chant",
                    source_reason="vocal_stem_harmony_classifier",
                    energy=0.8,
                    performer_hint="all_vocalists",
                )
            ],
        )
        routing = payload["vocal_routing"]["background_windows"]
        self.assertEqual(len(routing), 1)
        self.assertEqual(routing[0]["source_reason"], "vocal_stem_harmony_classifier")
        bg_roles = {cue["role"] for cue in payload["cues"]["background_face_activations"]}
        self.assertIn("group_chant", bg_roles)
        self.assertIn("group_chant_reaction", bg_roles)

        sequence_instructions = payload["xlights_translation"]["sequence_effect_instructions"]
        background_instructions = [
            instruction
            for instruction in sequence_instructions
            if instruction["vocal_role"] in {"group_chant", "group_chant_reaction"}
        ]
        self.assertTrue(background_instructions)
        self.assertTrue(all(instruction["target_model"] for instruction in background_instructions))
        self.assertTrue(any(instruction["timing_track"] == "background_phoneme" for instruction in background_instructions))

    def test_sequence_effect_instructions_drive_timing_track(self) -> None:
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=SimpleNamespace(
                models={
                    "NBH_RIGHT_HELIXMASCOT_CUSTOM": object(),
                    "NBH_RIGHT_SINGING_FACE_01_PANEL": object(),
                    "NBH_RIGHT_SINGING_FACE_02_PANEL": object(),
                }
            ),
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=2000, energy=0.9)],
            lyric_events=[SimpleNamespace(start_ms=100, end_ms=700, text="boom bright", confidence=0.9)],
            note_events=[],
            beat_ms=[0, 500, 1000, 1500],
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[120, 320, 520],
            build_lifts=[],
            releases=[],
            chronoflow_payload={},
            multiband=SimpleNamespace(tempo_bpm=120.0),
            enable_lyrics=True,
        )

        sequence_instructions = payload["xlights_translation"]["sequence_effect_instructions"]
        timing_track = snowman_band.build_timing_track(payload)
        self.assertEqual(len(timing_track), len(sequence_instructions))
        self.assertEqual(timing_track[0][0], sequence_instructions[0]["timing_label"])
        self.assertEqual(timing_track[0][1], sequence_instructions[0]["start_ms"])
        self.assertTrue(any(label.startswith("lead_singer:lead_vocal:") for label, _, _ in timing_track))

    def test_structured_drum_events_drive_intelligent_drummer_cues(self) -> None:
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=SimpleNamespace(models={"NBH_RIGHT_HELIXMASCOT_CUSTOM": object()}),
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=2000, energy=0.8)],
            lyric_events=[],
            note_events=[],
            beat_ms=[0, 500, 1000, 1500],
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[],
            vocal_peaks=[],
            build_lifts=[],
            releases=[],
            chronoflow_payload={},
            multiband=SimpleNamespace(tempo_bpm=120.0),
            enable_lyrics=False,
            drum_event_streams={
                "kick_events": [DrumEvent(0.5, 0.9, 0.86, {"low_ratio": 0.8}, 1, "kick")],
                "snare_events": [DrumEvent(1.0, 0.7, 0.78, {"mid_ratio": 0.6}, 2, "snare")],
            },
        )
        self.assertEqual(payload["debug"]["drum_intelligence_mode"], "typed_detection")
        self.assertTrue(any(cue.get("submodel") == "kick" for cue in payload["cues"]["drummer"]))
        self.assertTrue(payload["kit"]["drum_intelligence"]["motion_events"])


if __name__ == "__main__":
    unittest.main()
