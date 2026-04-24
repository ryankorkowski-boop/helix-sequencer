from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ProvenanceRecord:
    source_type: str
    provenance_note: str
    permission_status: str
    human_review_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
