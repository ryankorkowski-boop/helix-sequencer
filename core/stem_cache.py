from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

CACHE_SCHEMA = "helix.stem_cache.v1"
MANIFEST_NAME = "stem_cache_manifest.json"
DEFAULT_REQUIRED_STEMS = ("vocals", "drums", "bass", "other")


def audio_sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return a stable SHA-256 for the source audio without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(max(1, int(chunk_size)))
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def manifest_path(stem_dir: Path) -> Path:
    return stem_dir / MANIFEST_NAME


def write_stem_cache_manifest(
    audio_path: Path,
    stem_dir: Path,
    *,
    source: str,
    stems: dict[str, Path],
    separator: str | None = None,
) -> Path:
    """Persist enough information to safely reuse previously separated stems.

    Paths are stored relative to the stem cache directory so cache directories
    remain movable. The audio hash is authoritative; a same-named replacement
    song cannot accidentally reuse stems from older audio.
    """
    stem_dir.mkdir(parents=True, exist_ok=True)
    root = stem_dir.resolve()
    relative_stems: dict[str, str] = {}
    for name, path in sorted(stems.items()):
        candidate = Path(path).resolve()
        try:
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Stem path escapes cache directory: {path}") from exc
        relative_stems[str(name)] = relative.as_posix()

    payload = {
        "schema": CACHE_SCHEMA,
        "audio_sha256": audio_sha256(audio_path),
        "audio_size_bytes": int(audio_path.stat().st_size),
        "source": str(source),
        "separator": str(separator or source),
        "stems": relative_stems,
    }
    target = manifest_path(stem_dir)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def load_cached_stems(
    audio_path: Path,
    stem_dir: Path,
    *,
    allowed_sources: Iterable[str] | None = None,
    required_stems: Iterable[str] = DEFAULT_REQUIRED_STEMS,
) -> tuple[str, dict[str, Path]] | None:
    """Return cached stems only when the source audio and files still match."""
    target = manifest_path(stem_dir)
    if not audio_path.exists() or not target.exists():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict) or payload.get("schema") != CACHE_SCHEMA:
        return None

    try:
        expected_size = int(payload.get("audio_size_bytes", -1))
    except Exception:
        return None
    if expected_size != int(audio_path.stat().st_size):
        return None

    expected_hash = str(payload.get("audio_sha256", ""))
    if not expected_hash or expected_hash != audio_sha256(audio_path):
        return None

    source = str(payload.get("source", "")).strip()
    if not source:
        return None
    if allowed_sources is not None and source not in {str(item) for item in allowed_sources}:
        return None

    encoded_stems = payload.get("stems")
    if not isinstance(encoded_stems, dict):
        return None

    root = stem_dir.resolve()
    stems: dict[str, Path] = {}
    for name, relative_value in encoded_stems.items():
        if not isinstance(relative_value, str) or not relative_value.strip():
            return None
        candidate = (root / relative_value).resolve()
        if candidate != root and root not in candidate.parents:
            return None
        if not candidate.is_file():
            return None
        stems[str(name)] = candidate

    if not set(str(item) for item in required_stems).issubset(stems):
        return None
    return source, stems
