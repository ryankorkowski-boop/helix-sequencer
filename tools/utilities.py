from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


CANDIDATE_REPO_DIRS = ("xlights_src", "xlights_upstream", "xlights")
CATALOG_FILENAME = "effect_catalog.json"
_EFFECT_FILE_RE = re.compile(r"^[A-Za-z0-9_]+Effect\.cpp$")
_CTOR_NAME_RE = re.compile(r'RenderableEffect\s*\(\s*[^,]+,\s*"([^"]+)"')
_CONST_STRING_RE = re.compile(r'static\s+const\s+std::string\s+([A-Za-z_][A-Za-z0-9_]*)\("([^"]+)"\);')
_SETTINGS_DIRECT_RE = re.compile(
    r'(?:SettingsMap|GetSettings\(\))\s*\.\s*Get(?:Int|Double|Float|Bool|String)\(\s*"([^"]+)"'
)
_SETTINGS_VAR_RE = re.compile(
    r'(?:SettingsMap|GetSettings\(\))\s*\.\s*Get(?:Int|Double|Float|Bool|String)\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
)
_SETTINGS_CURVE_RE = re.compile(r'GetValueCurve(?:Int|Double|Float)?\(\s*"([^"]+)"')


def discover_xlights_repo(root: Path) -> Path | None:
    for folder in CANDIDATE_REPO_DIRS:
        candidate = root / folder
        if (candidate / "xLights" / "effects").exists():
            return candidate
    return None


def _extract_effect_name(source: str, fallback_name: str) -> str:
    match = _CTOR_NAME_RE.search(source)
    if match:
        value = match.group(1).strip()
        if value:
            return value
    suffix = fallback_name.replace("Effect.cpp", "")
    return suffix or fallback_name


def _extract_option_keys(source: str) -> list[str]:
    constants: dict[str, str] = {}
    for match in _CONST_STRING_RE.finditer(source):
        constants[match.group(1)] = match.group(2)

    keys: set[str] = set()
    for match in _SETTINGS_DIRECT_RE.finditer(source):
        raw = match.group(1).strip()
        if raw:
            keys.add(raw)

    for match in _SETTINGS_VAR_RE.finditer(source):
        var_name = match.group(1)
        mapped = constants.get(var_name, "").strip()
        if mapped:
            keys.add(mapped)

    for match in _SETTINGS_CURVE_RE.finditer(source):
        raw = match.group(1).strip()
        if raw:
            keys.add(raw)

    return sorted(keys)


def build_xlights_catalog(repo_root: Path) -> dict:
    effects_dir = repo_root / "xLights" / "effects"
    if not effects_dir.exists():
        raise FileNotFoundError(f"xLights effects directory not found: {effects_dir}")

    effect_entries: dict[str, dict] = {}
    all_option_keys: set[str] = set()
    for path in sorted(effects_dir.glob("*Effect.cpp")):
        if not _EFFECT_FILE_RE.match(path.name):
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        effect_name = _extract_effect_name(source, path.name)
        option_keys = _extract_option_keys(source)
        all_option_keys.update(option_keys)
        effect_entries[effect_name] = {
            "source_file": str(path),
            "option_keys": option_keys,
            "option_count": len(option_keys),
        }

    effect_names = sorted(effect_entries.keys(), key=lambda item: item.lower())
    return {
        "source_repo": str(repo_root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "effect_count": len(effect_names),
        "effect_names": effect_names,
        "effects": effect_entries,
        "all_option_keys": sorted(all_option_keys),
    }


def write_catalog(catalog: dict, path: Path) -> Path:
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return path


def load_catalog(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_or_build_catalog(root: Path, *, repo_root: Path | None = None, cache_path: Path | None = None) -> dict | None:
    cache = cache_path or (root / CATALOG_FILENAME)
    cached = load_catalog(cache)
    repo = repo_root or discover_xlights_repo(root)
    if repo is None:
        return cached
    try:
        catalog = build_xlights_catalog(repo)
    except Exception:
        return cached
    write_catalog(catalog, cache)
    return catalog


def normalize_effect_name(name: str, catalog: dict | None) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        return ""
    if not catalog:
        return cleaned
    lookup = {
        effect_name.lower(): effect_name
        for effect_name in catalog.get("effect_names", [])
        if isinstance(effect_name, str)
    }
    return lookup.get(cleaned.lower(), cleaned)


def catalog_effect_names(catalog: dict | None) -> list[str]:
    if not catalog:
        return []
    return [name for name in catalog.get("effect_names", []) if isinstance(name, str)]
