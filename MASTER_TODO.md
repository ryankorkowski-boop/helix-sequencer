# HELIX MASTER TODO & AGENT HANDOFF LEDGER

> Canonical project roadmap and cross-agent handoff layer.

## Current mission
Build Helix into a reliable AI-assisted xLights auto-sequencer while preserving deterministic sequencing, verified artifacts, and cumulative behavior.

## Beta roadmap baseline status

This repo is currently in the beta-safety phase described by `ROADMAP_BETA_TODO.md`.

- [x] Phase 0 guidance is in place: beta roadmap, safety baseline, and support/data-use policy are documented.
- [x] Core beta docs are linked from the README and are available under `docs/`.
- [x] Agent task index is aligned with the roadmap and points to the current next tasks.
- [x] Sample beta tester feedback checklist exists and is documented for testers.
- [ ] Continue with Phase 0/1 execution in the exact order called out by the roadmap before moving into engine-facing refactors.
- [ ] Keep this ledger updated as each beta phase completes.

## Current priority
The current repo priority is the beta-readiness sequence defined in `ROADMAP_BETA_TODO.md`:

1. Add/maintain `TASKS.md` pointing to the beta roadmap.
2. Maintain `docs/SUPPORT_MATRIX.md` and `docs/BETA_POLICY.md`.
3. Normalize dependencies and CI with `requirements-dev.txt`.
4. Add repo-safe smoke fixtures and structural validation.
5. Add run manifest/output safety behavior.
6. Add GUI beta mode + dry-check behavior.
7. Add beta tester docs and issue templates.
8. Add Windows packaging smoke coverage.
9. Only then begin engine facade/extraction work.

