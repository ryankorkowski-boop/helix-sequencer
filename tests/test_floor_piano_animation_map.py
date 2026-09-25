from __future__ import annotations

import unittest

from core.floor_piano_animation_map import (
    plan_bass_note,
    plan_chord_bloom,
    plan_drop_impact,
    plan_idle_shimmer,
    plan_melody_run,
    plan_note_hit,
)


class FloorPianoAnimationMapTests(unittest.TestCase):
    def test_note_hit_targets_single_key_and_sustain(self) -> None:
        plan = plan_note_hit("C", "LOW", velocity=0.75)
        members = tuple(member for event in plan.events for member in event.members)
        self.assertEqual(plan.trigger, "note_hit")
        self.assertIn("HX_FLOOR_PIANO_C_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_SUSTAIN_GLOW", members)

    def test_chord_bloom_targets_chord_notes_and_bloom_lane(self) -> None:
        plan = plan_chord_bloom("C", "major")
        members = tuple(member for event in plan.events for member in event.members)
        self.assertIn("HX_FLOOR_PIANO_C_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_E_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_G_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_CHORD_BLOOM", members)

    def test_melody_run_uses_motion_layer(self) -> None:
        plan = plan_melody_run(0, 4)
        self.assertEqual(plan.trigger, "melody_run")
        self.assertEqual(plan.events[0].layer, "motion")
        self.assertEqual(plan.events[0].members[0], "HX_FLOOR_PIANO_C_LOW")
        self.assertEqual(plan.events[0].members[-1], "HX_FLOOR_PIANO_E_LOW")

    def test_bass_note_emphasizes_low_octave(self) -> None:
        plan = plan_bass_note("E")
        members = tuple(member for event in plan.events for member in event.members)
        self.assertIn("HX_FLOOR_PIANO_E_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_OCTAVE_LOW", members)
        self.assertIn("HX_FLOOR_PIANO_VELOCITY_LANE", members)

    def test_drop_impact_targets_whole_keyboard(self) -> None:
        plan = plan_drop_impact()
        members = tuple(member for event in plan.events for member in event.members)
        self.assertIn("HX_FLOOR_PIANO_WHITE_KEYS", members)
        self.assertIn("HX_FLOOR_PIANO_BLACK_KEYS", members)
        self.assertIn("HX_FLOOR_PIANO_PLATFORM", members)

    def test_idle_shimmer_is_base_layer(self) -> None:
        plan = plan_idle_shimmer()
        self.assertEqual(plan.trigger, "idle")
        self.assertEqual(plan.events[0].layer, "base")


if __name__ == "__main__":
    unittest.main()


def test_plan_normalized_melody_run_maps_midi_range():
    from audio.musical_event_model import MusicalEvent
    from core.floor_piano_animation_map import plan_normalized_melody_run

    event = MusicalEvent(
        time_ms=1000,
        kind="melody_run",
        confidence=0.9,
        strength=0.8,
        instrument="keyboard",
        duration_ms=400,
        pitch_midi=60,
        metadata={"direction": "ascending", "pitches_midi": [36, 38, 40, 43]},
    )
    plan = plan_normalized_melody_run(event)
    assert plan.trigger == "melody_run"
    assert plan.events
    assert plan.events[0].members[0] == "HX_FLOOR_PIANO_C_LOW"
    assert plan.events[0].members[-1] == "HX_FLOOR_PIANO_G_LOW"


def test_normalized_melody_run_preserves_full_contour_and_descending_lane():
    from audio.musical_event_model import MusicalEvent
    from core.floor_piano_animation_map import plan_normalized_melody_run

    event = MusicalEvent(
        time_ms=1000,
        kind="melody_run",
        confidence=0.9,
        strength=0.8,
        instrument="keyboard",
        duration_ms=500,
        pitch_midi=67,
        metadata={"direction": "descending", "pitches_midi": [67, 65, 64, 60]},
    )
    plan = plan_normalized_melody_run(event)
    assert plan.events[0].members == (
        "HX_FLOOR_PIANO_G_4",
        "HX_FLOOR_PIANO_F_4",
        "HX_FLOOR_PIANO_E_4",
        "HX_FLOOR_PIANO_C_4",
    )
    assert plan.events[1].members == ("HX_FLOOR_PIANO_RIGHT_TO_LEFT_CHASE",)
