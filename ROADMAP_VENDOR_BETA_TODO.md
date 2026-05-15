# Helix Vendor Beta Roadmap / Autonomous TODO

Purpose: make Helix safe enough to hand a beta GUI to selected xLights vendors so they can test against their own real layouts and judge whether the project has merit.

This file is written for human maintainers, Codex-style coding agents, and autonomous repo agents. Agents should work top to bottom, keep changes small, open PRs per phase or per milestone, and update checkboxes with evidence links.

## Current repo facts to preserve

- Default branch: `feature/restructure-core`.
- Primary operator surface: `gui_launcher.py` -> `main.py` -> `core.sequence_builder` -> `core.effect_engine`.
- Active profile: `master`, currently resolving to `v27.3` through `core/engine_profiles.py`.
- Current active surface described by README: `core/`, `xlights/`, `tools/`, and `ai/`.
- Known high-risk area: `core/effect_engine.py` is very large and should be wrapped before major extraction.
- Beta goal is not perfect auto-sequencing. Beta goal is: install, open GUI, load vendor layout/audio/template, run sequence, produce inspectable xLights artifacts, collect structured feedback, and not damage user/vendor assets.

## Agent operating rules

1. Do not rewrite the engine first. Stabilize the harness, docs, and safety rails before changing sequencing behavior.
2. Avoid breaking the GUI command contract unless the README, tests, and beta checklist are updated in the same PR.
3. Treat vendor layouts, vendor sequences, third-party templates, and copyrighted songs as test inputs only, not training data.
4. Never commit vendor-provided private layouts, sequences, songs, or screenshots unless explicit written permission is present in repo docs.
5. Every PR must include one of: passing test log, manual reproduction steps, generated artifact path, or a clear reason testing was not possible.
6. Prefer additive wrappers and adapters around legacy code over large behavior-changing rewrites.
7. Maintain compatibility with xLights-importable outputs as the release gate.

## Definition of beta-ready

A vendor beta build is ready when all of these are true:

- [ ] Fresh clone bootstrap is documented and works on Windows.
- [ ] GUI opens from documented command or packaged executable.
- [ ] User can select audio, xLights layout, template XSQ, output directory, and profile.
- [ ] Missing or invalid inputs show friendly GUI errors, not stack traces.
- [ ] App never overwrites vendor source layout/template/audio files.
- [ ] Output directory gets a timestamped run folder.
- [ ] Each run writes a run manifest containing inputs, profile, engine version, timestamps, and generated files.
- [ ] Generated XSQ/import artifacts open in xLights or fail with a documented, reproducible error.
- [ ] A sample feedback form/checklist exists for vendors.
- [ ] License and data-use boundaries are documented in plain English.
- [ ] At least one clean-room demo layout/audio/template run is included for internal smoke testing.

## Phase 0 — Repository contract and safety baseline

Goal: make it safe for agents and humans to work without guessing what is supported.

### 0.1 Add support matrix

Create `docs/SUPPORT_MATRIX.md`.

Include:

- Supported OS for beta: Windows first; Linux/macOS best effort if true.
- Supported Python versions: choose and test 3.11 and/or 3.12 explicitly.
- GUI dependency notes: Tkinter/Tcl/Tk expectations.
- FFmpeg/imageio-ffmpeg expectations.
- Required runtime assets: template XSQ, xLights layout XML/XBKP, audio file.
- Supported profiles: `master` only for beta unless tests prove otherwise.
- Unsupported/legacy areas: archive, old variants, experimental Helixville folders unless intentionally included.

Acceptance:

- [ ] `docs/SUPPORT_MATRIX.md` exists.
- [ ] README links to it.
- [ ] The doc clearly says what a vendor should and should not expect from beta.

### 0.2 Create beta data-use and vendor-safety policy

Create `docs/VENDOR_BETA_POLICY.md`.

Include plain-English statements:

