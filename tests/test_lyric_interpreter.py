from __future__ import annotations

import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from core import lyric_interpreter


class LyricInterpreterTests(unittest.TestCase):
    def test_interpreter_detects_triggers_and_repeated_phrases(self) -> None:
        lyric_events = [
            SimpleNamespace(start_ms=1000, end_ms=1400, text="Rise up and shine"),
            SimpleNamespace(start_ms=2000, end_ms=2400, text="Rise up and shine"),
            SimpleNamespace(start_ms=3000, end_ms=3400, text="Drop the fire, drop the fire"),
        ]
        payload = lyric_interpreter.interpret_lyric_events(lyric_events, audio_mood_hint="balanced")

        self.assertTrue(payload["enabled"])
        self.assertGreaterEqual(len(payload["trigger_hits"]), 4)
        self.assertIn("motion_up", payload["trigger_counts"])
        self.assertIn("impact", payload["trigger_counts"])
        repeated_phrases = payload["repeated_phrases"]
        self.assertTrue(any(item["phrase"] == "rise up and shine" and item["kind"] == "line" for item in repeated_phrases))
        self.assertTrue(any(item["phrase"] == "drop the fire" for item in repeated_phrases))

    def test_interpreter_uses_lexical_signals_for_mood(self) -> None:
        lyric_events = [
            SimpleNamespace(start_ms=100, end_ms=400, text="love light smile"),
            SimpleNamespace(start_ms=500, end_ms=900, text="jump wild fire"),
        ]
        payload = lyric_interpreter.interpret_lyric_events(lyric_events, audio_mood_hint="brooding")

        self.assertEqual(payload["overall_mood"], "uplifting")
        self.assertGreater(payload["mood_signals"]["positive"], 0)
        self.assertGreater(payload["mood_signals"]["high_energy"], 0)

    def test_interpreter_empty_payload_falls_back_to_audio_mood(self) -> None:
        payload = lyric_interpreter.interpret_lyric_events([], audio_mood_hint="balanced")

        self.assertFalse(payload["enabled"])
        self.assertEqual(payload["overall_mood"], "neutral")
        self.assertEqual(payload["trigger_hits"], [])
        self.assertEqual(payload["repeated_phrases"], [])

    def test_interpreter_supports_configurable_lexicon_file(self) -> None:
        lyric_events = [
            SimpleNamespace(start_ms=1200, end_ms=1500, text="aurora flash"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "lexicon.json")
            payload_data = {
                "trigger_lexicon": {
                    "custom_magic": ["aurora", "flash"],
                }
            }
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(payload_data, fh)
            payload = lyric_interpreter.interpret_lyric_events(
                lyric_events,
                audio_mood_hint="neutral",
                lexicon_path=config_path,
            )

        self.assertIn("custom_magic", payload["trigger_counts"])
        self.assertEqual(payload["trigger_counts"]["custom_magic"], 2)


if __name__ == "__main__":
    unittest.main()
