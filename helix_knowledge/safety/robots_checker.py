from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests


@dataclass(slots=True)
class RobotsDecision:
    allowed: bool
    reason: str
    robots_url: str


class RobotsChecker:
    def __init__(self, *, user_agent: str = "HelixKnowledgeCollector/1.0", timeout_seconds: int = 15) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = max(1, int(timeout_seconds))
        self._cache: dict[str, tuple[RobotFileParser, str]] = {}

    def is_allowed(self, url: str) -> RobotsDecision:
        parsed = urlparse(url)
        if parsed.scheme in {"", "file"}:
            return RobotsDecision(True, "local source; robots not applicable", "")

        robots_url = self.robots_url_for(url)
        parser, fetch_reason = self._load_parser(robots_url)
        if parser is None:
            return RobotsDecision(False, fetch_reason, robots_url)

        try:
            allowed = parser.can_fetch(self.user_agent, url)
        except Exception as exc:
            return RobotsDecision(False, f"robots parsing failure: {exc}", robots_url)

        if allowed:
            return RobotsDecision(True, "allowed by robots.txt", robots_url)
        return RobotsDecision(False, "disallowed by robots.txt", robots_url)

    @staticmethod
    def robots_url_for(url: str) -> str:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        return urljoin(base, "/robots.txt")

    def _load_parser(self, robots_url: str) -> tuple[RobotFileParser | None, str]:
        if robots_url in self._cache:
            return self._cache[robots_url]

        try:
            response = requests.get(robots_url, timeout=self.timeout_seconds)
        except Exception as exc:
            reason = f"robots fetch failed: {exc}"
            self._cache[robots_url] = (None, reason)
            return (None, reason)

        if response.status_code == 404:
            parser = RobotFileParser()
            parser.parse(["User-agent: *", "Allow: /"])
            reason = "robots.txt missing; treated as allow"
            self._cache[robots_url] = (parser, reason)
            return parser, reason

        if response.status_code >= 400:
            reason = f"robots returned HTTP {response.status_code}"
            self._cache[robots_url] = (None, reason)
            return (None, reason)

        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        reason = "robots loaded"
        self._cache[robots_url] = (parser, reason)
        return parser, reason
