from __future__ import annotations

import json
import random
from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET

import librosa

import audio_intelligence as ai
import v1 as base
import variant_engine as ve


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "poly_reference"
REFERENCE_XSQ = ROOT / "poly.xsq"
TEMPLATE_XSQ = ROOT / "template.xsq"
LAYOUT_XML = ROOT / "xlights_rgbeffects.xml"
REFERENCE_TRACK = "Polyphonic Transcription"


def _set_media_file(root: ET.Element, audio_path: Path | None) -> None:
    head = root.find("head")
    if head is None:
        head = ET.Element("head")
        root.insert(0, head)
    media_el = head.find("mediaFile")
    if media_el is None:
        media_el = ET.SubElement(head, "mediaFile")
    media_el.text = str(audio_path) if audio_path is not None else ""


def _parse_reference_note_events(reference_xsq: Path) -> list[ve.NoteEvent]:
    root = ET.parse(reference_xsq).getroot()
    events: list[ve.NoteEvent] = []
    for el in root.findall(".//Element"):
        tp = (el.attrib.get("type", "") or el.attrib.get("Type", "")).lower()
        nm = (el.attrib.get("name", "") or el.attrib.get("Name", "")).strip().lower()
        if tp != "timing" or nm != REFERENCE_TRACK.lower():
            continue
        for eff in el.findall(".//Effect"):
            label = (eff.attrib.get("label", "") or "").strip()
            if not label:
                continue
            try:
                midi = int(round(float(librosa.note_to_midi(label))))
            except Exception:
                continue
            st = int(float(eff.attrib.get("startTime", "0") or 0))
            en = int(float(eff.attrib.get("endTime", str(st + 500)) or (st + 500)))
            events.append(
                ve.NoteEvent(
                    start_ms=st,
                    end_ms=max(st + 50, en),
                    notes=[(midi, 1.0)],
                    part="VERSE",
                    section="REFERENCE",
                )
            )
    return sorted(events, key=lambda event: (event.start_ms, event.end_ms))


def _extract_audio_note_events(audio_path: Path, style: ve.VariantStyle) -> list[ve.NoteEvent]:
    audio = base.analyze(audio_path)
    harmonic = ve.analyze_harmonic(audio)
    sections = base.detect_sections(audio)
    parts = ve.infer_song_parts(sections)
    event_times = base.compress_times_ms(audio.onset_ms[:], max(70, base.scaled_gap(72)))
    return ve.extract_polyphonic_events(audio, harmonic, event_times, sections, parts, style)


def _build_routes(layout: base.Layout, names: list[str], rng: random.Random) -> list[ve.KeyboardRoute]:
    coords = ai.parse_layout_coordinates(LAYOUT_XML, names) if LAYOUT_XML.exists() else {}
    pools = ve.discover_sequential_pools(names, layout)
    routes = ve.build_spatial_keyboard_routes(layout, pools, coords, rng)
    keep = {"north_canes", "south_canes", "white_spine", "line_white"}
    filtered: list[ve.KeyboardRoute] = []
    for route in routes:
        if route.name not in keep:
            continue
        if route.name in {"north_canes", "south_canes"}:
            filtered.append(replace(route, stride_normal=1, stride_dramatic=1))
        elif route.name == "white_spine":
            filtered.append(replace(route, stride_normal=2, stride_dramatic=1))
        else:
            filtered.append(replace(route, stride_normal=2, stride_dramatic=1))
    order = {name: idx for idx, name in enumerate(("north_canes", "south_canes", "white_spine", "line_white"))}
    filtered.sort(key=lambda route: order.get(route.name, 99))
    return filtered


