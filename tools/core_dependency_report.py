from __future__ import annotations

import ast
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core"
OUTPUT_PATH = ROOT / "docs" / "core_dependency_graph.md"


def _module_name(path: Path) -> str:
    return path.stem


def _core_files() -> list[Path]:
    return sorted(path for path in CORE_DIR.glob("*.py") if path.is_file())


def _imports_for_file(path: Path, known_modules: set[str]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if len(parts) >= 2 and parts[0] == "core" and parts[1] in known_modules:
                    imports.add(parts[1])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("core."):
                parts = node.module.split(".")
                if len(parts) >= 2 and parts[1] in known_modules:
                    imports.add(parts[1])
            if node.module == "core":
                for alias in node.names:
                    if alias.name in known_modules:
                        imports.add(alias.name)
    return imports


def _topological_order(graph: dict[str, set[str]]) -> list[str]:
    indegree: dict[str, int] = {node: 0 for node in graph}
    reverse: dict[str, set[str]] = defaultdict(set)
    for node, deps in graph.items():
        for dep in deps:
            if dep in indegree:
                indegree[node] += 1
                reverse[dep].add(node)
    queue = deque(sorted([node for node, degree in indegree.items() if degree == 0]))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in sorted(reverse.get(node, set())):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(graph):
        remaining = sorted(node for node in graph if node not in order)
        order.extend(remaining)
    return order


def _entrypoint_trace(graph: dict[str, set[str]], start: str) -> list[str]:
    if start not in graph:
        return []
    visited: set[str] = set()
    trace: list[str] = []
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        trace.append(node)
        for dep in sorted(graph.get(node, set()), reverse=True):
            if dep in graph:
                stack.append(dep)
    return trace


def build_report() -> str:
    files = _core_files()
    modules = {_module_name(path) for path in files}
    graph = {module: set() for module in modules}
    for path in files:
        module = _module_name(path)
        graph[module] = _imports_for_file(path, modules)

    topo = _topological_order(graph)
    sequence_trace = ["main.py -> core.sequence_builder -> core.effect_engine"]
    sequence_trace.extend([f"- {name}" for name in _entrypoint_trace(graph, "effect_engine")])

    lines: list[str] = []
    lines.append("# Core Dependency Graph")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- Analyzed `{len(files)}` files under `core/` using static AST import parsing.")
    lines.append("- Edges represent `core.*` import dependencies only.")
    lines.append("")
    lines.append("## Import Graph (Module -> Imports)")
    for module in sorted(graph):
        deps = sorted(graph[module])
        dep_text = ", ".join(deps) if deps else "(none)"
        lines.append(f"- `{module}` -> {dep_text}")
    lines.append("")
    lines.append("## Topological Build Order (Least-dependent first)")
    for idx, module in enumerate(topo, 1):
        lines.append(f"{idx}. `{module}`")
    lines.append("")
    lines.append("## Inferred Execution Order")
    lines.extend(sequence_trace)
    lines.append("")
    lines.append("## High-Risk Core Targets")
    for target in ("effect_engine", "audio_intelligence", "self_improving_scoring", "spatial_mapping_engine"):
        if target in graph:
            deps = ", ".join(sorted(graph[target])) or "(none)"
            lines.append(f"- `{target}` imports: {deps}")
        else:
            lines.append(f"- `{target}` is not present on this branch.")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_report(), encoding="utf-8")
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
