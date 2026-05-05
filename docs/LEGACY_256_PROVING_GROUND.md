# Legacy 256 Proving Ground

Status: Active calibration direction  
Scope: using a permission-backed legacy LMS sequence and a 256-channel layout to prove Helix placement discipline

## 1. Purpose

The legacy 256 setup is Helix's first serious constrained proving ground.

A 256-channel legacy layout forces disciplined sequencing:

- no hiding behind pixel density
- no matrix-only tricks
- no unlimited prop coverage
- clearer AC/channel behavior
- easier inspection of rejected effects
- easier comparison between `general`, `showcase`, and `pro` gates

## 2. Source Boundary

The GP LMS sequence may be used only under explicit permission and documented allowed use.

The repo must not assume the LMS file can be committed. The safe default is:

```text
local_fixtures/legacy_256/source_lms/*.lms
```

Local fixture files should remain outside committed source unless permission clearly allows storage and redistribution.

## 3. Recommended Fixture Layout

```text
fixtures/legacy_256/
  README.md
  permissions.md
  layout_256_manifest.json
  converted/
    template.xsq
    xlights_rgbeffects.xml
  expected/
    baseline_report.json

local_fixtures/legacy_256/
  source_lms/
    GP_sequence.lms
  audio/
    song.mp3
```

## 4. What GP LMS Should Be Used For

Allowed role, with permission:

- compatibility fixture
- sequence-length inspection
- channel-count inspection
- effect-density inspection
- AC-style behavior analysis
- baseline quality comparison

Not allowed by default:

- copying choreography
- extracting creator-specific style rules
- redistributing source LMS
- training from the LMS without clear permission scope

## 5. Calibration Goal

The goal is not to copy GP.

The goal is:

```text
Can Helix produce a clean, original 256-channel sequence that meets or exceeds the baseline engineering quality bar?
```

Measure:

- timing coverage
- channel coverage
- section contrast
- dead-channel avoidance
- rejected effects
- AC-safe effect choices
- musical coherence
- overlap/clutter
- density restraint

## 6. Profile Direction

Create original Helix legacy profiles:

- `legacy_256_clean`
- `legacy_256_showcase`
- `legacy_256_pro`

These profiles should prioritize:

- on/fade/chase style effects
- section clarity
- chorus lift
- controlled density
- strong beat alignment
- low rejected effects
- channel-family coverage
- AC-safe brightness/flash behavior

They should avoid:

- pixel-only effects
- matrix assumptions
- face/phoneme assumptions unless the layout has face channels
- uncontrolled full-layout flashing

## 7. First Workflow

1. Put the GP LMS locally under `local_fixtures/legacy_256/source_lms/`.
2. Run LMS inspection.
3. Import/convert the LMS into xLights if needed.
4. Save converted working files under `fixtures/legacy_256/converted/` only if permission allows.
5. Run Helix with the showcase preset against the 256 layout.
6. Compare reports.

Example command after converted xLights files exist:

```bash
PYTHONPATH=. python -m tools.run_sequence_with_quality_preset --quality-gate-preset showcase -- --profile legacy_256_showcase -- --template fixtures/legacy_256/converted/template.xsq --audio local_fixtures/legacy_256/audio/song.mp3 --layout-file fixtures/legacy_256/converted/xlights_rgbeffects.xml --single --output-dir test_runs/legacy_256_showcase --variants 3
```

## 8. Next Engineering Steps

1. Add a fixture manifest schema.
2. Add an LMS inspection tool.
3. Add tests using tiny synthetic LMS snippets.
4. Add legacy 256 profile definitions.
5. Add report comparison tooling.
6. Run the first real baseline locally.
