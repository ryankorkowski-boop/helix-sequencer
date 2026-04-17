from __future__ import annotations

import unittest

from core import gui_launcher


class GuiLauncherTests(unittest.TestCase):
    def test_build_sequence_command_includes_advanced_runtime_flags(self) -> None:
        cmd = gui_launcher._build_sequence_command(
            profile="master",
            template_path="template.xsq",
            audio_path="song.wav",
            layout_path="allmodels\\xlights_rgbeffects.xml",
            output_dir="outputs",
            feel="balanced",
            keyboard_mix="1.25",
            flash_guard="0.60",
            spatial_awareness="0.35",
            chase_style="group_to_group",
            layering_mode="smart_layer",
            palette_mode="cool",
            template_guidance=True,
            auto_timing_tracks=True,
            pixel_reactive=True,
            workspace_history=False,
            ac_lights_only=True,
        )

        self.assertIn("--template", cmd)
        self.assertIn("--audio", cmd)
        self.assertIn("--layout-file", cmd)
        self.assertIn("--output-dir", cmd)
        self.assertIn("--keyboard-mix", cmd)
        self.assertIn("--flash-guard", cmd)
        self.assertIn("--spatial-awareness", cmd)
        self.assertIn("--chase-style", cmd)
        self.assertIn("--layering-mode", cmd)
        self.assertIn("--palette-mode", cmd)
        self.assertIn("--template-guidance", cmd)
        self.assertIn("--auto-timing-tracks", cmd)
        self.assertIn("--pixel-reactive", cmd)
        self.assertIn("--no-workspace-history", cmd)
        self.assertIn("--ac-lights-only", cmd)

        self.assertEqual(cmd[cmd.index("--keyboard-mix") + 1], "1.25")
        self.assertEqual(cmd[cmd.index("--chase-style") + 1], "group_to_group")
        self.assertEqual(cmd[cmd.index("--palette-mode") + 1], "cool")

    def test_build_sequence_command_uses_negative_flags_when_disabled(self) -> None:
        cmd = gui_launcher._build_sequence_command(
            profile="master",
            template_path="template.xsq",
            audio_path="song.wav",
            layout_path="",
            output_dir="",
            feel="balanced",
            keyboard_mix="1.00",
            flash_guard="0.80",
            spatial_awareness="0.00",
            chase_style="none",
            layering_mode="replace",
            palette_mode="template",
            template_guidance=False,
            auto_timing_tracks=False,
            pixel_reactive=False,
            workspace_history=True,
            ac_lights_only=False,
        )

        self.assertNotIn("--layout-file", cmd)
        self.assertNotIn("--output-dir", cmd)
        self.assertIn("--no-template-guidance", cmd)
        self.assertIn("--no-auto-timing-tracks", cmd)
        self.assertIn("--no-pixel-reactive", cmd)
        self.assertIn("--workspace-history", cmd)
        self.assertNotIn("--ac-lights-only", cmd)


if __name__ == "__main__":
    unittest.main()
