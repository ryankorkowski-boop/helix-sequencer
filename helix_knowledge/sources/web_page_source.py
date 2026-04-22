from __future__ import annotations

import re
from typing import Iterable

import requests

from helix_knowledge.parsing.html_cleaner import clean_html
from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.storage.models import KnowledgeSource

from .base import BaseKnowledgeSource, CollectedDocument, CollectionResult, CrawlLogEntry, PolicyLogEntry

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _extract_title(html: str, fallback: str) -> str:
    match = _TITLE_RE.search(html or "")
    if not match:
        return fallback
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or fallback


class WebPageSource(BaseKnowledgeSource):
    def __init__(
        self,
        *,
        urls: Iterable[str],
        source_type: str = "web_page",
        tags: list[str] | None = None,
        trust_level: str = "medium",
        policy: SourcePolicy,
        robots_checker: RobotsChecker,
        rate_limiter: RateLimiter,
        timeout_seconds: int = 25,
        user_agent: str = "HelixKnowledgeCollector/1.0",
    ) -> None:
        super().__init__(
            source_type=source_type,
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
        self.urls = [str(url).strip() for url in urls if str(url).strip()]
        self.tags = list(tags or [])
        self.trust_level = trust_level
        self.timeout_seconds = max(5, int(timeout_seconds))
        self.user_agent = user_agent

    def collect(self) -> CollectionResult:
        result = CollectionResult()
        for url in self.urls:
            policy_decision = self.policy.evaluate(source_type=self.source_type, url=url)
            result.policy_logs.append(
                PolicyLogEntry(
                    url=url,
                    source_type=self.source_type,
                    allowed=policy_decision.allowed,
                    reason=policy_decision.reason,
                )
            )
            if not policy_decision.allowed:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="blocked_policy", notes=policy_decision.reason)
                )
                continue

            if self.robots_checker is not None:
                robots = self.robots_checker.is_allowed(url)
                if not robots.allowed:
                    result.crawl_logs.append(
                        CrawlLogEntry(url=url, source_type=self.source_type, status="blocked_robots", notes=robots.reason)
                    )
                    continue

            if self.rate_limiter is not None:
                self.rate_limiter.wait(url)

            try:
                response = requests.get(url, timeout=self.timeout_seconds, headers={"User-Agent": self.user_agent})
            except Exception as exc:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="error", notes=str(exc))
                )
                continue

            if response.status_code >= 400:
                result.crawl_logs.append(
                    CrawlLogEntry(
                        url=url,
                        source_type=self.source_type,
                        status="http_error",
                        http_status=response.status_code,
                        notes="request failed",
                    )
                )
                continue

            cleaned = clean_html(response.text)
            if not cleaned:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="empty", http_status=response.status_code)
                )
                continue

            source = KnowledgeSource(
                source_type=self.source_type,
                title=_extract_title(response.text, fallback=url),
                url=url,
                author="",
                date_published="",
                license_hint="",
                robots_allowed=True,
                terms_notes="",
                trust_level=self.trust_level,
                tags=self.tags,
            )
            result.documents.append(CollectedDocument(source=source, text=cleaned, metadata={"http_status": response.status_code}))
            result.crawl_logs.append(
                CrawlLogEntry(url=url, source_type=self.source_type, status="ok", http_status=response.status_code)
            )

        return result
