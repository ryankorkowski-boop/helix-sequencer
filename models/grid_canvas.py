from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


Coord = tuple[int, int]


@dataclass(frozen=True)
class GridCanvas:
    width: int
    height: int
    origin_mode: str = "top_left"
    coordinate_system: str = "integer_grid_xy"
    layers: list[str] = field(default_factory=lambda: ["body", "mouth", "instrument"])

    def contains(self, coord: Coord) -> bool:
        x, y = coord
        return 0 <= x < self.width and 0 <= y < self.height

    def node_id(self, coord: Coord) -> int:
        x, y = coord
        return (y * self.width) + x + 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class PixelRegion:
    name: str
    category: str
    coordinates: list[Coord]
    node_ids: list[int] = field(default_factory=list)
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)
    center_point: tuple[float, float] = (0.0, 0.0)
    pivot_point: tuple[float, float] | None = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_coords(
        cls,
        name: str,
        category: str,
        coords: Iterable[Coord],
        canvas: GridCanvas,
        *,
        tags: Iterable[str] = (),
        pivot_point: tuple[float, float] | None = None,
    ) -> "PixelRegion":
        clean = sorted({(int(x), int(y)) for x, y in coords if canvas.contains((int(x), int(y)))})
        if clean:
            xs = [x for x, _ in clean]
            ys = [y for _, y in clean]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            center = (sum(xs) / len(xs), sum(ys) / len(ys))
        else:
            bbox = (0, 0, 0, 0)
            center = (0.0, 0.0)
        return cls(
            name=name,
            category=category,
            coordinates=clean,
            node_ids=[canvas.node_id(coord) for coord in clean],
            bounding_box=bbox,
            center_point=(round(center[0], 3), round(center[1], 3)),
            pivot_point=pivot_point,
            tags=list(tags),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "category": self.category,
            "coordinates": [[x, y] for x, y in self.coordinates],
            "node_ids": self.node_ids,
            "bounding_box": list(self.bounding_box),
            "center_point": list(self.center_point),
            "pivot_point": list(self.pivot_point) if self.pivot_point is not None else None,
            "tags": self.tags,
        }


@dataclass
class MouthShapeTemplate:
    name: str
    phoneme_aliases: list[str]
    coordinates: list[Coord]
    bounding_box: tuple[int, int, int, int]
    style_tags: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phoneme_aliases": self.phoneme_aliases,
            "coordinates": [[x, y] for x, y in self.coordinates],
            "bounding_box": list(self.bounding_box),
            "style_tags": self.style_tags,
        }


@dataclass
class SubmodelTemplate:
    name: str
    category: str
    included_regions: list[str]
    included_coordinates: list[Coord]
    sequencing_tags: list[str]
    audio_stem_tags: list[str]
    export_grouping_metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "category": self.category,
            "included_regions": self.included_regions,
            "included_coordinates": [[x, y] for x, y in self.included_coordinates],
            "sequencing_tags": self.sequencing_tags,
            "audio_stem_tags": self.audio_stem_tags,
            "export_grouping_metadata": self.export_grouping_metadata,
        }


@dataclass
class DrawableModelTemplate:
    id: str
    display_name: str
    canvas: GridCanvas
    base_regions: dict[str, PixelRegion]
    mouth_regions: dict[str, PixelRegion]
    submodels: dict[str, SubmodelTemplate]
    overlay_rules: list[dict[str, object]]
    export_metadata: dict[str, object]

    def all_regions(self) -> dict[str, PixelRegion]:
        return {**self.base_regions, **self.mouth_regions}

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "canvas": self.canvas.to_dict(),
            "base_regions": {name: region.to_dict() for name, region in self.base_regions.items()},
            "mouth_regions": {name: region.to_dict() for name, region in self.mouth_regions.items()},
            "submodels": {name: submodel.to_dict() for name, submodel in self.submodels.items()},
            "overlay_rules": self.overlay_rules,
            "export_metadata": self.export_metadata,
        }
