from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core import model_parser as xmp
from tools.build_helixia_layout import main


class DebugBandSpecsTests(unittest.TestCase):
    def test_debug_phoneme_models_in_layout(self) -> None:
        """Debug: Print all models and submodels to understand the structure."""
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--output-dir", tmp, "--use-helixville4-band-model-specs"])
            tmp_path = Path(tmp)
            parsed = xmp.parse_layout(tmp_path / "xlights_rgbeffects.xml")
            
            print("\n=== DEBUG: All models in parsed layout ===")
            for model_name in sorted(parsed.models.keys()):
                if "SNOWMAN" in model_name:
                    print(f"  {model_name}")
            
            print("\n=== DEBUG: Models dict for HX_SNOWMAN_SINGER ===")
            singer = parsed.models.get("HX_SNOWMAN_SINGER")
            if singer:
                print(f"  Found: {singer.name}")
                print(f"  Submodels list: {singer.submodels}")
            
            print("\n=== DEBUG: Searching for MOUTH_PHONEME models ===")
            phoneme_models = [m for m in parsed.models.keys() if "MOUTH_PHONEME" in m]
            for pm in phoneme_models:
                print(f"  Found: {pm}")
            
            print("\n=== DEBUG: Check parsed.models dict ===")
            print(f"  Total models: {len(parsed.models)}")
            print(f"  'HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_PHONEME' in parsed.models: {'HX_SNOWMAN_SINGER/HX_SNOWMAN_SINGER_MOUTH_PHONEME' in parsed.models}")
            
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
