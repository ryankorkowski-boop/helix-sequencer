# Helix running checklist and recovery handoff

Updated: 2026-10-17. This is the **continuously maintained implementation tracker and standalone recovery handoff**.
Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Working branch: `codex/showcase-pilot-recovery-20261017`
Open PR: https://github.com/ryankorkowski-boop/helix-sequencer/pull/172
Release gate: **Do not merge, publish or claim approved showcase videos without owner review and explicit approval.**

## Status convention

- [ ] Not started / unfinished
- [x] Code committed (not automatically tested or approved)
- [!] Blocked; see explanation

Each milestone records code, tests, and native validation separately. A committed implementation is not equivalent to a tested or validated release.

## Recovery and stability

- [x] Recover branch and PR context; prior checkpoint `1b16dff5f6d9f50bdec759b9ccbead3a378b3b30`.
- [x] Fix stale GUI export-selector test assertion, commit `0c0e0887bdb9abb823683f367d2563faee47f396`; test now matches the GUI's current fail-closed warning.
- [x] Create this persistent running checklist/handoff document.
- [ ] Execute focused export/GUI tests on actual checkout; **not yet run in this session**.
- [ ] Confirm latest GitHub Actions results. No workflow runs were returned for commit `0c0e088` at initial inspection; earlier workflows were queued, not verified passing.
- [ ] Run full regression/CI suite; document command, SHA, result and failures.
- [ ] Resolve cancelled/queued workflows without treating cancellation as a test failure.

## Export integration

- [x] Validated `ShowExportRequest` and export rollback contract in `core/show_export_request.py` (earlier commits).
- [x] Legacy AC-only LMS converter exists: `tools/legacy_lms_export.py`. Requires explicit controller mapping CSV; cannot claim arbitrary pixel or modern LOR format support.
- [x] XSQ/LMS/Both conversion bridge: `tools/dual_format_export.py`, CLI and tests; recent commits `9df1a10`, `96fb86d`.
- [x] Source-based GUI action to convert an **existing** AC-only XSQ into XSQ + legacy LMS, commits `36e9a9c`, `16e903f`, `2697e27`.
- [ ] Connect output selection to the **main Run Sequence Build** pipeline. Current Both selector warns and resets to XSQ; separate conversion button is not automatic dual export.
- [ ] Include and test dual export in Windows packaged GUI. Current frozen build explicitly refuses the new separate action.
- [ ] Validate rollback including sidecars and avoid deleting any preexisting user files.
- [ ] Native import of generated LMS in compatible Light-O-Rama application.
- [ ] Native import/render of generated XSQ in xLights.

## Layout, music, band, and video

- [ ] Verify custom imported xLights layout and controller mapping end to end; never guess AC wiring.
- [ ] Verify small, traditional, mega-tree, band, advanced 3D and AC16 variants are materially distinct.
- [ ] Verify AC16, RGB pixel and mixed hardware routing.
- [ ] Verify seven standalone band xmodels, individual channel budgets, drum-stick contacts, vocal phonemes and 2D/3D parity.
- [ ] Verify note/instrument/lyric analysis against source audio and native rendered output.
- [!] Native xLights showcase MP4s: no newly verified native render or final approved videos in this session. Requires real renderer, source music and artifact validation.
- [ ] Verify Windows desktop and Android build artifacts and real startup behavior.
- [ ] Owner review and approval of authentic new videos before release integration.

## Current checkpoint / next actions

**Latest implementation commit before this report:** `0c0e0887bdb9abb823683f367d2563faee47f396`. **This report's commit will become the new branch head.** Always re-fetch the current branch head before edits.

1. Check `tests/test_gui_export_selector_contract.py` and `gui_launcher.py` are consistent, then execute focused tests (`python -m pytest -q tests/test_show_export_request.py tests/test_dual_format_export.py tests/test_gui_export_selector_contract.py`).
2. Inspect `gui_launcher.py::_run_sequence`, `_run_subprocess` and resulting XSQ path before integrating automatic Both. Require verified CSV and AC-compatible output; do not fabricate conversion for RGB.
3. Inspect Windows packaging/HelixCLI dispatch before enabling dual export in frozen GUI.
4. Inspect native xLights/LOR test infrastructure and music provenance; do not substitute synthetic MP4s.

**Environment limitation:** This session can read/write GitHub via connector but has not checked out and run this repository's tests or native xLights/LOR applications. GitHub commits are real; test success and native import are unverified.

**Resume protocol:** Read this file, `docs/SHOWCASE_REMAINING_WORK_20261017.md`, PR #172, latest branch commits, and CI runs; preserve all newer work. Update this document after each meaningful implementation/test milestone, with exact SHA and failures. If blocked or time expires, commit a complete checkpoint with next command and unresolved tasks.
