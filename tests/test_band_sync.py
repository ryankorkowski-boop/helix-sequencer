from __future__ import annotations

from types import SimpleNamespace
import unittest

from audio.drum_classification import DrumEvent
from core import band_sync


class BandSyncTests(unittest.TestCase):
    def test_global_timeline_tracks_sections_density_and_dominance(self) -> None:
        timeline = band_sync.build_global_music_timeline(
            parts=[
                SimpleNamespace(label="VERSE", start_ms=0, end_ms=1000, energy=0.35),
                SimpleNamespace(label="CHORUS", start_ms=1000, end_ms=2200, energy=0.88),
            ],
            beat_ms=[0, 500, 1000, 1500, 2000],
            onset_ms=[100, 300, 500, 1100, 1160, 1220, 1500, 1800],
            vocal_peaks=[1120, 1500],
            bass_peaks=[300, 1300],
            drum_event_streams={"kick_events": [DrumEvent(1.05, 0.8, 0.8, {}, 1, "kick")]},
            note_events=[SimpleNamespace(start_ms=1200, end_ms=1400, notes=[(64, 0.8)])],
        )
        self.assertEqual([segment.section_type for segment in timeline], ["verse", "chorus"])
        self.assertIn(timeline[1].density_level, {"medium", "busy"})
        self.assertIn("vocals", timeline[1].dominant_features)

    def test_state_machine_and_energy_distribution_prioritize_focus(self) -> None:
        segment = band_sync.TimelineSegment(0, 1200, 0.9, "chorus", "busy", ["vocals", "drums"], "phrase_01", "chorus_1")
        focus = band_sync.primary_focus_for_segment(segment)
        distribution = band_sync.distribute_energy(segment, focus)
        frames = band_sync.build_band_state_frames([segment])
        self.assertEqual(focus, "singer")
        self.assertEqual(frames[0].state, "climax")
        self.assertGreater(distribution.allocations["singer"], distribution.allocations["bassist"])
        self.assertLessEqual(sum(1 for value in distribution.allocations.values() if value > 0.55), 2)

    def test_phrase_motifs_reuse_and_intensify_repeated_chorus(self) -> None:
        timeline = [
            band_sync.TimelineSegment(0, 1000, 0.5, "chorus", "medium", ["vocals"], "phrase_01", "chorus_1"),
            band_sync.TimelineSegment(1000, 2000, 0.8, "chorus", "busy", ["vocals"], "phrase_02", "chorus_2"),
        ]
        motifs = band_sync.build_phrase_motifs(timeline)
        self.assertEqual(motifs[0]["variation"], "base")
        self.assertEqual(motifs[1]["variation"], "intensified")

    def test_conflict_resolution_and_spatial_coherence(self) -> None:
        frame = band_sync.BandStateFrame(
            0,
            1000,
            "groove",
            {"singer": 0.5, "drummer": 0.5, "guitarist": 0.48, "bassist": 0.43, "environment": 0.2},
            0.88,
            0.8,
            "locked_rhythm",
            "drummer",
        )
        conflicts = band_sync.resolve_effect_conflicts([frame])
        spatial = band_sync.build_spatial_coherence([frame])
        self.assertTrue(conflicts)
        self.assertEqual(spatial[0]["origin"], "drummer")

    def test_build_band_sync_plan_returns_debug_payload(self) -> None:
        payload = band_sync.build_band_sync_plan(
            parts=[SimpleNamespace(label="DROP", start_ms=0, end_ms=1000, energy=0.95)],
            beat_ms=[0, 500],
            onset_ms=[100, 200, 300],
            vocal_peaks=[],
            bass_peaks=[100],
            drum_event_streams={"kick_events": [DrumEvent(0.1, 0.8, 0.8, {}, 1, "kick")]},
            song_length_ms=1000,
        )
        self.assertEqual(payload["schema"], "helix.band_sync.v1")
        self.assertTrue(payload["timeline"])
        self.assertTrue(payload["debug"]["timeline_state_log"])


if __name__ == "__main__":
    unittest.main()
