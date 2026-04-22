from __future__ import annotations

import argparse
import json
import math
import statistics
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PERMISSIVE_LICENSES = {
    "mit",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mpl-2.0",
    "cc0-1.0",
    "unlicense",
}

COPYLEFT_LICENSES = {
    "gpl-3.0",
    "gpl-2.0",
    "lgpl-3.0",
    "lgpl-2.1",
    "agpl-3.0",
}


@dataclass
class SequenceRecord:
    repo: str
    license_spdx: str
    path: Path
    suffix: str


def _normalize_effect_name(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if text.endswith(" bpm"):
        return ""
    return text


def _to_int(raw: str, default: int = 0) -> int:
    try:
        return int(float(raw))
    except Exception:
        return default


def _model_family(name: str) -> str:
    norm = (name or "").strip().lower()
    if any(token in norm for token in ("matrix", "panel", "p10", "video")):
        return "matrix"
    if any(token in norm for token in ("mega", "tree")):
        return "mega_tree"
    if any(token in norm for token in ("arch", "arc")):
        return "arch"
    if any(token in norm for token in ("star", "snowflake")):
        return "star_snowflake"
    if any(token in norm for token in ("face", "head", "sing", "lyric")):
        return "face"
    if any(token in norm for token in ("cane",)):
        return "cane"
    if any(token in norm for token in ("spinner", "pinwheel")):
        return "spinner"
    if any(token in norm for token in ("flood", "strobe")):
        return "flood"
    if any(token in norm for token in ("line", "roof", "window", "icicle", "blvd")):
        return "line_outline"
    return "other"


def _iter_legal_sequence_files(
    manifest: dict[str, Any],
    *,
    include_copyleft: bool,
    min_stars: int,
) -> list[SequenceRecord]:
    out: list[SequenceRecord] = []
    for repo_row in manifest.get("repositories", []):
        if not isinstance(repo_row, dict):
            continue
        repo = str(repo_row.get("repo") or "").strip()
        stars = int(repo_row.get("stars") or 0)
        if not repo or stars < min_stars:
            continue
        lic = str(repo_row.get("license_spdx") or "").strip().lower()
        if lic in PERMISSIVE_LICENSES:
            pass
        elif include_copyleft and lic in COPYLEFT_LICENSES:
            pass
        else:
            continue

        for file_row in repo_row.get("files", []):
            if not isinstance(file_row, dict):
                continue
            if not bool(file_row.get("downloaded")):
                continue
            if str(file_row.get("category") or "") != "sequences":
                continue
            suffix = str(file_row.get("suffix") or "").lower()
            if suffix not in {".xsq", ".xml"}:
                continue
            output_path = str(file_row.get("output_path") or "").strip()
            if not output_path:
                continue
            path = Path(output_path)
            if not path.exists():
                continue
            out.append(SequenceRecord(repo=repo, license_spdx=lic, path=path, suffix=suffix))
    return out


def _iter_extra_sequence_files(
    *,
    extra_manifest: dict[str, Any] | None,
    extra_sequence_root: Path | None,
    include_copyleft: bool,
) -> list[SequenceRecord]:
    out: list[SequenceRecord] = []
    if extra_manifest:
        for row in extra_manifest:
            if not isinstance(row, dict):
                continue
            repo = str(row.get("repo") or "").strip()
            lic = str(row.get("license_spdx") or "").strip().lower()
            if lic in PERMISSIVE_LICENSES:
                pass
            elif include_copyleft and lic in COPYLEFT_LICENSES:
                pass
            else:
                continue
            for file_row in row.get("files", []):
                if not isinstance(file_row, dict):
                    continue
                if not bool(file_row.get("downloaded")):
                    continue
                rel_path = str(file_row.get("path") or "").strip()
                output_path = str(file_row.get("output_path") or "").strip()
                path = Path(output_path) if output_path else None
                if path is None or not path.exists():
                    continue
                suffix = path.suffix.lower()
                if suffix not in {".xsq", ".xml"}:
                    continue
                out.append(SequenceRecord(repo=repo, license_spdx=lic, path=path, suffix=suffix))

    if extra_sequence_root and extra_sequence_root.exists():
        for path in sorted(extra_sequence_root.rglob("*")):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".xsq", ".xml"}:
                continue
            out.append(SequenceRecord(repo="extra_sequence_root", license_spdx="manual", path=path, suffix=suffix))

    return out


def _quantiles(values: list[int]) -> dict[str, int]:
    if not values:
        return {"p25": 0, "p50": 0, "p75": 0, "p90": 0}
    sorted_values = sorted(values)
    return {
        "p25": int(sorted_values[max(0, int(len(sorted_values) * 0.25) - 1)]),
        "p50": int(statistics.median(sorted_values)),
        "p75": int(sorted_values[max(0, int(len(sorted_values) * 0.75) - 1)]),
        "p90": int(sorted_values[max(0, int(len(sorted_values) * 0.90) - 1)]),
    }


