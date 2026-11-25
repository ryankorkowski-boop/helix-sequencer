"""Create a source-bound manifest for already separated two-stage vocal stems.

This utility does not separate audio or establish singer identity.
Usage:
  python -m tools.prepare_vocal_separation_manifest original.wav lead.wav backing.wav --output stems.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from core.independent_vocals import analyze_independent_vocals
from core.vocal_separation_manifest import validate_vocal_separation_manifest


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(source: Path, lead: Path, backing: Path, output: Path) -> Path:
    source, lead, backing, output = (
        Path(source).resolve(), Path(lead).resolve(),
        Path(backing).resolve(), Path(output).resolve()
    )
    # Never overwrite source material or a singer stem with a manifest.
    if output in {source, lead, backing}:
        raise ValueError("Manifest output cannot overwrite source audio or singer stems")
    # A stem cannot simply be the original mix renamed as a singer track.
    source_hash = sha256(source)
    if source_hash in {sha256(lead), sha256(backing)}:
        raise ValueError("Vocal stem matches original audio; singer separation not established")
    # Fail before writing any misleading source provenance.
    analyze_independent_vocals(lead, backing)
    for stem in (lead, backing):
        if not stem.is_relative_to(output.parent):
            raise ValueError("Stem files must be within the output manifest directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "helix.vocal-separation.v1",
        "method": "vocals_first_then_lead_backing",
        "source_sha256": source_hash,
        "lead": {"path": str(lead.relative_to(output.parent)), "sha256": sha256(lead)},
        "backing": {"path": str(backing.relative_to(output.parent)), "sha256": sha256(backing)},
    }
    # Validate the manifest before publishing; atomic replace avoids partial JSON.
    import tempfile
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         prefix=".helix-stems-", suffix=".json",
                                         dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(manifest, indent=2) + "\n")
        validate_vocal_separation_manifest(temporary, source)
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("lead", type=Path)
    parser.add_argument("backing", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.source, args.lead, args.backing, args.output))


if __name__ == "__main__":
    main()
