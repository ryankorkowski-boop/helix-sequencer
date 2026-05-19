# Helix Beta Version Roadmap / Autonomous TODO

Purpose: make Helix safe enough to share as a beta GUI for real-world testing against copied xLights layouts, copied templates, and user-selected audio so testers can judge whether the project has merit.

This file is written for human maintainers, Codex-style coding agents, and autonomous repo agents. Agents should work top to bottom, keep changes small, open PRs per phase or per milestone, and update checkboxes with evidence links.

## Current repo facts to preserve

- Default branch: `feature/restructure-core`.
- Primary operator surface: `gui_launcher.py` -> `main.py` -> `core.sequence_builder` -> `core.effect_engine`.
- Active profile: `master`, currently resolving to `v27.3` through `core/engine_profiles.py`.
- Current active surface described by README: `core/`, `xlights/`, `tools/`, and `ai/`.
- Known high-risk area: `core/effect_engine.py` is very large and should be wrapped before major extraction.
- Beta goal is not perfect auto-sequencing. Beta goal is: install, open GUI, load copied layout/audio/template inputs, run sequence, produce inspectable xLights artifacts, collect structured feedback, and not damage user assets.

## Current status

Phase 0 and Phase 1 are complete enough to move forward. Dependency declarations, beta CI, bootstrap scripts, and smoke wrappers exist. Required checks should be run through `python scripts/ci/run_required_checks.py` so local wrappers and CI do not drift.

## Current next recommended task

Proceed with canonical output and beta safety hardening:

1. Strengthen xLights contract tests and structural fixtures.
2. Add clean-room importability smoke coverage.
3. Add run manifests and no-overwrite guarantees.
4. Continue GUI beta mode/dry-check behavior.

## Agent operating rules

1. Do not rewrite the engine first. Stabilize the harness, docs, and safety rails before changing sequencing behavior.
2. Avoid breaking the GUI command contract unless the README, tests, and beta checklist are updated in the same PR.
3. Treat third-party layouts, sequences, templates, and copyrighted songs as test inputs only, not training data.
4. Never commit private layouts, sequences, songs, screenshots, or tester-provided files unless explicit written permission is present in repo docs.
5. Every PR must include one of: passing test log, manual reproduction steps, generated artifact path, or a clear reason testing was not possible.
6. Prefer additive wrappers and adapters around legacy code over large behavior-changing rewrites.
7. Maintain compatibility with xLights-importable outputs as the release gate.

## Definition of beta-ready

A beta build is ready when all of these are true:

- [x] Fresh clone bootstrap is documented and works on supported Python versions through repo smoke scripts.
- [ ] GUI opens from documented command or packaged executable.
- [ ] User can select audio, xLights layout, template XSQ, output directory, and profile.
- [ ] Missing or invalid inputs show friendly GUI errors, not stack traces.
- [ ] App never overwrites source layout/template/audio files.
- [ ] Output directory gets a timestamped run folder.
- [ ] Each run writes a run manifest containing inputs, profile, engine version, timestamps, and generated files.
- [ ] Generated XSQ/import artifacts open in xLights or fail with a documented, reproducible error.
- [ ] A sample feedback form/checklist exists for beta testers.
- [x] License and data-use boundaries are documented in plain English.
- [ ] At least one clean-room demo layout/audio/template run is included for internal smoke testing.

## Phase 0 — Repository contract and safety baseline

Goal: make it safe for agents and humans to work without guessing what is supported.

- [x] `docs/SUPPORT_MATRIX.md` exists.
- [x] `docs/BETA_POLICY.md` exists.
- [x] `TASKS.md` exists and points to this roadmap.

## Phase 1 — Reproducible environment and CI

Goal: make local dev, CI, and beta packaging use one dependency contract.

- [x] `requirements-dev.txt` exists.
- [x] CI installs from declared requirements.
- [x] CI runs compile, profile-list, and focused beta smoke tests.
- [x] Bootstrap/smoke scripts exist for Unix and PowerShell.
- [x] Shared required-check runner exists at `scripts/ci/run_required_checks.py`.

