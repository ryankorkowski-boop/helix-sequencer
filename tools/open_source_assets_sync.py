from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

GITHUB_API_ROOT = "https://api.github.com"

PERMISSIVE_LICENSES = {
    "mit",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mpl-2.0",
    "cc0-1.0",
    "unlicense",
}

COPYLEFT_LICENSES = {
    "gpl-3.0",
    "gpl-2.0",
    "lgpl-3.0",
    "lgpl-2.1",
    "agpl-3.0",
}

EXTENSION_CATEGORY = {
    ".xsq": "sequences",
    ".xml": "sequences",
    ".xmodel": "models",
    ".lua": "lua",
    ".glsl": "shaders",
    ".frag": "shaders",
    ".vert": "shaders",
}

# Curated seeds chosen for public visibility and practical xLights/shader relevance.
SEED_REPOSITORIES = [
    "cp16net/xlights-sequences",
    "baccula/TeslaLightShow-HarderBetterFasterStronger",
    "rrevi/tesla-xlights-show",
    "wjenkins4107/xLightsLua",
    "ashima/webgl-noise",
    "hughsk/glsl-noise",
    "Experience-Monks/glsl-fast-gaussian-blur",
    "patriciogonzalezvivo/glslViewer",
]


@dataclass
class RepoPolicy:
    allowed_for_download: bool
    license_spdx: str
    mode: str
    reason: str


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "helix-open-source-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_get(url: str, token: str | None) -> Any:
    response = requests.get(url, headers=_headers(token), timeout=30)
    response.raise_for_status()
    return response.json()


def _repo_metadata(repo_full_name: str, token: str | None) -> dict[str, Any]:
    return _api_get(f"{GITHUB_API_ROOT}/repos/{repo_full_name}", token)


def classify_repo(repo: dict[str, Any], include_copyleft: bool) -> RepoPolicy:
    license_obj = repo.get("license")
    spdx = str(license_obj.get("spdx_id") if isinstance(license_obj, dict) else "").strip().lower()
    if not spdx:
        return RepoPolicy(False, "", "blocked", "missing SPDX license")
    if spdx in PERMISSIVE_LICENSES:
        return RepoPolicy(True, spdx, "allowed", "permissive license")
    if spdx in COPYLEFT_LICENSES:
        if include_copyleft:
            return RepoPolicy(True, spdx, "allowed_copyleft", "copyleft included by explicit flag")
        return RepoPolicy(False, spdx, "reference_only", "copyleft license excluded from default download")
    return RepoPolicy(False, spdx, "blocked", f"license not allowlisted ({spdx})")


def _walk_contents(
    repo_full_name: str,
    token: str | None,
    *,
    max_depth: int = 6,
    max_files: int = 240,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    queue: list[tuple[str, int]] = [("", 0)]
    while queue:
        if len(out) >= max_files:
            break
        path, depth = queue.pop(0)
        if depth > max_depth:
            continue
        url = f"{GITHUB_API_ROOT}/repos/{repo_full_name}/contents/{path}"
        try:
            payload = _api_get(url, token)
        except Exception:
            continue
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            continue
        for item in payload:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "")
            if item_type == "dir":
                queue.append((str(item.get("path") or ""), depth + 1))
                continue
            if item_type != "file":
                continue
            file_path = str(item.get("path") or "")
            suffix = Path(file_path).suffix.lower()
            category = EXTENSION_CATEGORY.get(suffix)
            if category is None:
                continue
            out.append(
                {
                    "path": file_path,
                    "download_url": str(item.get("download_url") or ""),
                    "size": int(item.get("size") or 0),
                    "sha": str(item.get("sha") or ""),
                    "category": category,
                    "suffix": suffix,
                }
            )
            if len(out) >= max_files:
                break
    return out


def _safe_relpath(text: str) -> Path:
    cleaned = text.replace("\\", "/").strip("/")
    parts = [part for part in cleaned.split("/") if part not in {"", ".", ".."}]
    return Path(*parts) if parts else Path("unnamed")


def _download_file(url: str, out_path: Path, token: str | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, headers=_headers(token), timeout=60)
    response.raise_for_status()
    out_path.write_bytes(response.content)