## Drummer / band current state
- [x] Canonical nine-component drummer contract documented.
- [x] Runtime drummer state model changed to nine integrated hit components.
- [x] Structure catalog changed to nine drummer sequencing components.
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Pose geometry spec now defines nine component composites with embedded contacting-stick geometry.
- [~] xLights model exporter still needs to emit the new component composites as the nine canonical sequencing submodels.
- [~] Drum detector uses HPSS/percussive onset analysis plus spectral features.
- [x] Classification now rejects high harmonic-contamination candidates when unsupported and suppresses ambiguous low-margin classifications into `drum_bus`.
- [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- [ ] Validate detector against real-song audio and quantify false positives.
- [ ] Generate real-song XSQ.
- [ ] Render full-song MP4 with audio.
- [ ] Human visual review of rendered drummer timing.

## Canonical drummer components
1. `HX_SNOWMAN_DRUMMER_KICK` = KICK + KICK_RIM
2. `HX_SNOWMAN_DRUMMER_SNARE` = SNARE + SNARE_RIM + SNARE_CONTACT_STICK
3. `HX_SNOWMAN_DRUMMER_TOM_1` = TOM_1 + TOM_1_CONTACT_STICK
4. `HX_SNOWMAN_DRUMMER_TOM_2` = TOM_2 + TOM_2_CONTACT_STICK
5. `HX_SNOWMAN_DRUMMER_TOM_3` = TOM_3 + TOM_3_CONTACT_STICK
6. `HX_SNOWMAN_DRUMMER_TOM_4` = TOM_4 + TOM_4_CONTACT_STICK
7. `HX_SNOWMAN_DRUMMER_HI_HAT` = HI_HAT + HIHAT_CONTACT_STICK
8. `HX_SNOWMAN_DRUMMER_CYMBAL_LEFT` = CYMBAL_LEFT + CYMBAL_LEFT_CONTACT_STICK
9. `HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT` = CYMBAL_RIGHT + CYMBAL_RIGHT_CONTACT_STICK

**Physical rule:** the contacting stick is part of the corresponding hit component. There are no independent stick sequencing channels. Kick has no stick.

## Detection architecture
**audio → HPSS/percussive isolation → onset candidates → spectral/transient features → confidence-gated drum classification → nine-component mapper → XSQ**

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Current nine-component geometry remains authoritative for the new implementation: four tom zones and contacting-stick geometry integrated into the hit component.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-10-16 — Phase 3 opt-in section composer
**Goal:** User approved Phase 3 after native audio PR #170. Add measured section
budgets behind `--section-composer`; feed existing placements without replacing
Birdsong/energy_wave or changing default output / locked drummer timing.

**Changed:** `core/{section_composer,section_placement,effect_engine}.py`,
`tools/section_composer_benchmark.py`, `tools/quality/scoring.py`,
`tests/test_section_composer.py`, `.github/workflows/{helix-ci,
quality-native-check}.yml`, `docs/SECTION_COMPOSER.md`, and this ledger.
**Preserved:** Existing fixed planners and all default profiles; existing
Birdsong phrase and energy_wave selectors; drum stems and performer channels.
No archive/helixville edits or paid/vendor/YouTube material/creator learning.

**New behavior:** Bounded chroma/MFCC self-similarity novelty, four-second
minimum segments, stable IDs, energy/density/palette/family plans, energy
build/drop markers and absolute-silence restraint. Successful placements
reserve conservative 50-ms root-model density slots. RGB palettes and static
brightness consume section budgets; AC colors are preserved. Protected
performers/groups and drum stems bypass caps. Unsupported active brightness
curves are rejected visibly rather than pretending a static slider caps them.
Opt-in engine reports include the measured plan/counters. Phase 1 quality
warns when later/higher energy does not receive a larger budget.

**Evidence:** All 224 selected beta smoke tests pass locally, including both
Phase 2/3 native artifact tests. All 90 targeted composer/quality/Birdsong/
route/effect tests pass. Scoped flake8 and strict mypy pass (eight checked
modules); new lines in the existing engine are lint clean. Actual v27.3
engine run records four measured sections and applies caps. Default-off XSQ
is byte-identical to the parent implementation, SHA256
`0c76f81274e02ae79a94f021b0034264a818c91087de83d5cb4603367397b7c6`.
Original 24-s AC energy_wave benchmark: saved-XSQ Phase 1 correlation improves
0.273532 -> 0.340514. Official pinned xLights 2026.18 FSEQ confirms actual
lit-channel correlation 0.265961 -> 0.338588 (8 channels, 480 frames/50 ms;
612 -> 558 nonzero samples). Both native MP4s have verified H.264/AAC,
24-second streams at time zero. Local artifacts:
`test_runs/section_composer_ac/{baseline,composed}/` and
`native_comparison.json`. Remote native CI passed at implementation commit
`1efb155ba5cc2bcab23dfd644ca93acf3e17f7c3`: 23 Phase 1/2 checks and 14
composer checks, no skips. [Native job](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38911330696/job/117007628631),
[74-file artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38911330696/artifacts/12049584096).
Downloaded ZIP digest verified; both CI MP4s are byte-identical to local
outputs, and CI matches both structural/native correlation results. Local
decoded video samples at .1, 7.1, 12.1, 18.1 and 23.9 s agree with FSEQ
light/rest windows. [Beta matrix](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38911330424)
passed Python 3.11/3.12: each 220 passed / 4 skipped for missing media tools
or native artifact environment. Those four ran in strict native CI. Scoped
lint and strict types passed in both beta jobs. Draft [PR #171](https://github.com/ryankorkowski-boop/helix-sequencer/pull/171)
is stacked on unmerged Phase 2; stop for review before Phase 4.

**Limitations/deferred:** Correlations still miss the unchanged 0.5 threshold;
quality/dead-air warnings are retained. This isolates the actual energy_wave
placement path with native table serialization, not whole-band or real-song
approval. The separate full-engine fixture retains the pre-existing snowman
`composite_submodels` planning error and legacy inline-export limitations.
RGB experiment: model-presence correlation improves, but actual channel
correlation declines 0.265961 -> 0.256274 because palette colors zero channels;
do not equate structural estimates with native bytes. Human visual/controller
review and drummer-oracle render approval remain pending. No release, merge
or tag. Stop after Phase 3 for review before Phase 4.

**Regression risks:** Coarse boundaries and library/platform differences;
minimum-length semantics do not claim verse/chorus labels. Density counts
root props, not unequal pixel-channel weights. Existing/protected content can
exceed new caps; conservative reservations can underfill after replacements.
Only static brightness caps are supported until bounded curves in Phase 5.
Existing full-suite/lint/type baseline failures and per-song error swallowing
are unchanged; no whole-repository clean-check claim.

### 2026-10-16 — Phase 2 native preview with original audio
**Goal:** Extend the existing official-native headless benchmark path to an
audio-synced MP4 without adding a renderer. User approved Phase 2 after PR #169.

**Changed:** `tools/native_preview.py`,
`tools/prepare_native_preview_benchmark.py`, REST response status handling in
`tools/check_xlights_rest_sequence.py`, `tests/test_native_preview.py`,
`.github/workflows/{helix-ci,quality-native-check}.yml`,
`docs/NATIVE_AUDIO_PREVIEW.md`, and this ledger.

**Preserved:** Every sequencing profile, XSQ source/effects, locked drummer
timing/oracle, model/channel behavior and learning path. Original audio is
read only. No archive/helixville edits, integration merge, release or tag.

**New behavior:** Explicit post-run native FSEQ render, own-process House
Preview export, ffmpeg video packet copy plus original-audio AAC mux, real
ffprobe stream/timestamp/duration checks and full decode. Fresh evidence
directories prevent stale outputs. Manifest gets provenance and a preview
report, preserving unrelated keys. Missing dependencies or failed native
export/mux produce fallback/null MP4 plus a warning. REST responses without
`res` use HTTP status while explicit native rejection codes are preserved.

**Evidence:** Local pinned official xLights 2026.18 produced H.264 + AAC,
4.000-second streams at timeline zero. Native FSEQ remains 4 channels,
80 frames/50 ms and 78 nonzero samples; input XSQ/layout hashes are unchanged.
Scoped flake8 and strict mypy pass for both new modules. All 50 targeted
quality/native/REST tests and all 210 updated beta smoke tests pass locally,
including real ffprobe, decoded audio markers and native light/rest windows.
Remote native audio CI passed at implementation commit
`069b6545b849e92103ae58e0c02c6cb22fdcb972` with 23 tests, including real
ffprobe and decoded native light/audio timeline verification:
[native job](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38899651480/job/116968447736),
[evidence artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38899651480/artifacts/12045681866).
The artifact ZIP digest was verified after download; its MP4 is byte-identical
to local output (SHA256 `87f86618188ab14835d110290d6a5efccf1c83dfd95202fe96be5f9fe6d7009b`).
[Beta matrix](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38899651457)
passed on Python 3.11 and 3.12: each 207 passed / 3 skipped because those
runners lack ffmpeg/ffprobe; all three media tests ran in the strict native
job (23 passed, no skips). Scoped lint/types passed in both beta jobs. Phase 2 draft
[PR #170](https://github.com/ryankorkowski-boop/helix-sequencer/pull/170)
is stacked on unmerged Phase 1; stop for review before Phase 3. No sequencing metric before/after change is expected for this phase.

**Limitations/deferred:** Synthetic four-second proof only, not the separate
real-song drummer review gate. Human visual/controller review remains pending.
Linux requires a display/Xvfb and prepared show/assets; native GUI `renderAll`
timed out, so headless FSEQ is loaded for export. Native House Preview size
depends on its configuration. Audio starts at zero, is AAC encoded and trimmed
only at the sequence end; no offset/short-audio padding. Source audio duration
metadata must be available to ffprobe. Phase 3 waits for user review.

**Regression risks:** Native version/platform, preview geometry and relative
asset resolution vary. No concurrent manifest writers are supported. Occupied
REST port, native errors, malformed media and stream mismatches fail clearly;
no automatic approximate renderer is used.

### 2026-10-16 — Phase 1 native verification follow-up (PR #169)
**Goal:** Replace the pending-CI status with actual evidence, repair the failed
artifact workflow, and expose native format problems hidden by structural tests.

**Changed:** `tools/quality/{inputs,scoring,native}.py`, quality fixtures and
tests, new native FSEQ tests, `.github/workflows/{helix-ci,
helix-birdsong-quality-artifact,quality-native-check}.yml`, quality docs and this
ledger. **Preserved:** all engine profiles, existing demo exporters, drummer
timing/oracle, learning behavior, and user input files. No renderer replacement.

**Findings:** Remote beta smoke passed on Python 3.11 and 3.12 at `7374d20`.
The older artifact job failed on `ModuleNotFoundError: core` because it invoked
tools by filename; commands now use `python -m tools...`. The broad CI audit
allows failures and is not evidence that the full suite or lint is clean.
The initial native fixture rendered black, and its missing FixedPointTiming
flag caused millisecond timestamps to be interpreted as seconds. Native
metadata, geometry and a zero-intensity On effect now replace the incomplete
fixture. Structural scores themselves remain the same.

**New behavior:** Scoring converts legacy native second-based times, with an
explicit warning-producing opt-in for unflagged legacy Helix millisecond
metadata. Inline settings/palettes not native to xLights warn. A bounded FSEQ
inspector reads actual compressed/sparse channel bytes and rejects invalid,
wrong-size or black benchmark output. A pinned official-native CI workflow
checks ramps, accents and rests and uploads its evidence.

**Evidence:** Official xLights 2026.18 Linux AppImage SHA256
`62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`
matches the official release digest. Native headless render exits 0. Corrected
fixture: 4 channels, 80 frames, 50 ms; 78 nonzero samples, 49 nonzero frames,
mean actual lit fraction .24375 versus structural estimate .4375. Native
samples include a decaying red ramp, blue accent at 1000 ms, red group accent
at 2500 ms, and darkness at 2000 and 3000 ms. Exact current fixture rendered
locally and passed those native byte assertions. Scoped flake8 and strict mypy
pass (five modules); 35 quality/native tests, 50 targeted tests, and all 195
selected beta smoke tests pass locally. The artifact exporter and diagnostic
renderer module commands both execute with PYTHONPATH unset. Follow-up remote
native CI passed at `7b2aabb2d8815091e9aaf7db0d6952e8bb9e4300`:
[native job](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38896155114/job/116956997381),
[native artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38896155114/artifacts/12043453689).
Runner output matches local channel metrics and all ramp/accent/rest assertions.
The beta smoke matrix passed on Python 3.11 and 3.12 in run `38896147529`;
the repaired quality-artifact exporter/diagnostic-render job passed in run
`38896147378`. Broad audits still tolerate the pre-existing failures; do not
read their green workflow status as a clean full-suite or lint result.
The first native runner attempt stopped on missing `libEGL.so.1` before any
render. The workflow now explicitly installs `libegl1` and prints the captured
render log while retaining the actual failing exit code. This is a strict gate,
not a continue-on-error audit. The failed attempt is not counted as validation.

**Limitations:** This is a synthetic 4-second metric fixture, not a real-song
band showcase. No native MP4/audio, human visual review or physical-controller
approval is claimed. The structural scorer remains labeled an estimate.
ZSTD FSEQ inspection needs libzstd; diagnostics are capped at 128 MiB. Native
CI uses the pinned 2026.18 build and does not prove older versions compatible.

**Deferred/risk:** Phase 2 and release integration await review. Existing full
suite/lint/type baseline failures are retained as documented below. Native
color routing and quantized ramp endpoints differ from continuous structural
estimates; do not tune thresholds by pretending those are identical.

### 2026-10-16 — Phase 1 saved-XSQ metrics harness (verification pending)
**Agent:** Codex
**Branch:** `codex/quality-metrics-20261016`

**Goal:** Establish deterministic, original diagnostics for generated XSQ before
any opt-in composer, layering, hardware-profile, or learning changes.

**Changed:** `tools/quality/{__init__,inputs,scoring,__main__}.py`,
`tests/test_quality_metrics.py`, `tests/fixtures/quality/`,
`docs/QUALITY_METRICS.md`, `.github/workflows/helix-ci.yml`, this ledger.

**Preserved:** Every sequencing profile, existing intent scorer, musical/drummer
timing, the oracle `b27e8d77a63027ed32bcf6851dcff3925472c155`, and input files.
No engine refactor, legacy-directory edits, automatic learning or new renderer.

**New behavior:** Pure saved-XSQ scorer plus explicit post-run CLI, overall and
section metrics, warning thresholds, atomic manifest `quality` update. Saved
effect/palette tables, inline settings, nested groups, and On ramps are handled.
Occupancy and focal intensity are explicitly estimates, not rendered values.
Golden clean-room benchmark and beta-CI CLI/artifact coverage added.

**Evidence:** Initial baseline: `python -m pytest -q
tests/test_birdsong_quality_score.py tests/test_beta_demo_fixture.py
tests/test_run_manager.py tests/test_birdsong_xsq_export.py` — 29 passed.
Final local checks:
- `python -m flake8 tools/quality tests/test_quality_metrics.py` — passed.
- `python -m mypy --strict --explicit-package-bases --follow-imports=silent
  tools/quality` — passed (four modules).
- `python -m pytest -q tests/test_quality_metrics.py` — 25 passed.
- Targeted harness + RunManager + existing Birdsong exporter/scorer + beta
  fixture set — 54 passed.
- Exact `Run beta smoke tests` command extracted from the updated workflow
  and executed locally — **185 passed** (Python 3.12). This is not a remote
  CI run or proof of the Python 3.11 matrix leg.
- `python -m tools.quality score test_runs/quality_benchmark` — report matches
  the golden file; manifest quality saved. Artifact paths:
  `test_runs/quality_benchmark/{benchmark.xsq,layout.xml,audio_features.json,
  quality_report.json,run_manifest.json}` (local generated diagnostics).
- `python -m compileall -q tools/quality tests/test_quality_metrics.py`,
  `python main.py --list-profiles`, `git diff --check` — passed.
- Full suite collection is blocked by the existing `assign_hand` import in
  `tests/test_drum_mapping.py`. With only that module excluded, this branch:
  **19 failed, 935 passed, 5 skipped, 1 xfailed**. Untouched base `1f66f5d`
  in a separate worktree: **19 failed, 910 passed, 5 skipped, 1 xfailed**.
  The exact same 19 test ids fail; the added 25 tests pass. No blanket claim
  of a clean repository test gate is made. Base failures include drummer
  classification/geometry, band exports/catalogs, preview mux and XSQ validation.
- Broader existing-area flake8 reports 6,667 violations; mypy reports 232 errors
  in 30 existing files. This phase does not mass-format or rewrite that code.
- Repository `template.xsq` paired with root `xlights_rgbeffects.xml` is rejected
  for unknown target `mt1`; that fixture pair is not a valid scoring benchmark.

**Limitations:** Native xLights is not installed in this execution environment;
no native import/render, real-audio MP4, visual or controller approval is claimed.
Features in the golden test are synthetic, not real-song detections. Occupancy
cannot evaluate pixel effects, curves, blending, shared channels or submodel
subsets. Explicit channel counts are required for channel weighting; otherwise
equal model weights are reported. Scoring must run after RunManager finishes.

**Deferred work:** Native verification and human review remain unchecked under
the existing verification gate. Phases 2–9 await phase-by-phase user review.
This entry does not supersede any earlier roadmap work or mark it complete.
The nine-phase task explicitly requires stopping for review after Phase 1.
**Publication update (2026-10-16):** After the initial automatic approval block,
the user explicitly approved branch publication and opening a draft PR.
Published `codex/quality-metrics-20261016` and opened draft
[PR #169](https://github.com/ryankorkowski-boop/helix-sequencer/pull/169)
against `feature/restructure-core`. Published implementation commit:
`4277c8345bd7164fd92c18cc614eafda9e24fe47`. Its tree exactly matches the
tested local implementation (`c3af6bbc5d3e2a4eaff17fd362273d1b8f4cfe9c`).
Native verification and Phase 1 review remain pending; no merge or tag occurred.

**Regression risks:** Unsupported xLights settings may require parser expansion;
initial thresholds can flag intentional AC restraint/repetition. No aesthetic
conclusion or sequencing optimization is inferred from synthetic metrics.

### 2026-10-02 — Beta tester feedback checklist documented
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Added a repo-safe beta tester feedback checklist document for single-run evidence collection.
- Linked the checklist from the root README so testers can find it from the main entrypoint.
- Kept the checklist focused on privacy-safe, local-only evidence collection without requiring private asset disclosure.

**Limitations:**
- This is a documentation gate only; it does not claim xLights import success or visual quality.
- The beta roadmap still requires run manifest, GUI, and packaging safety work before broader beta claims.

### 2026-10-02 — Beta roadmap baseline alignment
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Restored the task index to the beta-roadmap-first workflow required by `ROADMAP_BETA_TODO.md`.
- Added a repo-level beta baseline status note to this ledger so the project continues in the intended order.
- Preserved the active drummer work while making the higher-priority beta safety work explicit.

**Limitations:**
- This does not replace the deeper engineering work required for drum detection or xLights import validation.
- Beta-safety milestones must still be executed in order before engine refactor work begins.

### 2026-09-30 — Ground-truth regression oracle locked
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Recorded:**
- Prior known-good drummer behavior is anchored to commit `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- The historical 8-submodel V3 workflow is retained as a behavioral regression reference while the physical model evolves to nine components.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61c`

**Changed:** `audio/drum_classification.py`
- Added harmonic-contamination gating using the existing percussive/harmonic ratio.
- Added a minimum score-margin requirement between the best and runner-up drum classes.
- Ambiguous or weak events now become `drum_bus` instead of being confidently misclassified.

**Preserved:** existing kick/snare/tom/hat/cymbal feature scoring and six-stream event schema.

**Not yet verified:** real-song false-positive rate, XSQ output, and MP4 behavior.

### 2026-09-30 — Nine-component drummer geometry spec
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Changed:** `fixtures/band_geometry/drummer_v3_pose_spec.json`
- Four distinct tom zones and nine canonical hit composites.
- Contacting sticks are embedded in snare/tom/hi-hat/cymbal components.

**Known limitation:** xmodel exporter still needs to make the nine composites the canonical sequencing submodels.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.