## Phase 2 — GUI beta hardening and xLights contract

Goal: a tester can open the GUI and safely run against copied layout/template/audio inputs, while generated outputs remain structurally compatible with xLights expectations.

### 2.1 Strengthen canonical xLights output contract

Add focused structural tests and small fixtures for:

- canonical attribute casing such as `StartTime`, `Duration`, `Model`, and `Effect`
- nonnegative durations
- deterministic output order
- section-contained effect timing
- no `None` or `NaN` serialization
- generated model names matching known layout/template targets unless explicitly allowed

Acceptance:

- [ ] Tests catch empty or malformed output.
- [ ] Tests catch invalid timing order.
- [ ] Tests catch unknown model targets unless explicitly allowed.

### 2.2 Add beta mode to GUI

Implement a clear beta mode in `gui_launcher.py` or a small wrapper around it.

Requirements:

- Window title includes `Helix Sequencer — Beta Version`.
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

### 2.3 Add run folder and manifest behavior

Add a small run-management module, for example `core/run_manifest.py`.

Every run should create:

```txt
outputs/beta/YYYYMMDD-HHMMSS-<profile>/
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

### 2.4 Friendly errors

Replace raw exceptions at the GUI boundary with actionable messages.

Examples:

- Missing audio: "Choose a WAV/MP3 file first."
- Missing template: "Choose a template XSQ. Use a copy, not your original file."
- Missing layout: "Choose xlights_rgbeffects.xml or XBKP."
- Engine failure: "Run failed. Open helix.log and attach it to feedback."

Acceptance:

- [ ] At least five common failure cases are tested or manually documented.
- [ ] GUI does not close on engine failure.

## Phase 3 — Clean demo assets and smoke tests

Goal: test without private or copyrighted material.

### 3.1 Build clean-room demo fixture

Create `tests/fixtures/beta_demo/` with generated/simple assets only.

Acceptance:

- [ ] Fixture has no copyrighted music or private sequence content.
- [ ] Smoke test can run without internet or private files.

### 3.2 Add importability smoke

Acceptance:

- [ ] Generated output is parseable XML.
- [ ] Expected xLights sections/elements are present.
- [ ] Test fails if output is empty or malformed.

## Phase 4 — Beta package and release process

Goal: create something that can be shared for early testing without requiring repo knowledge.

- [ ] Create `docs/BETA_RELEASE_CHECKLIST.md`.
- [ ] Create `docs/BETA_README.md`.
- [ ] Add Windows executable smoke if packaging is intended.

## Phase 5 — Engine containment before refactor

Goal: reduce risk from the monolithic engine without destabilizing behavior.

- [ ] Add stable engine facade such as `core/engine_runner.py`.
- [ ] Add typed job config/result dataclasses.
- [ ] Create `docs/EFFECT_ENGINE_EXTRACTION_PLAN.md` before major extraction.

## Phase 6 — Feedback loop and product decision

Goal: turn beta results into a go/no-go and next feature list.

- [ ] Add `docs/BETA_FEEDBACK_FORM.md`.
- [ ] Add beta bug/feedback issue templates.
- [ ] Add `docs/BETA_SUCCESS_METRICS.md`.

## Non-goals before beta

- Full AI learning system.
- Training on user/tester sequences.
- Marketplace/model scraping.
- Production-quality unattended show deployment.
- Major rewrite of `core/effect_engine.py`.
- Supporting every legacy profile in the GUI.
- Perfect visual quality parity with top hand-sequenced shows.

## Status log

| Date | Agent/Human | Change | Evidence |
|---|---|---|---|
| 2026-05-15 | ChatGPT | Created beta-version autonomous roadmap and removed vendor framing. | `ROADMAP_BETA_TODO.md` |
| 2026-05-19 | ChatGPT | Marked Phase 1 complete enough for Phase 2 and documented shared required-check runner. | `scripts/ci/run_required_checks.py` |
