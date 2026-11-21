"""Freeze one source-bound analysis bundle for all three owner-approval renders.

This does not claim to resolve lead/harmony identities or render a video.
All consumers must verify the manifest before using the bundle.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def create(source, stems, output, source_commit):
    source = Path(source).resolve(strict=True)
    stems = Path(stems).resolve(strict=True)
    output = Path(output)
    if not source_commit or len(source_commit) != 40 or any(c not in "0123456789abcdef" for c in source_commit.lower()):
        raise ValueError("Full source commit required")
    files = {}
    for role in ("drums", "bass", "other", "vocals"):
        matches = list(stems.rglob(role + ".wav"))
        if len(matches) != 1:
            raise ValueError(f"Exactly one Demucs {role} stem required, found {len(matches)}")
        files[role] = {"path": str(matches[0].relative_to(stems)), "sha256": sha256(matches[0])}
    manifest = {"schema": "helix.shared-approval-analysis.v1",
                "source_audio_sha256": sha256(source), "source_audio_name": source.name,
                "source_commit": source_commit, "stems": files,
                "vocal_identity_verified": False,
                "render_roles": ["16-panel", "12-layout", "six-snowman-band"]}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["analysis_sha256"] = hashlib.sha256(canonical).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def verify(source, stems, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get("schema") != "helix.shared-approval-analysis.v1":
        raise ValueError("Wrong shared-analysis schema")
    claimed = manifest["analysis_sha256"]
    canonical = {k: v for k, v in manifest.items() if k != "analysis_sha256"}
    actual = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if actual != claimed or sha256(source) != manifest["source_audio_sha256"]:
        raise ValueError("Source or analysis manifest integrity failure")
    root = Path(stems).resolve(strict=True)
    for role, item in manifest["stems"].items():
        path = (root / item["path"]).resolve(strict=True)
        if not path.is_relative_to(root) or sha256(path) != item["sha256"]:
            raise ValueError(f"Invalid {role} stem provenance")
    if set(manifest["stems"]) != {"drums", "bass", "other", "vocals"}:
        raise ValueError("Incomplete stem bundle")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("stems", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = verify(args.source, args.stems, args.manifest) if args.verify else create(
        args.source, args.stems, args.manifest, args.source_commit)
    print(json.dumps({"analysis_sha256": result["analysis_sha256"],
                      "source_audio_sha256": result["source_audio_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
