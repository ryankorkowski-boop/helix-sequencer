from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from helix_knowledge.parsing.transcript_cleaner import clean_transcript
from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.storage.models import KnowledgeSource

from .base import BaseKnowledgeSource, CollectedDocument, CollectionResult, CrawlLogEntry, PolicyLogEntry


@dataclass(slots=True)
class GitHubRepoTarget:
    owner: str
    repo: str


class GitHubDocsSource(BaseKnowledgeSource):
    def __init__(
        self,
        *,
        repo_urls: list[str],
        policy: SourcePolicy,
        robots_checker: RobotsChecker | None,
        rate_limiter: RateLimiter,
        github_token: str | None = None,
    ) -> None:
        super().__init__(
            source_type="github_docs",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
        self.repo_urls = repo_urls
        self.github_token = (github_token or "").strip() or None

    def collect(self) -> CollectionResult:
        result = CollectionResult()
        for url in self.repo_urls:
            target = self._parse_repo_target(url)
            if target is None:
                result.policy_logs.append(
                    PolicyLogEntry(url=url, source_type=self.source_type, allowed=False, reason="invalid github repo URL")
                )
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="invalid", notes="could not parse owner/repo")
                )
                continue

            repo_meta = self._repo_metadata(target)
            if repo_meta is None:
                result.policy_logs.append(
                    PolicyLogEntry(url=url, source_type=self.source_type, allowed=False, reason="repo metadata fetch failed")
                )
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="error", notes="metadata fetch failed")
                )
                continue

            license_hint = str((repo_meta.get("license") or {}).get("spdx_id") or "").strip().lower()
            policy_decision = self.policy.evaluate(
                source_type=self.source_type,
                url=url,
                license_hint=license_hint,
            )
            result.policy_logs.append(
                PolicyLogEntry(url=url, source_type=self.source_type, allowed=policy_decision.allowed, reason=policy_decision.reason)
            )
            if not policy_decision.allowed:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="blocked_policy", notes=policy_decision.reason)
                )
                continue

            docs = self._fetch_docs(target)
            if not docs:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="empty", notes="no readable docs found")
                )
                continue

            for title, doc_url, text in docs:
                cleaned = clean_transcript(text)
                if not cleaned:
                    continue
                source = KnowledgeSource(
                    source_type=self.source_type,
                    title=title,
                    url=doc_url,
                    author=str(repo_meta.get("full_name") or ""),
                    date_published="",
                    license_hint=license_hint,
                    robots_allowed=True,
                    terms_notes="github docs import",
                    trust_level="medium",
                    tags=["github", "docs", "xlights"],
                )
                result.documents.append(CollectedDocument(source=source, text=cleaned, metadata={"repo": str(repo_meta.get("full_name") or "")}))
            result.crawl_logs.append(CrawlLogEntry(url=url, source_type=self.source_type, status="ok"))

        return result

    def _repo_metadata(self, target: GitHubRepoTarget) -> dict[str, Any] | None:
        endpoint = f"https://api.github.com/repos/{target.owner}/{target.repo}"
        data = self._get_json(endpoint)
        return data if isinstance(data, dict) else None

    def _fetch_docs(self, target: GitHubRepoTarget) -> list[tuple[str, str, str]]:
        docs: list[tuple[str, str, str]] = []

        readme_endpoint = f"https://api.github.com/repos/{target.owner}/{target.repo}/readme"
        readme_payload = self._get_json(readme_endpoint)
        if isinstance(readme_payload, dict):
            decoded = self._decode_content(readme_payload)
            if decoded:
                docs.append((f"{target.owner}/{target.repo} README", str(readme_payload.get("html_url") or ""), decoded))

        docs_endpoint = f"https://api.github.com/repos/{target.owner}/{target.repo}/contents/docs"
        docs_payload = self._get_json(docs_endpoint)
        if isinstance(docs_payload, list):
            for row in docs_payload[:20]:
                if not isinstance(row, dict):
                    continue
                path = str(row.get("path") or "")
                if not path.lower().endswith((".md", ".rst", ".txt")):
                    continue
                file_payload = self._get_json(str(row.get("url") or ""))
                if not isinstance(file_payload, dict):
                    continue
                decoded = self._decode_content(file_payload)
                if not decoded:
                    continue
                docs.append((f"{target.owner}/{target.repo}:{path}", str(row.get("html_url") or ""), decoded))

        return docs

    def _get_json(self, url: str) -> Any:
        if not url:
            return None
        if self.rate_limiter is not None:
            self.rate_limiter.wait(url)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "HelixKnowledgeCollector/1.0",
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        try:
            response = requests.get(url, timeout=25, headers=headers)
        except Exception:
            return None
        if response.status_code >= 400:
            return None
        try:
            return response.json()
        except Exception:
            return None

    @staticmethod
    def _decode_content(payload: dict[str, Any]) -> str:
        encoding = str(payload.get("encoding") or "").lower()
        raw = payload.get("content")
        if not isinstance(raw, str) or not raw.strip():
            return ""
        if encoding == "base64":
            try:
                return base64.b64decode(raw).decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return raw

    @staticmethod
    def _parse_repo_target(url: str) -> GitHubRepoTarget | None:
        parsed = urlparse(url)
        if "github.com" not in (parsed.netloc or "").lower():
            return None
        parts = [part for part in (parsed.path or "").split("/") if part]
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        if not owner or not repo:
            return None
        return GitHubRepoTarget(owner=owner, repo=repo)
