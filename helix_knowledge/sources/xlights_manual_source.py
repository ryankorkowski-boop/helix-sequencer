from __future__ import annotations

from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy

from .web_page_source import WebPageSource

_OFFICIAL_MANUAL_URLS = [
    "https://manual.xlights.org/xlights/",
    "https://manual.xlights.org/xlights/chapters/chapter-3-sequencer/",
    "https://manual.xlights.org/xlights/chapters/chapter-4-layout/",
    "https://manual.xlights.org/xlights/chapters/chapter-5-tools/",
    "https://manual.xlights.org/xlights/chapters/chapter-7-output-to-lights/",
]


class XLightsManualSource(WebPageSource):
    def __init__(
        self,
        *,
        urls: list[str] | None = None,
        policy: SourcePolicy,
        robots_checker: RobotsChecker,
        rate_limiter: RateLimiter,
    ) -> None:
        super().__init__(
            urls=urls or _OFFICIAL_MANUAL_URLS,
            source_type="xlights_manual",
            tags=["official", "manual", "xlights"],
            trust_level="high",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
