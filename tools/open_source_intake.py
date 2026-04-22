from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

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


@dataclass
class RepositoryRecord:
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    license_spdx: str
    updated_at: str
    legal_ok: bool
    legal_reason: str
    category: str


def _license_spdx(item: dict[str, Any]) -> str:
    license_obj = item.get("license")
    if not isinstance(license_obj, dict):
        return ""
    return str(license_obj.get("spdx_id") or "").strip().lower()


def license_status(spdx_id: str) -> tuple[bool, str]:
    if not spdx_id:
        return False, "missing SPDX license in API response"
    if spdx_id in PERMISSIVE_LICENSES:
        return True, "permissive SPDX license"
    return False, f"license not in allowlist ({spdx_id})"


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _search(query: str, *, per_page: int, page: int, token: str | None) -> list[dict[str, Any]]:
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max(1, min(100, int(per_page))),
        "page": max(1, int(page)),
    }
    session = _session()
    try:
        for attempt in range(3):
            try:
                response = session.get(GITHUB_SEARCH_URL, params=params, headers=_headers(token), timeout=30)
                response.raise_for_status()
                payload = response.json()
                items = payload.get("items")
                return items if isinstance(items, list) else []
            except RequestException:
                if attempt >= 2:
                    return []
                time.sleep(1.5 * (attempt + 1))
        return []
    finally:
        session.close()


def collect_repositories(
    *,
    query: str,
    category: str,
    min_stars: int,
    max_results: int,
    token: str | None,
    page_cap: int,
) -> list[RepositoryRecord]:
    out: list[RepositoryRecord] = []
    page = 1
    while len(out) < max_results:
        items = _search(query, per_page=min(100, max_results), page=page, token=token)
        if not items:
            break
        for item in items:
            stars = int(item.get("stargazers_count") or 0)
            if stars < min_stars:
                continue
            spdx = _license_spdx(item)
            legal_ok, legal_reason = license_status(spdx)
            out.append(
                RepositoryRecord(
                    full_name=str(item.get("full_name") or ""),
                    html_url=str(item.get("html_url") or ""),
                    description=str(item.get("description") or ""),
                    stars=stars,
                    forks=int(item.get("forks_count") or 0),
                    language=str(item.get("language") or ""),
                    topics=[str(topic) for topic in (item.get("topics") or []) if isinstance(topic, str)],
                    license_spdx=spdx,
                    updated_at=str(item.get("updated_at") or ""),
                    legal_ok=bool(legal_ok),
                    legal_reason=legal_reason,
                    category=category,
                )
            )
            if len(out) >= max_results:
                break
        page += 1
        if page > max(1, int(page_cap)):
            break
    out.sort(key=lambda row: row.stars, reverse=True)
    return out[:max_results]


def build_manifest(*, min_stars: int, max_results_per_category: int, token: str | None, page_cap: int) -> dict[str, Any]:
    xsq_query = 'xlights xsq extension:xsq OR "xlights sequence"'
    shader_query = 'shader glsl "audio reactive" OR "generative shader"'
    xsq = collect_repositories(
        query=xsq_query,
        category="xsq_sequences",
        min_stars=min_stars,
        max_results=max_results_per_category,
        token=token,
        page_cap=page_cap,
    )
    shaders = collect_repositories(
        query=shader_query,
        category="shaders",
        min_stars=min_stars,
        max_results=max_results_per_category,
        token=token,
        page_cap=page_cap,
    )
    all_rows = xsq + shaders
    return {
        "version": 1,
        "policy": {
            "allowlist_spdx": sorted(PERMISSIVE_LICENSES),
            "minimum_stars": int(min_stars),
            "download_behavior": "metadata_only_no_source_copy",
        },
        "summary": {
            "total_rows": len(all_rows),
            "legal_ok_count": sum(1 for row in all_rows if row.legal_ok),
            "blocked_count": sum(1 for row in all_rows if not row.legal_ok),
        },
        "repositories": [
            {
                "full_name": row.full_name,
                "html_url": row.html_url,
                "description": row.description,
                "stars": row.stars,
                "forks": row.forks,
                "language": row.language,
                "topics": row.topics,
                "license_spdx": row.license_spdx,
                "updated_at": row.updated_at,
                "legal_ok": row.legal_ok,
                "legal_reason": row.legal_reason,
                "category": row.category,
            }
            for row in all_rows
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect open-source XSQ/shader repository metadata with strict license filtering.",
    )
    parser.add_argument("--min-stars", type=int, default=20, help="Minimum star count.")
    parser.add_argument("--limit", type=int, default=30, help="Max repos per category.")
    parser.add_argument("--page-cap", type=int, default=10, help="Max paginated search pages per category.")
    parser.add_argument(
        "--output",
        default="outputs/open_source/open_source_manifest.json",
        help="Output JSON manifest path.",
    )
    parser.add_argument("--github-token", default="", help="Optional GitHub token (or set GITHUB_TOKEN).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = str(args.github_token or os.environ.get("GITHUB_TOKEN") or "").strip() or None
    payload = build_manifest(
        min_stars=max(0, int(args.min_stars)),
        max_results_per_category=max(1, int(args.limit)),
        token=token,
        page_cap=max(1, int(args.page_cap)),
    )
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Open-source manifest written: {out_path}")
    print(f"Legal OK: {payload['summary']['legal_ok_count']} | Blocked: {payload['summary']['blocked_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
