# Helix Implementation Roadmap

Status: Active planning document  
Scope: staged implementation from repo cleanup toward automatic sequencing

## 1. Roadmap Rules

This roadmap is intentionally staged. Do not skip validation gates.

Every implementation slice must be:

1. Small enough to review.
2. Covered by tests or deterministic fixtures.
3. Source-safe.
4. Backward compatible unless the change is explicitly a cleanup/removal.
5. Proven by commands, diffs, and report output.

Codex or any agent working on this repo must prefer one complete safe slice over many half-finished features.

## 2. Stage 0: Legal And Source Hygiene

Goal: ensure Helix has a clean foundation.

Required outcomes:

1. Questionable learning notes cleared or quarantined.
2. Source policy blocks unknown, paid, private, scraped, no-AI, no-scraping, and no-provenance inputs.
3. External resource manifests use `permitted_use`, not training authorization language.
4. Docs point to source-agnostic guidance.
5. Tests exist for blocked and allowed source types.

Exit gate:

- Legal/source hygiene search returns no obvious questionable retained guidance.
- `helix_knowledge/source_policy.py` blocks unsafe source types.
- Tests still pass locally or in CI.

## 3. Stage 1: Repo Truth And Baseline Proof

Goal: make current behavior inspectable before adding major features.

Tasks:

1. Inventory active modules, docs, tests, and generated assets.
2. Document current branch and recent commits when preparing large work.
3. Identify stale or duplicate files.
4. Ensure unit tests are runnable from a fresh checkout.
5. Confirm current xLights layout generation scripts produce stable outputs.

Exit gate:

- A baseline test command is documented.
- The test suite passes or known failures are documented with exact reasons.
- Generated files have clear owners.

## 4. Stage 2: Helixia As Canonical Test Layout

Goal: make Helixia the proof layout for automatic sequencing.

Tasks:

1. Confirm Helixia layout generator exists and is deterministic.
2. Confirm generated xLights layout files are committed or reproducibly generated.
3. Confirm houses/lots, snowman band, cactus, tubeman, and traditional props exist where intended.
4. Add model metadata for prop role, performer role, pixel/AC behavior, and power notes.
5. Add tests that inspect generated XML for expected prop families and groups.

Exit gate:

- `tests/test_helixia_layout.py` or equivalent proves the layout exists.
- Prop-role metadata is machine-readable.
- Layout output remains stable across repeated builds.

## 5. Stage 3: Layout Intelligence

Goal: let Helix understand arbitrary layouts before sequencing them.

Tasks:

1. Parse model names, types, coordinates, groups, submodels, and render order.
2. Classify prop families: roofline, window, arch, matrix, tree, face, character, performer, accent, flood/wash, AC, pixel.
3. Infer default prop roles:
   - structure
   - travel
   - hero
   - vocals
   - rhythm
   - mood
   - accent
   - performer
4. Support user override metadata.
5. Emit a layout intelligence report.

Exit gate:

- A fixture layout produces a stable JSON layout report.
- Tests prove expected props are classified correctly.
- Ambiguous models are flagged rather than silently guessed.

## 6. Stage 4: Audio Intelligence

Goal: create useful musical structure without overpromising.

Tasks:

1. Detect or import tempo, beat grid, sections, phrase boundaries, and accents.
2. Store energy curves and transient cues.
3. Support optional lyrics/phonemes when user-provided or lawfully generated.
4. Emit an audio intelligence report.
5. Keep fallback behavior deterministic for test fixtures.

Exit gate:

- A sample audio or fixture payload produces stable section/beat/energy output.
- Reports are machine-readable.
- No copyrighted audio is committed unless rights are explicit.

## 7. Stage 5: Visual Intent Planner

Goal: plan before placing effects.

Tasks:

1. Convert audio sections and layout roles into `VisualIntent` objects.
2. Assign focal target per section or moment.
3. Choose density budget, palette family, motion grammar, and prop-family participation.
4. Add character/performance moments for Helixia performer props.
5. Emit a visual plan artifact before effect rendering.

Exit gate:

- Tests prove a known section plan creates expected intent categories.
- The plan can be reviewed without opening xLights.
- The plan contains no source-specific choreography references.

## 8. Stage 6: Effect Placement Engine

Goal: turn visual intent into xLights-compatible effect placements.

Tasks:

1. Map intent types to allowed effect families.
2. Respect prop roles and layout geometry.
3. Keep layers readable.
4. Avoid unsafe flash density.
5. Avoid power overload and AC micro-flicker.
6. Emit placement reports and warnings.

Exit gate:

- Fixture input creates deterministic placement output.
- Placement reports include counts, roles, warnings, and quality metrics.
- Tests catch excessive flash-like events and unsupported prop mappings.

## 9. Stage 7: Quality Grading And Preview Reports

Goal: make quality measurable.

Tasks:

1. Score musicality, layout coverage, prop diversity, focal clarity, color discipline, motion coherence, rest/contrast, layer control, safety, and power awareness.
2. Produce human-readable and machine-readable reports.
3. Flag problems with actionable recommendations.
4. Support comparison between subtle, balanced, showcase, and max profiles using Helix-generated outputs only.

Exit gate:

- A test fixture produces a stable quality report.
- Low-quality fixtures fail or warn for clear reasons.
- Quality scoring is source-agnostic.

## 10. Stage 8: xLights Export And User Workflow

Goal: make output usable in real xLights workflows.

Tasks:

1. Export effect plans, timing tracks, debug sidecars, and layout-aware artifacts.
2. Preserve safe import boundaries.
3. Provide clear user instructions for importing into xLights.
4. Add smoke tests for exported file shape.
5. Keep generated artifacts deterministic where possible.

Exit gate:

- A complete sample run produces expected output files.
- Tests validate the files are structurally sane.
- User-facing instructions are current.

## 11. Stage 9: GUI And Operator Experience

Goal: make Helix usable without living in terminal logs.

Tasks:

1. Add a clear project wizard: audio, layout, profile, output folder.
2. Show legal/source-hygiene status.
3. Show layout intelligence report.
4. Show audio intelligence report.
5. Show visual plan preview.
6. Show quality warnings before export.
7. Support re-run with changed profile.

Exit gate:

- GUI can run a fixture project end-to-end.
- Errors are understandable.
- Advanced options do not hide safety-critical warnings.

## 12. Stage 10: Iterative Learning From Helix Outputs

Goal: improve from user feedback and internal experiments only.

Allowed learning loop:

1. Generate original Helix output.
2. User rates or edits it.
3. Helix stores feature-level feedback and quality metrics.
4. Future runs adjust parameters or planning heuristics.

Forbidden learning loop:

1. Scrape third-party shows.
2. Extract creator timing patterns.
3. Preserve vendor sequence structure.
4. Train from private or unclear-rights materials.

Exit gate:

- Learning memory records provenance.
- Unsafe source types are rejected.
- User feedback can be deleted or reset.

## 13. Recommended Next Implementation Slice

Start with Stage 2 and Stage 3 together only where they overlap:

1. Strengthen Helixia layout tests.
2. Emit a Helixia layout intelligence report.
3. Add prop-role metadata for snowman band, cactus, tubeman, houses/lots, rooflines, matrices, and trees.
4. Do not add new visual effects yet.
5. Do not merge unrelated core changes.

Validation command should be something like:

```bash
PYTHONPATH=. python -m pytest tests/test_helixia_layout.py tests/test_professional_sequence_intelligence.py
```

If those tests do not exist or do not match current names, the agent must inspect the repo and propose the exact current command before editing.
