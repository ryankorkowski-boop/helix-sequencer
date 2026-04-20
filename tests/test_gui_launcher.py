from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core import gui_launcher


class GuiLauncherTests(unittest.TestCase):
    def test_snowman_gallery_path_finds_expected_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            gallery = workspace / "outputs" / "snowman_bands" / "gallery.html"
            gallery.parent.mkdir(parents=True)
            gallery.write_text("<html></html>", encoding="utf-8")

            self.assertEqual(gui_launcher._snowman_gallery_path(workspace), gallery)

    def test_snowman_concept_paths_use_curated_order(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            concepts_dir = workspace / "outputs" / "snowman_bands"
            concepts_dir.mkdir(parents=True)

            for name in ("festival_of_frost.svg", "candy_cabaret.svg", "snowcap_swing.svg", "aurora_echo.svg"):
                (concepts_dir / name).write_text("<svg />", encoding="utf-8")

            ordered = gui_launcher._snowman_concept_paths(workspace)

            self.assertEqual(
                [path.stem for path in ordered],
                ["snowcap_swing", "aurora_echo", "candy_cabaret", "festival_of_frost"],
            )

    def test_describe_layout_choice_recognizes_allmodels_overlay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            layout = Path(temp_dir) / "allmodels" / "xlights_rgbeffects.xml"
            layout.parent.mkdir(parents=True)
            layout.write_text("<xml />", encoding="utf-8")

            message, color = gui_launcher._describe_layout_choice(str(layout))

            self.assertIn("Allmodels overlay ready", message)
            self.assertEqual(color, "#1b6f50")

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
            polish_enabled=True,
            workspace_history=False,
            learn_from_my_xsqs=False,
            variant_count="5",
            auto_shortlist=True,
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
        self.assertIn("--polish", cmd)
        self.assertIn("--no-workspace-history", cmd)
        self.assertIn("--variants", cmd)
        self.assertIn("--auto-shortlist", cmd)
        self.assertIn("--ac-lights-only", cmd)

        self.assertEqual(cmd[cmd.index("--keyboard-mix") + 1], "1.25")
        self.assertEqual(cmd[cmd.index("--chase-style") + 1], "group_to_group")
        self.assertEqual(cmd[cmd.index("--palette-mode") + 1], "cool")
        self.assertEqual(cmd[cmd.index("--variants") + 1], "5")

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
            polish_enabled=False,
            workspace_history=True,
            learn_from_my_xsqs=True,
            variant_count="2",
            auto_shortlist=False,
            ac_lights_only=False,
        )

        self.assertNotIn("--layout-file", cmd)
        self.assertNotIn("--output-dir", cmd)
        self.assertIn("--no-template-guidance", cmd)
        self.assertIn("--no-auto-timing-tracks", cmd)
        self.assertIn("--no-pixel-reactive", cmd)
        self.assertIn("--no-polish", cmd)
        self.assertIn("--workspace-history", cmd)
        self.assertIn("--variants", cmd)
        self.assertIn("--learn-from-my-xsqs", cmd)
        self.assertNotIn("--auto-shortlist", cmd)
        self.assertNotIn("--ac-lights-only", cmd)


if __name__ == "__main__":
    unittest.main()