- Vendors keep ownership of their layouts/sequences/assets.
- Helix beta should not train on vendor inputs by default.
- Vendor-provided material must stay out of git unless explicitly approved.
- Generated outputs may be watermarked or tagged as Helix-generated.
- xLights/GPL boundary is under review; do not market as proprietary xLights replacement.
- Beta is evaluation software; output quality is not guaranteed.

Acceptance:

- [ ] Policy exists and is linked from README and GUI beta notes.
- [ ] Policy distinguishes input assets, generated outputs, and persistent learning memory.

### 0.3 Add agent task index

Create or update `TASKS.md` as the short entrypoint for future agents.

It should say:

- Read this roadmap first.
- Run bootstrap/tests before editing.
- Work phases in order.
- Record decisions in `docs/DECISIONS.md`.
- Never commit private vendor files.

Acceptance:

- [ ] `TASKS.md` exists.
- [ ] It points to this file.
- [ ] It has a current "next recommended task" section.

## Phase 1 — Reproducible environment and CI

Goal: make local dev, CI, and beta packaging use one dependency contract.

### 1.1 Normalize dependency files

Add:

- `requirements-dev.txt`
- optional `constraints.txt` if pins are chosen
- optional `requirements-beta.txt` if packaging needs a slimmer set

Minimum content for `requirements-dev.txt`:

```txt
-r requirements.txt
pytest
scikit-learn
```

Then decide whether `scikit-learn` belongs in runtime or only dev/test.

Acceptance:

- [ ] `python -m pip install -r requirements.txt -r requirements-dev.txt` works.
- [ ] CI uses the same files.
- [ ] No dependency is installed in CI without being declared in a requirements file.

### 1.2 Replace/extend CI with a real beta gate

Create or update `.github/workflows/helix-ci.yml`.

Required jobs:

- compile all Python files
- run pytest
- run `python main.py --list-profiles`
- run a no-vendor smoke command using repo-safe demo assets
- optional Windows packaging smoke

Acceptance:

- [ ] CI runs on pull requests.
- [ ] CI runs on pushes to `feature/restructure-core` and roadmap/beta branches.
- [ ] CI uses Python versions documented in support matrix.
- [ ] CI artifact upload captures run manifests/logs when smoke runs succeed.

### 1.3 Add bootstrap scripts

Add simple scripts:

- `scripts/bootstrap_windows.ps1`
- `scripts/bootstrap_unix.sh`
- `scripts/run_smoke.ps1`
- `scripts/run_smoke.sh`

Acceptance:

- [ ] Scripts install dependencies.
- [ ] Scripts run compile/test/list-profiles.
- [ ] README beta instructions use these scripts.

## Phase 2 — GUI beta hardening

Goal: a vendor can open the GUI and safely run against their own layout.

### 2.1 Add beta mode to GUI

Implement a clear beta mode in `gui_launcher.py` or a small wrapper around it.

Requirements:

- Window title includes `Helix Sequencer — Vendor Beta`.
- Visible warning: "Use copies of layouts/templates. Helix will write to output folder only."
- Input selectors for audio, layout, template, output directory, profile.
- A "Run dry check" button validates inputs without sequencing.
- A "Run beta sequence" button executes the existing command path.
- Log output is visible and saveable.

Acceptance:

- [ ] GUI validates missing files before launch.
- [ ] GUI shows the exact command it will run.
- [ ] GUI disables run button while process is running.
- [ ] GUI captures stdout/stderr to a log file in the run folder.

### 2.2 Add run folder and manifest behavior

Add a small run-management module, for example `core/run_manifest.py`.

Every run should create:

```txt
outputs/vendor_beta/YYYYMMDD-HHMMSS-<profile>/
  run_manifest.json
  command.txt
  helix.log
  generated files...
```

Manifest fields:

- app name
- beta version string
- git commit if discoverable
- timestamp
- profile
- engine profile/version
- input paths and file hashes when safe
- output paths
- success/failure
- error summary
- xLights import notes if available

