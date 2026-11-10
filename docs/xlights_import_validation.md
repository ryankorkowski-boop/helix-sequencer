# xLights Import Validation Workflow (v1)

## Objective

Validate that Helix-generated XSQ artifacts can be imported into xLights and rendered against real layouts.

---

# Prerequisites

- xLights installed
- Helix-generated XSQ XML artifact
- Configured layout/models
- Local preview enabled

Recommended controllers:

- Falcon F16/F48
- WLED

---

# Step 1 — Generate XSQ Artifact

Run Helix export pipeline.

Expected output:

- timingtrack
- phoneme entries
- face effect placeholders

---

# Step 2 — Validate XML Structure

Run:

```bash
python tools/validate_xsq_structure.py exported_sequence.xsq
```

Expected:

```text
XSQ VALIDATION PASSED
```

---

# Step 3 — Import Into xLights

1. Open xLights
2. Open sequence tab
3. Create or open target sequence
4. Import generated XSQ artifact
5. Bind to target face model

---

# Step 4 — Validate Timing Tracks

Confirm:

- timing track exists
- phoneme entries appear ordered
- beat-aligned starts preserved
- no duplicate entries

---

# Step 5 — Validate Face Timing

Confirm:

- face model responds to phoneme timing
- transitions occur at expected beat grid positions
- section energy scaling visually changes intensity

---

# Step 6 — Render Preview

Enable local preview.

Validate:

- lyric timing appears synchronized
- beat alignment visually matches audio
- no invalid effect blocks
- no ordering corruption

---

# Step 7 — Controller Deployment

Push rendered sequence to:

- Falcon controller
- WLED target
- xSchedule deployment

Validate:

- physical prop timing
- synchronization stability
- deterministic playback behavior

---

# Recommended Validation Layouts

## Simple Singer Face

Single face model with phoneme mapping.

## Snowman Band Drummer

Validate multi-prop synchronization.

## Helixia Multi-Prop Layout

Stress test deterministic ordering.

---

# Expected Deterministic Guarantees

Helix should preserve:

- ordering
- timing
- phoneme identity
- intensity scaling
- beat alignment
- XML stability

across repeated exports.

---

# Evidence Capture

Use the structured evidence recorder so xLights/manual/controller results can be
attached to Issue #76 or a PR without overstating what happened:

```bash
python -m tools.capture_xlights_validation_evidence \
  --artifact-run-url https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/<run-id> \
  --artifact-digest sha256:<artifact-digest> \
  --xsq-import-status not_tested \
  --preview-render-status rendered \
  --visual-review-status not_reviewed \
  --controller-status not_tested \
  --probe-rest \
  --notes "Clean-room XSQ/MP4 artifacts generated; xLights GUI import still pending."
```

The command writes JSON and Markdown under `test_runs/xlights_validation_evidence/`.
Those files are local evidence artifacts; do not commit private screenshots,
layouts, templates, or tester media.

To generate a complete local review folder with clean-room XSQ/MP4 artifacts,
an evidence draft, and manual review steps, run:

```bash
python -m tools.build_xlights_review_kit \
  --artifact-run-url https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/<run-id> \
  --artifact-digest sha256:<artifact-digest>
```

The review kit writes to `test_runs/xlights_review_kit/` by default.

If xLights REST automation is enabled locally, run a read-only `checkSequence`
probe against the generated XSQ:

```bash
python -m tools.check_xlights_rest_sequence \
  --xsq test_runs/xlights_review_kit/helix_flow_demo.xsq
```

The command tries the documented local xLights/xFade REST automation ports and
writes JSON and Markdown under `test_runs/xlights_rest_sequence_check/`. A
`checked` result is useful supporting evidence that xLights accepted the
sequence for structural checking. A `blocked` result usually means the REST
service was not reachable, and a `failed` result means xLights returned a
non-success response for `checkSequence`.

This helper does not perform manual visual review, controller upload, channel
safety validation, or physical playback testing.

## Evidence Status Values

Use these values when recording validation evidence:

- XSQ import: `imported`, `failed`, `blocked`, `not_tested`
- Preview render: `rendered`, `failed`, `blocked`, `not_tested`
- Visual review: `passed`, `failed`, `blocked`, `not_reviewed`
- Controller/channel safety: `passed`, `failed`, `blocked`, `not_tested`

Do not mark Issue #76 xLights/manual/controller items complete unless the
corresponding evidence record reflects the completed status and links to
reviewable notes or artifacts.
