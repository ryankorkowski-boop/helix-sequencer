from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from helix_knowledge.parsing.chunker import chunk_text
from helix_knowledge.parsing.instruction_extractor import extract_task_drafts
from helix_knowledge.parsing.task_classifier import classify_task_text
from helix_knowledge.safety import RateLimiter, RobotsChecker, SourcePolicy
from helix_knowledge.sources import (
    CollectionResult,
    ForumSource,
    GitHubDocsSource,
    LocalFileSource,
    WebPageSource,
    XLightsManualSource,
    YouTubeTranscriptSource,
)
from helix_knowledge.storage import KnowledgeChunk, SQLiteKnowledgeStore, TaskCard
from helix_knowledge.storage.vector_store import KeywordVectorStore


def _default_db_path() -> Path:
    return (Path.cwd() / "outputs" / "knowledge" / "helix_knowledge.db").resolve()


def _summary_from_text(text: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return sentence[:240].strip()


def _console_safe(text: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return str(text).encode(encoding, errors="replace").decode(encoding, errors="replace")


def _infer_prerequisites(text: str) -> list[str]:
    prereqs: list[str] = []
    lowered = text.lower()
    rules = [
        ("controller", "Controller definitions are configured."),
        ("timing", "A timing track exists for the target section."),
        ("layout", "Models are present in layout with valid naming."),
        ("wled", "WLED device is reachable and mapped."),
        ("face", "Face or matrix models are assigned to lyric targets."),
    ]
    for token, statement in rules:
        if token in lowered:
            prereqs.append(statement)
    return prereqs[:4]


def _persist_collection(store: SQLiteKnowledgeStore, result: CollectionResult) -> tuple[int, int]:
    source_count = 0
    chunk_count = 0

    for policy in result.policy_logs:
        store.log_policy_decision(
            url=policy.url,
            source_type=policy.source_type,
            allowed=policy.allowed,
            reason=policy.reason,
        )

    for crawl in result.crawl_logs:
        store.log_crawl(
            url=crawl.url,
            source_type=crawl.source_type,
            status=crawl.status,
            http_status=crawl.http_status,
            notes=crawl.notes,
        )

    for doc in result.documents:
        store.upsert_source(doc.source)
        source_count += 1
        chunks = chunk_text(doc.text, heading=doc.source.title)
        for chunk in chunks:
            record = KnowledgeChunk(
                source_id=doc.source.id,
                raw_excerpt=chunk.text[:1200],
                cleaned_text=chunk.text,
                summary=_summary_from_text(chunk.text),
                heading=chunk.heading,
                confidence=0.45,
            )
            store.add_chunk(record)
            chunk_count += 1

    return source_count, chunk_count


def _collector_from_source(
    source_name: str,
    *,
    urls: list[str],
    policy: SourcePolicy,
    robots_checker: RobotsChecker,
    rate_limiter: RateLimiter,
    github_token: str | None,
):
    if source_name == "xlights_manual":
        return XLightsManualSource(
            urls=urls or None,
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
    if source_name == "xlights_blog":
        default_urls = urls or [
            "https://xlights.org/",
            "https://xlights.org/releases/",
        ]
        return WebPageSource(
            urls=default_urls,
            source_type="xlights_blog",
            tags=["official", "blog", "xlights"],
            trust_level="high",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
    if source_name == "forum":
        return ForumSource(
            urls=urls,
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
    if source_name == "github_docs":
        return GitHubDocsSource(
            repo_urls=urls,
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
            github_token=github_token,
        )
    if source_name == "web_page":
        return WebPageSource(
            urls=urls,
            source_type="web_page",
            tags=["public_web"],
            trust_level="medium",
            policy=policy,
            robots_checker=robots_checker,
            rate_limiter=rate_limiter,
        )
    raise ValueError(f"Unsupported source: {source_name}")


def _infer_source_name(url: str) -> str:
    lowered = url.lower()
    if "manual.xlights.org" in lowered:
        return "xlights_manual"
    if "xlights.org" in lowered:
        return "xlights_blog"
    if "github.com" in lowered:
        return "github_docs"
    if "forum" in lowered:
        return "forum"
    return "web_page"


def command_collect(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    policy = SourcePolicy()
    robots_checker = RobotsChecker()
    rate_limiter = RateLimiter(min_interval_seconds=float(args.min_delay_seconds))

    source_name = args.source
    urls = [str(url).strip() for url in (args.url or []) if str(url).strip()]

    if not source_name and not urls:
        raise SystemExit("collect requires --source or --url")

    collectors = []
    if source_name:
        collectors.append(
            _collector_from_source(
                source_name,
                urls=urls,
                policy=policy,
                robots_checker=robots_checker,
                rate_limiter=rate_limiter,
                github_token=args.github_token,
            )
        )
    else:
        by_source: dict[str, list[str]] = {}
        for url in urls:
            key = _infer_source_name(url)
            by_source.setdefault(key, []).append(url)
        for key, grouped_urls in by_source.items():
            collectors.append(
                _collector_from_source(
                    key,
                    urls=grouped_urls,
                    policy=policy,
                    robots_checker=robots_checker,
                    rate_limiter=rate_limiter,
                    github_token=args.github_token,
                )
            )

    total_sources = 0
    total_chunks = 0
    for collector in collectors:
        result = collector.collect()
        sources_added, chunks_added = _persist_collection(store, result)
        total_sources += sources_added
        total_chunks += chunks_added

    print(f"Knowledge collection complete. Sources added: {total_sources}, chunks added: {total_chunks}")
    print(f"DB: {Path(args.db).resolve()}")
    return 0


def command_import_transcript(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    policy = SourcePolicy()

    transcript_path = Path(args.path).resolve()
    if not transcript_path.exists():
        raise SystemExit(f"Transcript file not found: {transcript_path}")

    source = YouTubeTranscriptSource.from_transcript_file(
        path=transcript_path,
        title=args.title,
        video_url=args.video_url or f"user://transcript/{transcript_path.name}",
        channel_name=args.channel,
        policy=policy,
    )
    result = source.collect()
    sources_added, chunks_added = _persist_collection(store, result)

    print(f"Transcript imported. Sources added: {sources_added}, chunks added: {chunks_added}")
    return 0


def command_import_local(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    policy = SourcePolicy()

    in_path = Path(args.path).resolve()
    if not in_path.exists():
        raise SystemExit(f"Path not found: {in_path}")

    if in_path.is_dir():
        paths = [path for path in sorted(in_path.rglob("*")) if path.is_file()]
    else:
        paths = [in_path]

    source = LocalFileSource(paths=paths, policy=policy)
    result = source.collect()
    sources_added, chunks_added = _persist_collection(store, result)

    print(f"Local import complete. Sources added: {sources_added}, chunks added: {chunks_added}")
    return 0


def command_extract_tasks(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    chunks = store.fetch_chunks(only_unprocessed=True)
    created = 0

    for chunk in chunks:
        drafts = extract_task_drafts(chunk.cleaned_text)
        task_ids: list[str] = []
        for draft in drafts:
            classification = draft.classification or classify_task_text(draft.problem_statement)
            task = TaskCard(
                task_name=draft.task_name,
                task_category=classification.task_category,
                problem_statement=draft.problem_statement,
                step_by_step_solution=draft.step_by_step_solution,
                xlights_area=classification.xlights_area,
                applicable_models=classification.applicable_models,
                applicable_effects=classification.applicable_effects,
                prerequisites=_infer_prerequisites(chunk.cleaned_text),
                common_mistakes=draft.common_mistakes,
                troubleshooting_notes=draft.troubleshooting_notes,
                helix_relevance=classification.helix_relevance,
                source_ids=[chunk.source_id],
                confidence_score=draft.confidence,
                needs_human_review=classification.needs_human_review or draft.confidence < 0.70,
            )
            store.add_task_card(task)
            task_ids.append(task.id)
            created += 1
        if task_ids:
            store.mark_chunk_tasks(chunk.id, task_ids)

    print(f"Task extraction complete. New task cards: {created}")
    return 0


def command_search(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    all_cards = store.fetch_task_cards()
    keyword_store = KeywordVectorStore()
    keyword_store.index(all_cards)

    vector_hits = keyword_store.search(args.query, limit=max(1, int(args.limit)))
    sql_hits = store.search_task_cards(args.query, limit=max(1, int(args.limit)))

    merged: list[TaskCard] = []
    seen: set[str] = set()
    for card in vector_hits + sql_hits:
        if card.id in seen:
            continue
        seen.add(card.id)
        merged.append(card)

    if not merged:
        print("No matching task cards found.")
        return 0

    for idx, card in enumerate(merged[: max(1, int(args.limit))], start=1):
        first_step = card.step_by_step_solution[0] if card.step_by_step_solution else "(no steps captured)"
        print(_console_safe(f"[{idx}] {card.task_name} | category={card.task_category} | confidence={card.confidence_score:.2f}"))
        print(_console_safe(f"    area={card.xlights_area} | source_ids={','.join(card.source_ids)}"))
        print(_console_safe(f"    step1={first_step}"))
        print(_console_safe(f"    helix={card.helix_relevance}"))

    return 0


def command_export_taskcards(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    out_path = Path(args.output_path).resolve()
    count = store.export_task_cards_jsonl(out_path)
    print(f"Exported {count} task cards to {out_path}")
    return 0


def command_review_needed(args: argparse.Namespace) -> int:
    store = SQLiteKnowledgeStore(Path(args.db).resolve())
    cards = store.review_needed()
    if not cards:
        print("No task cards currently flagged for review.")
        return 0

    for idx, card in enumerate(cards[: max(1, int(args.limit))], start=1):
        print(_console_safe(f"[{idx}] {card.id} | {card.task_name} | confidence={card.confidence_score:.2f} | category={card.task_category}"))
        print(_console_safe(f"    reason=needs_human_review | sources={','.join(card.source_ids)}"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lawful xLights instructional knowledge collector for Helix.")
    parser.add_argument(
        "--db",
        default=str(_default_db_path()),
        help="SQLite DB path.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect from supported public sources.")
    collect.add_argument(
        "--source",
        choices=["xlights_manual", "xlights_blog", "forum", "github_docs", "web_page"],
        default="",
        help="Optional explicit source adapter.",
    )
    collect.add_argument("--url", action="append", help="URL to collect (repeatable).")
    collect.add_argument("--github-token", default="", help="Optional GitHub token for API requests.")
    collect.add_argument("--min-delay-seconds", type=float, default=1.5, help="Per-domain crawl delay.")
    collect.set_defaults(func=command_collect)

    import_transcript = subparsers.add_parser("import-transcript", help="Import a user-provided transcript.")
    import_transcript.add_argument("path", help="Path to transcript text file.")
    import_transcript.add_argument("--title", required=True, help="Video/title label for citation.")
    import_transcript.add_argument("--video-url", default="", help="Original video URL (optional but recommended).")
    import_transcript.add_argument("--channel", default="", help="Channel or author name.")
    import_transcript.set_defaults(func=command_import_transcript)

    import_local = subparsers.add_parser("import-local", help="Import local files (txt/md/pdf/json).")
    import_local.add_argument("path", help="File or directory to import.")
    import_local.set_defaults(func=command_import_local)

    extract = subparsers.add_parser("extract-tasks", help="Extract structured task cards from chunks.")
    extract.set_defaults(func=command_extract_tasks)

    search = subparsers.add_parser("search", help="Search task cards.")
    search.add_argument("query", help="Search query.")
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=command_search)

    export = subparsers.add_parser("export-taskcards", help="Export task cards to JSONL.")
    export.add_argument("output_path", help="JSONL output path.")
    export.set_defaults(func=command_export_taskcards)

    review = subparsers.add_parser("review-needed", help="List task cards requiring human review.")
    review.add_argument("--limit", type=int, default=25)
    review.set_defaults(func=command_review_needed)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
