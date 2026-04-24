#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import stat as statmod
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TARGET_FOLDERS = {
    "aaa",
    "q",
    "qqq",
    "bbb",
    "cod",
    "gen",
    "gptseq",
    "seq",
    "show",
    "x",
    "xlights_auto",
    "z",
}

PROJECT_KEYWORDS = (
    "helix",
    "dream",
    "sequence",
    "sequencer",
    "weaver",
    "lightweaver",
    "seqgen",
    "pixelbuilder",
    "xlights",
    "gptseq",
    "auto",
)

OLD_REFERENCE_TERMS = (
    "Dream Sequence Weaver",
    "dream_sequence_weaver",
    "DreamSequenceWeaver",
    "Helix Sequence Weaver",
    "helix_sequence_weaver",
    "HelixSequenceWeaver",
    "Sequence Weaver",
    "sequence_weaver",
    "LightWeaver",
    "SeqGen",
    "PixelBuilder",
    "gptseq",
    "xlights_auto",
)

INVENTORY_EXTENSIONS = {
    ".xsq",
    ".mp3",
    ".mp4",
    ".exe",
    ".py",
    ".json",
    ".xml",
    ".fseq",
    ".txt",
    ".md",
    ".log",
    ".cmd",
    ".ps1",
    ".vbs",
    ".spec",
    ".yml",
    ".yaml",
    ".xmodel",
    ".xbkp",
}

HASH_EXTENSIONS = {
    ".xsq",
    ".mp3",
    ".mp4",
    ".exe",
    ".fseq",
    ".xml",
    ".json",
    ".py",
    ".md",
    ".txt",
    ".log",
    ".xmodel",
    ".xbkp",
}

PRIORITY_HASH_EXTENSIONS = {
    ".xsq",
    ".mp3",
    ".mp4",
    ".exe",
    ".fseq",
    ".xml",
    ".json",
}

HASH_PRIORITY = {
    ".xsq": 0,
    ".fseq": 1,
    ".xml": 2,
    ".json": 3,
    ".mp3": 4,
    ".mp4": 5,
    ".exe": 6,
}

DEFAULT_MAX_HASH_FILES = 1500
DEFAULT_HASH_BUDGET_MB = 2048

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".xml",
    ".cmd",
    ".ps1",
    ".vbs",
    ".spec",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".csv",
}

ARCHIVE_DIRS = (
    "KEEP_Current",
    "KEEP_Important_Old_Work",
    "KEEP_XSQ_Source",
    "KEEP_Audio_And_Video",
    "KEEP_Layouts_Models_Configs",
    "KEEP_Docs_Notes",
    "QUARANTINE_Review_Before_Delete",
    "DELETE_CANDIDATES_Report_Only",
    "cleanup_reports",
)

JUNK_TOKENS = (
    "temp",
    "tmp",
    "cache",
    "rendercache",
    "trash",
    "broken",
    "fail",
    "failed",
    "old",
    "copy",
    "test",
    "spam",
    "debug",
)

MEANINGFUL_XSQ_TOKENS = (
    "final",
    "best",
    "master",
    "show",
    "sequence",
    "helix",
    "dream",
    "weaver",
    "song",
    "classic",
    "hardkor",
    "birdsong",
    "chrono",
    "visualizer",
)


@dataclass(frozen=True)
class FileRecord:
    path: str
    root: str
    rel_path: str
    name: str
    suffix: str
    size: int
    mtime: str
    sha256: str | None = None
    in_active_project: bool = False
    referenced_by_current_project: bool = False


@dataclass(frozen=True)
class HashSummary:
    priority_only: bool
    max_hash_files: int
    hash_budget_mb: int
    candidate_groups: int
    candidate_files: int
    candidate_bytes: int
    hashed_groups: int
    hashed_files: int
    hashed_bytes: int
    skipped_groups: int
    skipped_files: int
    skipped_bytes: int
    candidate_files_by_extension: dict[str, int]
    hashed_files_by_extension: dict[str, int]


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_bytes(size: int | float) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_lossy(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="cp1252")
            except Exception:
                return None
    except Exception:
        return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def ensure_archive(archive_root: Path) -> dict[str, Path]:
    archive_root.mkdir(parents=True, exist_ok=True)
    created: dict[str, Path] = {}
    for name in ARCHIVE_DIRS:
        path = archive_root / name
        path.mkdir(parents=True, exist_ok=True)
        created[name] = path
    return created


def should_skip_dir(path: Path, active_project: Path, archive_root: Path) -> bool:
    name = path.name.lower()
    if name in {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"}:
        return True
    if path.resolve() == archive_root.resolve() or is_relative_to(path, archive_root):
        return True
    return False


def has_windows_system_attribute(path: Path) -> bool:
    try:
        attrs = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attrs & getattr(statmod, "FILE_ATTRIBUTE_SYSTEM", 0))


