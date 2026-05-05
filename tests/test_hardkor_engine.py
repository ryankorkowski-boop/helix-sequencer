from __future__ import annotations

import types
import unittest

from core import effect_engine
from core import hardkor_engine


class HardKorEngineTests(unittest.TestCase):
    def test_parse_args_accepts_hardkor_flags(self) -> None:
        args = effect_engine.parse_args(
            effect_engine.VARIANTS["v27.3"],
            [
                "--hardkor",
                "--hardkor-intensity",
                "1.6",
                "--hardkor-profile",
                "ac256",
            ],
        )
        self.assertTrue(args.hardkor_enabled)
        self.assertAlmostEqual(float(args.hardkor_intensity), 1.6, places=3)
        self.assertEqual(str(args.hardkor_profile), "ac256")

    def test_hardkor_places_only_on_or_ramp_effects(self) -> None:
        names = [
            "Left Tree Red",
            "Left Tree Green",
            "Left Tree White",
            "Left Blvd Red",
            "Left Blvd Green",
            "Left Blvd White",
            "Center Blvd Red",
            "Center Blvd Green",
            "Center Blvd White",
            "Right Blvd Red",
            "Right Blvd Green",
            "Right Blvd White",
            "Right Linden Red",
            "Right Linden Green",
            "Right Linden White",
            "Mega Tree Red 1",
            "Mega Tree Green 1",
            "Mega Tree White 1",
            "Line Tree Red 1",
            "Line Tree Green 1",
            "Line Tree White 1",
            "Line Tree Red 2",
            "Line Tree Green 2",
            "Line Tree White 2",
            "North Candy Cane 1",
            "South Candy Cane 1",
            "Arch 1 Sec 1",
            "Arch 1 Sec 2",
            "Star 1",
            "Star 2",
            "sf2",
            "sf3",
            "Garage Trees Red 1",
            "Garage Trees Green 1",
            "Garage Trees White 1",
        ]

        placed: list[tuple[str, int, int, str, str, str]] = []

        def add_model(
            nm: str | None,
            st: int,
            en: int,
            label: str,
            eff: str = "On",
            tpl=None,
            cd_key: str | None = None,
            cd_ms: int = 0,
            stem: str = "other",
        ) -> None:
            if nm is None:
                return
            placed.append((nm, int(st), int(en), str(label), str(eff), str(stem)))

        parts = [
            types.SimpleNamespace(label="VERSE", start_ms=0, end_ms=4000),
            types.SimpleNamespace(label="PRECHORUS", start_ms=4000, end_ms=6000),
            types.SimpleNamespace(label="CHORUS", start_ms=6000, end_ms=9000),
        ]

        result = hardkor_engine.place_hardkor_sequence(
            names=names,
            parsed_layout=None,
            parts=parts,
            beat_ms=[0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000],
            bar_ms=[0, 2000, 4000, 6000, 8000],
            kicks=[250, 750, 1250, 1750, 2250, 2750, 3250, 3750, 4250, 4750, 5250, 5750, 6250, 6750],
            snares=[500, 1500, 2500, 3500, 4500, 5500, 6500],
            hats=[125, 375, 625, 875, 1125, 1375, 1625, 1875, 2125, 2375, 2625, 2875, 3125, 3375],
            bass_peaks=[240, 740, 1240, 1740, 2240, 2740, 3240, 3740, 4240, 4740, 5240, 5740],
            vocal_peaks=[900, 1900, 2900, 3900, 4900, 5900, 6900],
            build_lifts=[4100, 4600, 5100, 5600],
            releases=[6100, 6600, 7100, 7600],
            add_model=add_model,
            in_blackout=lambda _t: False,
            ramp_ok=True,
            intensity=1.2,
        )

        self.assertTrue(result.enabled)
        self.assertGreater(result.placements, 0)
        self.assertGreater(len(result.timing_spans), 0)
        effect_names = {entry[4] for entry in placed}
        self.assertTrue(effect_names.issubset({"On", "Ramp"}))
        labels = {entry[3] for entry in placed}
        self.assertIn("hardkor_bass_red_backbone", labels)
        self.assertIn("hardkor_arch_wave", labels)
        self.assertIn("hardkor_drop_full", labels)


if __name__ == "__main__":
    unittest.main()
