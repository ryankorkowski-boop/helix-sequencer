"""Run the full Helix Style Engine pipeline end-to-end.

This is the final executable entrypoint that:
- generates style decisions
- maps them to effects
- converts to xLights RGB XML
"""

from tools.style_engine_preview import run_preview
from xlights.style_xsq_bridge import decisions_to_xsq_effect_rows
from xlights.style_to_rgbeffects_converter import write_xlights_rgbeffects_xml


def run(output_path="helix_output.xml"):
    decisions = run_preview()
    rows = decisions_to_xsq_effect_rows(decisions)
    write_xlights_rgbeffects_xml(rows, output_path)
    print(f"Helix pipeline complete → {output_path}")


if __name__ == "__main__":
    run()
