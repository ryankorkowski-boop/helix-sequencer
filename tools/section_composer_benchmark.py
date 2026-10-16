"""Native, original-audio benchmark of the existing energy_wave placement path.

This isolates that real placement function; it is not a whole-band showcase.
XSQ serialization uses native tables and original fixture geometry conventions.
"""

from __future__ import annotations

import argparse
import json
import shutil
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np

from core import audio_trigger_routes
from core import effect_engine as engine
from core.section_composer import compose_sections
from core.section_placement import SectionPlacementBudget, section_palette
from tools.quality import score_sequence
from tools.quality.native import read_frames
from tools.quality.scoring import _correlation
from tools.native_preview import probe_media
from xlights.xsq_writer import EffectTemplate


def _native_document(names: list[str]) -> tuple[ET.Element, dict[str, Any]]:
    root = ET.Element("xsequence", FixedPointTiming="1")
    head = ET.SubElement(root, "head")
    for tag, value in (("version", "2026.18"), ("sequenceType", "Animation"),
                       ("sequenceTiming", "50 ms"),
                       ("sequenceDuration", "24.000")):
        ET.SubElement(head, tag).text = value
    palettes = ET.SubElement(root, "ColorPalettes")
    database = ET.SubElement(root, "EffectDB")
    display = ET.SubElement(root, "DisplayElements")
    effects = ET.SubElement(root, "ElementEffects")
    layers = {}
    for name in names:
        ET.SubElement(display, "Element", type="model", name=name, visible="1")
        element = ET.SubElement(effects, "Element", type="model", name=name)
        layers[name] = ET.SubElement(element, "EffectLayer")
    return root, {"palettes": palettes, "database": database, "layers": layers}


