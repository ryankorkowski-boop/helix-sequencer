"""Parse xLights custom-model node grids.

``CustomModel`` is the human-readable grid from ``XmlSerialize::ParseCustomModel``:
layers are separated by ``|``, rows by ``;``, and cells by ``,``. A cell value is a
1-based node number. Blank cells and values ``<= 0`` are empty. xLights reads
``CustomModelCompressed`` first when that attribute is non-empty
(``ParseCustomModelDataFromXml``). The compressed form is
``node,row,col`` or ``node,row,col,layer``, with 0-based indexes, and only lists
cells that exist.

Node order follows ``InitCustomMatrix``: one pixel per node number, sorted by
that number. Duplicate numbers keep the first cell. Positions are the cell
centers mapped into the model's world bounds (``WorldPos`` through ``WorldPos``
plus ``X2``/``Y2``/``Z2``). Row 0 is the top of the grid, matching xLights
``screenY = centerRow - row``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CustomNode:
    number: int
    column: int
    row: int
    layer: int


@dataclass(frozen=True)
class CustomGrid:
    nodes: tuple[CustomNode, ...]
    width: int
    height: int
    depth: int
    source: str


def parse_custom_model_attributes(attrs: Mapping[str, str]) -> CustomGrid | None:
    compressed = (attrs.get("CustomModelCompressed") or "").strip()
    plain = (attrs.get("CustomModel") or "").strip()
    if compressed:
        width, height, depth, cells = _parse_compressed(compressed)
        return _grid(cells, width, height, depth, "CustomModelCompressed")
    if plain:
        width, height, depth, cells = _parse_plain(plain)
        return _grid(cells, width, height, depth, "CustomModel")
    return None


def pixels_in_world_bounds(model: object) -> list[object]:
    from core.model_parser import PixelPoint

    origin = getattr(model, "coordinates", None) or (0.0, 0.0, 0.0)
    end = getattr(model, "end_coordinates", None) or origin
    span = (end[0] - origin[0], end[1] - origin[1], end[2] - origin[2])
    width = max(1, int(getattr(model, "grid_width", 1) or 1))
    height = max(1, int(getattr(model, "grid_height", 1) or 1))
    depth = max(1, int(getattr(model, "grid_depth", 1) or 1))
    pixels: list[PixelPoint] = []
    for node in list(getattr(model, "custom_nodes", []) or []):
        x = origin[0] + (node.column + 0.5) / width * span[0]
        y = origin[1] + span[1] - (node.row + 0.5) / height * span[1]
        z = origin[2] + (node.layer + 0.5) / depth * span[2]
        pixels.append(
            PixelPoint(
                index=node.number - 1,
                x=x,
                y=y,
                z=z,
                string_index=node.layer,
                node_index=node.number - 1,
            )
        )
    return pixels


def _grid(
    cells: list[tuple[int, int, int, int]],
    width: int,
    height: int,
    depth: int,
    source: str,
) -> CustomGrid:
    first: dict[int, tuple[int, int, int]] = {}
    for layer, row, column, value in cells:
        if value <= 0:
            continue
        first.setdefault(value, (column, row, layer))
    nodes = tuple(
        CustomNode(number=number, column=column, row=row, layer=layer)
        for number, (column, row, layer) in sorted(first.items())
    )
    return CustomGrid(
        nodes=nodes,
        width=max(1, width),
        height=max(1, height),
        depth=max(1, depth),
        source=source,
    )


def _parse_plain(custom_model: str) -> tuple[int, int, int, list[tuple[int, int, int, int]]]:
    layers = custom_model.split("|")
    parsed_layers: list[list[list[int]]] = []
    width = 1
    height = 1
    for layer_text in layers:
        rows = layer_text.split(";")
        height = max(height, len(rows))
        parsed_rows: list[list[int]] = []
        for row_text in rows:
            columns = row_text.split(",") if row_text != "" or "," in layer_text else [row_text]
            if row_text == "" and len(rows) == 1 and "," not in custom_model and "|" not in custom_model:
                columns = [row_text]
            width = max(width, len(columns))
            values: list[int] = []
            for column in columns:
                token = column.strip()
                if not token:
                    values.append(-1)
                    continue
                try:
                    values.append(int(token, 10))
                except ValueError:
                    values.append(-1)
            parsed_rows.append(values)
        parsed_layers.append(parsed_rows)
    cells: list[tuple[int, int, int, int]] = []
    for layer_index, rows in enumerate(parsed_layers):
        for row_index, columns in enumerate(rows):
            for column_index, value in enumerate(columns):
                cells.append((layer_index, row_index, column_index, value))
    return width, height, len(parsed_layers) or 1, cells


def _parse_compressed(compressed: str) -> tuple[int, int, int, list[tuple[int, int, int, int]]]:
    cells: list[tuple[int, int, int, int]] = []
    max_row = 0
    max_column = 0
    max_layer = 0
    for chunk in compressed.split(";"):
        token = chunk.strip()
        if not token:
            continue
        parts = [part.strip() for part in token.split(",")]
        if len(parts) not in {3, 4}:
            continue
        try:
            number = int(parts[0], 10)
            row = int(parts[1], 10)
            column = int(parts[2], 10)
            layer = int(parts[3], 10) if len(parts) == 4 else 0
        except ValueError:
            continue
        cells.append((layer, row, column, number))
        max_row = max(max_row, row)
        max_column = max(max_column, column)
        max_layer = max(max_layer, layer)
    if not cells:
        return 1, 1, 1, []
    return max_column + 1, max_row + 1, max_layer + 1, cells
