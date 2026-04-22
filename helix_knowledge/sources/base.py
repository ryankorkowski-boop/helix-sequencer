from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.storage.models import KnowledgeSource


@dataclass(slots=True)
class CollectedDocument:
    source: KnowledgeSource
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PolicyLogEntry:
    url: str
    source_type: str
    allowed: bool
    reason: str


@dataclass(slots=True)
class CrawlLogEntry:
    url: str
    source_type: str
    status: str
    http_status: int | None = None
    notes: str = ""


@dataclass(slots=True)
class CollectionResult:
    documents: list[CollectedDocument] = field(default_factory=list)
    policy_logs: list[PolicyLogEntry] = field(default_factory=list)
    crawl_logs: list[CrawlLogEntry] = field(default_factory=list)


class BaseKnowledgeSource(ABC):
    def __init__(
        self,
        *,
        source_type: str,
        policy: SourcePolicy,
        robots_checker: RobotsChecker | None,
        rate_limiter: RateLimiter | None,
    ) -> None:
        self.source_type = source_type
        self.policy = policy
        self.robots_checker = robots_checker
        self.rate_limiter = rate_limiter

    @abstractmethod
    def collect(self) -> CollectionResult:
        raise NotImplementedError