def prepare_benchmark(output: Path, *, rgb: bool = False) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    sr = 22050
    tones = [(220, .15), (330, .65), (196, .25), (440, .85)]
    audio = np.concatenate([
        np.sin(2 * np.pi * f * np.arange(sr * 6) / sr) * amplitude
        for f, amplitude in tones])
    audio_path = output / "original.wav"
    with wave.open(str(audio_path), "wb") as stream:
        stream.setparams((1, 2, sr, 0, "NONE", "not compressed"))
        stream.writeframes((audio * 32767).astype("<i2").tobytes())
    # Analyze the exact saved samples that native preview will mux.
    with wave.open(str(audio_path), "rb") as reader:
        audio = np.frombuffer(reader.readframes(reader.getnframes()),
                              dtype="<i2").astype(float) / 32768
    plan = compose_sections(audio, sr)
    (output / "section_plan.json").write_text(
        json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n")
    names = [f"Arch_{i:02d}" for i in range(8)]
    layout = ET.Element("xrgb")
    models = ET.SubElement(layout, "models")
    for i, name in enumerate(names):
        ET.SubElement(models, "model", {
            "name": name, "DisplayAs": "Single Line",
            "ChannelCount": "3" if rgb else "1",
            "StringType": "RGB Nodes" if rgb else "Single Color White",
            "StartChannel": str(1 + i * (3 if rgb else 1)),
            "parm1": "1", "parm2": "1", "parm3": "1",
            "LayoutGroup": "Default", "WorldPosX": str(120 + i % 4 * 180),
            "WorldPosY": str(180 + i // 4 * 180), "WorldPosZ": "0",
            "ScaleX": "10", "ScaleY": "10", "ScaleZ": "10",
            "PixelSize": "40"})
    ET.ElementTree(layout).write(
        output / "xlights_rgbeffects.xml", encoding="utf-8",
        xml_declaration=True)
    features = plan.to_dict()
    features["onsets_ms"] = list(range(0, 24000, 500))
    timeline: list[dict[str, object]] = [{"time_ms": t, "energy_smooth": float(
        np.interp(t, [a for a, _ in plan.energy_curve],
                  [v for _, v in plan.energy_curve]))}
        for t in range(0, 24000, 500)]
    routes = tuple(r for r in audio_trigger_routes.DEFAULT_ROUTES
                   if r.effect == "energy_wave")
    actions = audio_trigger_routes.build_audio_reactive_actions(
        timeline, routes=routes)
    summary: dict[str, Any] = {
        "scope": "existing_energy_wave_placement",
        "channels": 24 if rgb else 8,
        "action_count": len(actions), "results": {}}
    for enabled, label in ((False, "baseline"), (True, "composed")):
        folder = output / label
        folder.mkdir()
        root, document = _native_document(names)
        policy = SectionPlacementBudget(plan, {n: [n] for n in names})
        white = "C_BUTTON_Palette1=#ffffff,C_CHECKBOX_Palette1=1"

        def add_model(model: str, start: int, end: int, _label: str,
                      **kwargs: Any) -> None:
            palette = white
            if enabled:
                request = policy.propose(model, start, end, kwargs["eff"])
                if request is None:
                    return
                end = request.end_ms
                palette = section_palette(white, request.section, rgb=rgb)
                policy.commit(request)
            ref = str(len(document["database"]))
            ET.SubElement(document["database"], "Effect").text = (
                "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100")
            ET.SubElement(document["palettes"], "ColorPalette").text = palette
            ET.SubElement(document["layers"][model], "Effect", {
                "name": "On", "ref": ref, "palette": ref,
                "startTime": str(start), "endTime": str(end)})

        engine.place_audio_reactive_actions(
            actions=actions, pools=[engine.SequentialPool("arches", "arch",
                                                          names)],
            pool_state={}, ramp_ok=False,
            ramp_tpl=EffectTemplate(None, None),
            add_model=add_model, in_blackout=lambda _: False,
            reactive_track=[])
        xsq = folder / "benchmark.xsq"
        ET.indent(root)
        ET.ElementTree(root).write(xsq, encoding="utf-8", xml_declaration=True)
        for name in ("original.wav", "xlights_rgbeffects.xml"):
            shutil.copyfile(output / name, folder / name)
        quality = score_sequence(
            xsq, folder / "xlights_rgbeffects.xml", features)
        (folder / "audio_features.json").write_text(
            json.dumps(features, indent=2, sort_keys=True) + "\n")
        (folder / "run_manifest.json").write_text(json.dumps({
            "schema": "helix.run_manifest.v1", "warnings": [],
            "quality": quality, "section_composer": enabled,
        }, indent=2, sort_keys=True) + "\n")
        summary["results"][label] = quality["overall"]["energy_tracking"]
    (output / "comparison.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def verify_native_benchmark(output: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("Native benchmark verification requires ffprobe")
    summary = json.loads((output / "comparison.json").read_text())
    plan = json.loads((output / "section_plan.json").read_text())
    results: dict[str, Any] = {}
    for label in ("baseline", "composed"):
        manifest = json.loads(
            (output / label / "run_manifest.json").read_text())
        preview = manifest["native_preview"]
        assert preview["status"] == "success" and not preview["warnings"]
        assert preview["audio_stream_verified"]
        streams = probe_media(Path(preview["mp4"]), ffprobe)["streams"]
        assert {s["codec_type"] for s in streams} == {"video", "audio"}
        assert all(abs(float(s["duration"]) - 24) < .1 for s in streams)
        assert all(abs(float(s["start_time"])) < .03 for s in streams)
        data, channels, frames, step = read_frames(
            Path(preview["evidence_dir"]) / "benchmark.fseq")
        assert (channels, frames, step) == (summary["channels"], 480, 50)
        values = np.frombuffer(data, dtype=np.uint8).reshape(frames, channels)
        assert values.max() > 0
        energy = np.interp(
            np.arange(frames) * step,
            [p["time_ms"] for p in plan["energy"]],
            [p["value"] for p in plan["energy"]]).tolist()
        lit = (values > 0).mean(axis=1).tolist()
        model_lit = (values.reshape(frames, 8, channels // 8).max(axis=2)
                     > 0).mean(axis=1).tolist()
        results[label] = {
            "channel_correlation": _correlation(energy, lit),
            "model_presence_correlation": _correlation(energy, model_lit),
            "nonzero_samples": int((values > 0).sum()),
            "mp4_sha256": preview["mp4_sha256"],
            "xlights_version": preview["xlights_version"],
        }
    assert (results["composed"]["model_presence_correlation"]
            > results["baseline"]["model_presence_correlation"] + .05)
    if summary["channels"] == 8:
        assert (results["composed"]["channel_correlation"]
                > results["baseline"]["channel_correlation"] + .05)
    (output / "native_comparison.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rgb", action="store_true")
    parser.add_argument("--verify-native", action="store_true")
    args = parser.parse_args()
    result = (verify_native_benchmark(args.output) if args.verify_native
              else prepare_benchmark(args.output, rgb=args.rgb))
    print(json.dumps(result, indent=2))
