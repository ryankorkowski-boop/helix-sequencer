"""Preserve and validate the pinned renderer independently of branch cache scope."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

from tools.patch_xlights_native_export import CAMERA_NEW, SIZE_NEW

UPSTREAM_COMMIT = "839c0f590dc454bb7adb8a16c4dd92a70b46156e"
PLATFORM = "ubuntu24-x64"
SCHEMA = "helix.native_renderer_bundle.v1"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def artifact_name(patch: Path) -> str:
    return f"helix-native-build-{PLATFORM}-2026.18-{digest(patch)}"


def validate_tree(root: Path) -> None:
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
    ).strip()
    if actual != UPSTREAM_COMMIT:
        raise ValueError("Renderer is not the pinned upstream commit")
    for relative, expected in (
        ("src-ui-wx/xLightsMain.cpp", SIZE_NEW),
        ("src-ui-wx/app-shell/TabSequence.cpp", CAMERA_NEW),
    ):
        if (root / relative).read_text().count(expected) != 1:
            raise ValueError(f"Renderer patch absent or ambiguous: {relative}")
    if not (root / "bin/xLights").is_file() or not os.access(root / "bin/xLights", os.X_OK):
        raise ValueError("Compiled native renderer is absent or not executable")
    if not (root / "wxWidgets-xlights_2026.17c/lib/libwx_gtk3u-3.3.so.4.0.0").is_file():
        raise ValueError("Renderer bundle lacks its built wxWidgets runtime")


def pack(root: Path, output: Path, patch: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError("Bundle output must be outside the build tree")
    validate_tree(root)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "renderer.tar.gz"
    # Keep wxWidgets, support files, submodules and git identity. A bare executable
    # cannot restore the /usr wxWidgets installation on a fresh hosted runner.
    with tarfile.open(archive, "w:gz", compresslevel=1) as bundle:
        bundle.add(root, arcname="xlights-src")
    manifest = {
        "schema": SCHEMA, "platform": PLATFORM,
        "upstream_commit": UPSTREAM_COMMIT, "patch_sha256": digest(patch),
        "archive_sha256": digest(archive), "binary_sha256": digest(root / "bin/xLights"),
    }
    (output / "renderer.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def restore(bundle: Path, root: Path, patch: Path) -> dict:
    manifest = json.loads((bundle / "renderer.json").read_text())
    expected = {"schema": SCHEMA, "platform": PLATFORM,
                "upstream_commit": UPSTREAM_COMMIT, "patch_sha256": digest(patch)}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Renderer bundle identity does not match the pinned build")
    archive = bundle / "renderer.tar.gz"
    if manifest.get("archive_sha256") != digest(archive):
        raise ValueError("Renderer archive checksum mismatch")
    root = root.resolve()
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-restore-", dir=root.parent) as temp:
        staging = Path(temp)
        with tarfile.open(archive, "r:gz") as source:
            members = source.getmembers()
            if len(members) > 100_000 or sum(m.size for m in members) > 8 * 1024**3:
                raise ValueError("Renderer archive exceeds expected build bounds")
            for member in members:
                parts = Path(member.name).parts
                if not parts or parts[0] != "xlights-src" or ".." in parts:
                    raise ValueError("Renderer archive contains an unsafe path")
            # data rejects devices and links escaping the staging directory.
            source.extractall(staging, filter="data")
        candidate = staging / "xlights-src"
        validate_tree(candidate)
        if digest(candidate / "bin/xLights") != manifest.get("binary_sha256"):
            raise ValueError("Compiled renderer checksum mismatch")
        # Validate completely before replacing a potentially useful object cache.
        previous = staging / "previous"
        if root.exists():
            root.rename(previous)
        try:
            candidate.rename(root)
        except OSError:
            if previous.exists():
                previous.rename(root)
            raise
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("name", "pack", "restore"))
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    if args.action == "name":
        print(artifact_name(args.patch))
    elif args.root is None or args.bundle is None:
        parser.error("pack/restore require --root and --bundle")
    elif args.action == "pack":
        print(json.dumps(pack(args.root, args.bundle, args.patch)))
    else:
        print(json.dumps(restore(args.bundle, args.root, args.patch)))


if __name__ == "__main__":
    main()
