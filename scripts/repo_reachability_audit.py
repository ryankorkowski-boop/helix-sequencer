#!/usr/bin/env python3
"""Static reachability and duplication audit.

Parses Python with the ast module only. It does not import project modules,
so it will not execute core.effect_engine or load audio libraries.

Usage:
    python scripts/repo_reachability_audit.py
    python scripts/repo_reachability_audit.py --json /tmp/repo_audit.json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "archive",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
}
OPERATOR_SEEDS = ("main.py", "gui_launcher.py")
LAUNCHER_EXTRA_SEEDS = ("gui_launcher_drummer.py",)
ALT_ENTRY_SEEDS = ("run_drummer_v3_test.py",)


def iter_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def resolve_module(name: str, root: Path) -> str | None:
    if not name:
        return None
    rel = Path(*name.split("."))
    candidates = [
        root / rel.with_suffix(".py"),
        root / rel / "__init__.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return module_name(candidate, root)
    return None


class FileFacts:
    def __init__(self, path: Path, module: str) -> None:
        self.path = path
        self.module = module
        self.imports: set[str] = set()
        self.unresolved: set[str] = set()
        self.dynamic_modules: set[str] = set()
        self.string_scripts: set[str] = set()
        self.functions: list[dict] = []
        self.duplicate_functions: list[dict] = []
        self.parse_error: str | None = None
        self.loc = 0
        self.has_main = False
        self.has_main_guard = False


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def analyze_file(path: Path, root: Path) -> FileFacts:
    module = module_name(path, root)
    facts = FileFacts(path, module)
    source = path.read_text(encoding="utf-8", errors="replace")
    facts.loc = source.count("\n") + (0 if source.endswith("\n") or not source else 1)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        facts.parse_error = f"{exc.msg} (line {exc.lineno})"
        return facts

    # Top-level function bodies hashed so duplicate defs can be compared.
    top_funcs: dict[str, list[tuple[int, str]]] = defaultdict(list)

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                resolved = resolve_module(alias.name, root)
                if resolved:
                    facts.imports.add(resolved)
                else:
                    facts.unresolved.add(alias.name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level:
                package_parts = module.split(".")
                # from . import x  (level 1) stays in the current package
                # from .. import x climbs one extra package
                if path.name == "__init__.py":
                    base_parts = package_parts
                else:
                    base_parts = package_parts[:-1]
                climb = node.level - 1
                if climb:
                    base_parts = base_parts[:-climb] if climb <= len(base_parts) else []
                prefix = ".".join(base_parts)
                base = f"{prefix}.{node.module}" if node.module and prefix else (node.module or prefix)
            else:
                base = node.module or ""
            if base:
                resolved = resolve_module(base, root)
                if resolved:
                    facts.imports.add(resolved)
                linked_child = False
                # `from pkg import submodule` is a submodule edge even when pkg/__init__.py exists.
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    child = f"{base}.{alias.name}" if base else alias.name
                    child_resolved = resolve_module(child, root)
                    if child_resolved:
                        facts.imports.add(child_resolved)
                        linked_child = True
                if not resolved and not linked_child:
                    facts.unresolved.add(base)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._function(node)

        def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            qual = ".".join(self.scope + [node.name])
            facts.functions.append(
                {
                    "name": node.name,
                    "qual": f"{module}:{qual}" if module else qual,
                    "lineno": node.lineno,
                    "scope": ".".join(self.scope),
                }
            )
            if not self.scope:
                top_funcs[node.name].append((node.lineno, ast.dump(node, include_attributes=False)))
            if node.name == "main" and not self.scope:
                facts.has_main = True
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_If(self, node: ast.If) -> None:
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(isinstance(op, ast.Eq) for op in test.ops)
                and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in test.comparators)
            ):
                facts.has_main_guard = True
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_Call(self, node: ast.Call) -> None:
            name = _call_name(node.func)
            if name in {"import_module", "__import__"} and node.args:
                target = _const_str(node.args[0])
                if target:
                    resolved = resolve_module(target, root)
                    if resolved:
                        facts.dynamic_modules.add(resolved)
                    facts.imports.add(resolved) if resolved else facts.unresolved.add(target)
            if name == "LazyModule" and node.args:
                target = _const_str(node.args[0])
                if target:
                    facts.unresolved.add(f"lazy:{target}")
            self.generic_visit(node)

    Visitor().visit(tree)

    for name, bodies in top_funcs.items():
        if len(bodies) > 1:
            dumps = {body for _lineno, body in bodies}
            facts.duplicate_functions.append(
                {
                    "name": name,
                    "lines": [lineno for lineno, _body in bodies],
                    "bodies_identical": len(dumps) == 1,
                }
            )

    # String literals and Path / "..." joins that name repo python files.
    for node in ast.walk(tree):
        for text in _path_strings(node):
            if not text.endswith(".py"):
                continue
            normalized = text.replace("\\", "/").lstrip("./")
            candidate = (root / normalized).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                candidate = None
            if candidate is None or not candidate.exists():
                matches = list(root.rglob(Path(normalized).name))
                matches = [m for m in matches if ".git" not in m.parts and m.suffix == ".py"]
                candidate = matches[0] if len(matches) == 1 else None
            if candidate is None or not candidate.exists():
                continue
            if any(part in SKIP_DIR_NAMES for part in candidate.parts):
                continue
            facts.string_scripts.add(module_name(candidate, root))
    return facts


def _path_strings(node: ast.AST) -> list[str]:
    """Collect path-shaped string constants, including Path / 'a' / 'b.py' joins."""
    found: list[str] = []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        found.append(node.value)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts = _path_strings(node.left) + _path_strings(node.right)
        if parts:
            found.append("/".join(part.strip("/") for part in parts if part))
    elif isinstance(node, ast.JoinedStr):
        bits: list[str] = []
        static = True
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                bits.append(value.value)
            else:
                static = False
                break
        if static and bits:
            found.append("".join(bits))
    return found


def top_package(module: str) -> str:
    return module.split(".", 1)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static reachability audit (no imports).")
    parser.add_argument("--json", type=Path, help="Write machine-readable summary to this path.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root: Path = args.root

    files = iter_py_files(root)
    facts_by_module: dict[str, FileFacts] = {}
    for path in files:
        facts = analyze_file(path, root)
        facts_by_module[facts.module] = facts

    graph: dict[str, set[str]] = {name: set(facts.imports) | set(facts.dynamic_modules) for name, facts in facts_by_module.items()}
    inbound: dict[str, set[str]] = defaultdict(set)
    for src, deps in graph.items():
        for dep in deps:
            if dep in facts_by_module:
                inbound[dep].add(src)

    string_edges: dict[str, set[str]] = {name: set(facts.string_scripts) for name, facts in facts_by_module.items()}

    operator_seeds = {module_name(root / rel, root) for rel in OPERATOR_SEEDS if (root / rel).exists()}
    operator = _expand_with_strings(operator_seeds, graph, string_edges)

    launcher_seeds = operator_seeds | {module_name(root / rel, root) for rel in LAUNCHER_EXTRA_SEEDS if (root / rel).exists()}
    launcher = _expand_with_strings(launcher_seeds, graph, string_edges)

    alt_seeds = {module_name(root / rel, root) for rel in ALT_ENTRY_SEEDS if (root / rel).exists()}
    alt = _expand_with_strings(alt_seeds, graph, string_edges) if alt_seeds else set()

    test_modules = {name for name in facts_by_module if name.startswith("tests.") or name == "tests"}
    test_closure = _expand_with_strings(test_modules, graph, string_edges)

    tool_entry = {
        name
        for name, facts in facts_by_module.items()
        if (name.startswith("tools.") or name.startswith("scripts.")) and facts.has_main
    }
    tool_closure = _expand_with_strings(tool_entry, graph, string_edges)

    all_modules = set(facts_by_module)
    standalone_entries = sorted(
        name
        for name, facts in facts_by_module.items()
        if facts.has_main_guard and name not in operator and name not in launcher and not name.startswith("tests.")
    )
    referenced = operator | launcher | test_closure | tool_closure
    orphan = sorted(
        name
        for name, facts in facts_by_module.items()
        if name not in referenced
        and not facts.has_main_guard
        and not inbound.get(name)
        and not name.startswith("tests.")
    )
    # Imported by tests and not by the operator/launcher path. May also be imported by tools.
    test_only = sorted(
        name
        for name in all_modules
        if name not in operator
        and name not in launcher
        and name in test_closure
        and not name.startswith("tests.")
        and not name.startswith("tools.")
        and not name.startswith("scripts.")
    )
    test_only_and_tools = sorted(name for name in test_only if name in tool_closure)
    test_only_no_tools = sorted(name for name in test_only if name not in tool_closure)
    tool_only = sorted(
        name
        for name in (tool_closure - operator - launcher)
        if not name.startswith("tests.")
    )

    # Name reference counts across the non-archive tree.
    name_hits: dict[str, int] = defaultdict(int)
    for facts in facts_by_module.values():
        try:
            tree = ast.parse(facts.path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name_hits[node.id] += 1
            elif isinstance(node, ast.Attribute):
                name_hits[node.attr] += 1

    unreferenced_top_funcs: list[dict] = []
    for facts in facts_by_module.values():
        if facts.module.startswith("tests."):
            continue
        seen_names: set[str] = set()
        for fn in facts.functions:
            if fn["scope"]:
                continue
            if fn["name"] in seen_names:
                continue
            seen_names.add(fn["name"])
            if fn["name"].startswith("_") and not fn["name"].startswith("__"):
                # private: count defs vs total hits. A single hit means only the def
                # (the def itself is a Name in some Python versions? FunctionDef is not a Name).
                # ast.FunctionDef does not emit a Name for the function name, so 0 hits
                # means nothing references it. Calls use Name.
                pass
            hits = name_hits.get(fn["name"], 0)
            if hits == 0 and fn["name"] not in {"main"}:
                unreferenced_top_funcs.append(
                    {"module": facts.module, "name": fn["name"], "lineno": fn["lineno"], "hits": hits}
                )

    duplicates = []
    for facts in facts_by_module.values():
        for item in facts.duplicate_functions:
            duplicates.append({"module": facts.module, **item})

    # Same-name top-level functions whose bodies match across modules.
    body_index: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in files:
        facts = facts_by_module[module_name(path, root)]
        if facts.parse_error or facts.module.startswith("tests."):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                digest = ast.dump(node, include_attributes=False)
                body_index[(node.name, digest)].append(f"{facts.module}:{node.lineno}")

    cloned_functions = [
        {"name": name, "sites": sites}
        for (name, _digest), sites in body_index.items()
        if len(sites) > 1 and not name.startswith("__")
    ]
    cloned_functions.sort(key=lambda item: (-len(item["sites"]), item["name"]))

    cycles = []
    for src, deps in graph.items():
        for dep in deps:
            if src in graph.get(dep, ()):
                pair = tuple(sorted((src, dep)))
                if pair not in cycles and src != dep:
                    cycles.append(pair)

    package_loc: dict[str, int] = defaultdict(int)
    package_files: dict[str, int] = defaultdict(int)
    for facts in facts_by_module.values():
        pkg = top_package(facts.module)
        package_loc[pkg] += facts.loc
        package_files[pkg] += 1

    archive_files = list((root / "archive").rglob("*.py")) if (root / "archive").exists() else []
    archive_loc = 0
    for path in archive_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        archive_loc += text.count("\n") + 1

    summary = {
        "root": str(root),
        "python_files_excluding_archive": len(facts_by_module),
        "loc_excluding_archive": sum(facts.loc for facts in facts_by_module.values()),
        "archive_python_files": len(archive_files),
        "archive_loc": archive_loc,
        "parse_errors": [
            {"module": facts.module, "error": facts.parse_error}
            for facts in facts_by_module.values()
            if facts.parse_error
        ],
        "package_loc": dict(sorted(package_loc.items(), key=lambda kv: -kv[1])),
        "package_files": dict(sorted(package_files.items(), key=lambda kv: -kv[1])),
        "operator_module_count": len(operator),
        "operator_modules": sorted(operator),
        "launcher_module_count": len(launcher),
        "launcher_extra_modules": sorted(launcher - operator),
        "alt_entry_modules": sorted(alt),
        "test_only_modules": test_only,
        "test_only_also_tools": test_only_and_tools,
        "test_only_no_tools": test_only_no_tools,
        "tool_only_not_in_operator": tool_only[:250],
        "tool_only_count": len(tool_only),
        "standalone_entrypoints_outside_operator": standalone_entries,
        "orphan_modules": orphan,
        "duplicate_functions": duplicates,
        "cloned_function_count": len(cloned_functions),
        "cloned_functions_top": cloned_functions[:60],
        "unreferenced_top_level_functions": unreferenced_top_funcs,
        "import_cycles": [list(pair) for pair in cycles],
        "dynamic_import_sites": [
            {"module": facts.module, "targets": sorted(facts.dynamic_modules)}
            for facts in facts_by_module.values()
            if facts.dynamic_modules
        ],
    }

    text = json.dumps(summary, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.json}", file=sys.stderr)
    else:
        print(text)
    print(
        f"files={summary['python_files_excluding_archive']} operator={summary['operator_module_count']} "
        f"orphans={len(orphan)} test_only={len(test_only)} duplicate_defs={len(duplicates)} "
        f"unreferenced_funcs={len(unreferenced_top_funcs)} cycles={len(cycles)}",
        file=sys.stderr,
    )
    return 0


def _expand_with_strings(
    seeds: set[str],
    graph: dict[str, set[str]],
    string_edges: dict[str, set[str]],
) -> set[str]:
    seen: set[str] = set()
    stack = list(seeds)
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        deps = set(graph.get(item, ()))
        deps.update(string_edges.get(item, ()))
        for dep in deps:
            if dep not in seen:
                stack.append(dep)
    return seen


if __name__ == "__main__":
    raise SystemExit(main())