def _apply_poly_map(
    *,
    template_xsq: Path,
    output_xsq: Path,
    audio_path: Path | None,
    note_events: list[ve.NoteEvent],
    add_reference_track: bool,
    report_name: str,
) -> dict:
    rng = random.Random(base.SEED + base.stable_name_seed(output_xsq.stem.lower()))
    xsq = base.load_xsq(template_xsq)
    if LAYOUT_XML.exists():
        base.sync_xsq_to_layout(xsq, LAYOUT_XML)
    _set_media_file(xsq.root, audio_path)

    for nm, el in xsq.elements.items():
        base.clear_effects(el, "all", base.AUTO_LAYER_NAME)
        if base.REMOVE_STARTUP_BLIP:
            base.remove_startup_blip(el, base.STARTUP_BLIP_WINDOW_MS)

    layer_names = {
        "main": "AUTO_poly_reference_main",
        "support": "AUTO_poly_reference_support",
        "spatial": "AUTO_poly_reference_spatial",
    }
    layers = {
        layer_key: {nm: base.ensure_layer(el, layer_name) for nm, el in xsq.elements.items()}
        for layer_key, layer_name in layer_names.items()
    }
    occupied: dict[str, dict[str, list[tuple[int, int]]]] = {layer_key: {} for layer_key in layer_names}
    placement_counts = {layer_key: 0 for layer_key in layer_names}

    def place_on_layer(layer_key: str, nm: str, st: int, en: int, eff: str, tpl: base.EffectTemplate) -> bool:
        if nm not in layers[layer_key]:
            return False
        windows = occupied[layer_key].setdefault(nm, [])
        start_ms = int(st)
        end_ms = int(max(start_ms + 1, en))
        if windows and start_ms < windows[-1][1]:
            start_ms = windows[-1][1] + 1
        if end_ms - start_ms < 50:
            return False
        base.add_effect(layers[layer_key][nm], start_ms, end_ms, eff, tpl)
        windows.append((start_ms, end_ms))
        placement_counts[layer_key] += 1
        return True

    def add_model(
        nm: str | None,
        st: int,
        en: int,
        label: str,
        eff: str = "On",
        tpl: base.EffectTemplate | None = None,
        **_kwargs,
    ) -> None:
        if nm is None:
            return
        label_lower = label.lower()
        if "support" in label_lower:
            layer_key = "support"
        elif any(token in label_lower for token in ("white_spine", "line_white")):
            layer_key = "spatial"
        else:
            layer_key = "main"
        template = tpl or (xsq.ramp_tpl if eff.strip().lower() == "ramp" else xsq.on_tpl)
        place_on_layer(layer_key, nm, st, en, eff, template)

    names = sorted(xsq.elements.keys())
    layout = base.discover_layout(names)
    routes = _build_routes(layout, names, rng)
    reference_scale = ve.load_reference_scale_midis(REFERENCE_XSQ if REFERENCE_XSQ.exists() else None)
    keyboard_track: list[tuple[str, int, int]] = []

    ve.place_spatial_keyboard_routes(
        style=ve.VARIANTS["v20.1"],
        note_events=note_events,
        routes=routes,
        reference_scale_midis=reference_scale,
        keyboard_mix=1.15,
        ramp_ok=(xsq.ramp_tpl.settings is not None or xsq.ramp_tpl.palette is not None),
        ramp_tpl=xsq.ramp_tpl,
        add_model=add_model,
        in_blackout=lambda _t: False,
        keyboard_track=keyboard_track,
    )

    if add_reference_track:
        spans = [(ve.note_label(event.notes), event.start_ms, event.end_ms) for event in note_events if event.notes]
        base.write_timing_track(xsq.root, REFERENCE_TRACK, spans, active=False)
    if keyboard_track:
        base.write_timing_track(xsq.root, "AUTO Poly Map", keyboard_track[:2000], active=False)

    try:
        base.indent_xml(xsq.root)
    except Exception:
        pass
    output_xsq.parent.mkdir(parents=True, exist_ok=True)
    xsq.tree.write(output_xsq, encoding="utf-8", xml_declaration=True)

    payload = {
        "name": report_name,
        "template": template_xsq.name,
        "audio": audio_path.name if audio_path is not None else "",
        "output": output_xsq.name,
        "note_events": len(note_events),
        "keyboard_track_spans": len(keyboard_track),
        "placements": placement_counts,
        "routes": [route.name for route in routes],
    }
    report_path = output_xsq.with_name(f"{output_xsq.stem}.report.json")
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base.log("Generating refreshed poly reference sequences")

    reference_events = _parse_reference_note_events(REFERENCE_XSQ)
    if not reference_events:
        raise RuntimeError("No note events found in poly.xsq Polyphonic Transcription track.")

    refreshed_path = OUTPUT_DIR / "poly_refreshed.xsq"
    refreshed_payload = _apply_poly_map(
        template_xsq=REFERENCE_XSQ,
        output_xsq=refreshed_path,
        audio_path=None,
        note_events=reference_events,
        add_reference_track=False,
        report_name="poly_refreshed",
    )
    base.log(f"Saved: {refreshed_path.name} | note_events={refreshed_payload['note_events']}")

    thirteen_audio = ROOT / "13.wav"
    thirteen_events = _extract_audio_note_events(thirteen_audio, ve.VARIANTS["v20.1"])
    poly13_path = OUTPUT_DIR / "13poly.xsq"
    poly13_payload = _apply_poly_map(
        template_xsq=TEMPLATE_XSQ,
        output_xsq=poly13_path,
        audio_path=thirteen_audio,
        note_events=thirteen_events,
        add_reference_track=True,
        report_name="13poly",
    )
    base.log(f"Saved: {poly13_path.name} | note_events={poly13_payload['note_events']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
