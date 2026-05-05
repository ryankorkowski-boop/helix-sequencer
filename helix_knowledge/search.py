from __future__ import annotations

from collections import Counter

from helix_knowledge.models import TechniqueCard


def search_cards(cards: list[TechniqueCard], query: str, limit: int = 10) -> list[TechniqueCard]:
    tokens = [token.lower() for token in query.split() if token.strip()]
    if not tokens:
        return cards[:limit]
    scored: list[tuple[int, TechniqueCard]] = []
    for card in cards:
        haystack = " ".join(
            [
                card.title,
                card.category,
                card.strategy,
                card.problem,
                " ".join(card.tags),
                " ".join(card.applicable_prop_types),
            ]
        ).lower()
        counts = Counter(token for token in tokens if token in haystack)
        score = sum(counts.values())
        if score:
            scored.append((score, card))
    scored.sort(key=lambda item: (-item[0], item[1].title))
    return [card for _score, card in scored[:limit]]
