"""Package the exact xLights layout beside newly generated XSQ files.

An XSQ alone does not contain the model positions/controller show configuration.
Copying a layout snapshot into the same directory prevents accidental use of
a different layout. Never overwrite a mismatched prior show configuration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same_or_copy(src: Path, dest: Path) -> str:
    if dest.exists():
        if _sha(src) != _sha(dest):
            raise ValueError(
                f"Existing show file {dest} differs from the selected {src}. "
                "Use a fresh output folder for this layout so sequences are not "
                "silently paired with the wrong models/controllers."
            )
        return "already_matching"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return "copied"


def package_xlights_layout(xsqs: list[Path], layout: Path) -> list[dict]:
    """Place xlights_rgbeffects.xml + optional networks alongside each XSQ.

    Only explicitly produced XSQ destinations are passed by the caller. The
    selected source layout (including .xbkp backups) remains read-only.
    Returns provenance, not a claim of independently verified playback.
    """
    layout = Path(layout)
    if layout.suffix.lower() not in {".xml", ".xbkp"}:
        raise ValueError(f"Not an xLights layout XML/backup: {layout}")
    source_root = ET.parse(layout).getroot()
    if source_root.tag != "xrgb" or not source_root.findall("./models/model"):
        raise ValueError("Selected layout lacks xLights xrgb model definitions")
    outputs = sorted({Path(path).parent.resolve() for path in xsqs})
    if not outputs:
        return []
    network = layout.parent / "xlights_networks.xml"
    # Determine conflicts in advance to avoid partial copies.
    source_files = [("xlights_rgbeffects.xml", layout)]
    if network.is_file():
        ET.parse(network)
        source_files.append(("xlights_networks.xml", network))
    for folder in outputs:
        for name, src in source_files:
            dest = folder / name
            if dest.exists() and _sha(dest) != _sha(src):
                raise ValueError(f"Layout/network collision at {dest}; use a new output folder")
    result = []
    for folder in outputs:
        copied = {}
        for name, src in source_files:
            dest = folder / name
            status = _same_or_copy(src, dest)
            copied[name] = {"status": status, "sha256": _sha(dest)}
        payload = {
            "schema": "helix.xlights_show_context.v1",
            "xsqs": sorted(p.name for p in xsqs if p.parent.resolve() == folder),
            "layout_original_file": layout.name,
            "files": copied,
            "network_config_included": network.is_file(),
            "media_files_may_require_relinking": True,
            "native_xlights_render_verified": False,
            "note": "Open this directory as an xLights Show Directory. Verify audio, missing resources and real controller mappings before playing.",
        }
        manifest = folder / "helix_show_context.json"
        if manifest.exists():
            old = json.loads(manifest.read_text(encoding="utf-8"))
            if old.get("files") != payload["files"]:
                # File hashes were preflighted. A manifest mismatch may be just
                # copied/already_matching states, which are non-semantic.
                for name in copied:
                    previous = old.get("files", {}).get(name, {})
                    if previous.get("sha256") not in {None, copied[name]["sha256"]}:
                        raise ValueError("Existing show-context manifest references another layout")
        manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        result.append({"directory": str(folder), "manifest": str(manifest), **payload})
    return result



def package_audio_alongside(sequences: list[Path], audio: Path | None) -> list[Path]:
    """Keep portable show audio beside new sequencer outputs, without clobbering.

    The sequence head/mediaFile and legacy LMS musicFilename use audio.name.
    This is optional for nonmusical sequences, and never rewrites the source.
    """
    if audio is None:
        return []
    audio = Path(audio)
    if not audio.is_file():
        raise FileNotFoundError(f"Selected audio missing: {audio}")
    destinations = []
    for folder in sorted({Path(p).parent.resolve() for p in sequences}):
        dest = folder / audio.name
        _same_or_copy(audio, dest)
        destinations.append(dest)
    return destinations
