# Helix Competitive Optimization Roadmap

Status: Active implementation plan (started 2026-11-16)  
Goal: Make Helix output consistently more intentional, layout-aware, and pro-looking than existing auto-sequencers (Downunder Auto Sequencer, xLightsAI, MCP generators, generic vendor sequences).

Principle: Improve the existing `core.sequence_builder` / `core.effect_engine` path. Do not replace the renderer. Measure improvements. Preserve determinism.

## Competitive differentiators to emphasize
- Section-aware energy arcs and coordinated group choreography (not independent prop loops).
- Prop-role intelligence and 3D spatial / audience-readability awareness.
- Stronger audio depth (stems, instrument routing, reliable phonemes).
- Band/character fidelity (three-tom drummer, singers, etc.).
- Controllable post-generation (presets, reports, editable XSQ).
- Deterministic, verifiable quality.

## Implementation slices (from AUTO_SEQUENCING_OUTPUT_IMPROVEMENT_SLICES.md, prioritized)

### Slice 1 — Sequence Plan Contract (IN PROGRESS)
- Minimal `sequence_plan` schema: sections, intensity targets, palette intent, prop emphasis, restraint.
- Advisory only; no renderer behavior change yet.
- File: `core/sequence_plan.py`
- Wired fail-soft into `full_show_orchestrator`.

### Slice 2 — Prop Role Map
- Vocabulary: centerpiece, outline, accent, character, singer, percussion, background, foreground, etc.
- Name-based inference for common models.
- Advisory first.

### Slice 3 — Density and Restraint Rules
- Whole-house hit limits, strobe caps, gaps, simultaneous dominant effect caps.
- Density scoring in reports.

### Slice 4 — Section Identity Scoring
- Coverage metrics, contrast between adjacent sections, intensity ramps, finale strength.

### Slice 5 — Palette Discipline
- Style-specific color families, penalize churn, reward motif persistence.

### Slice 6 — Motif Memory
- Reuse visual motifs across repeated sections with variation.

### Slice 7 — Manual-Lock Respect
- Protect locked effects from auto overwrite.

### Slice 8 — Explainable Variant Scores
- Expand reports for timing, density, contrast, palette, coverage.

### Slice 9 — Regression Fixtures
- Deterministic quality report snapshots.

### Slice 10 — GUI Integration
- Quality mode selection and toggles (after CLI/reporting is stable).

## Running checklist / handoff
- [x] Roadmap document created.
- [x] Sequence plan contract module added (`core/sequence_plan.py`).
- [x] Fail-soft wiring into full_show_orchestrator.
- [ ] Prop role map module.
- [ ] Density/restraint scoring.
- [ ] Section identity metrics.
- [ ] Palette discipline hooks.
- [ ] Motif memory.
- [ ] Integration into sequence_builder path (beyond orchestrator report).
- [ ] Tests for new contracts.
- [ ] Quality report enhancements.
- [ ] Drummer three-tom exporter alignment (parallel track).
- [ ] Vocal/phoneme reliability improvements (parallel track).

## Verification
Default proof (existing path still works):
```bash
PYTHONPATH=. python -m tools.run_sequence_with_quality_preset --quality-gate-preset showcase --dry-run -- --profile v27.3 -- --template template.xsq --audio LightsOutTheme.mp3 --layout-file allmodels/xlights_rgbeffects.xml --single --output-dir test_runs/showcase --variants 3
```

New plan can be exercised via full_show_orchestrator report.

## Handoff notes
This work is additive and fail-soft. Next agent should continue with Slice 2 (prop roles) and deepen the sequence_plan usage inside the builder without changing default output until scoring is in place.
