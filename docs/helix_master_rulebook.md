# Helix Master Rulebook For xLights

Date: 2026-05-01  
Status: Active  
Scope: Legal-safe, source-agnostic sequencing engineering for xLights environments.

## 0. Purpose

This rulebook defines how Helix should design, adapt, validate, and automate xLights sequences without copying protected choreography or source-specific expression.

The document is intended to be:

1. Technical and operational.
2. Legal-safe by default.
3. Deterministic first, AI second.
4. Reproducible across layouts, songs, and sequencing teams.

## 1. Rule Language

Normative keywords:

1. MUST: mandatory.
2. SHOULD: recommended default with documented exceptions.
3. MAY: optional tactic.

## 2. Legal Boundary

1. Helix MUST learn process and mechanics, not protected creative expression.
2. Helix MUST NOT copy sequence timelines, phrase maps, or model-specific choreography from third-party works.
3. Helix MUST NOT ingest paid/private materials without explicit rights.
4. Helix MUST preserve provenance records for all extracted rules.
5. Helix MUST output generalized technical language, not source imitation.

## 3. Source Trust Model

Priority for behavior truth:

1. Official manual and release notes.
2. Official repository documentation and code behavior.
3. Public community troubleshooting discussions.
4. Internal experiments and project-specific heuristics.

Conflict protocol:

1. Prefer higher-tier source.
2. Create a minimal reproducible test.
3. Record chosen interpretation and confidence.

## 4. xLights Object Model And File Contracts

Helix MUST treat these artifacts as the canonical project graph:

1. `xlights_rgbeffects.xml`: layout, models, controllers, groups, and many sequence-related definitions.
2. `.xsq` / `.xml` sequence files: effect placement metadata.
3. `.fseq`: rendered channel output.
4. `.xmodel`: custom/imported model definition.
5. `.xmap`: import mapping between donor and target models.
6. `.xtiming`: exported/imported timing tracks.
7. `.xvc`: value curve definitions.
8. `.xcc`: color curve definitions.
9. `.xpreset`: effect preset bundles.

Helix SHOULD keep show folder structure stable and explicit.

## 5. Render Pipeline Laws

Helix MUST internalize render order:

1. Data layers render bottom to top.
2. Model layers render bottom to top.
3. Models/groups render in Master View order (top to bottom).
4. Overlapping channels are resolved by this render order, not by placement time.

Operational implications:

1. Unexpected overrides are usually ordering errors first, parameter errors second.
2. Large umbrella groups SHOULD be positioned intentionally to avoid accidental dominance.
3. Non-Master views are sequencing convenience views and do not define final render order.

## 6. Layout, Mapping, And Channel Governance

### 6.1 Model Construction

1. Models MUST reflect real physical topology before sequencing begins.
2. Model type, strand count, node count, and orientation MUST match wiring reality.
3. Start channel definition SHOULD use controller-aware assignment where possible.
4. Non-contiguous addressing MAY use per-strand start channels.

### 6.2 Channel Integrity

1. Channel overlap warnings MUST be resolved unless overlap is intentional.
2. Intentional overlap MUST be documented in model notes.
3. Shadow/surrogate model use MUST be explicit and tracked.

### 6.3 Group Strategy

1. Groups SHOULD represent functional orchestration sets (all house, rhythm props, vocals, accents).
2. Group internal order MUST be treated as render-significant for per-model render styles.
3. Minimal grid SHOULD be default for groups to reduce render cost.
4. Preview-scale grid SHOULD be used only when an effect requires it.

### 6.4 Submodels

1. Submodels SHOULD be used for repeatable partial-control zones.
2. Submodel boundaries MUST reflect real prop segmentation.
3. Submodel naming SHOULD be semantic (`left_arc`, `roof_inner`, `face_outline`).

## 7. Timing Architecture Rules

### 7.1 Timing Track Taxonomy

Helix SHOULD separate timing concerns:

1. Beat grid track.
2. Phrase/section track.
3. Word/lyric track.
4. Phoneme track.
5. Accent/transient track.

### 7.2 Timing Track Operations

1. Timing tracks MAY be created from fixed intervals, imported files, or manual edits.
2. Import/export via `.xtiming` SHOULD be used for reproducible collaboration.
3. Imported tracks from external formats MUST be validated against waveform alignment.

