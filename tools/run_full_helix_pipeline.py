"""Run the full Helix Style Engine pipeline end-to-end.

Now supports real WAV input. If a path is provided, it will generate segments
from audio instead of using the preview demo.
"""

from tools.style_engine_preview import run_preview
from tools.audio_segment_adapter import wav_to_audio_segments
from tools.style_engine import HelixStyleEngine, LayoutProfile
from xlights.style_xsq_bridge import decisions_to_xsq_effect_rows
from xlights.style_to_rgbeffects_converter import write_xlights_rgbeffects_xml


def build_default_layout():
    return LayoutProfile.from_iterable([
        {"name": "MegaTree", "role": "centerpiece"},
        {"name": "Arch_01", "role": "motion"},
        {"name": "HouseOutline", "role": "outline"},
        {"name": "Matrix", "role": "matrix"},
        {"name": "HelixStrand", "role": "centerpiece", "supports_3d": True},
    ])


def run(output_path="helix_output.xml", wav_path: str | None = None):
    if wav_path:
        segments = wav_to_audio_segments(wav_path)
        engine = HelixStyleEngine("SpatialHelix", build_default_layout())
        decisions = [engine.decide(seg) for seg in segments]
    else:
        decisions = run_preview()

    rows = decisions_to_xsq_effect_rows(decisions)
    write_xlights_rgbeffects_xml(rows, output_path)
    print(f"Helix pipeline complete → {output_path}")


if __name__ == "__main__":
    run()