Acceptance:

- [ ] Manifest exists for success and failure.
- [ ] Output path is never the same as input layout/template path.
- [ ] Tests cover manifest creation and no-overwrite behavior.

### 2.3 Friendly errors

Replace raw exceptions at the GUI boundary with actionable messages.

Examples:

- Missing audio: "Choose a WAV/MP3 file first."
- Missing template: "Choose a template XSQ. Use a copy, not your original vendor file."
- Missing layout: "Choose xlights_rgbeffects.xml or XBKP."
- Engine failure: "Run failed. Open helix.log and attach it to feedback."

Acceptance:

- [ ] At least five common failure cases are tested or manually documented.
- [ ] GUI does not close on engine failure.

## Phase 3 — Clean demo assets and smoke tests

Goal: test without vendor/private/copyrighted material.

### 3.1 Build clean-room demo fixture

Create `tests/fixtures/vendor_beta_demo/` with generated/simple assets only.

Include:

- tiny synthetic WAV generated by script or committed if license-safe
- minimal xLights layout XML
- minimal template XSQ
- README explaining that these are clean-room fixtures

Acceptance:

- [ ] Fixture has no copyrighted music or vendor sequence content.
- [ ] Smoke test can run without internet or private files.

### 3.2 Add importability smoke

Create a test that verifies generated XML/XSQ structure enough to catch obvious breakage.

Acceptance:

- [ ] Generated output is parseable XML.
- [ ] Expected xLights sections/elements are present.
- [ ] Test fails if output is empty or malformed.

### 3.3 Add snapshot-lite output checks

Avoid brittle full-file snapshots. Check structural invariants instead:

- has timing/effects sections
- has nonzero effects
- effect start/end times are ordered
- effect targets map to known model/group names
- no NaN/None serialized into XML

Acceptance:

- [ ] Tests catch empty output.
- [ ] Tests catch invalid time ordering.
- [ ] Tests catch unknown model target unless explicitly allowed.

## Phase 4 — Vendor beta package and release process

Goal: create something you can hand to a small vendor without explaining the repo.

### 4.1 Create beta package checklist

Create `docs/BETA_RELEASE_CHECKLIST.md`.

Include:

- version/date
- commit SHA
- OS tested
- Python/runtime tested
- CI run link
- manual GUI smoke result
- sample output path
- known limitations
- data-use warning
- feedback link/email

Acceptance:

- [ ] Checklist exists.
- [ ] It has copy/paste sections for each beta drop.

### 4.2 Windows executable smoke

If PyInstaller is intended:

- confirm `.spec` works
- build on Windows CI
- launch smoke if possible
- attach artifact

Acceptance:

- [ ] Windows build job succeeds or is explicitly documented as not ready.
- [ ] Generated executable can start GUI on a clean Windows machine or VM.

### 4.3 Beta README for vendors

Create `docs/VENDOR_BETA_README.md`.

Vendor-facing content:

- What Helix is: auto-sequencing helper for xLights workflows.
- What to test: load copied layout/template/audio, run, import/open result, judge usefulness.
- What not to test yet: production show deployment without manual review.
- How to report issues.
- What files to send back: manifest, log, screenshots, generated XSQ if comfortable.
- What files not to send: private source layouts/sequences unless intentionally sharing.

Acceptance:

- [ ] Non-developer can follow it.
- [ ] It never promises production quality.
- [ ] It explains how to protect vendor assets.

## Phase 5 — Engine containment before refactor

Goal: reduce risk from the monolithic engine without destabilizing behavior.

### 5.1 Add stable engine facade

Create `core/engine_runner.py` or similar.

It should expose one clear function:

```python
def run_sequence_job(config: SequenceJobConfig) -> SequenceJobResult:
    ...
```

Do not rewrite engine internals yet. Wrap current `effect_engine.main_for(...)` path.

