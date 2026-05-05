from tools.pr14_stem_intelligence_adapter import detect_pr14_stem_events
from tools.stem_routing import StemRouter
from xlights.style_xsq_bridge import validate_xsq_effect_rows
from xlights.style_to_rgbeffects_converter import write_xlights_rgbeffects_xml


def stem_routes_to_effect_rows(routes):
    rows = []
    for r in routes:
        rows.append({
            "model": r.target_model,
            "start": r.start,
            "duration": r.duration,
            "effect": r.action,
            "palette": ["white"],
            "intensity": r.intensity,
            "motion": r.target_submodel,
            "intent": r.event_type,
        })
    return rows


def run(wav_path, output_path="helix_stem_output.xml"):
    separated = detect_pr14_stem_events(wav_path)

    router = StemRouter()
    routes = []
    for stem_events in separated.values():
        routes.extend(router.route_events(stem_events))

    rows = stem_routes_to_effect_rows(routes)
    validate_xsq_effect_rows(rows)

    write_xlights_rgbeffects_xml(rows, output_path)

    print(f"Stem-driven pipeline complete → {output_path}")


if __name__ == "__main__":
    run("2.wav")
