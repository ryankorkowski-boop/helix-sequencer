# xLights State of the Union + Vendor Benchmark Plan (2026-04-23)

## Objective
Produce XSQ output that rivals or exceeds paid vendor sequencing quality while staying legally compliant.

## What We Confirmed from Official xLights Docs

1. Start from the official quick-start flow (install, setup, new sequence, model creation, sequencer) and keep this as the onboarding baseline.
- Source: https://xlights.org/quick-start-guide/

2. Model import and model download are native in xLights Layout tab.
- Source: https://manual.xlights.org/xlights/chapters/chapter-four-tabs/download-import-models

3. Sequence import is the canonical route for purchased/shared vendor material, with model mapping in Import Effects.
- Source: https://manual.xlights.org/xlights/chapters/chapter-five-menus/import

4. xLights has built-in "Download Sequences/Lyrics" for free sequence links via Google Drive.
- Source: https://manual.xlights.org/xlights/chapters/chapter-five-menus/tools

5. Render order and Render All behavior materially affect final output quality and troubleshooting.
- Source: https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/render-all

6. Effect presets are reusable/shareable and should be part of our style system.
- Source: https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/effect-presets

## Practical Forum/Community Insights to Adopt

1. Package each sequence frequently as a disaster-recovery checkpoint.
- Source: https://auschristmaslighting.com/threads/xlights-tips-and-tricks.10722/post-95497

2. Preserve model provenance in model descriptions (vendor/source links), aiding maintenance and legal traceability.
- Source: https://auschristmaslighting.com/threads/xlights-tips-and-tricks.10722/post-95497

3. Keep render-order discipline (large groups and overlays intentionally ordered in Master View).
- Source: https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/render-all

## Legal Free Resource Intake (xLights Universe)

We created a machine-readable registry at:
- xlights/legal_free_resources_manifest.json

Current free/legal intake lanes:
1. xLights built-in free sequence list (Tools -> Download Sequences/Lyrics).
2. xLights native model import/download ecosystem.
3. Community free-to-test sequence catalogs.
4. Free custom xModel generation/export tools.

Guardrails:
1. Never redistribute downloaded vendor content unless explicitly allowed by the source terms.
2. Treat "free to download" and "free to redistribute/train" as different permissions.
3. Store license notes and source URL with every imported artifact.

## Professional Benchmark Set (for quality bar)

We curated a benchmark registry at:
- xlights/vendor_benchmark_manifest.json

Benchmark cohorts (examples):
1. Commercial benchmark source 1 (membership model, premium quality positioning)
2. Commercial benchmark source 2 (instrument-level sequencing emphasis)
3. Commercial benchmark source 3 (group/submodel-heavy methodology)
4. Commercial benchmark source 4 (professional packaging and licensing guidance)
5. Marketplace benchmark source 1 (creator diversity and catalog breadth)

Legal benchmark policy:
1. Use publicly available previews/metadata for style analysis by default.
2. Only use purchased sequence files when license allows private reference use.
3. Do not re-publish vendor sequence assets.

## Engine Work Added in This Branch

1. Added a full modular birdsong subsystem:
- core/birdsong_engine.py

2. Integrated birdsong into core runtime pipeline:
- CLI switches, runtime tuning, sequence timing-track output, and report payload wiring in core/effect_engine.py

3. Added unit tests for birdsong confidence, placement behavior, and CLI parsing:
- tests/test_birdsong_engine.py

4. Added legal asset sync utility:
- tools/open_source_assets_sync.py

## Workflow Improvements to Exceed Vendor Output

1. Add a recurring benchmark replay: run our sequences against a fixed vendor benchmark panel and compare metrics from report JSON.
2. Version style packs (effect preset families, transition motifs) like software releases.
3. Enforce per-song quality gates (coverage, diversity, density control, motif consistency) before shipping.
4. Require legal metadata for every external asset at intake time.
5. Keep specialized engines modular (birdsong, lyric sync, pulse logic) and compose them by policy, not ad-hoc edits.
