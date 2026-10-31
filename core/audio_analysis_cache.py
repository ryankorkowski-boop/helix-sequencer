"""Opt-in, content-addressed cache for reusable audio analysis arrays.

No decoding or analysis is performed at import time. Callers choose which
features to cache and retain ownership of analysis algorithms.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable
from zipfile import BadZipFile

import numpy as np

CACHE_VERSION = 1


def audio_cache_key(audio_path: str | Path, parameters: dict[str, object]) -> str:
    """Hash source bytes and canonical analysis parameters (not just mtime)."""
    digest = hashlib.sha256()
    digest.update(f"helix-audio-cache-v{CACHE_VERSION}\0".encode())
    digest.update(json.dumps(parameters, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    with Path(audio_path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cached_arrays(
    cache_dir: str | Path,
    key: str,
    compute: Callable[[], dict[str, np.ndarray]],
    *,
    validate: Callable[[dict[str, np.ndarray]], None] | None = None,
) -> dict[str, np.ndarray]:
    """Load an NPZ hit or compute and atomically publish a cache miss.

    Only trusted local cache directories should be used. Invalid cache entries
    are treated as misses. Concurrent writers may duplicate computation, but
    each completed replacement is atomic.
    """
    if len(key) != 64 or any(ch not in "0123456789abcdef" for ch in key):
        raise ValueError("cache key must be a lowercase SHA-256 hex digest")
    directory = Path(cache_dir)
    target = directory / f"{key}.npz"
    if target.is_file():
        try:
            with np.load(target, allow_pickle=False) as archive:
                arrays = {name: archive[name] for name in archive.files}
            if validate is not None:
                validate(arrays)
            return arrays
        except (OSError, ValueError, EOFError, KeyError, BadZipFile):
            pass
    arrays = {name: np.asarray(value) for name, value in compute().items()}
    if any(array.dtype.hasobject for array in arrays.values()):
        raise TypeError("object arrays cannot be cached")
    if validate is not None:
        validate(arrays)
    directory.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".helix-analysis-", suffix=".npz", dir=directory)
    try:
        with os.fdopen(fd, "wb") as output:
            np.savez_compressed(output, **arrays)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return arrays
