from __future__ import annotations

from collections import Counter
import re

from .models import TaskCard

_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")


def _tokenize(text: str) -> Counter[str]:
    return Counter(_TOKEN_RE.findall((text or "").lower()))


class KeywordVectorStore:
    """Lightweight keyword scorer used when no external vector DB is configured."""

    def __init__(self) -> None:
        self._index: dict[str, Counter[str]] = {}
        self._cards: dict[str, TaskCard] = {}

    def index(self, task_cards: list[TaskCard]) -> None:
        for card in task_cards:
            text = " ".join(
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
            )
            self._index[card.id] = _tokenize(text)
            self._cards[card.id] = card

    def search(self, query: str, limit: int = 5) -> list[TaskCard]:
        q = _tokenize(query)
        if not q:
            return []

        scored: list[tuple[float, str]] = []
        for task_id, vec in self._index.items():
            overlap = sum(min(vec[token], q[token]) for token in q)
            if overlap <= 0:
                continue
            score = overlap / max(1, sum(q.values()))
            scored.append((score, task_id))

        scored.sort(key=lambda item: (item[0], self._cards[item[1]].confidence_score), reverse=True)
        return [self._cards[item[1]] for item in scored[: max(1, int(limit))]]
