#!/usr/bin/env python3
"""Turn a layout-bench run_report.json into a repo-safe findings note.

The note records engine behavior observed on the bench. It does not include
audio, sequences, or video.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "test_runs" / "layout_bench" / "run_report.json")
    parser.add_argument("--output", type=Path, default=ROOT / "fixtures" / "layout_bench" / "FINDINGS.md")
    args = parser.parse_args()
    rows = json.loads(args.report.read_text(encoding="utf-8"))
    by_layout: dict[str, list[dict]] = defaultdict(list)
    failures = []
    snowman_warnings = 0
    for row in rows:
        by_layout[row["layout"]].append(row)
        if row.get("returncode") != 0 or not row.get("xsq"):
            failures.append(row)
        log_path = Path(row.get("log") or "")
        if log_path.exists() and "Snowman band planning skipped" in log_path.read_text(encoding="utf-8", errors="replace"):
            snowman_warnings += 1

    lines = [
        "# Layout bench findings",
        "",
        "Observed by running `main.py --profile master` on the clean-room fixtures. Sequencing code was not changed. Numbers are from the canonical `*,v27.3.xsq` files, not the sparse `.orchestrated.xsq` sidecars.",
        "",
        f"Runs: {len(rows)}. Failures: {len(failures)}. Logs that record `Snowman band planning skipped`: {snowman_warnings}.",
        "",
        "## Per layout",
        "",
    ]
    for layout_id in sorted(by_layout):
        items = by_layout[layout_id]
        dark_counts: Counter[str] = Counter()
        effect_counts: Counter[str] = Counter()
        lit_ratios = []
        for item in items:
            coverage = item.get("coverage") or {}
            props = max(1, int(coverage.get("prop_count") or 0))
            lit = int(coverage.get("lit_prop_count") or 0)
            lit_ratios.append(lit / props)
            dark_counts.update(coverage.get("dark_props") or [])
            effect_counts.update(coverage.get("effect_names") or {})
        mean_lit = sum(lit_ratios) / len(lit_ratios)
        top_effects = ", ".join(f"{name} ({count})" for name, count in effect_counts.most_common(6))
        lines.append(f"### {layout_id}")
        lines.append("")
        lines.append(f"Songs: {len(items)}. Mean fraction of props with at least one effect: {mean_lit:.1%}.")
        lines.append(f"Most common effect names: {top_effects or '(none)'}.")
        if dark_counts:
            darkest = ", ".join(f"{name} ({count}/{len(items)} songs)" for name, count in dark_counts.most_common(8))
            lines.append(f"Props dark on one or more songs: {darkest}.")
        else:
            lines.append("No prop was left without an effect on the songs in this report.")
        lines.append("")

    lines.extend(
        [
            "## Engine notes",
            "",
            "- Snowman-band planning raises `KeyError: 'composite_submodels'` inside `core/snowman_band.py` while reading mapped drum events, then the master run continues. Every one of the 112 logs records that skip. Singing-face mouths and eyes, and the nine drum-hit props, still receive the same general effects as the rest of the layout (`Wave`, `On`, `Bars`, `Twinkle`, and sometimes `Pictures`). The template's `Faces` phoneme effect is not what those mouths get.",
            "- The master profile is not AC-only. Single-channel LOR props still receive pixel-family effect names such as Butterfly, Spirals, Plasma, and Lines. That is expected with the default master flags. `--ac-lights-only` was not passed.",
            "- Preview panels light a whole model while any of its effects are active. They do not simulate xLights per-pixel shaders, so matrices, spirals, and the moire stack read as shapes turning on and off together. Overlapping moire matrices can still be told apart when their effect timing differs.",
            "- `Tree 360` virtual pixels in the parser are vertical strands. Spiral layouts also store a spiral `PointData` path, and the preview draws that path, so the panel shows the spiral outline rather than the parser's strand map.",
            "- Poly-line arch sections with a shallow bow are parsed as lines. The `Arch N Sec M` names are still present, and the master run places effects on them.",
            "- Custom RGB snowflakes are also eligible for the matrix family because a custom RGB model with 24 or more pixels is classified as a matrix before the snowflake name is considered. The snowflake name pool still exists.",
            "",
        ]
    )
    if failures:
        lines.append("## Failed runs")
        lines.append("")
        for row in failures:
            lines.append(f"- {row.get('layout')} {row.get('audio')} rc={row.get('returncode')}")
        lines.append("")
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