### 7.3 Practical Performance Rule

1. Heavy global dependency on one timing track SHOULD be avoided on large sequences.
2. Track cloning by purpose MAY improve interaction responsiveness in complex projects.
3. Timing edits MUST be followed by targeted playback checks on affected windows.

## 8. Effect Placement And Arrangement System

### 8.1 Section-First Strategy

Helix SHOULD build in macro sections:

1. Intro: establish motif and palette.
2. Verse: moderate density, directional clarity.
3. Pre-chorus/build: controlled escalation.
4. Chorus/drop: broad coverage and contrast.
5. Bridge: deliberate variation.
6. Outro: energy release and closure.

### 8.2 Role Layering

Each section SHOULD include distinct functional layers:

1. Foundation layer (ambient continuity).
2. Rhythm layer (drums/percussion locks).
3. Lead layer (melody/vocal focus).
4. Accent layer (fills, hits, transitions).

### 8.3 Placement Constraints

1. Effect density MUST remain readable at full-preview speed.
2. Simultaneous high-energy effects SHOULD be capped by section intent.
3. Repeated motifs SHOULD vary one parameter at a time (position, direction, cycle, palette, or scale).

## 9. Parameter Engineering

### 9.1 Deterministic Parameter Workflow

For every effect edit:

1. Define intent first (motion, texture, emphasis, handoff).
2. Set base parameter values.
3. Add value/color curves only where dynamic modulation is required.
4. Validate against model preview and house preview.

### 9.2 Use Effect Assist And Layer Tools

1. Effect Assist SHOULD be used for coordinate-based effects (for example morph-like point placement).
2. Layer settings SHOULD handle geometry transforms before custom workaround logic.
3. Bulk edit MAY be used for controlled global tuning, followed by selective rollback.

## 10. Intensity And Value Curve Rules

### 10.1 Value Curve Scope

Value curves modulate effect attributes over time or other domains, and MUST be used intentionally.

Typical uses:

1. Cycles ramping through a phrase.
2. Progressive motion acceleration/deceleration.
3. Controlled duty-cycle or pulse shaping.
4. Sub-buffer/transform modulation for staging movement.

### 10.2 Intensity Stack

Helix MUST distinguish these layers of brightness control:

1. Effect-level intensity behavior (for example On/Ramp settings and animated attributes).
2. Model-level dimming curves and gamma adjustments.
3. Color-dependent apparent brightness.

Guidance:

1. Use model dimming/gamma for hardware normalization and eye comfort.
2. Use effect-level intensity curves for musical expression.
3. Avoid compensating layout/wiring problems with aggressive brightness curves.

### 10.3 Curve Hygiene

1. Curves SHOULD remain sparse and interpretable.
2. Shared reusable curves MAY be exported/imported via `.xvc`.
3. Curve presets SHOULD be named by intent (`slow_attack`, `double_pulse`, `late_ramp`).

## 11. Color And Color Curve Rules

### 11.1 Palette Architecture

1. Palette selection MUST match section emotional intent.
2. Phrase-level dominant color count SHOULD be constrained for readability.
3. Rapid full-palette churn SHOULD be limited to explicit high-energy windows.

### 11.2 Color Curves

1. Timed color curves control changes across effect duration.
2. Spatial color curves control changes across model coordinates and direction.
3. Blend mode choice (gradient vs sharp) MUST match transition intent.
4. Color curves MAY be exported/imported via `.xcc`.

### 11.3 Single-Channel Color Routing

1. Single-channel props respond to relevant channel components.
2. Group-level RGB effects on mixed prop types MUST be preview-validated for routing behavior.
3. White and mixed colors SHOULD be tested on real hardware when using mixed channel types.

## 12. Layering, Blending, And Canvas Governance

### 12.1 Layer Blending Discipline

1. Blend mode choice MUST be intentional, not default drift.
2. Transition in/out settings SHOULD be reset when no longer required.
3. Mix sliders SHOULD be used to avoid full-layer domination when layering textures.

### 12.2 Canvas Mode

1. Canvas mode MUST be used only for effects that rely on prior-layer pixel data.
2. Canvas mode usage MUST be isolated and documented because it changes render semantics.
3. Debugging canvas issues SHOULD include quick A/B with erase-like behavior.

