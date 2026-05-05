from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MotifMemory:
    motifs_by_role: dict[str, list[str]] = field(default_factory=dict)

    def remember(self, role: str, motif: str) -> None:
        self.motifs_by_role.setdefault(role, [])
        if motif not in self.motifs_by_role[role]:
            self.motifs_by_role[role].append(motif)

    def recall(self, role: str) -> list[str]:
        return list(self.motifs_by_role.get(role, []))
