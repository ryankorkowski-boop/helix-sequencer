"""Layout adapters for AC-safe preview rendering.

Keeps preview logic independent from xLights XML parsing while providing
stable names for models/groups.
"""

from dataclasses import dataclass, field


@dataclass
class PreviewModel:
    name: str
    channels: list[int] = field(default_factory=list)
    group: str | None = None


@dataclass
class PreviewLayout:
    models: dict[str, PreviewModel] = field(default_factory=dict)

    def add_model(self, model: PreviewModel) -> None:
        self.models[model.name] = model

    def targets(self) -> list[str]:
        return list(self.models.keys())

    def resolve(self, name: str) -> PreviewModel | None:
        return self.models.get(name)
