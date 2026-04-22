from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from helix_knowledge.parsing.transcript_cleaner import clean_transcript
from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.storage.models import KnowledgeSource

from .base import BaseKnowledgeSource, CollectedDocument, CollectionResult, CrawlLogEntry, PolicyLogEntry


@dataclass(slots=True)
class TranscriptItem:
    title: str
    video_url: str
    channel_name: str
    transcript_text: str
    official_api: bool = False
    user_provided: bool = True


class YouTubeTranscriptSource(BaseKnowledgeSource):
    def __init__(
        self,
        *,
        items: list[TranscriptItem],
        policy: SourcePolicy,
        robots_checker: RobotsChecker | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(
            source_type="youtube_transcript",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
        self.items = items

    @classmethod
    def from_transcript_file(
        cls,
        *,
        path: Path,
        title: str,
        video_url: str,
        channel_name: str,
        policy: SourcePolicy,
    ) -> "YouTubeTranscriptSource":
        text = path.read_text(encoding="utf-8", errors="ignore")
        item = TranscriptItem(
            title=title,
            video_url=video_url,
            channel_name=channel_name,
            transcript_text=text,
            official_api=False,
            user_provided=True,
        )
        return cls(items=[item], policy=policy)

    def collect(self) -> CollectionResult:
        result = CollectionResult()
        for item in self.items:
            policy_decision = self.policy.evaluate(
                source_type=self.source_type,
                url=item.video_url,
                title=item.title,
                is_user_provided=item.user_provided,
                via_official_api=item.official_api,
            )
            result.policy_logs.append(
                PolicyLogEntry(
                    url=item.video_url,
                    source_type=self.source_type,
                    allowed=policy_decision.allowed,
                    reason=policy_decision.reason,
                )
            )
            if not policy_decision.allowed:
                result.crawl_logs.append(
                    CrawlLogEntry(
                        url=item.video_url,
                        source_type=self.source_type,
                        status="blocked_policy",
                        notes=policy_decision.reason,
                    )
                )
                continue

            cleaned = clean_transcript(item.transcript_text)
            if not cleaned:
                result.crawl_logs.append(
                    CrawlLogEntry(url=item.video_url, source_type=self.source_type, status="empty")
                )
                continue

            source = KnowledgeSource(
                source_type=self.source_type,
                title=item.title or "YouTube Transcript",
                url=item.video_url,
                author=item.channel_name,
                date_published="",
                license_hint="youtube_transcript_user_provided" if item.user_provided else "youtube_transcript_api",
                robots_allowed=True,
                terms_notes="transcript import only; no media download",
                trust_level="medium",
                tags=["youtube", "transcript", "official_api" if item.official_api else "user_provided"],
            )
            result.documents.append(
                CollectedDocument(
                    source=source,
                    text=cleaned,
                    metadata={
                        "official_api": item.official_api,
                        "user_provided": item.user_provided,
                    },
                )
            )
            result.crawl_logs.append(CrawlLogEntry(url=item.video_url, source_type=self.source_type, status="ok"))

        return result
