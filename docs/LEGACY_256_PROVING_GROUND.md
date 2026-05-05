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

## 6. Implemented Profiles

Helix now has original Legacy 256 profile wrappers:

- `legacy_256_clean`
- `legacy_256_showcase`
- `legacy_256_pro`

They use the existing engine path and constrained defaults:

- base profile `v9.2`
- no matrix intelligence
- no auto timing tracks
- no workspace history
- no save settings
- single output mode

These profiles prioritize:

- on/fade/chase style effects
- section clarity
- chorus lift
- controlled density
- strong beat alignment
- low rejected effects
- channel-family coverage
- AC-safe brightness/flash behavior

They avoid:

- pixel-only effects
- matrix assumptions
- face/phoneme assumptions unless the layout has face channels
- uncontrolled full-layout flashing

## 7. Local Setup

Put local-only assets here:

```text
local_fixtures/legacy_256/source_lms/GP_sequence.lms
local_fixtures/legacy_256/audio/song.mp3
```

Put converted xLights working files here when available and permitted:

```text
fixtures/legacy_256/converted/template.xsq
fixtures/legacy_256/converted/xlights_rgbeffects.xml
```

## 8. Check Readiness First

Run this before any real evaluation:

```bash
PYTHONPATH=. python -m tools.check_legacy_256_readiness --output test_runs/legacy_256_readiness.json
```

This reports:

- `ready_for_dry_run`
- `ready_for_real_run`
- missing required files
- manifest validation
- next commands to run

A dry run only needs the committed manifest to validate. A real run needs:

- local audio
- converted `template.xsq`
- converted `xlights_rgbeffects.xml`

The GP LMS is optional for generation but recommended for inspection.

## 9. Inspect The GP LMS Locally

```bash
PYTHONPATH=. python -m tools.inspect_lms local_fixtures/legacy_256/source_lms/GP_sequence.lms --output test_runs/legacy_256_lms_inspection.json
```

## 10. Dry-Run Individual Profiles

```bash
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_clean --dry-run
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_showcase --dry-run
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_pro --dry-run
```

## 11. Run Individual Profiles

```bash
PYTHONPATH=. python -m tools.run_legacy_256_profile legacy_256_showcase \
  --template fixtures/legacy_256/converted/template.xsq \
  --audio local_fixtures/legacy_256/audio/song.mp3 \
  --layout-file fixtures/legacy_256/converted/xlights_rgbeffects.xml \
  --output-dir test_runs/legacy_256_showcase
```

## 12. Compare Reports

```bash
PYTHONPATH=. python -m tools.compare_legacy_256_reports \
  test_runs/legacy_256_clean/*.report.json \
  test_runs/legacy_256_showcase/*.report.json \
  test_runs/legacy_256_pro/*.report.json \
  --output test_runs/legacy_256_comparison.json
```

## 13. Full Evaluation Dry-Run

```bash
PYTHONPATH=. python -m tools.run_legacy_256_evaluation \
  --manifest fixtures/legacy_256/layout_256_manifest.json \
  --lms local_fixtures/legacy_256/source_lms/GP_sequence.lms \
  --template fixtures/legacy_256/converted/template.xsq \
  --audio local_fixtures/legacy_256/audio/song.mp3 \
  --layout-file fixtures/legacy_256/converted/xlights_rgbeffects.xml \
  --output-root test_runs/legacy_256_evaluation \
  --dry-run
```

## 14. Full Evaluation Real Run

```bash
PYTHONPATH=. python -m tools.run_legacy_256_evaluation \
  --manifest fixtures/legacy_256/layout_256_manifest.json \
  --lms local_fixtures/legacy_256/source_lms/GP_sequence.lms \
  --template fixtures/legacy_256/converted/template.xsq \
  --audio local_fixtures/legacy_256/audio/song.mp3 \
  --layout-file fixtures/legacy_256/converted/xlights_rgbeffects.xml \
  --output-root test_runs/legacy_256_evaluation
```

## 15. First Local Checkpoint

The first successful checkpoint is:

```text
test_runs/legacy_256_evaluation/legacy_256_evaluation.json
```

It should contain:

- manifest validation
- optional LMS inspection
- clean/showcase/pro run steps
- comparison winner
- warnings/errors

## 16. CI/Local Smoke Tests

These tests do not need the real GP LMS or audio assets:

```bash
PYTHONPATH=. python -m pytest \
  tests/test_legacy_256_manifest.py \
  tests/test_inspect_lms.py \
  tests/test_legacy_256_profiles.py \
  tests/test_compare_legacy_256_reports.py \
  tests/test_run_legacy_256_evaluation.py \
  tests/test_check_legacy_256_readiness.py \
  -q
```

## 17. Next Engineering Steps

1. Run the readiness checker locally.
2. Run the full evaluation dry-run locally.
3. Fix any missing path or conversion issues.
4. Run the real evaluation.
5. Inspect `legacy_256_evaluation.json` and the winning `.report.json`.
6. Calibrate the existing engine weights based on actual rejected-effect, clutter, overlap, and section-coverage numbers.