### 12.3 Persistent Buffer

1. Persistent rendering MAY create useful trails and accumulations.
2. Persistent use MUST be visually validated for smearing artifacts.

## 13. Shader Rules

### 13.1 Shader Preconditions

1. Shader files MUST be present and compatible.
2. OpenGL capability MUST satisfy shader requirements.
3. Some shaders require canvas mode; this MUST be checked before troubleshooting.

### 13.2 Shader Diagnostics

Color-coded failure interpretation:

1. Missing file.
2. Compilation/format incompatibility.
3. Hardware capability mismatch.

### 13.3 Shader Performance

1. Shader-heavy sequences SHOULD be performance-profiled early.
2. Driver and hardware configuration SHOULD be validated when shader anomalies appear.

## 14. Custom Model Engineering

### 14.1 Grid Construction

1. Node numbering MUST reflect actual wiring order.
2. Grid dimensions SHOULD be minimal but complete.
3. Flip/rotate/compress/trim tools SHOULD be used before manual renumbering when possible.

### 14.2 Visual-Assisted Build

1. Background-image aided modeling MAY be used for complex outlines.
2. Generated custom-model workflows SHOULD be validated for missed/duplicate nodes.

### 14.3 Model Portability

1. Export custom models as `.xmodel` for reuse.
2. Imported `.xmodel` assets MUST be reviewed for channel and geometry compatibility.
3. Face/state/submodel definitions in imported custom models MUST be sanity-checked.

### 14.4 Remap Custom Models

1. Remap tools MAY transfer faces/states/submodels to rewired variants.
2. Source and target models MUST be dimensionally compatible with aligned node positions.

## 15. Singing Faces, Phonemes, And State-Based Props

### 15.1 Face Definition Rules

1. Each singing model MUST have explicit face definitions.
2. Phoneme-to-node mapping MUST be reviewed visually and on output.
3. Eye, outline, and lead in/out settings SHOULD be used deliberately for readability.

### 15.2 Timing Pipeline

1. Phrase -> word -> phoneme breakdown SHOULD be corrected manually where needed.
2. Unknown words MUST be resolved through dictionary workflows or manual adjustment.
3. Multi-voice setups SHOULD use separate tracks and explicit mapping.

### 15.3 Face Effect Placement

1. Face effects MUST bind to the correct timing track and face definition.
2. Outline and transparency options SHOULD be tested against lower layers.
3. Duplicate-use timing across voices MAY be used intentionally for choruses/unison.

### 15.4 State Effect For Non-Face Props

1. State definitions SHOULD map label tokens to node ranges.
2. Timing labels MUST exactly match state tokens.
3. State mode and color mode SHOULD be selected based on whether iteration or direct state recall is desired.

## 16. Import, Data Layers, Conversion, And Adaptation

### 16.1 Import Effects Vs Data Layers

Choose intentionally:

1. Import Effects when editable per-effect adaptation is required.
2. Data Layer import when fast mapped playback/overlay is sufficient.

Constraints:

1. Data-layer imported content is not directly effect-editable.
2. Re-import MUST be used if the source file changes.

### 16.2 Import Mapping Workflow

1. Open donor content in an isolated folder first.
2. Study model intent and topology before mapping.
3. Ensure target sequence view has models available before import mapping.
4. Map by function/topology, not by naming similarity alone.
5. Save mapping as `.xmap` for repeatability.

### 16.3 Sequence Adaptation To New Layouts

1. Preserve role equivalence (lead prop -> lead prop, rhythm prop -> rhythm prop).
2. Rebuild spatial motifs for geometry mismatches.
3. Validate imported timing tracks and remap drift after render.
4. Keep imported and native layers distinguishable until final polish pass.

### 16.4 Conversion Tool Boundary

1. File conversion tools SHOULD be used for cross-format conversion and player outputs.
2. Conversion tool SHOULD NOT be used as the primary path for creating editable xLights effect structure.
3. Use verbose mapping diagnostics when channel mapping is uncertain.

## 17. Export, Packaging, And Portability

1. Rendered output SHOULD be regenerated before sharing/deploying.
2. Packaging SHOULD include all required dependencies for reproducibility.
3. Audio-sharing decisions MUST follow rights constraints.
4. Export model workflows MUST choose between rendered-clean export and context-including export based on goal.
5. FSEQ version/compression choice MUST match target player/controller compatibility.