Acceptance:

- [ ] GUI and CLI can call the facade.
- [ ] Facade returns structured success/failure data.
- [ ] Existing behavior remains unchanged except better reporting.

### 5.2 Add typed job config/result dataclasses

Create dataclasses for:

- audio path
- template path
- layout path
- output directory
- profile
- beta/dry-run flags
- engine extra args

Acceptance:

- [ ] No new call path passes unstructured dicts where dataclass is expected.
- [ ] Unit tests cover config validation.

### 5.3 Identify first extraction targets

Do not extract yet unless tests are strong enough. Create `docs/EFFECT_ENGINE_EXTRACTION_PLAN.md`.

Recommended first seams:

1. input discovery/validation
2. output artifact naming
3. manifest/report writing
4. profile/version dispatch
5. quality scoring/reporting
6. learning-memory hooks

Acceptance:

- [ ] Plan lists current functions/regions by name when known.
- [ ] Plan defines tests required before each extraction.

## Phase 6 — Feedback loop and product decision

Goal: turn vendor beta results into a go/no-go and next feature list.

### 6.1 Add vendor feedback form template

Create `docs/VENDOR_FEEDBACK_FORM.md`.

Questions:

- xLights version used
- layout size/type
- import success yes/no
- did generated effects land on expected props/groups?
- timing quality 1-5
- effect choice quality 1-5
- color/palette quality 1-5
- manual cleanup required
- would this save time if improved?
- top 3 missing features
- showstopper bugs
- permission level for using their feedback/assets

Acceptance:

- [ ] Form exists and is linked from vendor README.

### 6.2 Add issue templates

Create `.github/ISSUE_TEMPLATE/vendor-beta-bug.md` and `.github/ISSUE_TEMPLATE/vendor-beta-feedback.md`.

Acceptance:

- [ ] Templates request manifest/logs.
- [ ] Templates warn not to upload private assets publicly.

### 6.3 Define beta success metrics

Add to `docs/BETA_SUCCESS_METRICS.md`:

- install success rate
- GUI launch success rate
- run completion rate
- xLights import success rate
- vendor usefulness score
- average manual cleanup time estimate
- top failure classes

Acceptance:

- [ ] Metrics doc exists.
- [ ] Product decision criteria are explicit.

## Immediate first tasks for agents

Start here, in this exact order:

1. Add `TASKS.md` pointing to this roadmap.
2. Add `docs/SUPPORT_MATRIX.md`.
3. Add `docs/VENDOR_BETA_POLICY.md`.
4. Add `requirements-dev.txt` and update CI to use it.
5. Add clean-room demo smoke fixture or script-generated fixture.
6. Add run manifest support without changing sequencing output.
7. Add GUI beta mode/dry-check behavior.
8. Add vendor-facing README and feedback form.
9. Add Windows packaging smoke.
10. Only then begin engine facade/extraction work.

## Non-goals before vendor beta

- Full AI learning system.
- Training on vendor sequences.
- Marketplace/vendor model scraping.
- Production-quality unattended show deployment.
- Major rewrite of `core/effect_engine.py`.
- Supporting every legacy profile in the GUI.
- Perfect visual quality parity with top hand-sequenced shows.

## Suggested PR slicing

PR 1: docs-only beta roadmap, support matrix, vendor policy, tasks index.

PR 2: dependency/CI normalization.

PR 3: clean-room smoke fixture and XML structural checks.

PR 4: run manifest and output folder safety.

PR 5: GUI beta mode and dry check.

PR 6: vendor beta README, feedback form, issue templates.

PR 7: Windows package smoke.

PR 8: engine facade with typed config/result.

## Status log

Update this section after each PR.

| Date | Agent/Human | Change | Evidence |
|---|---|---|---|
| 2026-05-15 | ChatGPT | Created initial autonomous vendor beta roadmap. | `ROADMAP_VENDOR_BETA_TODO.md` |
