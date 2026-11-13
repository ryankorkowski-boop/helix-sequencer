"""Run real Helix production audio through the isolated Polar Prism float.

Example:
 python -m tools.render_parade_float --audio /private/Polar\\ Prism\\ Parade.mp3 \\
   --sha256 VERIFIED_SOURCE_SHA --work /tmp/polar-prism --xlights /path/to/xLights

Never substitutes another audio file. An offline xLights binary is required for
native FSEQ and MP4; this script does not claim they exist before verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from models.parade_float import AUDIO, TITLE, GROUPS, build, inventory
from tools.build_current_comparison import build as build_native_layout
from tools.phoneme_source import digest
from tools.render_full_song_comparison import render_panel, write_json


def _layout(number, plan, *, duration, **kwargs):
    if number != 1:
        raise ValueError("Only one parade-float scene is supported")
    return build(plan, duration=duration)


def add_macro_groups(folder: Path):
    """Materialize the six editorial layers as portable native xLights groups.

    Keep the group hierarchy orthogonal to the actual source-clock effects:
    grouping selects related physical models but never manufactures cues.
    """
    import xml.etree.ElementTree as ET

    folder = Path(folder)
    path = folder / "xlights_rgbeffects.xml"
    tree = ET.parse(path)
    root = tree.getroot()
    models = root.find("models")
    groups = root.find("modelGroups")
    if models is None or groups is None:
        raise ValueError("Missing native model/group blocks")
    all_models = list(models.findall("model"))
    names = {item.get("name") for item in all_models}
    existing = {g.get("name") for g in groups.findall("modelGroup")}
    for macro, zones in GROUPS.items():
        # Actual membership is encoded by HX_ZONE_* groups.
        members = []
        for zone in zones:
            child = next((group for group in groups.findall("modelGroup")
                          if group.get("name") == "HX_ZONE_" + zone), None)
            if child is not None:
                members.extend(n for n in child.get("models", "").split(",") if n in names)
        members = sorted(set(members))
        if not members:
            raise ValueError(f"Editorial layer has no native models: {macro}")
        if macro not in existing:
            ET.SubElement(groups, "modelGroup", {
                "name": macro, "models": ",".join(members),
                "layout": "minimalGrid", "LayoutGroup": "Default", "GridSize": "600"})
    tree.write(path, encoding="utf-8", xml_declaration=True)
    receipt_path = folder / "run_manifest.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["layout_sha256"] = digest(path)
    receipt["macro_group_names"] = sorted(GROUPS)
    write_json(receipt_path, receipt)
    return receipt


def run(audio: Path, sha256: str, work: Path, xlights: Path):
    audio, work, xlights = Path(audio), Path(work), Path(xlights)
    if audio.name != AUDIO:
        raise ValueError(f"Expected exact source filename: {AUDIO}")
    if digest(audio) != sha256:
        raise ValueError("Original Drive recording SHA mismatch")
    if not xlights.is_file():
        raise FileNotFoundError(f"Native xLights binary unavailable: {xlights}")
    work.mkdir(parents=True, exist_ok=True)
    # Use existing source-hash production checkpoint and standard Helix CLI.
    production = work / "production"
    if not (production / "run_manifest.json").exists():
        # Current prepare() also builds the default sixteen views. Avoid
        # fabricating those when only this float was requested.
        import shutil
        import subprocess
        import sys
        from tools.render_full_song_comparison import ROOT
        media = production / "media" / audio.name
        media.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(audio, media)
        cmd = [sys.executable, str(ROOT / "main.py"), "--profile", "master", "--",
               "--template", str(ROOT / "template.xsq"), "--audio", str(media),
               "--layout-file", str(ROOT / "xlights_rgbeffects.xml"),
               "--output-dir", str(production / "sequence"), "--single",
               "--variants", "1", "--no-prompt", "--no-save-settings",
               "--no-workspace-history", "--no-learning-memory",
               "--palette-mode", "warm", "--sync-lyrics-heads"]
        with (production / "sequencer.log").open("w") as logfile:
            subprocess.run(cmd, cwd=ROOT, stdout=logfile,
                           stderr=subprocess.STDOUT, check=True)
        plans = list((production / "sequence").rglob("*.snowman_band.json"))
        if len(plans) != 1:
            raise RuntimeError("Helix did not produce exactly one source plan")
        write_json(production / "run_manifest.json", {
            "audio_name": audio.name,
            "audio_sha256": sha256,
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "plan_sha256": digest(plans[0])})
    else:
        source = json.loads((production / "run_manifest.json").read_text())
        import subprocess
        from tools.render_full_song_comparison import ROOT
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        plans = list((production / "sequence").rglob("*.snowman_band.json"))
        if (source["audio_sha256"] != sha256
                or digest(production / "media" / AUDIO) != sha256
                or source.get("source_commit") != current_commit
                or len(plans) != 1
                or digest(plans[0]) != source.get("plan_sha256")):
            raise ValueError("Existing production cache belongs to different source or code")
    layouts = work / "parade_layouts"
    folder = layouts / "01"
    if not folder.exists():
        build_native_layout(production, None, layouts, numbers=(1,),
                            names=(TITLE,), layout_builder=_layout,
                            preserve_addresses=(), instrumental=True,
                            expected_sha256=sha256)
    if not (folder / "run_manifest.json").exists():
        raise RuntimeError("No source-bound native layout manifest")
    add_macro_groups(folder)
    row, report, fseq = render_panel(folder, audio, xlights)
    if report["status"] != "success":
        raise RuntimeError("Native render not verified")
    receipt = dict(source_sha256=sha256, audio_name=AUDIO,
                   layout=TITLE, design=inventory(),
                   native_receipt=report,
                   fseq_sha256=digest(fseq),
                   xsq_sha256=digest(folder / row["xsq"]),
                   source_bound=True, owner_approved=False)
    write_json(work / "parade_floats_verified.json", receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio",type=Path,required=True)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--xlights",type=Path,required=True)
    a=parser.parse_args()
    print(json.dumps(run(a.audio,a.sha256,a.work,a.xlights),indent=2))


if __name__=="__main__":
    main()
