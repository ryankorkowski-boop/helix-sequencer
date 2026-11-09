"""Fail-closed validation for issue #210 real-audio engine comparison manifests.

Run before assembling any 16-panel native comparison. This is not a renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_VARIANTS = tuple(range(1, 17))
REQUIRED_SHARED = ("audio_sha256", "layout_sha256", "camera_id", "palette_sha256", "channel_map_sha256", "fps", "source_commit")


def validate_comparison_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    panels = manifest.get("panels")
    if not isinstance(panels, list):
        return ["panels must be a list"]
    if len(panels) != 16:
        errors.append(f"expected 16 panels; found {len(panels)}")
    numbers = [p.get("panel") for p in panels if isinstance(p, dict)]
    if sorted(n for n in numbers if type(n) is int) != list(REQUIRED_VARIANTS):
        errors.append("panel identifiers must be exactly 1 through 16, once each")
    baseline = next((p for p in panels if isinstance(p, dict) and p.get("panel") == 1), {})
    for field in REQUIRED_SHARED:
        expected = baseline.get(field)
        if expected is None or expected == "":
            errors.append(f"baseline missing {field}")
        for p in panels:
            if isinstance(p, dict) and p.get("panel") != 1 and p.get(field) != expected:
                errors.append(f"panel {p.get('panel')} differs in frozen field {field}")
    signatures: dict[str, int] = {}
    for p in panels:
        if not isinstance(p, dict):
            errors.append("panel entry is not an object")
            continue
        num = p.get("panel")
        if p.get("audio_kind") != "real" or p.get("features_source") != "source_audio":
            errors.append(f"panel {num}: synthetic or unverified audio/features")
        if p.get("engine_execution_verified") is not True:
            errors.append(f"panel {num}: engine execution not verified")
        if p.get("native_render_verified") is not True:
            errors.append(f"panel {num}: native render not verified")
        for hash_field in ("xsq_sha256", "fseq_sha256"):
            value = p.get(hash_field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                errors.append(f"panel {num}: invalid or missing {hash_field}")
        if p.get("synthetic_fallback_used") is not False:
            errors.append(f"panel {num}: synthetic fallback not explicitly excluded")
        signature = p.get("fseq_sha256")
        if isinstance(signature, str) and signature:
            if signature in signatures:
                errors.append(f"panel {num}: identical FSEQ hash to panel {signatures[signature]}")
            else:
                signatures[signature] = num
        if num in (9, 15, 16):
            if p.get("birdsong_enabled") is not True:
                errors.append(f"panel {num}: required Birdsong engine is disabled")
            rows = p.get("birdsong_native_rows")
            if type(rows) is not int or rows <= 0 or p.get("birdsong_real_features_verified") is not True:
                errors.append(f"panel {num}: Birdsong not proven in native output with real features")
    return errors



def verify_local_artifacts(manifest: dict, root: Path) -> list[str]:
    """Verify actual native bytes, not only self-reported hashes.

    Paths are relative to the trusted comparison workspace; absolute paths,
    parent traversal and symlink escapes are rejected.
    """
    errors: list[str] = []
    if not isinstance(manifest, dict) or not isinstance(manifest.get("panels"), list):
        return ["manifest panels unavailable for artifact verification"]
    root = root.resolve()
    for panel in manifest["panels"]:
        if not isinstance(panel, dict):
            errors.append("invalid panel entry")
            continue
        for kind in ("xsq", "fseq"):
            rel = panel.get(f"{kind}_path")
            expected = panel.get(f"{kind}_sha256")
            if not isinstance(rel, str) or not rel:
                errors.append(f"panel {panel.get('panel')}: missing {kind}_path")
                continue
            path = Path(rel)
            if path.is_absolute() or ".." in path.parts:
                errors.append(f"panel {panel.get('panel')}: unsafe {kind}_path")
                continue
            resolved = (root / path).resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                errors.append(f"panel {panel.get('panel')}: missing or escaped {kind} artifact")
                continue
            digest = hashlib.sha256()
            with resolved.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                errors.append(f"panel {panel.get('panel')}: {kind} bytes differ from claimed SHA256")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path, help="verify actual XSQ/FSEQ bytes under this directory")
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate_comparison_manifest(payload)
    if args.artifact_root is not None:
        errors.extend(verify_local_artifacts(payload, args.artifact_root))
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
