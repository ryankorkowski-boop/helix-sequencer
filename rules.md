# Ultimate xLights Rules (Legal + Technical)

This file is a policy-and-engineering ruleset for building high-quality xLights sequences without copying proprietary choreography.

## Canonical Policy Stack

If this file and other policy docs diverge, resolve in this order:

1. `docs/legal_learning_policy.md`
2. `docs/source_hygiene_checklist.md`
3. `docs/helix_master_rulebook.md`
4. `rules.md` (this file as compact quick-reference)

## 1) Legal And Ethical Boundary (Non-Negotiable)

1. Use official docs, release notes, and public tool documentation as process knowledge, not as choreography templates.
2. Do not copy timeline patterns, phrase maps, effect timing, or model-by-model artistic choices from third-party sequences.
3. Imported sequences are for licensed use and adaptation within rights granted by the source; do not redistribute assets beyond license terms.
4. Preserve attribution, source URLs, and license notes for every imported model/asset/preset.
5. Learning systems must only persist your own legally generated outputs and metadata, never unlicensed third-party sequence content.

## 2) Source Priority And Trust Model

1. Tier 1 (authoritative): xLights manual, xlights.org, official release/change notes, xLights GitHub.
2. Tier 2 (project-owned practice): user-authored notes, Helix-generated experiments, and local regression fixtures.
3. Tier 3 (community troubleshooting): public troubleshooting guidance may inform debugging only when provenance is clear.
4. When sources conflict:
   - Prefer current official manual/release notes.
   - Validate with a small reproducible test sequence.

## 3) Core Project Hygiene Rules

1. Keep show/media directories explicit and stable.
2. Back up before upgrades or major imports.
3. Keep sequence, layout, media, presets, and custom assets in predictable subfolders.
4. Version-lock high-stakes shows (document the xLights release used).
5. Use deterministic naming:
   - Models: semantic + location + index.
   - Groups: functional intent (`ALL_MODELS`, `CHORUS_FRONT`, `FACES`).
   - Timing tracks: purpose + granularity (`BEAT_120`, `LYRIC_WORDS`, `PHRASES`).

## 4) Layout Engineering Rules

1. Build accurate model geometry before sequencing effects.
2. Use Model Groups for orchestration, but keep specialized props independent when needed.
3. Prefer minimal internal grids for model groups unless a larger grid is strictly needed.
4. Avoid oversized group grids that increase render cost and obscure intent.
5. Maintain submodels and states carefully; validate after model remaps.
6. Keep channel mapping authoritative and single-sourced; avoid ambiguous dual mappings.

## 5) View And Render Order Laws

1. Master View controls model render order.
2. Data layers render bottom-to-top.
3. Model effect layers render bottom-to-top.
4. Large umbrella groups should be placed intentionally in order so they do not unintentionally override detailed layers.
5. If output looks wrong, inspect order first before changing effect content.

## 6) Timing Discipline Rules

1. Timing tracks are planning scaffolds; effects become independent after placement.
2. Maintain multiple timing tracks for different tasks:
   - Beat grid
   - Phrase/section grid
   - Lyric word/phoneme tracks
3. Keep one active timing track when placing effects; display multiple only when reviewing relationships.
4. Use fixed timing for coarse rhythmic work, variable timing for expressive edits.
5. Import/export timing tracks for reproducible collaboration.

## 7) Sequencing Construction Rules

1. Sequence by section intent, not random effect placement:
   - Verse: restrained motion
   - Build: growing density/energy
   - Chorus: broader visual coverage/contrast
   - Outro: controlled release
2. Separate role layers:
   - Foundation (structure)
   - Rhythm (percussion response)
   - Melody/lead focus
   - Accent/transitions
3. Limit concurrent clutter. More effects is not always better.
4. Use presets to standardize reusable micro-patterns (color+movement combinations), not to clone full sequence identity.
5. Prefer effect families that match prop topology (line effects on lines, matrix dynamics on matrices, etc.).

## 8) Import/Mapping Rules

1. Always inspect external sequence material in an isolated folder first.
2. Render and preview before mapping.
3. Build explicit donor-to-target mapping notes for model counts and topology.
4. Map by function and geometry, not by name similarity alone.
5. Re-render after mapping and resolve channel/group mismatches before artistic edits.
6. Keep imported timing and effect layers distinguishable from native work until final integration pass.
7. Use only material where the license and intended use are clear.

## 9) Performance And Render Stability Rules