def build_ruleset(
    *,
    manifest: dict[str, Any],
    extra_manifest: list[dict[str, Any]] | None,
    extra_sequence_root: Path | None,
    include_copyleft: bool,
    min_stars: int,
) -> dict[str, Any]:
    base_files = _iter_legal_sequence_files(
        manifest,
        include_copyleft=include_copyleft,
        min_stars=min_stars,
    )
    extra_files = _iter_extra_sequence_files(
        extra_manifest=extra_manifest,
        extra_sequence_root=extra_sequence_root,
        include_copyleft=include_copyleft,
    )
    dedup: dict[str, SequenceRecord] = {}
    for rec in base_files + extra_files:
        dedup[str(rec.path.resolve())] = rec
    sequence_files = list(dedup.values())

    global_effects: Counter[str] = Counter()
    family_effects: dict[str, Counter[str]] = defaultdict(Counter)
    effect_durations: dict[str, list[int]] = defaultdict(list)
    transitions: Counter[tuple[str, str]] = Counter()
    family_layers: dict[str, list[int]] = defaultdict(list)
    per_repo_effects: dict[str, Counter[str]] = defaultdict(Counter)
    ignored_non_sequence_xml = 0
    no_model_effect_files = 0
    parsed_files = 0
    parsed_repos: set[str] = set()
    parse_errors: list[dict[str, str]] = []

    for record in sequence_files:
        try:
            root = ET.parse(record.path).getroot()
        except Exception as exc:
            parse_errors.append({"path": str(record.path), "error": repr(exc)})
            continue

        if root.tag != "xsequence":
            ignored_non_sequence_xml += 1
            continue

        parsed_files += 1
        parsed_repos.add(record.repo)
        has_model_effects = False
        for element in root.findall(".//ElementEffects/Element[@type='model']"):
            model_name = str(element.attrib.get("name") or "")
            family = _model_family(model_name)
            layers = element.findall("EffectLayer")
            family_layers[family].append(len(layers))
            for layer in layers:
                events: list[tuple[int, str]] = []
                for effect in layer.findall("Effect"):
                    name = _normalize_effect_name(
                        str(effect.attrib.get("name") or effect.attrib.get("effect") or effect.attrib.get("label") or "")
                    )
                    if not name:
                        continue
                    has_model_effects = True
                    start_ms = _to_int(str(effect.attrib.get("startTime") or "0"))
                    end_ms = _to_int(str(effect.attrib.get("endTime") or str(start_ms)))
                    duration = max(0, end_ms - start_ms)
                    global_effects[name] += 1
                    family_effects[family][name] += 1
                    per_repo_effects[record.repo][name] += 1
                    effect_durations[name].append(duration)
                    events.append((start_ms, name))
                events.sort(key=lambda row: row[0])
                for i in range(len(events) - 1):
                    transitions[(events[i][1], events[i + 1][1])] += 1
        if not has_model_effects:
            no_model_effect_files += 1

    family_rules: dict[str, Any] = {}
    for family, counter in family_effects.items():
        total = sum(counter.values())
        top_items = counter.most_common(8)
        family_rules[family] = {
            "top_effects": [
                {
                    "effect": effect,
                    "count": int(count),
                    "weight": round(float(count) / max(1, total), 5),
                    "duration_ms": _quantiles(effect_durations.get(effect, [])),
                }
                for effect, count in top_items
            ],
            "layering": {
                "avg_layers": round(float(statistics.mean(family_layers.get(family, [1]))), 3),
                "max_layers": int(max(family_layers.get(family, [1]))),
                "multi_layer_rate": round(
                    sum(1 for n in family_layers.get(family, []) if n > 1) / max(1, len(family_layers.get(family, []))),
                    5,
                ),
            },
        }

    top_global = global_effects.most_common(20)
    top_transitions = transitions.most_common(20)
    transition_rules = [
        {
            "from": a,
            "to": b,
            "count": int(count),
            "confidence": round(float(count) / max(1, sum(v for (x, _y), v in transitions.items() if x == a)), 5),
        }
        for (a, b), count in top_transitions
    ]

    general_rules = []
    if top_global:
        general_rules.append("Prefer high-support effects first, then diversify with low-weight accents.")
    if transition_rules:
        general_rules.append("Follow common effect-pair transitions to keep phrase continuity.")
    if no_model_effect_files > 0:
        general_rules.append("Treat channel-render-only files as timing references, not prop-effect exemplars.")

    return {
        "version": 1,
        "source_policy": {
            "include_copyleft": bool(include_copyleft),
            "min_stars": int(min_stars),
            "allowed_permissive_spdx": sorted(PERMISSIVE_LICENSES),
            "allowed_copyleft_spdx": sorted(COPYLEFT_LICENSES) if include_copyleft else [],
        },
        "corpus_summary": {
            "files_considered": len(sequence_files),
            "files_parsed": parsed_files,
            "non_sequence_xml_ignored": ignored_non_sequence_xml,
            "files_with_no_model_effects": no_model_effect_files,
            "parse_error_count": len(parse_errors),
            "repos_used": sorted(parsed_repos),
        },
        "top_effects_global": [
            {
                "effect": effect,
                "count": int(count),
                "weight": round(float(count) / max(1, sum(global_effects.values())), 5),
                "duration_ms": _quantiles(effect_durations.get(effect, [])),
            }
            for effect, count in top_global
        ],
        "family_rules": family_rules,
        "transition_rules": transition_rules,
        "general_rules": general_rules,
        "per_repo_top_effects": {
            repo: [{"effect": effect, "count": int(count)} for effect, count in counter.most_common(8)]
            for repo, counter in sorted(per_repo_effects.items())
        },
        "parse_errors": parse_errors[:40],
    }


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Open-Source Sequence Ruleset")
    lines.append("")
    summary = payload.get("corpus_summary", {})
    lines.append("## Corpus")
    lines.append(f"- Files considered: {summary.get('files_considered', 0)}")
    lines.append(f"- Files parsed: {summary.get('files_parsed', 0)}")
    lines.append(f"- Files with no model effects: {summary.get('files_with_no_model_effects', 0)}")
    lines.append(f"- Repos used: {', '.join(summary.get('repos_used', []))}")
    lines.append("")
    lines.append("## Top Effects (Global)")
    for row in payload.get("top_effects_global", [])[:12]:
        lines.append(
            f"- {row.get('effect')}: count={row.get('count')} weight={row.get('weight')} "
            f"dur(p50)={row.get('duration_ms', {}).get('p50', 0)}ms"
        )
    lines.append("")
    lines.append("## Family Rules")
    for family, row in sorted(payload.get("family_rules", {}).items()):
        layering = row.get("layering", {})
        lines.append(
            f"- {family}: avg_layers={layering.get('avg_layers')} "
            f"multi_layer_rate={layering.get('multi_layer_rate')}"
        )
        for effect_row in row.get("top_effects", [])[:5]:
            lines.append(
                f"  - {effect_row.get('effect')} ({effect_row.get('count')}, w={effect_row.get('weight')}, "
                f"p50={effect_row.get('duration_ms', {}).get('p50', 0)}ms)"
            )
    lines.append("")
    lines.append("## Transition Rules")
    for row in payload.get("transition_rules", [])[:12]:
        lines.append(
            f"- {row.get('from')} -> {row.get('to')}: count={row.get('count')} confidence={row.get('confidence')}"
        )
    lines.append("")
    lines.append("## General Rules")
    for rule in payload.get("general_rules", []):
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract legal-safe sequence placement rules from open-source xLights files.")
    parser.add_argument("--manifest", default="outputs/open_source/assets_manifest.json", help="Input asset manifest JSON.")
    parser.add_argument("--output-json", default="outputs/open_source/sequence_ruleset_vendor_open.json", help="Output ruleset JSON.")
    parser.add_argument("--output-md", default="outputs/open_source/sequence_ruleset_vendor_open.md", help="Output markdown summary.")
    parser.add_argument(
        "--extra-manifest",
        default="outputs/open_source/vendor_open_xsq_manifest_2026-04-22.json",
        help="Optional extra manifest for approved vendor-open .xsq files.",
    )
    parser.add_argument(
        "--extra-sequence-root",
        default="",
        help="Optional additional sequence root to scan for .xsq/.xml files.",
    )
    parser.add_argument("--min-stars", type=int, default=0, help="Minimum stars for source repos.")
    parser.add_argument("--include-copyleft", action="store_true", help="Include GPL/LGPL/AGPL repositories.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    extra_manifest_path = Path(args.extra_manifest).resolve() if str(args.extra_manifest).strip() else None
    extra_manifest: list[dict[str, Any]] | None = None
    if extra_manifest_path and extra_manifest_path.exists():
        loaded = json.loads(extra_manifest_path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            extra_manifest = loaded
    extra_sequence_root = Path(args.extra_sequence_root).resolve() if str(args.extra_sequence_root).strip() else None
    payload = build_ruleset(
        manifest=manifest,
        extra_manifest=extra_manifest,
        extra_sequence_root=extra_sequence_root,
        include_copyleft=bool(args.include_copyleft),
        min_stars=max(0, int(args.min_stars)),
    )

    output_json = Path(args.output_json).resolve()
    output_md = Path(args.output_md).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_to_markdown(payload), encoding="utf-8")

    print(f"Ruleset JSON: {output_json}")
    print(f"Ruleset Markdown: {output_md}")
    print(f"Parsed files: {payload['corpus_summary']['files_parsed']}")
    print(f"Top effects: {[row['effect'] for row in payload.get('top_effects_global', [])[:8]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