## 18. Lua And Automation Rules

### 18.1 Script Runner Basics

The scripting environment exposes script variables and helper functions for automation flows.  
Scripts SHOULD be treated as production automation code with review and rollback paths.

### 18.2 Lua Safety Rules

1. Scripts MUST be idempotent where possible.
2. Scripts MUST log intent and outcomes.
3. Scripts MUST avoid force-closing sequences unless explicitly required.
4. Scripts MUST preserve show-folder and sequence integrity.

### 18.3 Automation API Usage

Automated command workflows MAY perform:

1. Open sequence.
2. Render all.
3. Save sequence/layout.
4. Batch render.
5. Export/package workflows.
6. Import/mapping commands where supported.

Caution:

1. Experimental automation endpoints MUST be version-gated.
2. Automation command sets MAY evolve; scripts SHOULD validate command support at runtime.

### 18.4 Recommended Automation Pattern

1. Validate environment and version.
2. Load sequence with explicit issue-handling mode.
3. Run deterministic edits.
4. Render.
5. Run check/validation.
6. Save artifacts.
7. Emit machine-readable summary log.

## 19. Performance Engineering

### 19.1 Primary Levers

1. Minimize oversized group grids.
2. Use low-definition render tactically for heavy sequencing sessions.
3. Manage render cache location and size.
4. Purge render cache when stale behavior appears.
5. Use simpler source media dimensions for heavy picture/video workflows.

### 19.2 Diagnostic Sequence

When performance drops:

1. Disable expensive layers class-by-class.
2. Reduce group grid complexity.
3. Test with simplified timing dependencies.
4. Validate graphics driver and shader path behavior.
5. Re-render and compare timings.

## 20. Quality Gates And Validation

### 20.1 Minimum Technical Gate

Before release:

1. Render complete with no unresolved critical issues.
2. Check sequence findings triaged.
3. Mapping integrity reviewed (channels, views, groups, submodels).
4. Timing/faces pass verified in playback.
5. Export/package reproducibility tested.

### 20.2 Visual Readability Gate

1. No sustained clutter in major sections.
2. Focal props remain readable during vocals and lead moments.
3. Contrast and motion direction support musical phrase boundaries.
4. Transition quality remains stable across section handoffs.

### 20.3 Regression Gate

1. Layout changes require targeted re-render and spot-check.
2. Controller mapping changes require output sanity checks.
3. Imported sequence updates require remap and precedence revalidation.

## 21. Competitive Evaluation Rubric (Judge-Oriented)

Suggested scoring weights:

1. Musicality and phrasing alignment: 25
2. Structural coherence across sections: 20
3. Mapping and topology fitness: 20
4. Layering clarity and visual readability: 15
5. Technical robustness and reproducibility: 10
6. Originality under legal-safe constraints: 10

Automatic deductions:

1. Unreadable clutter or persistent collisions.
2. Render-order mistakes causing accidental overrides.
3. Unresolved mapping errors or broken face tracks.
4. Unjustified heavy effects reducing playback usability.
5. Legal/source hygiene violations.

## 22. Anti-Patterns

1. Sequencing entire songs from a single umbrella layer without refinement.
2. Using randomization as a substitute for phrase intent.
3. Ignoring Master View render order while troubleshooting.
4. Treating data-layer imports as editable effect-native content.
5. Building giant preview-scale group grids by default.
6. Applying automation without post-render validation.

## 23. Helix Execution Checklist

### 23.1 Before Sequencing

1. Confirm layout/controller/channel integrity.
2. Confirm model/group naming standards.
3. Confirm timing-track architecture.
4. Confirm legal/source hygiene context.

### 23.2 During Sequencing

1. Follow section plan.
2. Keep layer roles explicit.
3. Apply curves only when musically justified.
4. Validate at preview and house levels continuously.

### 23.3 Before Release

1. Render all and save.
2. Run checks and resolve critical findings.
3. Verify faces/phonemes where applicable.
4. Export/package and test portability.
5. Record provenance and gate status.

## 24. Change Control

1. Rulebook updates MUST be small, testable, and scoped.
2. Any behavior-changing rule update MUST include rationale and validation notes.
3. Legacy guidance SHOULD be archived with date and replacement reference.

