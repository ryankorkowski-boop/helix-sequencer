from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import uuid


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class KnowledgeSource:
    id: str = field(default_factory=lambda: _new_id("src"))
    source_type: str = ""
    title: str = ""
    url: str = ""
    author: str = ""
    date_published: str = ""
    date_collected: str = field(default_factory=utc_now_iso)
    license_hint: str = ""
    robots_allowed: bool = False
    terms_notes: str = ""
    trust_level: str = "medium"
    tags: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, object]:
        row = asdict(self)
        row["tags"] = json.dumps(self.tags)
        return row


@dataclass(slots=True)
class KnowledgeChunk:
    id: str = field(default_factory=lambda: _new_id("chk"))
    source_id: str = ""
    raw_excerpt: str = ""
    cleaned_text: str = ""
    summary: str = ""
    start_time: float | None = None
    end_time: float | None = None
    heading: str = ""
    extracted_tasks: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_record(self) -> dict[str, object]:
        row = asdict(self)
        row["extracted_tasks"] = json.dumps(self.extracted_tasks)
        return row


@dataclass(slots=True)
class TaskCard:
    id: str = field(default_factory=lambda: _new_id("task"))
    task_name: str = ""
    task_category: str = "best_practices"
    problem_statement: str = ""
    step_by_step_solution: list[str] = field(default_factory=list)
    xlights_area: str = "general"
    applicable_models: list[str] = field(default_factory=list)
    applicable_effects: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    common_mistakes: list[str] = field(default_factory=list)
    troubleshooting_notes: list[str] = field(default_factory=list)
    helix_relevance: str = ""
    source_ids: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    needs_human_review: bool = True

    def to_record(self) -> dict[str, object]:
        row = asdict(self)
        for key in (
            "step_by_step_solution",
            "applicable_models",
            "applicable_effects",
            "prerequisites",
            "common_mistakes",
            "troubleshooting_notes",
            "source_ids",
        ):
            row[key] = json.dumps(row[key])
        row["needs_human_review"] = int(bool(self.needs_human_review))
        return row

    @staticmethod
    def from_row(row: dict[str, object]) -> "TaskCard":
        def _load_json(value: object) -> list[str]:
            if isinstance(value, str):
                try:
                    loaded = json.loads(value)
                except Exception:
                    return [value] if value else []
                if isinstance(loaded, list):
                    return [str(item) for item in loaded]
            return []

        return TaskCard(
            id=str(row.get("id") or ""),
            task_name=str(row.get("task_name") or ""),
            task_category=str(row.get("task_category") or "best_practices"),
            problem_statement=str(row.get("problem_statement") or ""),
            step_by_step_solution=_load_json(row.get("step_by_step_solution")),
            xlights_area=str(row.get("xlights_area") or "general"),
            applicable_models=_load_json(row.get("applicable_models")),
            applicable_effects=_load_json(row.get("applicable_effects")),
            prerequisites=_load_json(row.get("prerequisites")),
            common_mistakes=_load_json(row.get("common_mistakes")),
            troubleshooting_notes=_load_json(row.get("troubleshooting_notes")),
            helix_relevance=str(row.get("helix_relevance") or ""),
            source_ids=_load_json(row.get("source_ids")),
            confidence_score=float(row.get("confidence_score") or 0.0),
            needs_human_review=bool(int(row.get("needs_human_review") or 0)),
        )
