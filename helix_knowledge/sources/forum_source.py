from __future__ import annotations

from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy

from .web_page_source import WebPageSource


class ForumSource(WebPageSource):
    def __init__(
        self,
        *,
        urls: list[str],
        policy: SourcePolicy,
        robots_checker: RobotsChecker,
        rate_limiter: RateLimiter,
    ) -> None:
        super().__init__(
            urls=urls,
            source_type="forum",
            tags=["forum", "community", "xlights"],
            trust_level="medium",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
