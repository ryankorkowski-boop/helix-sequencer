# LEGAL HYGIENE REPORT

Status: NOT CLEAN

Date: 2026-05-01
Branch: feature/restructure-core

## Suspicious Items Found

- path: core/effect_engine.py:5860, 5935, 5998, 10468, 10604, 10605, 11103, 11123, 11146
- risk: medium
- reason: Active placement modes and function names are source-specific (`xtreme_*`) rather than source-agnostic Helix terminology.
- action: Rename to neutral Helix naming (`showcase_essentials`, `showcase_submodel`, `showcase_director` etc.), add migration aliases if needed.

- path: core/engine_style_catalog.py:1084, 1087, 1112, 1134, 1137
- risk: medium
- reason: User-facing style naming references a specific creator/vendor identity (`Extreme`, `xtreme_*`).
- action: Rewrite style titles/modes into source-agnostic labels while preserving behavior.

- path: xlights/vendor_benchmark_manifest.json:6, 7, 8
- risk: medium
- reason: Direct vendor/source branding references in tracked benchmark manifest.
- action: Keep only if strictly needed for provenance/legal tracking; otherwise generalize benchmark buckets and move named sources to a controlled legal-notes location.

- path: docs/xlights_vendor_benchmark_research_2026-04-23.md:59, 60
- risk: medium
- reason: Source-specific benchmark narrative with named vendor reference.
- action: Rewrite to generalized capability benchmarking language; keep named references only in explicit legal provenance docs.

- path: rules.md:185
- risk: medium
- reason: Includes a direct tutorial-vendor link in a general ruleset.
- action: Remove vendor-specific tutorial link from core rules file; keep only official docs/community category references.

- path: archive/legacy_versions/sequencer_launcher.py:168-174, 262
- risk: low
- reason: Archived legacy labels include `Vendor Edition` naming; not active runtime path.
- action: Optional cleanup; can defer if archive is non-runtime.

- path: core/audio_intelligence.py:906, 948, 992, 995, 1017
- risk: low
- reason: `transcription/transcript` wording appears in audio/lyric pipeline context, not tutorial scraping.
- action: Keep.

## Removed

- None (non-destructive audit pass).

## Rewritten

- None (non-destructive audit pass).

## Remaining Safe References

- Legal policy and guardrail mentions of `vendor`, `forum`, `proprietary`, and `copied` in policy docs are acceptable when used for compliance boundaries.
- `copy.deepcopy`/`copied` variable names in code are technical copy semantics, not source-copying behavior.

## Tests Run

- `python -m pytest -q`
- Result: 185 passed, 4 warnings.

## History Cleanup Needed

- no
- reason: No direct evidence of high-risk copied transcript dumps, caption files, or proprietary sequence text in tracked files from this audit. Current risk is primarily source-specific naming/content that should be normalized via forward cleanup commits.

## Recommended Next Step

1. Open a focused legal-hygiene cleanup PR/commit series to remove source-specific naming in active code/docs (`xtreme_*`, vendor-specific links) while keeping behavior unchanged.
2. Re-run this scan and require `Status: CLEAN` before merge of PR #16.
