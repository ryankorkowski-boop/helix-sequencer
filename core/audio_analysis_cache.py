"""Persistent results for deterministic, local audio analysis."""

from __future__ import annotations

import hashlib
import json
import platform
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


# Bump when the analysis pipeline or its serialized result changes.
_CACHE_VERSION = 1
_DSP_PACKAGES = (
    "audioread", "librosa", "llvmlite", "numba", "numpy", "scipy", "soundfile",
)


def _distribution_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def result_path(
    audio_path: Path, audio_digest: str, settings: dict[str, object], cache_root: Path,
) -> Path:
    key = {
        "version": _CACHE_VERSION,
        "input_name": audio_path.name,
        "input_digest": audio_digest,
        "settings": settings,
        "platform": [platform.system(), platform.machine(), platform.python_version()],
        "dsp_versions": {name: _distribution_version(name) for name in _DSP_PACKAGES},
    }
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()
    return cache_root / "results" / f"{digest}.json"


def read_result(path: Path, stems: dict[str, Path]) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["version"] != _CACHE_VERSION:
            return None
        if {name: file_digest(stem) for name, stem in stems.items()} != payload["stems"]:
            return None
        return payload["result"] if isinstance(payload["result"], dict) else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def write_result(path: Path, result: dict, stem_digests: dict[str, str]) -> None:
    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump({"version": _CACHE_VERSION, "stems": stem_digests, "result": result}, handle)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
