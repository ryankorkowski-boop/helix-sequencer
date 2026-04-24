from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from helix_knowledge.models import TechniqueCard


class TechniqueCardStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS technique_cards (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def save_cards(self, cards: list[TechniqueCard]) -> int:
        with sqlite3.connect(self.path) as conn:
            for card in cards:
                conn.execute(
                    "INSERT OR REPLACE INTO technique_cards (id, title, payload) VALUES (?, ?, ?)",
                    (card.id, card.title, json.dumps(card.to_dict(), sort_keys=True)),
                )
        return len(cards)

    def load_cards(self) -> list[TechniqueCard]:
        with sqlite3.connect(self.path) as conn:
            rows = list(conn.execute("SELECT payload FROM technique_cards ORDER BY title"))
        return [TechniqueCard(**json.loads(row[0])) for row in rows]
