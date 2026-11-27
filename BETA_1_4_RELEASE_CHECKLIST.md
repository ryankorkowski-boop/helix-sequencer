# BETA 1.4 RELEASE CHECKLIST

Persistent handoff for Helix Sequencer Beta 1.4. Resume here. Do not treat a checked box as accepted unless its evidence line is present. Owner visual approval is still required before any accepted release.

Updated: 2026-11-27 00:30 UTC by the release integration session.
Release approved: **NO**. Do not merge PR #264. Do not publish an accepted Beta 1.4.

## Where the work actually is

| Item | Value |
|---|---|
| Repository | https://github.com/ryankorkowski-boop/helix-sequencer |
| Default branch | `feature/restructure-core` at `f4895c644acfe3605bad5b8bf97e255bc6e2fac8` (older than the live integration; do not restart from it) |
| Active working branch | `codex/beta14-live-engine-integration` |
| Active HEAD at this writing | `de2961b636feb68fa2e05e8ee054724be8940a7b` (docs-only ledger on top of the code below) |
| Code under test | `c5954fef098834fa79538285d7bb00eb514b787b` |
| Draft PR | [#264](https://github.com/ryankorkowski-boop/helix-sequencer/pull/264) `integration/beta14-recovered-logic-20261126` → `integration/unified-beta-completion-20261117`. Draft. `mergeable_state=unstable`. |
| Donor for governed placement | PR [#261](https://github.com/ryankorkowski-boop/helix-sequencer/pull/261) commit `4fd2ddbced8d2f3822f2b9b3fd270bd4ae340957` |
| Related open PRs, not bulk-merged | [#259](https://github.com/ryankorkowski-boop/helix-sequencer/pull/259) unified orchestration, [#260](https://github.com/ryankorkowski-boop/helix-sequencer/pull/260) BeatGrid live placement, [#262](https://github.com/ryankorkowski-boop/helix-sequencer/pull/262) and [#263](https://github.com/ryankorkowski-boop/helix-sequencer/pull/263) CooperativeShowDirector (fork `anotherkorkowski-ux`), [#265](https://github.com/ryankorkowski-boop/helix-sequencer/pull/265) showcase gallery |
| Latest published release | Helix Beta 1.3, tag `helix-beta-v1.3`, 2026-11-13. There is no Beta 1.4 GitHub Release. |
| Older running notes | `docs/BETA_1_4_RUNNING_CHECKLIST.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `MASTER_TODO.md`. This file supersedes them for release status. Do not delete them. |

`CooperativeShowDirector` is **not** in the live tree. `CompositionGovernor` (`core/composition_governor.py`) is the conductor already used by the masterpiece evaluator, iterative convergence, and GUI diagnostics. The nine-pass director is `MultiPassOrchestrationDirector` via `core/effects_orchestrator_bridge.py`, called from `core/sequence_builder.py`. Do not add a second orchestrator. Extract only non-duplicated ideas from PRs #262/#263 after a file-level diff.

## Acceptance legend

VERIFIED = evidence cited below. PARTIAL = code or a diagnostic artifact exists, gate not closed. FAILED = a current run failed. BLOCKED = needs an input this session cannot invent. OWNER REVIEW REQUIRED = subjective or legal acceptance.

## 1. Intelligence under one conductor

- [x] PARTIAL — One governor exists: `CompositionGovernor.evaluate()` scores density, motion overload, dominance, and contrast. It is not a second show director.
- [x] PARTIAL — Nine-pass orchestration is invoked from ordinary sequence building (`sequence_builder.py` calls `run_effects_orchestration`). Invocation is real. Promotion into the rendered XSQ still requires `--promote-orchestrated-template` and is audited by `core/engine_activation_audit.py`. Sidecar production is not exported-effect proof.
- [ ] BLOCKED for silent auto-wiring — Song-derived sections reach the nine-pass director only through validated `--orchestration-sections-json`. `core/audio_section_timeline_adapter.py` rejects energy-curve fallbacks, `tail_fill`, and confidence under 0.7. Do not bypass that guard. Next code step: when a real analysis file already has SHA-matched section events at confidence ≥ 0.7, pass that timeline into the ordinary path. Leave low-confidence audio on the synthetic seed and say so in the audit.
- [ ] NOT DONE — File-level extract from CooperativeShowDirector (PRs #262/#263). Diff against `4fd2ddbc` / `c5954fef` before copying anything. Discard a competing director.
- [ ] NOT VERIFIED as a single live run — Piano note, drum hit, and Birdsong response from source audio through admission, editable XSQ, and decoded native channels. Prior focused tests exist; this session has not re-run them.

## 2. RoFormer and performers

- [x] PARTIAL / ESTIMATED_REVIEW — PR #264 wires `--auto-roformer-review` and a 30-second native 16-panel estimated review. Model output is explicitly not verified singer identity. `verify_native_vocal_source.py` correctly refuses to promote model-separated singers.
- [x] VERIFIED limitation — The E14 archive (`604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10`) has one mixed vocal bus and zero independent tracks. Original WAV `8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171`. Do not mark performer verification complete.
- [x] FAILED as an acceptance gate, correctly — Phoneme native job [45905839922](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839922) at `c5954fef`: `visible_stage_motion` median_motion **0.374** (threshold 0.65). Media retained as diagnostic. Not approval.
- [x] FAILED closed, correctly — Fresh six-snowman job [45905840026](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840026) rendered a native 1920×1080 MP4 (quantitative visibility passed: median_motion 0.936, median_luma 20.924) then exited: independent lead/harmony identity unverified. Downstream band acceptance [45905840088](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840088) failed only because that producer was not successful. Diagnostic artifact [15158206792](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840026/artifacts/15158206792) expires **2026-12-10**.
- [x] FAILED closed, correctly — Twelve-layout job [45905839973](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839973): `Pilot acceptance evidence missing: vocal timing and approved-reference identity gates remain open`.
- [ ] BLOCKED — Owner must supply aligned isolated lead and harmony for the exact take, or accept estimated-review labeling forever. Do not fabricate mouths when the second candidate is silent.
- [ ] PARTIAL — Desktop RoFormer ONNX export of the pinned dependency fails on complex STFT. Android keeps Demucs/RoFormer off-device (`helix_mobile.py`). No Android vocal-separation parity.

## 3. Native xLights

- [x] VERIFIED on earlier heads, not re-proven as final acceptance — Multiple native FSEQ/MP4 decodes are recorded in `docs/BETA_COMPLETION_LIVE_HANDOFF.md` (nine-panel, sixteen-panel estimated, six-snowman, Beta 1.3 vs 1.4). Those are evidence of native rendering, not of this release.
- [x] FAILED — Full Infinity job [45905840011](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840011) at `c5954fef`: native preview status `fallback`, warning `xLights REST startup timed out`. XSQ SHA `64b20f1442183529cfb0ed0185b2829ee23bda7849e7d9386ff585cccb05d81a`. Artifact [15159126413](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840011/artifacts/15159126413). Group-load batching landed in `c5954fef`; the REST startup timeout is the remaining blocker. Do not call the 10,240-prop movie verified.
- [ ] NOT DONE — Canonical 256-channel arch correction check (four arches × eight sections, center/apex section 5 deleted, 32 active arch channels) against the real layout files in this session. Do not guess the LOR color-ribbon LED tree map.
- [ ] OWNER REVIEW REQUIRED — 16-panel visual acceptance. Baseline to preserve, not to accept:

  - Requested baseline: [run 45800149044](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45800149044) artifact [15114156910](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45800149044/artifacts/15114156910) `Real-Vocals-30s-16-Panel-ESTIMATED-REVIEW`, 477,234,804 bytes, commit `f068aecb2e821dce785227a9d3ca66caf1e08ab5`, expires **2026-12-26 11:36 UTC**. Prior decode: 1080p/30 H.264/AAC, 29.96 s, soundtrack correlation 0.99944, zero lag. ESTIMATED_REVIEW.
  - Newer estimated 16-panel at `625bcc73`: [run 45898800676](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45898800676) artifact [15157222257](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45898800676/artifacts/15157222257), expires **2026-12-26 22:24 UTC**. Also not acceptance.

## 4. Application packages (not a GitHub Release)

- [x] VERIFIED CI smoke, not a published release — Android offline beta [45905840131](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131) succeeded at `c5954fef`.
  - API 30 artifact [15159823225](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131/artifacts/15159823225), 407,514,685 bytes, expires 2027-02-24.
  - API 36 artifact [15159378331](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131/artifacts/15159378331), 407,821,988 bytes, expires 2027-02-24.
  - These are debug/stability packages from CI, not a signed Play release named `Helix-Sequencer-v1.4-beta-Android.apk`. Confirm versionName/versionCode before anyone calls them Beta 1.4.
- [x] VERIFIED CI smoke, expiring — Windows portable [45905840039](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840039) succeeded at `c5954fef`. ZIP artifact [15158197246](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840039/artifacts/15158197246), 384,381,295 bytes, expires **2026-12-26 22:44 UTC**. Unsigned unless the workflow signs it; this checklist does not claim a signature. Not yet copied to a GitHub Release.
- [x] VERIFIED earlier, same class of package — Windows at `a2b791f3` and Android eight-variant VideoView on API 30 and 36 at `0e17f13` are recorded in the live handoff. They are not this HEAD's release assets.
- [ ] NOT DONE — Clean-device install of a release-signed APK and a clean-Windows launch of an EXE outside the CI runner. No code-signing credentials were available in this session.
- [ ] NOT DONE — `WEBSITE_RELEASE_HANDOFF.md`. Do not write it until a real draft or prerelease URL and checksums exist.

## 5. CI at code SHA `c5954fef` (PR #264 head)

Passed: Compliance [45905840068](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840068), Birdsong [45905839932](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839932), Beta CI [45905840027](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840027), Helix CI [45905839956](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839956), Unified integration [45905840117](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840117), Android offline [45905840131](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131), Windows portable [45905840039](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840039).

Failed, and must stay failed until the underlying gate is real:

- Phoneme stage motion 0.374 < 0.65 ([45905839922](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839922)).
- Fresh band vocal-identity gate ([45905840026](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840026)).
- Twelve-panel missing pilot vocal/reference evidence ([45905839973](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839973)).
- Infinity xLights REST startup timeout ([45905840011](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840011)).
- Accepted-native-band waiter ([45905840088](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840088)) — symptom of the fresh-band failure, not a separate product bug.

Do not weaken these gates to get a green badge.

## 6. Definition of done — current classification

| Gate | Status |
|---|---|
| One conductor, no second intelligence engine | PARTIAL |
| Required features on the production path | PARTIAL |
| Native xLights rendering | PARTIAL (short layouts verified on earlier SHAs; Infinity FAILED) |
| New 16-panel visual acceptance | OWNER REVIEW REQUIRED |
| Performer / vocal separation | PARTIAL, explicitly ESTIMATED_REVIEW; identity BLOCKED |
| Android APK installs and functions | PARTIAL (CI emulator proof at `c5954fef`; not a published signed release) |
| Windows EXE launches | PARTIAL (CI portable ZIP at `c5954fef`, expires 2026-12-26; unsigned disclosure required) |
| Required tests | PARTIAL (unit/integration CI green; native acceptance red for known gates) |
| Binaries on GitHub Releases with checksums | NOT DONE |
| Website handoff | NOT DONE |
| Owner approval | OWNER REVIEW REQUIRED |

## 7. Exact next actions

1. Preserve expiring artifacts before 2026-12-26: baseline 16-panel `15114156910`, newer 16-panel `15157222257`, and Windows portable ZIP `15158197246`. Put them on a **draft** GitHub release labeled baseline, not Beta 1.4 accepted. Record SHA-256 after download.
2. Diff PR #261 governor and PR #262/#263 CooperativeShowDirector against `c5954fef`. Port only missing admission/physical-target/timing rules into `CompositionGovernor` and the existing nine-pass path. No new director class.
3. Ordinary-path sections: if `audio_analysis.json` already satisfies `timeline_from_audio_analysis`, feed it. If it does not, leave the synthetic seed and keep `synthetic_seed_only: true` in the activation audit.
4. Infinity: the group-load patch is in. The new failure is xLights REST startup timeout on the 10,240-prop show. Inspect `tools/native_preview.py` startup wait and the job log around REST bind, then rerun only that workflow. Do not raise the timeout blindly without a log line that shows progress.
5. Phoneme stage motion 0.374: inspect the retained diagnostic media before changing choreography. Do not lower 0.65.
6. Ask the owner for isolated lead/harmony, or written acceptance of ESTIMATED_REVIEW, before any release note claims singer verification.
7. After 1–6, and only with owner visual acceptance: tag, draft the prerelease, upload APK, EXE, checksums, this checklist, installation notes, and the new 16-panel MP4. Then write `WEBSITE_RELEASE_HANDOFF.md`.

## 8. Modified files this session

- `BETA_1_4_RELEASE_CHECKLIST.md` (this file)
- `MASTER_TODO.md` (pointer only)

No production code changed in the commit that added this checklist.
