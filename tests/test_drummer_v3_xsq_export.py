from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
import soundfile as sf

from tools.export_drummer_v3_xsq import export_drummer_v3_xsq


def test_export_contains_real_v3_submodel_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sr = 22050
        y = np.zeros(sr, dtype=np.float32)
        for start, freq in ((0.20, 90), (0.50, 1800), (0.75, 6500)):
            idx = int(start * sr)
            length = int(0.08 * sr)
            t = np.arange(length) / sr
            y[idx:idx + length] += (np.sin(2 * np.pi * freq * t) * np.exp(-t * 35)).astype(np.float32)
        audio = root / "drums.wav"
        xsq = root / "drummer_v3.xsq"
        sf.write(audio, y, sr)

        payload = export_drummer_v3_xsq(audio, xsq)
        assert payload["event_count"] >= 2

        root_xml = ET.parse(xsq).getroot()
        names = {e.attrib["name"] for e in root_xml.findall("./ElementEffects/Element")}
        assert "HX_SNOWMAN_DRUMMER_V3_HIT_KICK" in names
        assert "HX_SNOWMAN_DRUMMER_V3_HIT_SNARE" in names
        assert "HX_SNOWMAN_DRUMMER_V3_HIT_HIHAT" in names

        effects = root_xml.findall("./ElementEffects/Element/EffectLayer/Effect")
        assert effects
        assert all("HX_SNOWMAN_DRUMMER_V3_" in e.attrib.get("label", "") for e in effects)
