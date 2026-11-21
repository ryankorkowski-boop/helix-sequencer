"""Source-bound manifest for optional two-stage lead/backing separation.

Inspired by MVSep's vocals-first karaoke workflow, without requiring MVSep
or uploading user audio. Outputs must be produced by an upstream separator;
this module verifies the declared source and returns paths to the existing
independent-vocals gate. It does not assert singer identity.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def validate_vocal_separation_manifest(manifest_path: str | Path,
                                       original_audio: str | Path) -> tuple[Path, Path]:
    """Verify a two-stage stem bundle against the original source bytes.

    Manifest schema helix.vocal-separation.v1:
      source_sha256, method='vocals_first_then_lead_backing',
      lead={path,sha256}, backing={path,sha256}.
    All paths are relative to the manifest directory and cannot escape it.
    """
    manifest_path = Path(manifest_path).resolve()
    source = Path(original_audio)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != "helix.vocal-separation.v1":
        raise ValueError("Unsupported vocal separation manifest schema")
    if data.get("method") != "vocals_first_then_lead_backing":
        raise ValueError("Vocal separation must use the declared vocals-first workflow")
    if data.get("source_sha256") != _digest(source):
        raise ValueError("Vocal separation source audio SHA256 mismatch")
    root = manifest_path.parent
    paths = []
    for role in ("lead", "backing"):
        entry = data.get(role)
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"Missing {role} stem path")
        relative = Path(entry["path"])
        if relative.is_absolute() or not relative.parts:
            raise ValueError(f"Unsafe {role} stem path")
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise ValueError(f"Unsafe or missing {role} stem path")
        if entry.get("sha256") != _digest(candidate):
            raise ValueError(f"{role} stem SHA256 mismatch")
        paths.append(candidate)
    if paths[0] == paths[1]:
        raise ValueError("Lead and backing stems reference the same file")
    if data["lead"]["sha256"] == data["backing"]["sha256"]:
        raise ValueError("Duplicate vocal stems: independent harmony not established")
    if any(data["source_sha256"] == data[role]["sha256"] for role in ("lead", "backing")):
        raise ValueError("Singer stem matches original source audio; separation not established")
    return paths[0], paths[1]
