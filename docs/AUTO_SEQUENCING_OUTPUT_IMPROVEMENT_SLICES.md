# Auto Sequencing Output Improvement Slices

Status: active plan  
Scope: improve output quality through the existing `core.sequence_builder` / `core.effect_engine` path  
Principle: calibrate and instrument the current engine before adding a competing renderer

## Why This Exists

Helix already has a maintained generation path and quality gate wrapper. The next work should improve the actual output by tightening timing, section identity, prop-role decisions, color discipline, density restraint, and scoring. This plan is intentionally sliced so each step can be reviewed, tested, and reverted independently.

## Current Ground Truth

The current active path is the existing builder/effect engine stack, not a replacement sidecar renderer:

```bash
PYTHONPATH=. python -m tools.run_sequence_with_quality_preset --quality-gate-preset showcase --dry-run -- --profile v27.3 -- --template template.xsq --audio LightsOutTheme.mp3 --layout-file allmodels/xlights_rgbeffects.xml --single --output-dir test_runs/showcase --variants 3
```

Primary seams:

- `core/effect_engine.py`
- `core/sequence_builder.py`
- `core/engine_style_catalog.py`
- `tools/build_helpers/variants.py`
- `tools/build_helpers/calibration.py`
- `tools/run_sequence_with_quality_preset.py`
- `xlights/xsq_writer.py`

## Output Quality Target

A better Helix sequence should be:

- musically timed, not merely audio-reactive
- section-aware, with visible intro / verse / chorus / bridge / finale contrast
- prop-aware, using different model groups for different musical jobs
- restrained, with strong moments saved for actual strong musical moments
- color-coherent, with palettes that persist long enough to read
- layered, with foreground / background / accent motion separated
- measurable, with scoring that can explain why one variant won
- legal-safe, using source-agnostic quality metrics rather than copying shows

## Slice 1 — Add Sequence Plan Contract

Goal: define the data Helix should emit or infer before rendering effects.

Deliverables:

- Add a minimal `sequence_plan` schema/contract.
- Include sections, target intensity, palette intent, prop group emphasis, and restraint settings.
- Do not route the renderer through it yet.

Acceptance:

- Contract is documented.
- Sample JSON can be validated or sanity-checked.
- No behavior change to existing renders.

## Slice 2 — Add Prop Role Map

Goal: stop treating every xLights model as interchangeable.

Deliverables:

- Add a prop-role vocabulary: `centerpiece`, `outline`, `accent`, `character`, `singer`, `percussion`, `background`, `foreground`, `strobe`, `fill`.
- Add a simple name-based inference layer for common props: mega tree, roofline, arches, snowman singer, drummer, guitarist, bassist, mini trees, house outlines.
- Keep it advisory at first.

Acceptance:

- Given model names, Helix can produce role hints.
- Existing output remains unchanged unless a caller explicitly asks for the hints.

## Slice 3 — Add Density and Restraint Rules

Goal: reduce clutter and avoid firing everything constantly.

Deliverables:

- Add source-agnostic restraint limits: whole-house hits per section, strobe caps, minimum gap between major hits, maximum simultaneous dominant effects.
- Add a density score and overuse penalty to candidate reporting.

Acceptance:

- Reports show where density was too high.
- Existing quality gates can penalize clutter without banning creative output.

## Slice 4 — Add Section Identity Scoring

Goal: make chorus/verse/finale look different on purpose.

Deliverables:

- Add section coverage metrics.
- Add contrast scoring between adjacent sections.
- Reward visible intensity ramps and finale strength.

Acceptance:

- Variant shortlist can explain section contrast.
- A flat-looking render should score lower than a render with clear section shape.

## Slice 5 — Add Palette Discipline

Goal: improve readability and polish through controlled color choices.

Deliverables:

- Add palette names and allowed color families per style.
- Penalize random color churn unless the style explicitly allows it.
- Reward repeated motif colors across recurring sections.

Acceptance:

- Reports flag color chaos.
- Styles can still opt into chaotic/comedy/EDM palettes when intentional.

## Slice 6 — Add Motif Memory

Goal: make generated sequences feel composed rather than random.

Deliverables:

- Identify repeated musical sections.
- Reuse visual motifs with variation instead of inventing unrelated effects every time.
- Track motif family, palette, prop group, and intensity range.

Acceptance:

- Repeated choruses can share a visual identity.
- Motif reuse appears in reports.

## Slice 7 — Add Manual-Lock Respect

Goal: let human hero moments coexist with auto generation.

Deliverables:

- Mark manually placed effects as locked.
- Prevent auto-fill from overwriting locked regions unless explicitly allowed.
- Add reporting for avoided/trimmed generated effects near locked areas.

Acceptance:

- Manual work survives auto-generation.
- Reports prove what Helix respected.

## Slice 8 — Promote Winning Variants With Explainable Scores

Goal: make variant selection trustworthy.

Deliverables:

- Expand shortlist output to show timing, audit, density, section contrast, palette, prop coverage, and rejected-effect count.
- Make `showcase` and `vendor` presets explain why a candidate passed or failed.

Acceptance:

- A user can understand why one variant was selected.
- Failed variants include actionable reasons.

## Slice 9 — Build Regression Fixtures

Goal: prevent future changes from silently making output worse.

Deliverables:

- Add deterministic smoke fixtures for one small layout and one known test audio file.
- Snapshot the quality report, not the full exported sequence.
- Keep snapshots tolerant enough to survive harmless formatting changes.

Acceptance:

- Tests catch major quality-score regressions.
- Tests do not require proprietary/vendor sequence files.

## Slice 10 — Integrate Into GUI Carefully

Goal: expose improvements without overwhelming the user.

Deliverables:

- Add output-quality mode selection: `general`, `showcase`, `vendor`.
- Add toggles for palette discipline, density restraint, section contrast, and manual-lock respect.
- Keep safe defaults.

Acceptance:

- Existing GUI launch still works.
- New controls map to documented engine flags or wrapper options.

## Working Rule

Every slice must answer three questions before merging:

1. What output behavior does this improve?
2. How do we measure the improvement?
3. What command proves the old path still works?

Default proof command:

```bash
PYTHONPATH=. python -m tools.run_sequence_with_quality_preset --quality-gate-preset showcase --dry-run -- --profile v27.3 -- --template template.xsq --audio LightsOutTheme.mp3 --layout-file allmodels/xlights_rgbeffects.xml --single --output-dir test_runs/showcase --variants 3
```

## Do Not Do Yet

- Do not replace `core.effect_engine.py` with a new renderer.
- Do not add AI calls to the render loop.
- Do not learn from third-party/vendor sequences unless the source and permission are explicitly legal and documented.
- Do not copy exact public display choreography.
- Do not make GUI changes until the command-line/reporting path is stable.