def run_sync(
    *,
    output_root: Path,
    include_copyleft: bool,
    max_files_per_repo: int,
    repo_limit: int,
    token: str | None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    download_count = 0
    seed_repos = list(SEED_REPOSITORIES)
    if repo_limit > 0:
        seed_repos = seed_repos[:repo_limit]
    for repo_name in seed_repos:
        try:
            repo = _repo_metadata(repo_name, token)
        except Exception as exc:
            records.append(
                {
                    "repo": repo_name,
                    "status": "error",
                    "reason": f"metadata fetch failed: {exc}",
                    "files": [],
                }
            )
            continue

        policy = classify_repo(repo, include_copyleft=include_copyleft)
        files = _walk_contents(repo_name, token, max_depth=6, max_files=max(1, int(max_files_per_repo)))
        files = sorted(files, key=lambda row: (row["category"], row["path"]))[: max(1, int(max_files_per_repo))]

        repo_record = {
            "repo": repo_name,
            "html_url": str(repo.get("html_url") or ""),
            "stars": int(repo.get("stargazers_count") or 0),
            "updated_at": str(repo.get("updated_at") or ""),
            "license_spdx": policy.license_spdx,
            "status": policy.mode,
            "reason": policy.reason,
            "files": [],
        }

        for file_row in files:
            rel_path = _safe_relpath(file_row["path"])
            target_path = output_root / file_row["category"] / repo_name.replace("/", "__") / rel_path
            file_record = {
                "path": file_row["path"],
                "category": file_row["category"],
                "suffix": file_row["suffix"],
                "download_url": file_row["download_url"],
                "size": int(file_row["size"]),
                "downloaded": False,
                "output_path": str(target_path),
            }
            if policy.allowed_for_download and file_row["download_url"]:
                try:
                    _download_file(file_row["download_url"], target_path, token)
                    file_record["downloaded"] = True
                    download_count += 1
                except Exception as exc:
                    file_record["download_error"] = str(exc)
            repo_record["files"].append(file_record)
        records.append(repo_record)

    manifest = {
        "version": 1,
        "policy": {
            "permissive_allowlist": sorted(PERMISSIVE_LICENSES),
            "copyleft_allowlist": sorted(COPYLEFT_LICENSES),
            "include_copyleft": bool(include_copyleft),
            "max_files_per_repo": int(max_files_per_repo),
            "repo_limit": int(repo_limit),
            "seed_repositories": seed_repos,
        },
        "summary": {
            "repo_count": len(records),
            "downloaded_file_count": int(download_count),
            "allowed_repo_count": sum(1 for row in records if row.get("status") in {"allowed", "allowed_copyleft"}),
            "reference_only_repo_count": sum(1 for row in records if row.get("status") == "reference_only"),
            "blocked_repo_count": sum(1 for row in records if row.get("status") == "blocked"),
            "error_repo_count": sum(1 for row in records if row.get("status") == "error"),
        },
        "repositories": records,
    }
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync open-source xLights/shader assets with license gating.")
    parser.add_argument("--output-root", default="external/open_source_assets", help="Local download root folder.")
    parser.add_argument("--manifest", default="outputs/open_source/assets_manifest.json", help="Manifest JSON path.")
    parser.add_argument("--max-files-per-repo", type=int, default=240, help="File cap per repo after filtering.")
    parser.add_argument("--repo-limit", type=int, default=0, help="Optional max number of seed repos (0 means all).")
    parser.add_argument("--include-copyleft", action="store_true", help="Allow downloading GPL/LGPL/AGPL assets.")
    parser.add_argument("--github-token", default="", help="Optional GitHub token (or set GITHUB_TOKEN).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = str(args.github_token or os.environ.get("GITHUB_TOKEN") or "").strip() or None
    output_root = Path(args.output_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = run_sync(
        output_root=output_root,
        include_copyleft=bool(args.include_copyleft),
        max_files_per_repo=max(1, int(args.max_files_per_repo)),
        repo_limit=max(0, int(args.repo_limit)),
        token=token,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Manifest: {manifest_path}")
    print(f"Downloads: {manifest['summary']['downloaded_file_count']}")
    print(
        "Repos allowed/reference/blocked/error: "
        f"{manifest['summary']['allowed_repo_count']}/"
        f"{manifest['summary']['reference_only_repo_count']}/"
        f"{manifest['summary']['blocked_repo_count']}/"
        f"{manifest['summary']['error_repo_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
