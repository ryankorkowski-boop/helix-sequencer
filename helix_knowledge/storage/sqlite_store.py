from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .models import KnowledgeChunk, KnowledgeSource, TaskCard


class SQLiteKnowledgeStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    author TEXT,
                    date_published TEXT,
                    date_collected TEXT,
                    license_hint TEXT,
                    robots_allowed INTEGER,
                    terms_notes TEXT,
                    trust_level TEXT,
                    tags TEXT
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    raw_excerpt TEXT,
                    cleaned_text TEXT,
                    summary TEXT,
                    start_time REAL,
                    end_time REAL,
                    heading TEXT,
                    extracted_tasks TEXT,
                    confidence REAL,
                    FOREIGN KEY(source_id) REFERENCES sources(id)
                );

                CREATE TABLE IF NOT EXISTS task_cards (
                    id TEXT PRIMARY KEY,
                    task_name TEXT,
                    task_category TEXT,
                    problem_statement TEXT,
                    step_by_step_solution TEXT,
                    xlights_area TEXT,
                    applicable_models TEXT,
                    applicable_effects TEXT,
                    prerequisites TEXT,
                    common_mistakes TEXT,
                    troubleshooting_notes TEXT,
                    helix_relevance TEXT,
                    source_ids TEXT,
                    confidence_score REAL,
                    needs_human_review INTEGER
                );

                CREATE TABLE IF NOT EXISTS crawl_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    source_type TEXT,
                    status TEXT,
                    http_status INTEGER,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS source_policy_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    source_type TEXT,
                    allowed INTEGER,
                    reason TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                """
            )

    def upsert_source(self, source: KnowledgeSource) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sources (
                    id, source_type, title, url, author, date_published, date_collected,
                    license_hint, robots_allowed, terms_notes, trust_level, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_type=excluded.source_type,
                    title=excluded.title,
                    url=excluded.url,
                    author=excluded.author,
                    date_published=excluded.date_published,
                    date_collected=excluded.date_collected,
                    license_hint=excluded.license_hint,
                    robots_allowed=excluded.robots_allowed,
                    terms_notes=excluded.terms_notes,
                    trust_level=excluded.trust_level,
                    tags=excluded.tags
                """,
                (
                    source.id,
                    source.source_type,
                    source.title,
                    source.url,
                    source.author,
                    source.date_published,
                    source.date_collected,
                    source.license_hint,
                    int(bool(source.robots_allowed)),
                    source.terms_notes,
                    source.trust_level,
                    json.dumps(source.tags),
                ),
            )

    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    id, source_id, raw_excerpt, cleaned_text, summary,
                    start_time, end_time, heading, extracted_tasks, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    chunk.source_id,
                    chunk.raw_excerpt,
                    chunk.cleaned_text,
                    chunk.summary,
                    chunk.start_time,
                    chunk.end_time,
                    chunk.heading,
                    json.dumps(chunk.extracted_tasks),
                    float(chunk.confidence),
                ),
            )

    def mark_chunk_tasks(self, chunk_id: str, task_ids: list[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE chunks SET extracted_tasks = ? WHERE id = ?",
                (json.dumps(task_ids), chunk_id),
            )

    def add_task_card(self, task: TaskCard) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO task_cards (
                    id, task_name, task_category, problem_statement, step_by_step_solution,
                    xlights_area, applicable_models, applicable_effects, prerequisites,
                    common_mistakes, troubleshooting_notes, helix_relevance, source_ids,
                    confidence_score, needs_human_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.task_name,
                    task.task_category,
                    task.problem_statement,
                    json.dumps(task.step_by_step_solution),
                    task.xlights_area,
                    json.dumps(task.applicable_models),
                    json.dumps(task.applicable_effects),
                    json.dumps(task.prerequisites),
                    json.dumps(task.common_mistakes),
                    json.dumps(task.troubleshooting_notes),
                    task.helix_relevance,
                    json.dumps(task.source_ids),
                    float(task.confidence_score),
                    int(bool(task.needs_human_review)),
                ),
            )

    def log_crawl(self, *, url: str, source_type: str, status: str, http_status: int | None, notes: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO crawl_log (url, source_type, status, http_status, notes) VALUES (?, ?, ?, ?, ?)",
                (url, source_type, status, http_status, notes),
            )

    def log_policy_decision(self, *, url: str, source_type: str, allowed: bool, reason: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO source_policy_decisions (url, source_type, allowed, reason) VALUES (?, ?, ?, ?)",
                (url, source_type, int(bool(allowed)), reason),
            )

    def fetch_chunks(self, *, only_unprocessed: bool = False) -> list[KnowledgeChunk]:
        query = "SELECT * FROM chunks"
        if only_unprocessed:
            query += " WHERE extracted_tasks IS NULL OR extracted_tasks = '' OR extracted_tasks = '[]'"
        query += " ORDER BY rowid ASC"
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        out: list[KnowledgeChunk] = []
        for row in rows:
            task_json = row["extracted_tasks"] or "[]"
            try:
                task_ids = json.loads(task_json)
            except Exception:
                task_ids = []
            if not isinstance(task_ids, list):
                task_ids = []
            out.append(
                KnowledgeChunk(
                    id=str(row["id"]),
                    source_id=str(row["source_id"]),
                    raw_excerpt=str(row["raw_excerpt"] or ""),
                    cleaned_text=str(row["cleaned_text"] or ""),
                    summary=str(row["summary"] or ""),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    heading=str(row["heading"] or ""),
                    extracted_tasks=[str(item) for item in task_ids],
                    confidence=float(row["confidence"] or 0.0),
                )
            )
        return out

    def fetch_sources(self) -> dict[str, KnowledgeSource]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM sources").fetchall()
        out: dict[str, KnowledgeSource] = {}
        for row in rows:
            try:
                tags = json.loads(row["tags"] or "[]")
            except Exception:
                tags = []
            if not isinstance(tags, list):
                tags = []
            src = KnowledgeSource(
                id=str(row["id"]),
                source_type=str(row["source_type"]),
                title=str(row["title"] or ""),
                url=str(row["url"] or ""),
                author=str(row["author"] or ""),
                date_published=str(row["date_published"] or ""),
                date_collected=str(row["date_collected"] or ""),
                license_hint=str(row["license_hint"] or ""),
                robots_allowed=bool(int(row["robots_allowed"] or 0)),
                terms_notes=str(row["terms_notes"] or ""),
                trust_level=str(row["trust_level"] or "medium"),
                tags=[str(item) for item in tags],
            )
            out[src.id] = src
        return out

    def fetch_task_cards(self) -> list[TaskCard]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM task_cards ORDER BY rowid ASC").fetchall()
        return [TaskCard.from_row(dict(row)) for row in rows]

    def review_needed(self) -> list[TaskCard]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM task_cards WHERE needs_human_review = 1 ORDER BY confidence_score ASC").fetchall()
        return [TaskCard.from_row(dict(row)) for row in rows]

    def search_task_cards(self, query: str, limit: int = 10) -> list[TaskCard]:
        needle = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM task_cards
                WHERE task_name LIKE ?
                   OR task_category LIKE ?
                   OR problem_statement LIKE ?
                   OR step_by_step_solution LIKE ?
                   OR xlights_area LIKE ?
                   OR helix_relevance LIKE ?
                   OR applicable_models LIKE ?
                   OR applicable_effects LIKE ?
                ORDER BY confidence_score DESC
                LIMIT ?
                """,
                (needle, needle, needle, needle, needle, needle, needle, needle, max(1, int(limit))),
            ).fetchall()
        exact = [TaskCard.from_row(dict(row)) for row in rows]
        if exact:
            return exact

        tokens = [token for token in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(token) >= 2]
        if not tokens:
            return []

        scored: list[tuple[float, TaskCard]] = []
        for card in self.fetch_task_cards():
            haystack = " ".join(
                [
                    card.task_name,
                    card.task_category,
                    card.problem_statement,
                    " ".join(card.step_by_step_solution),
                    card.xlights_area,
                    card.helix_relevance,
                    " ".join(card.applicable_models),
                    " ".join(card.applicable_effects),
                ]
            ).lower()
            score = sum(1 for token in tokens if token in haystack)
            if score <= 0:
                continue
            scored.append((float(score), card))

        scored.sort(key=lambda row: (row[0], row[1].confidence_score), reverse=True)
        return [row[1] for row in scored[: max(1, int(limit))]]

    def export_task_cards_jsonl(self, path: Path) -> int:
        cards = self.fetch_task_cards()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for card in cards:
                fh.write(json.dumps(card.to_record(), ensure_ascii=False) + "\n")
        return len(cards)

    def count_table(self, table_name: str) -> int:
        if table_name not in {"sources", "chunks", "task_cards", "crawl_log", "source_policy_decisions"}:
            raise ValueError(f"Unsupported table name: {table_name}")
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"] if row else 0)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "db_path": str(self.db_path),
            "sources": self.count_table("sources"),
            "chunks": self.count_table("chunks"),
            "task_cards": self.count_table("task_cards"),
            "crawl_log": self.count_table("crawl_log"),
            "source_policy_decisions": self.count_table("source_policy_decisions"),
        }
