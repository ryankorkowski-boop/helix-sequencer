# Existing Engine Calibration Plan

Status: Active direction  
Scope: calibrating the current `core.sequence_builder` / `core.effect_engine` path

## 1. Correction

Helix already has an existing placement/effect engine. The correct implementation path is calibration, not replacement.

The active generation path is:

```bash
python -m core.sequence_builder --profile v27.3 -- --template template.xsq --audio LightsOutTheme.mp3 --layout-file allmodels/xlights_rgbeffects.xml --single --output-dir test_runs/manual_preview --variants 1 --no-prompt --no-save-settings --no-workspace-history --no-polish --no-auto-timing-tracks --no-matrix-intelligence
```

Future work should improve this path unless there is a clear tested reason to create a new path.

## 2. Current Calibration Seams

Primary files:

- `core/effect_engine.py`
- `core/sequence_builder.py`
- `core/engine_style_catalog.py`
- `tools/build_helpers/variants.py`
- `xlights/xsq_writer.py`

Important existing concepts:

- runtime variant candidates
- quality gates
- audit score
- rejected-effect count
- shortlist score
- polish score
- self-improving score
- template profile
- workspace history profile
- layout-aware model routing

## 3. Quality Gate Presets

The calibration layer now exposes three gate presets:

| Preset | Min Quality | Min Audit | Max Rejected Effects | Purpose |
| --- | ---: | ---: | ---: | --- |
| `general` | 90 | 80 | 28000 | normal useful output |
| `showcase` | 93 | 86 | 18000 | strong public-demo output |
| `vendor` | 96 | 90 | 12000 | strictest internal bar |

These are source-agnostic quality bars. They are not based on copying external shows.

## 4. Scoring Calibration

The shortlist score should reward:

- quality score
- audit score
- musical coherence
- section coverage
- structure
- layout coverage
- detail
- family diversity
- dominance balance
- polish improvements
- self-improving score

The shortlist score should penalize:

- overlap
- clutter
- excessive rejected effects
- failed quality gates

## 5. Next Code Steps

1. Wire `quality_gate_preset` into `core.effect_engine` command options.
2. Add a command option such as:

```bash
--quality-gate-preset showcase
```

3. Use the preset when choosing/promoting shortlisted candidates.
4. Keep existing explicit threshold options as overrides.
5. Add tests for preset resolution and gate behavior.
6. Run real sequence smoke generation through the existing path.

## 6. Do Not Do

Do not replace the existing engine with the newer `helix_intent` render sidecar path.

The newer placement-report modules may still be useful as instrumentation, but they should not become the main renderer unless the existing engine cannot support the required behavior.

## 7. Legal-Safe Showcase Goal

The goal is not to copy any public display.

The goal is to reach public-display-level polish through source-agnostic measurements:

- clean timing
- clear focal motion
- readable layering
- strong section identity
- controlled density
- low rejected-effect count
- good prop coverage
- coherent color and motion
- safe brightness/flash behavior
