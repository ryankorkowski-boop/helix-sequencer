from __future__ import annotations

import json
import re
from pathlib import Path

from helix_knowledge.parsing.transcript_cleaner import clean_transcript
from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.storage.models import KnowledgeSource

from .base import BaseKnowledgeSource, CollectedDocument, CollectionResult, CrawlLogEntry, PolicyLogEntry


def _clean_markdown(text: str) -> str:
    cleaned = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\1", cleaned)
    cleaned = re.sub(r"\r", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class LocalFileSource(BaseKnowledgeSource):
    def __init__(
        self,
        *,
        paths: list[Path],
        source_type: str = "local_file",
        policy: SourcePolicy,
        robots_checker: RobotsChecker | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(
            source_type=source_type,
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
        self.paths = [Path(path).resolve() for path in paths]

    def collect(self) -> CollectionResult:
        result = CollectionResult()
        for path in self.paths:
            url = str(path)
            policy_decision = self.policy.evaluate(
                source_type=self.source_type,
                url=url,
                is_user_provided=True,
            )
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

            if not path.exists() or not path.is_file():
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="missing", notes="file does not exist")
                )
                continue

            suffix = path.suffix.lower()
            try:
                text = self._read_file(path)
            except Exception as exc:
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="error", notes=str(exc))
                )
                continue

            if not text.strip():
                result.crawl_logs.append(
                    CrawlLogEntry(url=url, source_type=self.source_type, status="empty", notes="no readable text")
                )
                continue

            if suffix in {".md", ".markdown", ".rst"}:
                text = _clean_markdown(text)
            else:
                text = clean_transcript(text)

            source = KnowledgeSource(
                source_type=self.source_type,
                title=path.name,
                url=url,
                author="user_provided",
                date_published="",
                license_hint="user_provided",
                robots_allowed=True,
                terms_notes="local import",
                trust_level="medium",
                tags=["local", suffix.lstrip(".")],
            )
            result.documents.append(CollectedDocument(source=source, text=text, metadata={"path": str(path)}))
            result.crawl_logs.append(CrawlLogEntry(url=url, source_type=self.source_type, status="ok"))

        return result

    @staticmethod
    def _read_file(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".markdown", ".rst", ".log", ".csv"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            return json.dumps(payload, indent=2)
        if suffix == ".pdf":
            return LocalFileSource._read_pdf(path)
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            import pypdf  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"PDF import needs pypdf installed: {exc}") from exc

        reader = pypdf.PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages).strip()
