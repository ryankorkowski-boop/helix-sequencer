"""Consolidate corrected song exports into seven independent portable shows."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PATH_SETTING = re.compile(r"(?:^|,)([^,=]*(?:FILEPICKER|Filename)[^,=]*)=([^,]*)", re.IGNORECASE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_local(folder: Path, value: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"Machine-specific reference: {value}")
    result = (folder / path).resolve()
    if not result.is_relative_to(folder.resolve()) or not result.is_file():
        raise ValueError(f"Missing or external reference in {folder.name}: {value}")
    return result


def model_nodes(path: Path) -> bytes:
    return ET.tostring(ET.parse(path).getroot().find("models"))


def validate_sequence(folder: Path, xsq: Path, *, duration: float | None = None,
                      audio_hash: str | None = None) -> dict:
    layout = ET.parse(folder / "xlights_rgbeffects.xml").getroot()
    models = {m.get("name"): {s.get("name") for s in m.findall("subModel")}
              for m in layout.findall("models/model")}
    groups = {g.get("name"): g.get("models", "").split(",")
              for g in layout.findall("modelGroups/modelGroup")}
    def target(name: str, seen: frozenset = frozenset()) -> bool:
        if name in seen:
            return False
        if name in groups:
            return all(target(m, seen | {name}) for m in groups[name])
        parent, sep, sub = name.partition("/")
        return parent in models and (not sep or sub in models[parent])
    for group in groups:
        if not target(group):
            raise ValueError(f"Unresolved layout group: {group}")
    for node in layout.iter():
        for key, value in node.attrib.items():
            if key in ("Image", "ObjFile") and value:
                resolve_local(folder, value)
    root = ET.parse(xsq).getroot()
    head = root.find("head")
    seconds = float(head.findtext("sequenceDuration"))
    media = head.findtext("mediaFile", "")
    if duration is not None:
        if head.findtext("sequenceType") != "Media":
            raise ValueError("Full-song sequence is not Media type")
        expected = math.ceil(duration * 1000 / 50) * .05
        if abs(seconds - expected) > .001:
            raise ValueError(f"Incomplete sequence duration: {seconds} vs {expected}")
        if sha256(resolve_local(folder, media)) != audio_hash:
            raise ValueError("Packaged soundtrack differs from preserved source")
    elif media:
        resolve_local(folder, media)
    catalog = set(json.loads((ROOT / "xlights/effect_catalog.json").read_text())["effect_names"])
    settings = root.findall("EffectDB/Effect")
    palettes = root.findall("ColorPalettes/ColorPalette")
    scheduled = []
    for element in root.findall("ElementEffects/Element"):
        if element.get("type") == "timing":
            continue
        name = element.get("name", "")
        if not target(name):
            raise ValueError(f"Sequence has unresolved target: {name}")
        for layer in element:
            if layer.tag == "SubModelEffectLayer" and not target(name + "/" + layer.get("name", "")):
                raise ValueError(f"Sequence has unresolved submodel: {name}/{layer.get('name')}")
            for effect in layer.findall("Effect"):
                scheduled.append(effect)
                if effect.get("name") not in catalog:
                    raise ValueError(f"Non-native effect: {effect.get('name')}")
                start, end = int(effect.get("startTime")), int(effect.get("endTime"))
                if not 0 <= start < end <= round(seconds * 1000):
                    raise ValueError("Effect outside sequence duration")
                if "ref" in effect.attrib and not 0 <= int(effect.get("ref")) < len(settings):
                    raise ValueError("Invalid effect settings reference")
                if "palette" in effect.attrib and not 0 <= int(effect.get("palette")) < len(palettes):
                    raise ValueError("Invalid native palette reference")
    if not scheduled:
        raise ValueError("Sequence has no scheduled effects")
    for setting in settings:
        for _, value in PATH_SETTING.findall(setting.text or ""):
            if value:
                resolve_local(folder, value)
    return {"file": xsq.name, "kind": "full_song" if duration is not None else "lighting_study",
            "duration_seconds": seconds, "media": media, "scheduled_effects": len(scheduled),
            "latest_effect_end_ms": max(int(e.get("endTime")) for e in scheduled),
            "xsq_sha256": sha256(xsq), "references_resolve": True, "native_effect_names": True}


def prepare(batch: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"Choose a new delivery directory; refusing to overwrite {output}")
    manifest = json.loads((batch / "batch_manifest.json").read_text())
    output.mkdir(parents=True)
    sources = [ROOT / "showcase/Helix_Aurora"] + sorted((ROOT / "showcase/flavors").glob("Helix_*"))
    report = {"schema": "helix.portable_xlights_shows.v1", "baseline_commit": "b56f2cf4a39401e201b729e253c8037509bb8c3f",
              "default_show": "Helix_Fire_and_Ice", "default_sequence": "Wire_Tree__Helix_Fire_and_Ice.xsq",
              "shows": [], "laptop_launch": "blocked: current executor is cloud Linux, not the laptop"}
    for source in sources:
        folder = output / source.name
        shutil.copytree(source, folder)
        baseline_proof = folder / "native_verification.json"
        if baseline_proof.is_file():
            baseline_proof.rename(folder / "baseline_native_verification.json")
        (folder / "media").mkdir(exist_ok=True)
        rows = [r for r in manifest["runs"] if Path(r["folder"]).name == source.name]
        if source.name != "Helix_Aurora" and len(rows) != 5:
            raise ValueError(f"Expected all five complete songs for {source.name}")
        proofs = []
        if rows:
            layout = batch / rows[0]["folder"] / "xlights_rgbeffects.xml"
            if model_nodes(layout) != model_nodes(source / "xlights_rgbeffects.xml"):
                raise ValueError("Generated show changed preserved physical model nodes")
            shutil.copy2(layout, folder / layout.name)
            for row in rows:
                original = batch / row["folder"]
                if (original / "xlights_rgbeffects.xml").read_bytes() != layout.read_bytes():
                    raise ValueError("Songs for one layout have incompatible layout definitions")
                media = folder / "media" / row["audio"]
                shutil.copy2(original / row["audio"], media)
                xsq = folder / row["xsq"]
                tree = ET.parse(original / row["xsq"])
                tree.getroot().find("head/mediaFile").text = "media/" + media.name
                tree.write(xsq, encoding="utf-8", xml_declaration=True)
                proof = validate_sequence(folder, xsq, duration=row["duration_seconds"], audio_hash=row["audio_sha256"])
                # Only mediaFile changes; cue/settings/palette trees must survive intact.
                before = ET.parse(original / row["xsq"]).getroot()
                before.find("head/mediaFile").text = "media/" + media.name
                if ET.tostring(before) != ET.tostring(ET.parse(xsq).getroot()):
                    raise ValueError("Portability repair changed sequence content")
                proof.update({"track": row["title"], "audio_sha256": row["audio_sha256"],
                              "source_xsq_sha256": sha256(original / row["xsq"]), "cue_content_preserved": True})
                proofs.append(proof)
        demo = folder / (source.name + "_Showcase.xsq")
        if demo.is_file():
            proofs.append(validate_sequence(folder, demo))
        network = ET.parse(folder / "xlights_networks.xml").getroot()
        if list(network):
            raise ValueError("Prepared show contains configured output networks")
        (folder / "README_PORTABLE.txt").write_text(
            f"{source.name}\n\nSelect this folder as the xLights show directory.\n"
            "Full-song sequences are Media XSQs; audio lives in media/.\n"
            "The *_Showcase.xsq is a separate 24-second lighting study without audio.\n"
            "Keep assets/, models/ and media/ in place. No output networks are configured.\n"
            "Baseline verification describes the original show; SHOWS.json records this prepared delivery.\n"
            "Musical/artistic acceptance remains pending.\n")
        report["shows"].append({"folder": folder.name, "prepared_absolute_path": str(folder.resolve()),
                                "layout_sha256": sha256(folder / "xlights_rgbeffects.xml"),
                                "physical_model_nodes_preserved": True, "output_networks_empty": True, "sequences": proofs})
    report["full_song_sequences"] = sum(s["kind"] == "full_song" for show in report["shows"] for s in show["sequences"])
    report["lighting_studies"] = sum(s["kind"] == "lighting_study" for show in report["shows"] for s in show["sequences"])
    if len(report["shows"]) != 7 or report["full_song_sequences"] != 30:
        raise ValueError("Delivery does not contain seven shows and thirty complete songs")
    shutil.copy2(ROOT / "tools/launch_portable_xlights.py", output / "launch_xlights.py")
    (output / "Open_Fire_and_Ice.command").write_text(
        '#!/bin/sh\ncd "$(dirname "$0")" || exit 1\n'
        'if command -v python3 >/dev/null 2>&1; then exec python3 launch_xlights.py "$@"; '
        'else echo "Python 3 is required; ask local Codex to run launch_xlights.py."; exit 1; fi\n')
    (output / "Open_Fire_and_Ice.command").chmod(0o755)
    (output / "Open_Fire_and_Ice.cmd").write_text(
        '@echo off\r\ncd /d "%~dp0"\r\nwhere py >nul 2>nul\r\n'
        'if %errorlevel% equ 0 (py -3 launch_xlights.py %*) else (python launch_xlights.py %*)\r\n'
        'if errorlevel 1 pause\r\n')
    (output / "README.txt").write_text(
        "HELIX — SEVEN PORTABLE XLIGHTS SHOWS\n\n"
        "Extract the entire ZIP into a new folder. Each Helix_* folder is an independent show.\n"
        "Windows: run Open_Fire_and_Ice.cmd. macOS/Linux: run Open_Fire_and_Ice.command.\n"
        "Python 3 and installed xLights 2026.18+ are required.\n"
        "The launcher renders Wire Tree in Fire & Ice, then opens the desktop without exiting.\n"
        "If discovery fails: python launch_xlights.py --xlights <installed executable path>\n"
        "Switching layouts changes show folders; switching songs within one layout does not.\n"
        "Aurora has its preserved 24-second lighting study only; no full-song Aurora export is claimed.\n"
        "Native render verification is recorded in SHOWS.json. Cloud validation is not laptop playback.\n"
        "The latest master handoff ledger is MASTER_TODO.md on feature/portable-xlights-shows.\n")
    (output / "SHOWS.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def package(output: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(output.rglob("*")):
            if any(part.casefold() in {"backup", "backups", "cache", "caches", "__pycache__"}
                   for part in path.relative_to(output).parts):
                continue
            if path.is_dir() and not any(path.iterdir()):
                z.writestr(str(output.name / path.relative_to(output)) + "/", "")
            elif path.is_file() and path.suffix not in (".log", ".bak"):
                z.write(path, output.name / path.relative_to(output))
    with zipfile.ZipFile(archive) as z:
        if z.testzip():
            raise ValueError("Portable archive CRC check failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/Helix_Portable_Shows"))
    args = parser.parse_args()
    report = prepare(args.batch, args.output)
    package(args.output, args.output.with_suffix(".zip"))
    print(json.dumps({"shows": len(report["shows"]), "full_songs": report["full_song_sequences"], "output": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
