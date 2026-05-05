# LEGAL HYGIENE REPORT

Status: CLEAN

Date: 2026-05-01
Branch: feature/restructure-core

## Suspicious Items Found

- path: core/effect_engine.py (active placement helpers and placement mode routing)
- risk: resolved
- reason: previously source-specific naming in active runtime path.
- action: renamed to source-agnostic `mapped_*` naming while preserving behavior.

- path: core/engine_style_catalog.py (v18 style titles and placement modes)
- risk: resolved
- reason: previously creator/source-specific naming in user-facing style metadata.
- action: renamed style labels and placement modes to source-agnostic equivalents.

- path: rules.md (provenance section)
- risk: resolved
- reason: previously included creator-specific tutorial link.
- action: replaced with source-agnostic tutorial category guidance.

- path: xlights/vendor_benchmark_manifest.json and docs/xlights_vendor_benchmark_research_2026-04-23.md
- risk: resolved
- reason: previously used named commercial sources in benchmark examples.
- action: anonymized benchmark source identifiers and references.

## Removed

- Source-specific active naming and links listed above.

## Rewritten

- Active placement and style identifiers now use source-agnostic naming.
- Benchmark/provenance references now use anonymized cohort identifiers.

## Remaining Safe References

- Policy/legal docs may still contain terms such as `vendor`, `forum`, `transcript`, or `copied` in compliance context.
- Archive files may retain historical labels; they are non-runtime and outside active generation path.

## Tests Run

- `python -m pytest -q`
- Result: 185 passed, 4 warnings.

## History Cleanup Needed

- no (for legal contamination)
- reason: no high-risk copied transcript/caption/proprietary sequence content found in active tracked runtime paths.

## Recommended Next Step

1. Keep this report as merge evidence.
2. Start isolated power-engine development in `core/power_engine.py` and validate with dedicated tests before runtime integration.
