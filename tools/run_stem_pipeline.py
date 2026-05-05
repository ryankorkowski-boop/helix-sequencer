from tools.pr14_stem_intelligence_adapter import detect_pr14_stem_events
from tools.stem_routing import StemRouter
from tools.stem_effect_realism import routes_to_realism_effect_rows
from tools.cinematic_sequencing import apply_cinematic_arc
from tools.effect_stabilizer import stabilize_effect_rows
from xlights.style_xsq_bridge import validate_xsq_effect_rows
from xlights.style_to_rgbeffects_converter import write_xlights_rgbeffects_xml


def run(wav_path, output_path="helix_stem_output.xml"):
    separated = detect_pr14_stem_events(wav_path)

    router = StemRouter()
    routes = []
    for stem_events in separated.values():
        routes.extend(router.route_events(stem_events))

    rows = routes_to_realism_effect_rows(routes)

    # Cinematic arc layer (builds song progression)
    rows = apply_cinematic_arc(rows)

    # Stabilization layer (keeps it clean and watchable)
    rows = stabilize_effect_rows(rows)

    validate_xsq_effect_rows(rows)

    write_xlights_rgbeffects_xml(rows, output_path)

    print(f"Stem-driven CINEMATIC pipeline complete → {output_path}")


if __name__ == "__main__":
    run("2.wav")
