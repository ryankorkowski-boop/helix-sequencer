"""Explicit post-run scoring, preserving all unrelated manifest fields."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from tools.quality import score_sequence


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path.name}")
    return value


def _resolve(raw: str, run_dir: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    # RunManager records paths relative to its launch cwd; portable bundles
    # may instead use paths relative to the run directory. Refuse ambiguity.
    candidates = {p.resolve() for p in (run_dir / path, path) if p.is_file()}
    if len(candidates) != 1:
        raise ValueError(f"Missing or ambiguous input path: {raw}")
    return candidates.pop()


def score_run(
    run_dir: Path, *, xsq: Path | None = None,
    layout: Path | None = None, features: Path | None = None,
) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    manifest = _json_object(manifest_path)
    if xsq is None:
        raw_paths = {a["path"] for a in manifest.get("artifacts", [])
                     if a.get("kind") == "xsq"}
        if not raw_paths:
            paths = sorted(run_dir.glob("*.xsq"))
        else:
            paths = sorted({_resolve(p, run_dir) for p in raw_paths})
        if len(paths) != 1:
            raise ValueError("Expected exactly one XSQ; pass --xsq explicitly")
        xsq = paths[0]
    if layout is None:
        raw_layout = manifest.get("layout_path")
        if not raw_layout:
            raise ValueError("Manifest has no layout_path; pass --layout")
        layout = _resolve(raw_layout, run_dir)
    feature_path = features or run_dir / "audio_features.json"
    report = score_sequence(xsq, layout, _json_object(feature_path))
    manifest["quality"] = report
    # An interrupted write must leave the old manifest intact.
    fd, raw_temp = tempfile.mkstemp(prefix=".quality-", dir=run_dir)
    temp = Path(raw_temp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(manifest_path)
    finally:
        temp.unlink(missing_ok=True)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    score = commands.add_parser("score")
    score.add_argument("run_dir", type=Path)
    score.add_argument("--xsq", type=Path)
    score.add_argument("--layout", type=Path)
    score.add_argument("--features", type=Path)
    args = parser.parse_args(argv)
    try:
        report = score_run(args.run_dir, xsq=args.xsq, layout=args.layout,
                           features=args.features)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        parser.exit(2, f"quality score: {exc}\n")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
