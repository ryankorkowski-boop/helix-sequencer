# Helix Sequencer — Master Recovery Roadmap

Updated 2026-10-19. Statuses below are provisional unless verified. This document complements existing MASTER_TODO.md and PR #188's live checklist; do not replace either.

## Immediate gates
- [x] Identify current default branch: feature/restructure-core.
- [x] Identify active PR #188 recovery and integration effort.
- [ ] Reconcile PR #188 checklist with default branch and all open PRs. Next: read docs/HELIX_LIVE_IMPLEMENTATION_CHECKLIST.md on PR #188 head.
- [ ] Diagnose queued Actions: inspect run IDs, runner labels, concurrency, permissions, quotas, environment gates. Do not blindly redispatch. Verify a lightweight run starts and finishes.
- [ ] Integrate and test PR #187 editable XSQ rows; native xLights opening required.
- [ ] Connect PR #184 style adapter to real native XSQ emitter; verify real effect output.
- [ ] Connect PR #183 face detection to GUI, vocal routing and native Faces effects.
- [ ] Validate PR #181 keyboardist with real audio and visual review.
- [ ] Complete layout import, persistence and tier matching from PR #185.
- [ ] Capture and verify genuine GUI evidence from PR #186.
- [ ] Verify Meteors/Shader and musical model targeting, issue #176.
- [ ] Render authentic full-song Bells of Mathmas snowman band and six-panel native xLights MP4, with original audio and independent model effects.
- [ ] Validate editable XSQ and supported LMS exports with native tools.
- [ ] Validate Windows EXE and Android APK builds on supported environments.
- [ ] Audit MIT references, PolyForm Noncommercial compatibility and homeowner/vendor licensing language; obtain owner legal approval.
- [ ] Owner visual review, protected integration and release approval.

## Preservation and gates
Existing MASTER_TODO.md contains historical drummer ground truth commit b27e8d77a63027ed32bcf6851dcff3925472c155 and workflow run 35486153096. Preserve those references. Open issues #154/#163-166 explicitly require separate owner authorization for Universal Library Stage B; do not treat this recovery assignment as approval to publish or bulk-distribute music. Do not merge release branches without approval.

## Status rules
Only mark VERIFIED after recording actual tests, artifacts, commits and native validation. A queued workflow, a draft PR or a structural XML test is not a verified deliverable. Update this file and AGENT_HANDOFF.md every milestone, commit/push before expensive jobs and before resource exhaustion.
