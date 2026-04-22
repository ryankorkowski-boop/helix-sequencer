from __future__ import annotations

from dataclasses import dataclass, field
import re

from .task_classifier import classify_task_text, TaskClassification

_ACTION_PATTERN = re.compile(
    r"\b(to do|click|right click|drag|select|use|set|open|enable|disable|import|export|render|assign|map|create)\b",
    re.IGNORECASE,
)
_WARNING_PATTERN = re.compile(r"\b(common mistake|avoid|if this happens|warning|don['’]t|never)\b", re.IGNORECASE)
_SPLIT_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass(slots=True)
class ExtractedTaskDraft:
    task_name: str
    problem_statement: str
    step_by_step_solution: list[str] = field(default_factory=list)
    common_mistakes: list[str] = field(default_factory=list)
    troubleshooting_notes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    classification: TaskClassification | None = None


def _sentences(text: str) -> list[str]:
    parts = [piece.strip() for piece in _SPLIT_SENTENCE.split(text.strip()) if piece.strip()]
    if not parts:
        return [text.strip()] if text.strip() else []
    return parts


def _guess_task_name(problem_statement: str, category: str) -> str:
    base = problem_statement[:72].strip(" .")
    if base:
        return base
    return f"xLights {category.replace('_', ' ')} guidance"


def extract_task_drafts(text: str) -> list[ExtractedTaskDraft]:
    lines = _sentences(text)
    if not lines:
        return []

    actions = [line for line in lines if _ACTION_PATTERN.search(line)]
    warnings = [line for line in lines if _WARNING_PATTERN.search(line)]

    if not actions and len(lines) > 1:
        actions = lines[1: min(4, len(lines))]
    if not actions:
        actions = lines[:1]

    problem = lines[0]
    classif = classify_task_text(text)

    troubleshooting: list[str] = []
    for line in lines:
        lower = line.lower()
        if "if this happens" in lower or "troubleshoot" in lower or "fix" in lower:
            troubleshooting.append(line)

    confidence = 0.55
    if len(actions) >= 2:
        confidence += 0.15
    if classif.task_category != "best_practices":
        confidence += 0.15
    if warnings:
        confidence += 0.05
    confidence = min(0.98, confidence)

    draft = ExtractedTaskDraft(
        task_name=_guess_task_name(problem, classif.task_category),
        problem_statement=problem,
        step_by_step_solution=actions[:8],
        common_mistakes=warnings[:4],
        troubleshooting_notes=troubleshooting[:5],
        confidence=confidence,
        classification=classif,
    )
    return [draft]
