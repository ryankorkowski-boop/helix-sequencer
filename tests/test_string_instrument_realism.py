from __future__ import annotations

from types import SimpleNamespace
import unittest

from animation import string_motion
from audio import instrument_detection
from core import snowman_band


class StringInstrumentRealismTests(unittest.TestCase):
    def test_guitar_detection_derives_strum_sustain_and_chord_change(self) -> None:
        events, debug = instrument_detection.derive_guitar_events(
            [
                SimpleNamespace(start_ms=100, end_ms=260, notes=[(60, 0.7), (64, 0.8), (67, 0.6)]),
                SimpleNamespace(start_ms=500, end_ms=1200, notes=[(69, 0.9)]),
            ]
        )
        types = [event.event_type for event in events]
        self.assertIn("strum", types)
        self.assertIn("sustained_note", types)
        self.assertIn("chord_change", types)
        self.assertEqual(debug["fallback_mode"], "note_events")

    def test_bass_detection_maps_peaks_and_low_sustains(self) -> None:
        events, debug = instrument_detection.derive_bass_events(
            [250],
            [SimpleNamespace(start_ms=200, end_ms=900, notes=[(43, 0.8), (55, 0.4)])],
        )
        self.assertTrue(any(event.event_type == "pluck" for event in events))
        self.assertTrue(any(event.event_type == "sustained_note" for event in events))
        self.assertIn("bass_peaks", debug["fallback_mode"])

    def test_motion_mapping_uses_expected_submodels_and_band_sync_focus(self) -> None:
        guitar_events, _ = instrument_detection.derive_guitar_events(
            [SimpleNamespace(start_ms=100, end_ms=240, notes=[(60, 0.8), (64, 0.8)])]
        )
        bass_events, _ = instrument_detection.derive_bass_events(
            [120],
            [SimpleNamespace(start_ms=100, end_ms=400, notes=[(43, 0.8)])],
        )
        sync = {
            "performer_focus": [{"start_ms": 0, "end_ms": 1000, "primary_focus": "guitarist"}],
            "energy_distributions": [{"start_ms": 0, "end_ms": 1000, "allocations": {"guitarist": 0.8, "bassist": 0.2}}],
        }
        guitar_cues = string_motion.build_guitar_motion_cues(guitar_events, band_sync_payload=sync)
        bass_cues = string_motion.build_bass_motion_cues(bass_events, band_sync_payload=sync)
        self.assertEqual(guitar_cues[0]["submodel"], "strum_zone")
        self.assertEqual(bass_cues[0]["submodel"], "pluck_zone")
        self.assertGreater(guitar_cues[0]["expression"]["brightness"], bass_cues[0]["expression"]["brightness"])

    def test_fallback_logic_never_fails_silently(self) -> None:
        guitar_events, guitar_debug = instrument_detection.derive_guitar_events([], beat_ms=[0, 500, 1000])
        bass_events, bass_debug = instrument_detection.derive_bass_events([], [], beat_ms=[0, 500, 1000])
        self.assertTrue(guitar_events)
        self.assertTrue(bass_events)
        self.assertEqual(guitar_debug["fallback_mode"], "rhythm_energy")
        self.assertEqual(bass_debug["fallback_mode"], "beat")

    def test_snowman_band_payload_exposes_string_realism_debug(self) -> None:
        payload = snowman_band.build_snowman_band_plan(
            parsed_layout=SimpleNamespace(models={"NBH_RIGHT_HELIXMASCOT_CUSTOM": object()}),
            parts=[SimpleNamespace(label="CHORUS", start_ms=0, end_ms=1800, energy=0.85)],
            lyric_events=[],
            note_events=[SimpleNamespace(start_ms=200, end_ms=620, notes=[(43, 0.8), (64, 0.7), (67, 0.7)])],
            beat_ms=[0, 500, 1000, 1500],
            kicks=[],
            snares=[],
            hats=[],
            bass_peaks=[240, 740],
            vocal_peaks=[],
            build_lifts=[],
            releases=[],
            chronoflow_payload={},
            band_sync_payload={
                "schema": "helix.band_sync.v1",
                "performer_focus": [{"start_ms": 0, "end_ms": 1800, "primary_focus": "bassist"}],
                "energy_distributions": [{"start_ms": 0, "end_ms": 1800, "allocations": {"guitarist": 0.2, "bassist": 0.7}}],
            },
            multiband=SimpleNamespace(tempo_bpm=112.0),
            enable_lyrics=False,
        )
        realism = payload["kit"]["string_instrument_realism"]
        self.assertEqual(realism["schema"], "helix.string_instrument_realism.v1")
        self.assertTrue(payload["cues"]["guitarist"])
        self.assertTrue(payload["cues"]["bassist"])
        self.assertTrue(realism["guitar"]["mapping_log"])
        self.assertTrue(realism["bass"]["motion_timeline"])
        self.assertGreater(payload["debug"]["string_realism_events"], 0)


if __name__ == "__main__":
    unittest.main()
