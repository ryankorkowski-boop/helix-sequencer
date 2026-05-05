from __future__ import annotations

from types import SimpleNamespace
import unittest

from effects.piano_effect import PianoEffectConfig, build_piano_effect_plan, load_note_events, suitability_score
from music.note_events import NoteEvent
from render.piano_renderer import render_frame


class PianoEffectTests(unittest.TestCase):
    def test_note_range_filtering_from_helix_events(self) -> None:
        events = load_note_events(
            helix_note_events=[SimpleNamespace(start_ms=100, end_ms=300, notes=[(48, 0.5), (60, 0.9), (84, 0.8)])],
            note_range_start=50,
            note_range_end=72,
        )
        self.assertEqual([event.pitch for event in events], [60])

    def test_true_piano_renders_simultaneous_notes(self) -> None:
        events = [
            NoteEvent(0.0, 1.0, 60, 0.4, source="test"),
            NoteEvent(0.0, 1.0, 64, 0.9, source="test"),
        ]
        frame = render_frame(events, 0.5, PianoEffectConfig(note_range_start=60, note_range_end=64, color_mode="classic"))
        active = [key for key in frame["keys"] if key["active"]]  # type: ignore[index]
        self.assertEqual([key["pitch"] for key in active], [60, 64])
        self.assertLess(active[0]["intensity"], active[1]["intensity"])

    def test_decay_sustain_keeps_note_visible_after_end(self) -> None:
        config = PianoEffectConfig(note_range_start=60, note_range_end=60, sustain_render_mode="decay", key_decay_ms=500)
        frame = render_frame([NoteEvent(0.0, 1.0, 60, 1.0)], 1.25, config)
        key = frame["keys"][0]  # type: ignore[index]
        self.assertTrue(key["active"])
        self.assertGreater(key["intensity"], 0.0)
        self.assertLess(key["intensity"], 1.0)

    def test_bars_mode_rendering(self) -> None:
        config = PianoEffectConfig(mode="bars", note_range_start=60, note_range_end=72, orientation="horizontal", color_mode="pitch_class")
        frame = render_frame([NoteEvent(0.0, 2.0, 66, 0.75)], 1.0, config)
        self.assertEqual(frame["mode"], "bars")
        self.assertEqual(len(frame["bars"]), 1)
        self.assertAlmostEqual(frame["bars"][0]["progress"], 0.5)

    def test_build_plan_handles_empty_stream(self) -> None:
        plan = build_piano_effect_plan([], PianoEffectConfig(note_range_start=60, note_range_end=72), frame_times=[0.0])
        self.assertEqual(plan["schema"], "helix.piano_effect.v1")
        self.assertEqual(plan["note_events"], [])
        self.assertTrue(plan["keyboard_geometry"]["keys"])

    def test_suitability_scoring(self) -> None:
        matrix = SimpleNamespace(name="Front Matrix", model_type="matrix")
        tree = SimpleNamespace(name="Mega Tree", model_type="tree")
        self.assertGreater(suitability_score(matrix)["score"], suitability_score(tree)["score"])
        self.assertEqual(suitability_score(SimpleNamespace(name="Custom Piano Keyboard"))["route"], "literal_keyboard")


if __name__ == "__main__":
    unittest.main()
