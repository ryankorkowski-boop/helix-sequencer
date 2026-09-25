from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

from audio.musical_event_model import MusicalEvent, MusicalEventMap
from tools.integrate_drummer_v3_into_xsq import inject_drummer_v3


class DrummerV3IntegrationTests(unittest.TestCase):
    def test_integration_targets_real_drummer_model_and_emits_pose_track(self) -> None:
        event_map = MusicalEventMap(
            duration_ms=2000,
            events=[
                MusicalEvent(200, "drum_kick", 0.95, 0.90, "test", instrument="kick"),
                MusicalEvent(500, "drum_snare", 0.88, 0.82, "test", instrument="snare"),
                MusicalEvent(800, "drum_hihat", 0.80, 0.65, "test", instrument="hihat"),
                MusicalEvent(1100, "drum_cymbal", 0.92, 0.88, "test", instrument="cymbal"),
            ],
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = ET.Element("xsequence")
            ET.SubElement(root, "ElementEffects")
            base = Path(tmp) / "base.xsq"
            output = Path(tmp) / "drummer.xsq"
            audio = Path(tmp) / "song.mp3"
            audio.write_bytes(b"placeholder")
            ET.ElementTree(root).write(base, encoding="utf-8", xml_declaration=True)

            with patch("tools.integrate_drummer_v3_into_xsq.build_musical_event_map", return_value=event_map):
                report = inject_drummer_v3(base, output, audio, physical_channels=True)

            self.assertEqual(report["event_count"], 4)
            self.assertTrue(report["contract"]["single_visual_target"])
            self.assertTrue(report["physical_channels_enabled"])

            parsed = ET.parse(output).getroot()
            names = {element.get("name") for element in parsed.findall(".//Element")}
            self.assertIn("HX_SNOWMAN_DRUMMER", names)
            self.assertIn("HX_DRUMMER_CH01_KICK", names)
            self.assertIn("HX_DRUMMER_CH08_BODY_IMPACT", names)

            track = next(t for t in parsed.findall("timingtrack") if t.get("name") == "AUTO_Drummer_V3")
            self.assertEqual(len(track.findall("Effect")), 4)
            self.assertEqual(
                [effect.get("name") for effect in track.findall("Effect")],
                ["kick_hit", "snare_hit", "hi_hat_pulse", "right_crash"],
            )


if __name__ == "__main__":
    unittest.main()