1. Use minimal grids and avoid unnecessary giant groups.
2. Purge render cache when behavior appears stale or after major model topology changes.
3. Keep heavy bitmap/video effects constrained to where they matter.
4. Reduce layout/model overdraw and duplicate high-cost layers.
5. Batch render only selected target sequences for turnaround speed.
6. Profile sluggish sequences by disabling expensive layers one class at a time.

## 10) Check/Validation Rules

1. Treat sequence checks as quality gates, not optional warnings.
2. Resolve high-impact warnings first:
   - render-order conflicts
   - mapping mismatches
   - stale/legacy value curve/state artifacts
3. Re-run checks after every structural change (layout remap, group order changes, major imports).
4. Track recurring warning classes and create local fix playbooks.

## 11) Packaging, Support, And Reproducibility

1. Use package/log tools when escalating issues.
2. Include sequence + layout + logs + relevant assets required to reproduce.
3. Keep a reproducible debug kit:
   - xLights version
   - OS/build info
   - minimal failing sequence
   - screenshots/video of expected vs actual

## 12) Audio/Lyric Intelligence Rules (Helix-Specific)

1. Mood/genre hints should influence macro scene choices, not override structure.
2. Lyric detection should be dependency-aware:
   - primary transcription path
   - fallback path
   - explicit "no lyrics found" handling
3. Lyric interpretation should remain rule-based first:
   - trigger lexicons
   - repeat phrase detection
   - mood score from lexical + audio context
4. Keep semantic lyric cues additive and bounded; never let them flood timeline density.

## 13) Quality Rulebook (Helix-Specific)

1. Quality score must be decomposable into components (density, structure, keyboard balance, validation, coverage, detail, diversity, dominance, audit blend).
2. Audit score must reflect overlap/clutter control, section coverage, intensity balance, and musical coherence.
3. Gate pass/fail should include:
   - minimum quality
   - minimum audit
   - maximum rejected placements
4. Any score threshold change must be versioned and justified by regression tests.

## 14) Anti-Patterns To Avoid

1. Sequencing from one giant all-model group first and never refining.
2. Ignoring Master View render order when overrides appear.
3. Overusing random effects without scene intent.
4. Importing donor sequences directly into production folder without sandbox pass.
5. Treating community anecdote as canonical behavior.
6. Adding AI-driven complexity before deterministic placement hygiene.

## 15) PR/Merge Rules For This Repo

1. Keep modular slices small and testable.
2. Integrate helper/tooling slices before high-risk runtime changes.
3. Add or update targeted tests with each behavior change.
4. Avoid broad merges of many runtime subsystems at once.
5. Document risk, rollback, and validation commands for each slice.

## 16) Practical Enforcement Checklist

1. Before sequencing:
   - layout validated
   - group/render order reviewed
   - timing tracks prepared
2. During sequencing:
   - section intent visible
   - density under control
   - check warnings monitored
3. Before release:
   - full render
   - check/validation pass
   - packaged reproducibility bundle
   - legal/source attribution notes complete

## 17) Provenance (Research Inputs)

- xLights Quick Start Guide: [xlights.org/quick-start-guide](https://xlights.org/quick-start-guide/)
- xLights Manual (Render All): [manual.xlights.org/.../render-all](https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/render-all)
- xLights Manual (Timing Tracks): [manual.xlights.org/.../timing-tracks](https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/timing-tracks)
- xLights Manual (Layers): [manual.xlights.org/.../layers](https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/layers)
- xLights Manual (Effect Presets): [manual.xlights.org/.../effect-presets](https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/effect-presets)
- xLights Manual (Import): [manual.xlights.org/.../import](https://manual.xlights.org/xlights/chapters/chapter-five-menus/import)
- xLights Manual (Tools): [manual.xlights.org/.../tools](https://manual.xlights.org/xlights/chapters/chapter-five-menus/tools)
- xLights Manual (Model Groups): [manual.xlights.org/.../model-groups](https://manual.xlights.org/xlights/chapters/chapter-four-tabs/model-groups)
- xLights Manual (Help/Support links): [manual.xlights.org/.../help](https://manual.xlights.org/xlights/chapters/chapter-five-menus/help)
- xLights Downloads/Releases: [xlights.org/releases](https://xlights.org/releases/)
- xLights GitHub Wiki Home: [github.com/xLightsSequencer/xLights/wiki](https://github.com/xLightsSequencer/xLights/wiki)

Note: This ruleset intentionally captures methods, guardrails, and workflow heuristics only. It excludes proprietary sequence choreography and restricted content replication.
