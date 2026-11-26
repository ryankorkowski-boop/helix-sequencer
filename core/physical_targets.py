"""Resolve xLights model rows to their shared physical node ranges."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from core.model_parser import normalize_name

NodeMask = int  # -1 covers the whole root, including unsupported submodel mappings.


def _nodes(element: ET.Element) -> NodeMask:
    if element.get("type", "ranges").lower() != "ranges":
        return -1
    lines = [value for key, value in element.attrib.items() if re.fullmatch(r"line\d+", key, re.I)]
    mask = 0
    for line in lines:
        for token in line.split(","):
            token = token.strip()
            if not token or token == "0":  # Blank buffer cells carry no nodes.
                continue
            match = re.fullmatch(r"([1-9]\d*)(?:\s*-\s*([1-9]\d*))?", token)
            if not match:
                return -1
            start, end = sorted((int(match[1]), int(match[2] or match[1])))
            if end > 1_000_000:
                return -1
            mask |= ((1 << (end - start + 1)) - 1) << (start - 1)
    return mask or -1


class PhysicalTargets:
    """Index layout membership for placement, layer checks and manual protection."""

    def __init__(self, path: Path):
        layout = ET.parse(path).getroot()
        leaves: dict[str, tuple[str, NodeMask]] = {}
        groups: dict[str, list[str]] = {}
        aliases: dict[str, set[str]] = defaultdict(set)
        self.face_definitions: dict[str, tuple[str, ...]] = {}
        self.role_hints: dict[str, tuple[str, ...]] = {}
        self.issues: dict[str, str] = {}
        self.invalid: set[str] = set()

        def register(element: ET.Element, name: str, parent: str = "") -> None:
            hints = [name, element.get("role", "")]
            aliases[normalize_name(name)].add(name)
            for alias in (item for child in element if child.tag.lower() == "aliases" for item in child):
                value = alias.get("name", "").strip()
                if value.lower().startswith("oldname:"):
                    value = value.split(":", 1)[1].strip()
                if value:
                    hints.append(value)
                    aliases[normalize_name(value)].add(name)
                    if parent:
                        aliases[normalize_name(f"{parent}/{value}")].add(name)
            definitions = tuple(
                child.get("Name", child.get("name", "")).strip() for child in element
                if child.tag.lower() == "faceinfo"
            )
            if definitions:
                self.face_definitions[name] = tuple(value for value in definitions if value)
                hints.append("singer")
            self.role_hints[name] = tuple(hints)

        for element in layout.findall("./models/model"):
            root = element.get("name", "").strip()
            if not root:
                continue
            leaves[root] = (root, -1)
            register(element, root)
            for sub in element.findall("subModel"):
                short = sub.get("name", "").strip()
                if short:
                    name = f"{root}/{short}"
                    mask = _nodes(sub)
                    leaves[name] = (root, mask)
                    register(sub, name, root)
                    if mask == -1:
                        self.issues[name] = "unsupported node mapping; protects the whole root"
        for element in layout.findall("./modelGroups/modelGroup"):
            group = element.get("name", "").strip()
            if group:
                groups[group] = [item.strip() for item in element.get("models", "").split(",") if item.strip()]
                register(element, group)

        self._canonical = set(leaves) | set(groups)
        self._aliases = aliases
        self.members: dict[str, frozenset[str]] = {
            name: frozenset({name}) for name in leaves
        }

        def walk(name: str, visiting: set[str]) -> tuple[set[str], set[str]]:
            if name in visiting:
                return set(), {f"cycle at {name}"}
            if name in leaves:
                return {name}, set()
            members: set[str] = set()
            errors: set[str] = set()
            for raw in groups[name]:
                child = self.resolve(raw)
                if child is None:
                    errors.add(f"unresolved or ambiguous member {raw}")
                    continue
                found, failed = walk(child, visiting | {name})
                members.update(found)
                errors.update(failed)
            if not members and not errors:
                errors.add(f"empty group {name}")
            return members, errors

        for group in groups:
            members, errors = walk(group, set())
            self.members[group] = frozenset(members)
            if errors:
                self.invalid.add(group)
                self.issues[group] = "; ".join(sorted(errors))

        # Equivalent node ranges share one set of xLights rows. A large group
        # can span multiple ranges without combining disjoint layer counts.
        masks_by_root: dict[str, dict[str, NodeMask]] = defaultdict(dict)
        for row, members in self.members.items():
            for leaf in members:
                root, mask = leaves[leaf]
                masks_by_root[root][row] = masks_by_root[root].get(row, 0) | mask

        self.rows: dict[str, list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
        for root, masks in masks_by_root.items():
            partitions = {-1}
            for mask in set(masks.values()) - {-1}:
                partitions = {part for old in partitions for part in (old & mask, old & ~mask) if part}
            row_sets = {tuple(sorted(row for row, mask in masks.items() if mask & part)) for part in partitions}
            for row_set in sorted(row_sets):
                for row in row_set:
                    self.rows[row].append((root, row_set))

        self._shared_rows = {row: frozenset(peer for _, peers in sets for peer in peers)
                             for row, sets in self.rows.items()}
        self.leaf_roots = {name: root for name, (root, _) in leaves.items()}

    def resolve(self, name: str) -> str | None:
        if name in self._canonical:
            return name
        matches = self._aliases.get(normalize_name(name), ())
        if len(matches) == 1:
            return next(iter(matches))
        if not matches and "/" in name:
            root, short = name.split("/", 1)
            parent = self.resolve(root)
            if parent is not None and parent != root:
                return self.resolve(f"{parent}/{short}")
        return None

    def shared_rows(self, name: str) -> frozenset[str]:
        return self._shared_rows.get(self.resolve(name), frozenset())
