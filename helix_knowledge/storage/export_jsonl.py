from __future__ import annotations

import json
from pathlib import Path

from .models import TaskCard


def export_taskcards_jsonl(task_cards: list[TaskCard], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for task in task_cards:
            fh.write(json.dumps(task.to_record(), ensure_ascii=False) + "\n")
    return len(task_cards)