def iter_files(root: Path, active_project: Path, archive_root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    if root.is_file():
        yield root
        return
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except (OSError, PermissionError):
            continue
        for child in children:
            if child.is_symlink():
                continue
            if child.is_dir():
                if not should_skip_dir(child, active_project, archive_root):
                    stack.append(child)
            elif child.is_file():
                yield child


def folder_size_and_count(root: Path, active_project: Path, archive_root: Path) -> tuple[int, int]:
    total = 0
    count = 0
    for path in iter_files(root, active_project, archive_root):
        try:
            total += path.stat().st_size
            count += 1
        except OSError:
            pass
    return total, count


def has_project_signals(path: Path) -> bool:
    lower_name = path.name.lower()
    if any(keyword in lower_name for keyword in PROJECT_KEYWORDS):
        return True
    signal_names = {
        "readme.md",
        "requirements.txt",
        "dream_sequence_weaver.spec",
        "xlights_rgbeffects.xml",
        "template.xsq",
    }
    try:
        shallow = list(path.iterdir()) if path.is_dir() else []
    except OSError:
        return False
    for child in shallow:
        child_name = child.name.lower()
        if child_name in signal_names:
            return True
        if child.is_file() and any(keyword in child_name for keyword in PROJECT_KEYWORDS):
            return True
    return False


def discover_scan_roots(desktop: Path, active_project: Path, archive_root: Path) -> tuple[list[Path], list[str], list[str], list[Path]]:
    found_targets: list[str] = []
    missing_targets: list[str] = []
    related_dirs: list[Path] = []
    scan_roots: list[Path] = []

    for name in sorted(TARGET_FOLDERS):
        path = desktop / name
        if path.exists() and path.is_dir():
            found_targets.append(name)
            scan_roots.append(path)
        else:
            missing_targets.append(name)

    try:
        desktop_children = list(desktop.iterdir())
    except OSError:
        desktop_children = []

    for child in desktop_children:
        if child.resolve() == archive_root.resolve() or is_relative_to(child, archive_root):
            continue
        if child.is_dir() and child.name not in TARGET_FOLDERS and has_project_signals(child):
            related_dirs.append(child)
            scan_roots.append(child)
        elif child.is_file() and child.suffix.lower() in INVENTORY_EXTENSIONS:
            lowered = child.name.lower()
            if any(keyword in lowered for keyword in PROJECT_KEYWORDS) or child.suffix.lower() in {".xsq", ".fseq", ".xml", ".xmodel", ".py"}:
                scan_roots.append(child)

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in scan_roots:
        key = str(root.resolve()).lower()
        if key not in seen:
            seen.add(key)
            deduped.append(root)
    return deduped, found_targets, missing_targets, related_dirs


def identify_active_project(desktop: Path, preferred: Path) -> tuple[Path, list[dict[str, object]]]:
    candidates: list[Path] = []
    for child in desktop.iterdir():
        if child.is_dir():
            candidates.append(child)
    repo_root = find_repo_root(preferred)
    if repo_root not in candidates:
        candidates.append(repo_root)

    scored: list[dict[str, object]] = []
    for candidate in candidates:
        score = 0
        reasons: list[str] = []
        if (candidate / ".git").exists():
            score += 50
            reasons.append("contains .git")
        readme = candidate / "README.md"
        if readme.exists():
            text = read_text_lossy(readme) or ""
            if "Helix Sequencer" in text:
                score += 35
                reasons.append("README mentions Helix Sequencer")
            elif "Helix" in text:
                score += 15
                reasons.append("README mentions Helix")
        for entry in ("main.py", "gui_launcher.py", "requirements.txt", "tools", "core", "xlights"):
            if (candidate / entry).exists():
                score += 6
                reasons.append(f"has {entry}")
        if candidate.resolve() == repo_root.resolve():
            score += 30
            reasons.append("contains this cleanup script checkout")
        newest = newest_mtime_sample(candidate)
        scored.append(
            {
                "path": str(candidate),
                "score": score,
                "reasons": reasons,
                "newest_mtime": datetime.fromtimestamp(newest).isoformat() if newest else "",
            }
        )
    scored.sort(key=lambda item: (int(item["score"]), str(item["newest_mtime"])), reverse=True)
    chosen = Path(str(scored[0]["path"])) if scored else repo_root
    return chosen, scored


def newest_mtime_sample(root: Path, max_files: int = 500) -> float:
    newest = 0.0
    seen = 0
    stack = [root]
    while stack and seen < max_files:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except (OSError, PermissionError):
            continue
        for child in children:
            if seen >= max_files:
                break
            if child.is_symlink():
                continue
            if child.is_dir():
                if child.name.lower() not in {".git", ".venv", "__pycache__", "node_modules"}:
                    stack.append(child)
                continue
            try:
                newest = max(newest, child.stat().st_mtime)
                seen += 1
            except OSError:
                continue
    return newest


def build_reference_index(active_project: Path, exe_names: Iterable[str] = ()) -> tuple[set[str], list[dict[str, object]]]:
    reference_terms = set(OLD_REFERENCE_TERMS)
    reference_terms.update(name for name in exe_names if name)
    reference_terms.update(
        [
            "aaa",
            "qqq",
            "bbb",
            "cod",
            "gptseq",
            "xlights_auto",
        ]
    )
    referenced_names: set[str] = set()
    old_reference_hits: list[dict[str, object]] = []
    for path in iter_files(active_project, active_project, active_project / "Helix_Cleanup_Archive"):
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if is_relative_to(path, active_project / ".git"):
            continue
        text = read_text_lossy(path)
        if text is None:
            continue
        rel = safe_rel(path, active_project)
        for term in sorted(reference_terms, key=len, reverse=True):
            if not term:
                continue
            if term.lower() in text.lower():
                lines = [idx + 1 for idx, line in enumerate(text.splitlines()) if term.lower() in line.lower()]
                old_reference_hits.append({"file": rel, "term": term, "lines": lines[:20], "hit_count": len(lines)})
        for token in re.findall(r"[\w .()#@+-]+\.(?:xsq|mp3|mp4|exe|fseq|xml|json|py|xmodel|xbkp)", text, flags=re.I):
            referenced_names.add(Path(token.strip()).name.lower())
    return referenced_names, old_reference_hits


def collect_records(
    scan_roots: list[Path],
    active_project: Path,
    archive_root: Path,
    referenced_names: set[str],
    reports: Path,
) -> tuple[list[FileRecord], dict[str, dict[str, object]], list[dict[str, object]]]:
    records: list[FileRecord] = []
    folder_stats: dict[str, dict[str, object]] = {}
    errors: list[dict[str, object]] = []
    for root in scan_roots:
        progress(reports, f"scanning {root}")
        if root.is_dir() and has_windows_system_attribute(root) and not is_relative_to(root, active_project):
            errors.append(
                {
                    "path": str(root),
                    "error": "PARTIAL_SCAN_REVIEW_REQUIRED: root has Windows System directory attribute and was skipped to avoid an unresponsive Desktop enumeration.",
                }
            )
            folder_stats[str(root)] = {"file_count": 0, "total_size": 0, "partial_scan": True}
            continue
        if root.is_dir():
            folder_stats[str(root)] = {"file_count": 0, "total_size": 0}
        for path in iter_files(root, active_project, archive_root):
            try:
                stat = path.stat()
            except OSError as exc:
                errors.append({"path": str(path), "error": str(exc)})
                continue
            suffix = path.suffix.lower()
            name_lower = path.name.lower()
            if suffix not in INVENTORY_EXTENSIONS and not name_lower.startswith("xlights_"):
                continue
            root_key = str(root if root.is_dir() else path.parent)
            if root_key in folder_stats:
                folder_stats[root_key]["file_count"] = int(folder_stats[root_key]["file_count"]) + 1
                folder_stats[root_key]["total_size"] = int(folder_stats[root_key]["total_size"]) + stat.st_size
            records.append(
                FileRecord(
                    path=str(path),
                    root=str(root if root.is_dir() else path.parent),
                    rel_path=safe_rel(path, root if root.is_dir() else path.parent),
                    name=path.name,
                    suffix=suffix or "<none>",
                    size=stat.st_size,
                    mtime=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    sha256=None,
                    in_active_project=is_relative_to(path, active_project),
                    referenced_by_current_project=path.name.lower() in referenced_names,
                )
            )
    return records, folder_stats, errors


def duplicate_hash_candidate_counts(records: list[FileRecord], priority_only: bool = True) -> Counter[str]:
    size_buckets: dict[tuple[str, int], list[FileRecord]] = defaultdict(list)
    allowed_extensions = PRIORITY_HASH_EXTENSIONS if priority_only else HASH_EXTENSIONS
    for record in records:
        if record.suffix in allowed_extensions or (not priority_only and record.name.lower().startswith("xlights_")):
            size_buckets[(record.suffix, record.size)].append(record)

    counts: Counter[str] = Counter()
    for group in size_buckets.values():
        if len(group) >= 2:
            for record in group:
                counts[record.suffix] += 1
    return counts


def _hash_group_sort_key(indices: list[int], records: list[FileRecord]) -> tuple[int, int, int]:
    sample = records[indices[0]]
    priority = HASH_PRIORITY.get(sample.suffix, 99)
    active_or_referenced = sum(1 for idx in indices if records[idx].in_active_project or records[idx].referenced_by_current_project)
    group_bytes = sum(records[idx].size for idx in indices)
    return (priority, -active_or_referenced, -group_bytes)


def add_hashes_for_duplicate_sizes(
    records: list[FileRecord],
    errors: list[dict[str, object]],
    reports: Path,
    *,
    max_hash_files: int,
    hash_budget_mb: int,
    priority_only: bool,
) -> tuple[list[FileRecord], HashSummary]:
    size_buckets: dict[tuple[str, int], list[int]] = defaultdict(list)
    allowed_extensions = PRIORITY_HASH_EXTENSIONS if priority_only else HASH_EXTENSIONS
    for idx, record in enumerate(records):
        if record.suffix in allowed_extensions or (not priority_only and record.name.lower().startswith("xlights_")):
            size_buckets[(record.suffix, record.size)].append(idx)

    updated = list(records)
    hash_groups = [indices for indices in size_buckets.values() if len(indices) >= 2]
    hash_groups.sort(key=lambda indices: _hash_group_sort_key(indices, records))

    candidate_files = sum(len(indices) for indices in hash_groups)
    candidate_bytes = sum(records[idx].size for indices in hash_groups for idx in indices)
    candidate_by_ext: Counter[str] = Counter()
    for indices in hash_groups:
        for idx in indices:
            candidate_by_ext[records[idx].suffix] += 1

    file_limit = max(0, int(max_hash_files))
    byte_limit = max(0, int(hash_budget_mb)) * 1024 * 1024
    selected_groups: list[list[int]] = []
    selected_files = 0
    selected_bytes = 0
    skipped_groups = 0
    skipped_files = 0
    skipped_bytes = 0
    hashed_by_ext: Counter[str] = Counter()

    for indices in hash_groups:
        group_files = len(indices)
        group_bytes = sum(records[idx].size for idx in indices)
        over_file_limit = file_limit > 0 and selected_files + group_files > file_limit
        over_byte_limit = byte_limit > 0 and selected_bytes + group_bytes > byte_limit
        if over_file_limit or over_byte_limit:
            skipped_groups += 1
            skipped_files += group_files
            skipped_bytes += group_bytes
            continue
        selected_groups.append(indices)
        selected_files += group_files
        selected_bytes += group_bytes
        for idx in indices:
            hashed_by_ext[records[idx].suffix] += 1

    progress(
        reports,
        (
            f"hashing {selected_files} priority files across {len(selected_groups)} same-size groups; "
            f"deferred {skipped_files} files across {skipped_groups} groups"
        ),
    )
    for indices in selected_groups:
        if len(indices) < 2:
            continue
        for idx in indices:
            record = updated[idx]
            try:
                digest = sha256_file(Path(record.path))
            except OSError as exc:
                errors.append({"path": record.path, "error": f"hash failed: {exc}"})
                continue
            updated[idx] = replace(record, sha256=digest)

    summary = HashSummary(
        priority_only=priority_only,
        max_hash_files=file_limit,
        hash_budget_mb=max(0, int(hash_budget_mb)),
        candidate_groups=len(hash_groups),
        candidate_files=candidate_files,
        candidate_bytes=candidate_bytes,
        hashed_groups=len(selected_groups),
        hashed_files=selected_files,
        hashed_bytes=selected_bytes,
        skipped_groups=skipped_groups,
        skipped_files=skipped_files,
        skipped_bytes=skipped_bytes,
        candidate_files_by_extension=dict(sorted(candidate_by_ext.items())),
        hashed_files_by_extension=dict(sorted(hashed_by_ext.items())),
    )
    write_text(reports / "duplicate_hash_summary.json", json.dumps(asdict(summary), indent=2))
    return updated, summary


def record_sort_key(record: FileRecord) -> tuple[int, str, str]:
    return (record.size, record.mtime, record.path)


def choose_duplicate_keeper(group: list[FileRecord]) -> FileRecord:
    def score(record: FileRecord) -> tuple[int, int, int, str]:
        name = record.name.lower()
        junk_penalty = -10 if any(token in name for token in JUNK_TOKENS) else 0
        clear_bonus = 10 if any(token in name for token in MEANINGFUL_XSQ_TOKENS) else 0
        active_bonus = 100 if record.in_active_project else 0
        referenced_bonus = 60 if record.referenced_by_current_project else 0
        return (active_bonus + referenced_bonus + clear_bonus + junk_penalty, record.size, int(datetime.fromisoformat(record.mtime).timestamp()), record.path)

    return max(group, key=score)


def duplicate_groups(records: list[FileRecord]) -> list[dict[str, object]]:
    buckets: dict[str, list[FileRecord]] = defaultdict(list)
    for record in records:
        if record.sha256:
            buckets[record.sha256].append(record)
    groups: list[dict[str, object]] = []
    for digest, group in buckets.items():
        if len(group) < 2:
            continue
        keeper = choose_duplicate_keeper(group)
        groups.append(
            {
                "sha256": digest,
                "size": keeper.size,
                "keeper": keeper,
                "duplicates": [item for item in group if item.path != keeper.path],
                "all": sorted(group, key=lambda item: item.path.lower()),
            }
        )
    groups.sort(key=lambda item: int(item["size"]), reverse=True)
    return groups


def duplicate_candidate_rows(groups: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group in groups:
        keeper: FileRecord = group["keeper"]  # type: ignore[assignment]
        for duplicate in group["duplicates"]:  # type: ignore[index]
            rows.append(
                {
                    "action": "DELETE_CANDIDATE_EXACT_DUPLICATE",
                    "candidate": duplicate.path,
                    "keeper": keeper.path,
                    "sha256": group["sha256"],
                    "size": duplicate.size,
                    "reason": "Exact hash duplicate; keeper selected by active-project/reference/name/mtime preference.",
                    "safe_to_delete_without_review": "yes" if not duplicate.in_active_project else "no-active-project-file",
                }
            )
    return rows


def classify_xsq(records: list[FileRecord], dup_candidates: set[str]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for record in sorted((r for r in records if r.suffix == ".xsq"), key=lambda item: item.path.lower()):
        name = record.name.lower()
        reasons: list[str] = []
        classification = "QUARANTINE"
        if record.path in dup_candidates:
            classification = "DELETE_CANDIDATE"
            reasons.append("exact duplicate hash with selected keeper")
        elif record.size < 1024:
            classification = "DELETE_CANDIDATE"
            reasons.append("tiny .xsq, likely broken or placeholder")
        elif record.in_active_project or record.referenced_by_current_project:
            classification = "KEEP"
            reasons.append("inside active project or referenced by active project")
        elif any(token in name for token in MEANINGFUL_XSQ_TOKENS):
            classification = "KEEP"
            reasons.append("meaningful sequence name")
        elif any(token in name for token in JUNK_TOKENS):
            classification = "QUARANTINE"
            reasons.append("old/test/junk-style name but not exact duplicate")
        else:
            reasons.append("ambiguous .xsq outside active project")
        out.append({"classification": classification, "path": record.path, "size": record.size, "mtime": record.mtime, "reasons": reasons})
    return out


def classify_media(records: list[FileRecord], dup_candidates: set[str]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for record in sorted((r for r in records if r.suffix in {".mp3", ".mp4"}), key=lambda item: item.path.lower()):
        classification = "QUARANTINE"
        reasons: list[str] = []
        if record.path in dup_candidates:
            classification = "DELETE_CANDIDATE"
            reasons.append("exact duplicate hash with selected keeper")
        elif record.in_active_project or record.referenced_by_current_project:
            classification = "KEEP"
            reasons.append("inside active project or referenced by active project")
        elif record.size < 1024:
            classification = "DELETE_CANDIDATE"
            reasons.append("tiny media file, likely broken")
        elif any(token in record.name.lower() for token in ("preview", "render", "test", "copy", "old")):
            classification = "QUARANTINE"
            reasons.append("looks like preview/test media but not exact duplicate")
        else:
            classification = "KEEP"
            reasons.append("canonical-looking source media")
        out.append({"classification": classification, "path": record.path, "size": record.size, "mtime": record.mtime, "reasons": reasons})
    return out


def classify_exes(records: list[FileRecord], active_project: Path, dup_candidates: set[str], referenced_names: set[str]) -> list[dict[str, object]]:
    exes = sorted((r for r in records if r.suffix == ".exe"), key=lambda r: r.mtime, reverse=True)
    active_exes = [r for r in exes if r.in_active_project]
    current = active_exes[0] if active_exes else (exes[0] if exes else None)
    out: list[dict[str, object]] = []
    for record in exes:
        reasons: list[str] = []
        classification = "QUARANTINE"
        if current and record.path == current.path:
            classification = "KEEP"
            reasons.append("latest/current executable candidate")
        elif record.name.lower() in referenced_names:
            classification = "KEEP"
            reasons.append("referenced by current project")
        elif record.path in dup_candidates:
            classification = "DELETE_CANDIDATE"
            reasons.append("exact duplicate executable with selected keeper")
        elif any(term.lower().replace(" ", "") in record.name.lower().replace("_", "").replace(" ", "") for term in OLD_REFERENCE_TERMS):
            classification = "DELETE_CANDIDATE"
            reasons.append("old project executable name and not referenced")
        elif record.size < 1024 * 128:
            classification = "QUARANTINE"
            reasons.append("small executable artifact; manual review")
        else:
            reasons.append("uncertain executable; quarantine for review")
        out.append({"classification": classification, "path": record.path, "size": record.size, "mtime": record.mtime, "reasons": reasons})
    return out


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "_None found._\n"
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines) + "\n"


def write_discovery_report(
    reports: Path,
    scan_roots: list[Path],
    found_targets: list[str],
    missing_targets: list[str],
    related_dirs: list[Path],
    records: list[FileRecord],
    folder_stats: dict[str, dict[str, object]],
    errors: list[dict[str, object]],
) -> None:
    ext_counts = Counter(r.suffix for r in records)
    ext_sizes = Counter()
    for record in records:
        ext_sizes[record.suffix] += record.size
    priority_hash_counts = duplicate_hash_candidate_counts(records, priority_only=True)
    full_hash_counts = duplicate_hash_candidate_counts(records, priority_only=False)
    largest = sorted(records, key=lambda r: r.size, reverse=True)[:30]
    important = [
        r
        for r in records
        if r.suffix in {".py", ".json", ".xml", ".md", ".txt", ".xmodel", ".xbkp", ".cmd", ".ps1", ".vbs", ".spec"}
        and (r.in_active_project or any(keyword in r.name.lower() for keyword in PROJECT_KEYWORDS) or r.referenced_by_current_project)
    ][:200]
    lines = [
        "# Helix Desktop Cleanup Audit",
        "",
        f"Generated: {now_stamp()}",
        "",
        "## Folders Found",
        markdown_table(["target"], [[x] for x in found_targets]),
        "## Folders Missing",
        markdown_table(["target"], [[x] for x in missing_targets]),
        "## Related Folders Included",
        markdown_table(["folder"], [[str(x)] for x in related_dirs]),
        "## Scan Roots",
        markdown_table(["root"], [[str(x)] for x in scan_roots]),
        "## Folder Sizes",
        markdown_table(
            ["folder", "files", "size"],
            [[folder, stats["file_count"], format_bytes(int(stats["total_size"]))] for folder, stats in sorted(folder_stats.items())],
        ),
        "## File Counts By Extension",
        markdown_table(
            ["extension", "count", "size"],
            [[ext, count, format_bytes(ext_sizes[ext])] for ext, count in sorted(ext_counts.items())],
        ),
        "## Duplicate Hash Candidate Counts",
        "Priority hashing is used by default so audit-only can finish before exhaustive low-value cache/log hashing.",
        "",
        markdown_table(
            ["extension", "priority candidate files", "full candidate files"],
            [
                [ext, priority_hash_counts.get(ext, 0), full_hash_counts.get(ext, 0)]
                for ext in sorted(set(priority_hash_counts) | set(full_hash_counts))
            ],
        ),
        "## Largest Files",
        markdown_table(["size", "mtime", "path"], [[format_bytes(r.size), r.mtime, r.path] for r in largest]),
        "## Important-Looking Source / Config / Layout / Notes",
        markdown_table(["ext", "size", "path"], [[r.suffix, format_bytes(r.size), r.path] for r in important]),
        "## Scan Errors",
        markdown_table(["path", "error"], [[e["path"], e["error"]] for e in errors]),
    ]
    write_text(reports / "desktop_cleanup_audit.md", "\n".join(lines))


def write_current_project_report(reports: Path, active_project: Path, scored: list[dict[str, object]], exe_report: list[dict[str, object]]) -> None:
    current_exes = [item for item in exe_report if item["classification"] == "KEEP"]
    old_exes = [item for item in exe_report if item["classification"] != "KEEP"]
    lines = [
        "# Current Project Identification",
        "",
        f"Generated: {now_stamp()}",
        "",
        f"Chosen active project path: `{active_project}`",
        "",
        "## Why This Appears Current",
        markdown_table(["path", "score", "reasons", "newest mtime"], [[s["path"], s["score"], ", ".join(s["reasons"]), s["newest_mtime"]] for s in scored[:10]]),
        "## Current Executable Candidates",
        markdown_table(["classification", "size", "mtime", "path", "reasons"], [[e["classification"], format_bytes(int(e["size"])), e["mtime"], e["path"], "; ".join(e["reasons"])] for e in current_exes]),
        "## Old Executable Candidates",
        markdown_table(["classification", "size", "mtime", "path", "reasons"], [[e["classification"], format_bytes(int(e["size"])), e["mtime"], e["path"], "; ".join(e["reasons"])] for e in old_exes]),
        "## Risk Notes",
        "- The active project is never deleted by this tool.",
        "- `.git` folders are never traversed for cleanup actions.",
        "- Old executable deletion requires explicit `--delete-safe-duplicates` or `--full-safe-cleanup`, and referenced executables are kept.",
    ]
    write_text(reports / "current_project_identification.md", "\n".join(lines))


def write_duplicates_report(reports: Path, groups: list[dict[str, object]], candidate_rows: list[dict[str, object]], hash_summary: HashSummary) -> None:
    lines = [
        "# Duplicate Hash Report",
        "",
        f"Generated: {now_stamp()}",
        "",
        "## Hash Scope",
        f"- Priority-only hashing: `{hash_summary.priority_only}`",
        f"- Candidate same-size groups: {hash_summary.candidate_groups}",
        f"- Candidate files: {hash_summary.candidate_files} ({format_bytes(hash_summary.candidate_bytes)})",
        f"- Hashed groups: {hash_summary.hashed_groups}",
        f"- Hashed files: {hash_summary.hashed_files} ({format_bytes(hash_summary.hashed_bytes)})",
        f"- Deferred groups: {hash_summary.skipped_groups}",
        f"- Deferred files: {hash_summary.skipped_files} ({format_bytes(hash_summary.skipped_bytes)})",
        f"- Max hash files: {hash_summary.max_hash_files or 'unlimited'}",
        f"- Hash budget: {str(hash_summary.hash_budget_mb) + ' MB' if hash_summary.hash_budget_mb else 'unlimited'}",
        "",
        "## Candidate Files By Extension",
        markdown_table(
            ["extension", "candidate files", "hashed files"],
            [
                [ext, hash_summary.candidate_files_by_extension.get(ext, 0), hash_summary.hashed_files_by_extension.get(ext, 0)]
                for ext in sorted(set(hash_summary.candidate_files_by_extension) | set(hash_summary.hashed_files_by_extension))
            ],
        ),
        "## Exact Duplicate Results",
        "",
        f"Duplicate groups: {len(groups)}",
        f"Duplicate delete candidates: {len(candidate_rows)}",
        "",
    ]
    for idx, group in enumerate(groups, start=1):
        keeper: FileRecord = group["keeper"]  # type: ignore[assignment]
        lines.extend(
            [
                f"## Group {idx}",
                "",
                f"- SHA256: `{group['sha256']}`",
                f"- Size: {format_bytes(int(group['size']))}",
                f"- Keeper: `{keeper.path}`",
                "",
                markdown_table(
                    ["role", "active", "referenced", "mtime", "path"],
                    [
                        [
                            "KEEPER" if item.path == keeper.path else "DUPLICATE_CANDIDATE",
                            item.in_active_project,
                            item.referenced_by_current_project,
                            item.mtime,
                            item.path,
                        ]
                        for item in group["all"]  # type: ignore[index]
                    ],
                ),
            ]
        )
    write_text(reports / "duplicates_report.md", "\n".join(lines))
    with (reports / "duplicate_delete_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["action", "candidate", "keeper", "sha256", "size", "reason", "safe_to_delete_without_review"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidate_rows:
            writer.writerow(row)


def write_classification_report(path: Path, title: str, rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["classification"]) for row in rows)
    lines = [
        f"# {title}",
        "",
        f"Generated: {now_stamp()}",
        "",
        "## Counts",
        markdown_table(["classification", "count"], [[key, value] for key, value in sorted(counts.items())]),
        "## Files",
        markdown_table(
            ["classification", "size", "mtime", "path", "reasons"],
            [[row["classification"], format_bytes(int(row["size"])), row["mtime"], row["path"], "; ".join(row["reasons"])] for row in rows],
        ),
    ]
    write_text(path, "\n".join(lines))


def write_old_reference_report(reports: Path, hits: list[dict[str, object]]) -> None:
    lines = [
        "# Old Reference Cleanup Report",
        "",
        f"Generated: {now_stamp()}",
        "",
        "Audit-only finding list. No replacements were made unless `--fix-old-references` was explicitly used.",
        "",
        markdown_table(["file", "term", "hit count", "line samples"], [[h["file"], h["term"], h["hit_count"], ", ".join(str(x) for x in h["lines"])] for h in hits]),
    ]
    write_text(reports / "old_reference_cleanup_report.md", "\n".join(lines))


def write_dry_run_plan(
    reports: Path,
    duplicate_rows: list[dict[str, object]],
    xsq_rows: list[dict[str, object]],
    media_rows: list[dict[str, object]],
    exe_rows: list[dict[str, object]],
) -> None:
    potential_recovery = sum(int(row["size"]) for row in duplicate_rows)
    xsq_delete = [r for r in xsq_rows if r["classification"] == "DELETE_CANDIDATE"]
    media_delete = [r for r in media_rows if r["classification"] == "DELETE_CANDIDATE"]
    exe_delete = [r for r in exe_rows if r["classification"] == "DELETE_CANDIDATE"]
    lines = [
        "# Dry-Run Deletion Plan",
        "",
        f"Generated: {now_stamp()}",
        "",
        "**No deletion has been performed by `--audit-only`.**",
        "",
        f"Potential exact-duplicate space recoverable: {format_bytes(potential_recovery)}",
        "",
        "## Safe First Actions",
        "1. Review `duplicates_report.md` and `duplicate_delete_candidates.csv`.",
        "2. Run `--quarantine` before any deletion if you want files moved out of old folders but preserved.",
        "3. Run `--delete-safe-duplicates` only after confirming duplicate keepers are correct.",
        "4. Run `--fix-old-references` only after reviewing `old_reference_cleanup_report.md`.",
        "",
        "## Delete Candidate Summary",
        markdown_table(
            ["category", "count"],
            [
                ["exact duplicates", len(duplicate_rows)],
                [".xsq delete candidates", len(xsq_delete)],
                ["media delete candidates", len(media_delete)],
                [".exe delete candidates", len(exe_delete)],
            ],
        ),
        "## Important Guardrails",
        "- The active repo is skipped for delete/quarantine actions unless a file is an exact duplicate and a better keeper exists outside the delete set.",
        "- `.git` folders are never deleted.",
        "- Non-duplicate `.xsq` files should be quarantined, not deleted, unless you manually approve the report.",
    ]
    write_text(reports / "dry_run_deletion_plan.md", "\n".join(lines))


def write_final_summary(
    reports: Path,
    scan_roots: list[Path],
    records: list[FileRecord],
    duplicate_rows: list[dict[str, object]],
    xsq_rows: list[dict[str, object]],
    media_rows: list[dict[str, object]],
    exe_rows: list[dict[str, object]],
    old_ref_hits: list[dict[str, object]],
    operations: list[dict[str, object]],
    archive_root: Path,
    mode: str,
) -> None:
    total_size = sum(r.size for r in records)
    counts_by_ext = Counter(r.suffix for r in records)
    moved = [op for op in operations if op["action"] == "MOVE"]
    deleted = [op for op in operations if op["action"] == "DELETE"]
    edited = [op for op in operations if op["action"] == "EDIT"]
    lines = [
        "# Final Cleanup Summary",
        "",
        f"Generated: {now_stamp()}",
        f"Mode executed: `{mode}`",
        f"Archive folder: `{archive_root}`",
        "",
        "## Folders Scanned",
        markdown_table(["root"], [[str(root)] for root in scan_roots]),
        f"Total inventoried size scanned: {format_bytes(total_size)}",
        "",
        "## Operation Counts",
        markdown_table(
            ["operation", "count"],
            [["moved/quarantined", len(moved)], ["deleted", len(deleted)], ["edited references", len(edited)]],
        ),
        "## Classified Counts",
        markdown_table(
            ["category", "keep", "quarantine", "delete candidates"],
            [
                [".xsq", sum(1 for r in xsq_rows if r["classification"] == "KEEP"), sum(1 for r in xsq_rows if r["classification"] == "QUARANTINE"), sum(1 for r in xsq_rows if r["classification"] == "DELETE_CANDIDATE")],
                [".mp3/.mp4", sum(1 for r in media_rows if r["classification"] == "KEEP"), sum(1 for r in media_rows if r["classification"] == "QUARANTINE"), sum(1 for r in media_rows if r["classification"] == "DELETE_CANDIDATE")],
                [".exe", sum(1 for r in exe_rows if r["classification"] == "KEEP"), sum(1 for r in exe_rows if r["classification"] == "QUARANTINE"), sum(1 for r in exe_rows if r["classification"] == "DELETE_CANDIDATE")],
            ],
        ),
        "## Space",
        f"- Exact duplicate space eligible for recovery after review: {format_bytes(sum(int(r['size']) for r in duplicate_rows))}",
        f"- Actual space deleted in this run: {format_bytes(sum(int(op.get('size', 0)) for op in deleted))}",
        "",
        "## Old References",
        f"- Old reference hits found: {len(old_ref_hits)}",
        f"- Text files edited in this run: {len(edited)}",
        "",
        "## Manual Review Needed",
        "- Review `QUARANTINE` rows in the XSQ/media/exe reports.",
        "- Review old-name references before running `--fix-old-references`.",
        "- Generated AAATEST/video preview spam should be quarantined first unless exact duplicate reports prove it is redundant.",
        "",
        "## Risky Decisions Avoided",
        "- Non-duplicate `.xsq` files are not deleted automatically.",
        "- Active project files are not deleted by default.",
        "- Binary files are never edited.",
    ]
    write_text(reports / "final_cleanup_summary.md", "\n".join(lines))
    write_text(reports / "inventory_counts.json", json.dumps({"by_extension": counts_by_ext, "total_size": total_size}, indent=2))


def operation_log_path(reports: Path) -> Path:
    return reports / "cleanup_operations.jsonl"


def progress(reports: Path, message: str) -> None:
    line = f"{now_stamp()} {message}"
    print(message, file=sys.stderr, flush=True)
    with (reports / "cleanup_progress.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def log_operation(reports: Path, operations: list[dict[str, object]], payload: dict[str, object]) -> None:
    payload = {"timestamp": now_stamp(), **payload}
    operations.append(payload)
    with operation_log_path(reports).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def unique_destination(base: Path, source: Path, desktop: Path) -> Path:
    rel_parts: list[str]
    try:
        rel = source.resolve().relative_to(desktop.resolve())
        rel_parts = list(rel.parts)
    except ValueError:
        rel_parts = [source.name]
    dest = base.joinpath(*rel_parts)
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    for idx in range(1, 10000):
        candidate = parent / f"{stem}__dup{idx}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to find unique destination for {source}")


def move_to_archive(source: Path, destination_root: Path, desktop: Path, reports: Path, operations: list[dict[str, object]]) -> None:
    dest = unique_destination(destination_root, source, desktop)
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = source.stat().st_size
    shutil.move(str(source), str(dest))
    log_operation(reports, operations, {"action": "MOVE", "source": str(source), "destination": str(dest), "size": size})


def delete_file(source: Path, reports: Path, operations: list[dict[str, object]]) -> None:
    size = source.stat().st_size
    source.unlink()
    log_operation(reports, operations, {"action": "DELETE", "source": str(source), "size": size})


def perform_quarantine(
    rows: list[dict[str, object]],
    desktop: Path,
    active_project: Path,
    quarantine_root: Path,
    reports: Path,
    operations: list[dict[str, object]],
) -> None:
    for row in rows:
        if row.get("classification") != "QUARANTINE":
            continue
        source = Path(str(row["path"]))
        if not source.exists() or is_relative_to(source, active_project):
            continue
        move_to_archive(source, quarantine_root, desktop, reports, operations)


def perform_delete_duplicates(
    rows: list[dict[str, object]],
    active_project: Path,
    reports: Path,
    operations: list[dict[str, object]],
) -> None:
    for row in rows:
        source = Path(str(row["candidate"]))
        keeper = Path(str(row["keeper"]))
        if not source.exists() or not keeper.exists():
            continue
        if is_relative_to(source, active_project):
            continue
        if source.resolve() == keeper.resolve():
            continue
        delete_file(source, reports, operations)


def replacement_for(term: str) -> str:
    if term in {"dream_sequence_weaver", "helix_sequence_weaver", "sequence_weaver"}:
        return "helix_sequencer"
    if term in {"DreamSequenceWeaver", "HelixSequenceWeaver"}:
        return "HelixSequencer"
    if term in {"Dream Sequence Weaver", "Helix Sequence Weaver", "Sequence Weaver", "LightWeaver", "SeqGen", "PixelBuilder", "gptseq", "xlights_auto"}:
        return "Helix Sequencer"
    return term


def perform_fix_old_references(active_project: Path, hits: list[dict[str, object]], reports: Path, operations: list[dict[str, object]]) -> None:
    files = sorted({str(hit["file"]) for hit in hits})
    backup_root = reports / "reference_edit_backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    for rel in files:
        path = active_project / rel
        if not path.exists() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        original = read_text_lossy(path)
        if original is None:
            continue
        updated = original
        for term in OLD_REFERENCE_TERMS:
            updated = updated.replace(term, replacement_for(term))
        if updated == original:
            continue
        backup = unique_destination(backup_root, path, active_project)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        path.write_text(updated, encoding="utf-8", newline="\n")
        diff = "\n".join(difflib.unified_diff(original.splitlines(), updated.splitlines(), fromfile=str(path), tofile=str(path), lineterm=""))
        diff_path = reports / "reference_edit_diffs" / f"{rel.replace(os.sep, '__').replace('/', '__')}.diff"
        write_text(diff_path, diff)
        log_operation(reports, operations, {"action": "EDIT", "file": str(path), "backup": str(backup), "diff": str(diff_path)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and safely clean legacy Helix/xLights Desktop project folders.")
    parser.add_argument("--desktop", type=Path, default=Path.home() / "Desktop")
    parser.add_argument("--archive", type=Path, default=None, help="Defaults to <Desktop>/Helix_Cleanup_Archive")
    parser.add_argument("--audit-only", action="store_true", help="Generate reports only. This is the default.")
    parser.add_argument("--quarantine", action="store_true", help="Move uncertain files to QUARANTINE_Review_Before_Delete.")
    parser.add_argument("--delete-safe-duplicates", action="store_true", help="Delete exact duplicate candidates outside the active project.")
    parser.add_argument("--fix-old-references", action="store_true", help="Backup and replace old project-name references in the active project.")
    parser.add_argument("--full-safe-cleanup", action="store_true", help="Run quarantine, safe duplicate deletion, and old-reference fixes.")
    parser.add_argument("--hash-all", action="store_true", help="Hash all supported same-size duplicate candidates instead of priority cleanup extensions only.")
    parser.add_argument(
        "--max-hash-files",
        type=int,
        default=DEFAULT_MAX_HASH_FILES,
        help="Maximum same-size duplicate candidate files to hash in one run. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--hash-budget-mb",
        type=int,
        default=DEFAULT_HASH_BUDGET_MB,
        help="Maximum total bytes to hash, in MB. Use 0 for unlimited.",
    )
    return parser.parse_args()


def selected_mode(args: argparse.Namespace) -> str:
    modes = [name for name in ("quarantine", "delete_safe_duplicates", "fix_old_references", "full_safe_cleanup") if getattr(args, name)]
    if not modes:
        return "audit-only"
    if len(modes) > 1:
        raise SystemExit("Choose one mode at a time.")
    return modes[0].replace("_", "-")


def main() -> int:
    args = parse_args()
    desktop = args.desktop.resolve()
    archive_root = (args.archive or (desktop / "Helix_Cleanup_Archive")).resolve()
    archive_dirs = ensure_archive(archive_root)
    reports = archive_dirs["cleanup_reports"]
    mode = selected_mode(args)
    operations: list[dict[str, object]] = []

    script_repo = find_repo_root(Path(__file__).resolve())
    progress(reports, "Identifying active project...")
    active_project, scored_projects = identify_active_project(desktop, script_repo)

    progress(reports, "Discovering scan roots...")
    scan_roots, found_targets, missing_targets, related_dirs = discover_scan_roots(desktop, active_project, archive_root)

    progress(reports, "Building current-project reference index...")
    referenced_names, old_reference_hits = build_reference_index(active_project)
    progress(reports, f"Collecting records from {len(scan_roots)} roots...")
    records, folder_stats, errors = collect_records(scan_roots, active_project, archive_root, referenced_names, reports)
    progress(reports, f"Collected {len(records)} records. Writing inventory-first audit report...")
    write_discovery_report(reports, scan_roots, found_targets, missing_targets, related_dirs, records, folder_stats, errors)
    progress(reports, "Hashing possible exact duplicates within configured budget...")
    records, hash_summary = add_hashes_for_duplicate_sizes(
        records,
        errors,
        reports,
        max_hash_files=args.max_hash_files,
        hash_budget_mb=args.hash_budget_mb,
        priority_only=not bool(args.hash_all),
    )

    progress(reports, "Classifying duplicates and cleanup candidates...")
    groups = duplicate_groups(records)
    duplicate_rows = duplicate_candidate_rows(groups)
    dup_candidate_paths = {str(row["candidate"]) for row in duplicate_rows}
    xsq_rows = classify_xsq(records, dup_candidate_paths)
    media_rows = classify_media(records, dup_candidate_paths)
    exe_rows = classify_exes(records, active_project, dup_candidate_paths, referenced_names)

    progress(reports, "Writing reports...")
    write_discovery_report(reports, scan_roots, found_targets, missing_targets, related_dirs, records, folder_stats, errors)
    write_duplicates_report(reports, groups, duplicate_rows, hash_summary)
    write_classification_report(reports / "xsq_classification_report.md", "XSQ Classification Report", xsq_rows)
    write_classification_report(reports / "media_cleanup_report.md", "Media Cleanup Report", media_rows)
    write_classification_report(reports / "exe_cleanup_report.md", "Executable Cleanup Report", exe_rows)
    write_old_reference_report(reports, old_reference_hits)
    write_current_project_report(reports, active_project, scored_projects, exe_rows)
    write_dry_run_plan(reports, duplicate_rows, xsq_rows, media_rows, exe_rows)

    if mode in {"quarantine", "full-safe-cleanup"}:
        perform_quarantine(xsq_rows + media_rows + exe_rows, desktop, active_project, archive_dirs["QUARANTINE_Review_Before_Delete"], reports, operations)
    if mode in {"delete-safe-duplicates", "full-safe-cleanup"}:
        perform_delete_duplicates(duplicate_rows, active_project, reports, operations)
    if mode in {"fix-old-references", "full-safe-cleanup"}:
        perform_fix_old_references(active_project, old_reference_hits, reports, operations)

    write_final_summary(reports, scan_roots, records, duplicate_rows, xsq_rows, media_rows, exe_rows, old_reference_hits, operations, archive_root, mode)

    print(f"Mode: {mode}")
    print(f"Active project: {active_project}")
    print(f"Archive: {archive_root}")
    print(f"Reports: {reports}")
    print(f"Files inventoried: {len(records)}")
    print(f"Hash scope: {'priority extensions' if hash_summary.priority_only else 'all supported extensions'}")
    print(f"Files hashed: {hash_summary.hashed_files} / {hash_summary.candidate_files}")
    print(f"Files deferred from hashing: {hash_summary.skipped_files}")
    print(f"Duplicate groups: {len(groups)}")
    print(f"Duplicate candidates: {len(duplicate_rows)}")
    print(f"Operations performed: {len(operations)}")
    if mode == "audit-only":
        print("No files were moved, deleted, or edited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
