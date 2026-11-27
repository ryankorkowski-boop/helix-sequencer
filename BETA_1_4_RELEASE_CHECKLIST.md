# BETA 1.4 RELEASE CHECKLIST

Persistent handoff for Helix Sequencer Beta 1.4. Resume here. Do not treat a checked box as accepted unless its evidence line is present. Owner visual approval is still required before any accepted release.

Updated: 2026-11-27. Admission wiring that already passed Helix CI is `7ddf34aa35391d47be32bcda45f147c16e3935d0`. This change retires the four deleted arch apex circuits on top of that commit. After it is pushed, trust `git rev-parse HEAD`. Branches: `codex/beta14-live-engine-integration` and `integration/beta14-recovered-logic-20261126` (PR #264). Release approved: **NO**.

## Where the work actually is

| Item | Value |
|---|---|
| Repository | https://github.com/ryankorkowski-boop/helix-sequencer |
| Default branch | `feature/restructure-core` at `f4895c644acfe3605bad5b8bf97e255bc6e2fac8` (older than the live integration; do not restart from it) |
| Active working branch | `codex/beta14-live-engine-integration` |
| Admission commit already on both branches | `7ddf34aa35391d47be32bcda45f147c16e3935d0` |
| Code under the in-progress Infinity render | `7ddf34aa35391d47be32bcda45f147c16e3935d0` until a newer push starts another run |
| Draft PR | [#264](https://github.com/ryankorkowski-boop/helix-sequencer/pull/264) `integration/beta14-recovered-logic-20261126` → `integration/unified-beta-completion-20261117`. Draft. `mergeable_state=unstable`. |
| Donor for governed placement | PR [#261](https://github.com/ryankorkowski-boop/helix-sequencer/pull/261) commit `4fd2ddbced8d2f3822f2b9b3fd270bd4ae340957` |
| Related open PRs, not bulk-merged | [#259](https://github.com/ryankorkowski-boop/helix-sequencer/pull/259) unified orchestration, [#260](https://github.com/ryankorkowski-boop/helix-sequencer/pull/260) BeatGrid live placement, [#262](https://github.com/ryankorkowski-boop/helix-sequencer/pull/262) and [#263](https://github.com/ryankorkowski-boop/helix-sequencer/pull/263) CooperativeShowDirector (fork `anotherkorkowski-ux`), [#265](https://github.com/ryankorkowski-boop/helix-sequencer/pull/265) showcase gallery |
| Latest published release | Helix Beta 1.3, tag `helix-beta-v1.3`, 2026-11-13. There is no Beta 1.4 GitHub Release. |
| Older running notes | `docs/BETA_1_4_RUNNING_CHECKLIST.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md`, `MASTER_TODO.md`. This file supersedes them for release status. Do not delete them. |

`CooperativeShowDirector` is **not** in the live tree. `CompositionGovernor` (`core/composition_governor.py`) is the conductor already used by the masterpiece evaluator, iterative convergence, and GUI diagnostics. The nine-pass director is `MultiPassOrchestrationDirector` via `core/effects_orchestrator_bridge.py`, called from `core/sequence_builder.py`. Do not add a second orchestrator. Extract only non-duplicated ideas from PRs #262/#263 after a file-level diff.

## Acceptance legend

VERIFIED = evidence cited below. PARTIAL = code or a diagnostic artifact exists, gate not closed. FAILED = a current run failed. BLOCKED = needs an input this session cannot invent. OWNER REVIEW REQUIRED = subjective or legal acceptance.

## 1. Intelligence under one conductor

- [x] PARTIAL — Role-lane and shared-row admission is now inside the live placer, not a second director. `add_model` uses `core/orchestration_balance.py` (piano overlay, vocal face, overlay/flash section caps). `attempt_place_effect` uses `physical_placement_block` from `core/physical_targets.py`. The section cap counts only a placement that lands. Local tests of those two modules passed. `effect_engine` itself was syntax-checked and not imported here (`audio` is absent from this sparse checkout). No rendered XSQ has been decoded for this gate.
- [x] PARTIAL — One governor exists: `CompositionGovernor.evaluate()` scores density, motion overload, dominance, and contrast. It is not a second show director. `PlacementSession` from PR #261 was not copied; this tree has no `MusicalContext`.
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
- [x] FAILED at `c5954fef`, fix committed, not re-run — Full Infinity job [45905840011](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840011): native preview status `fallback`, warning `xLights REST startup timed out`. XSQ SHA `64b20f1442183529cfb0ed0185b2829ee23bda7849e7d9386ff585cccb05d81a`. The workflow already passed `--render-timeout 1800`, but `tools/native_preview.py` still gave `getVersion` only 120s. `rest_startup_timeout()` now keeps 120s for ordinary previews and allows up to 600s when a longer render budget was requested. It logs `HELIX_NATIVE_REST_WAIT` every 30s. Unit test added. **The Infinity movie is still not verified.** Rerun `.github/workflows/helix-infinity-layout.yml` on this commit before claiming anything else.
- [x] PARTIAL, file checked, not a native movie — Canonical AC layout `xlights_rgbeffects.xml` had 256 models and channels 1–256, including the deleted apex models `Arch 1 Sec 5` (133), `Arch 2 Sec 5` (142), `Arch 3 Sec 5` (151), and `Arch 4 Sec 5` (160). Those four models and their group memberships are removed. Each arch now has sections 1–4 and 6–9 (32). Surviving addresses are unchanged, including Arch 1 Sec 1 = 129, Arch 1 Sec 6 = 134, Arch 4 Sec 6 = 2, Arch 4 Sec 9 = 25. The retired channels are not reused. Local tests: `tests/test_source_ac_review.py` and `tests/test_source_role_routing.py` passed. `tests/test_preview_renderer.py` polyline case passed against `Roof Top White` and asserts `Arch 2 Sec 5` is absent. `tests/test_prepare_drive_ac_preview.py` could not run here because this sandbox is Python 3.10 (`hashlib.file_digest` is 3.11+). CI is 3.11/3.12.
- [x] NOT FOUND, do not invent — This same file has no LOR color-ribbon LED tree and no 16-strip tree. The only RGB Nodes model is `merRy christmas 4`, channel 164, `parm2=1`, a single-line model. Mega-tree rows are single-color AC strands. The 16-strip specification is still not in this checkout.
- [ ] OWNER REVIEW REQUIRED — 16-panel visual acceptance. Baseline to preserve, not to accept:

  - Requested baseline, preserved as a **draft** (not a public Beta 1.4 release): [draft release](https://github.com/ryankorkowski-boop/helix-sequencer/releases/tag/untagged-a987b0145879edf508eb), tag name `baseline/pr264-estimated-16panel-20261126`, target `f068aecb2e821dce785227a9d3ca66caf1e08ab5`. Re-downloaded and checksum-verified:
    - `Helix-Baseline-16-Panel-ESTIMATED-REVIEW-f068aecb.mp4` — 8,336,391 bytes — SHA-256 `b50f315ce2e4f981db92cdb38eccec5b3c1fb525b2b46e645960bb73d29bc831`
    - `Helix-Baseline-16-Panel-comparison_manifest.json` — 59,507 bytes — SHA-256 `e562f1e9855ac99443c8eab07d363b24dd9db0dec67f63bf3677a32e75f90cee`
    - This is `Full_Length_16_Panel_Comparison.mp4` from Actions artifact [15114156910](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45800149044/artifacts/15114156910) (run [45800149044](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45800149044), expires 2026-12-26 11:36 UTC). ESTIMATED_REVIEW. Not owner acceptance. The other per-panel native renders in that 869 MB artifact were not re-uploaded.
  - Newer estimated 16-panel at `625bcc73`: [run 45898800676](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45898800676) artifact [15157222257](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45898800676/artifacts/15157222257), expires **2026-12-26 22:24 UTC**. Not copied to the draft. Also not acceptance.

## 4. Application packages (not a GitHub Release)

- [x] VERIFIED CI smoke, not a published release — Android offline beta [45905840131](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131) succeeded at `c5954fef`.
  - API 30 artifact [15159823225](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131/artifacts/15159823225), 407,514,685 bytes, expires 2027-02-24.
  - API 36 artifact [15159378331](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840131/artifacts/15159378331), 407,821,988 bytes, expires 2027-02-24.
  - These are debug/stability packages from CI, not a signed Play release named `Helix-Sequencer-v1.4-beta-Android.apk`. Confirm versionName/versionCode before anyone calls them Beta 1.4.
- [x] PRESERVED on the draft, not a release — Windows portable at `7ddf34aa` run [45917803280](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45917803280). Asset `Helix-CI-Portable-UNSIGNED-7ddf34aa-Windows.zip` on the draft baseline release. 386,609,631 bytes. SHA-256 `864588c9545632b85c0bb190b8e197a2a53af850abb08a8c128ac1a986492b03`. GitHub's stored digest matches that SHA-256. Local `sha256sum` matched the SHA file inside artifact `15163124053` before upload. Folder with `Helix.exe` and `HelixCLI.exe`, not a single installer. No signtool step, so unsigned. Smoke returned 0 for a 4-frame FSEQ probe, LOR, xLights engine, and eight simulated preview movies. `demucs_executed` is false. Not clean-machine acceptance.
- [x] VERIFIED CI smoke at `5a7ceb2`, superseded for preservation by the `7ddf34aa` zip above — run [45916719983](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45916719983), artifact [15162747653](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45916719983/artifacts/15162747653), 384,382,504 bytes, expires **2026-12-27 00:33 UTC**. Not uploaded separately.
- [x] VERIFIED CI smoke, expiring, older SHA — Windows portable [45905840039](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840039) succeeded at `c5954fef`. ZIP artifact [15158197246](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840039/artifacts/15158197246), 384,381,295 bytes, expires **2026-12-26 22:44 UTC**. Prefer the `5a7ceb2` ZIP above if both still exist.
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

1. Done: the `7ddf34aa` Windows portable ZIP is on the draft baseline release and the SHA-256 matches GitHub's stored digest. Do not publish that draft as Beta 1.4. The older artifact ZIPs can expire.
2. Infinity on `7ddf34aa` run [45917803675](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45917803675) finished "Generate the full musical XSQ on all 10,240 props" and was compiling the native renderer when this note was written. That means sequence generation did not crash. It does not mean the role-lane gates fired, and it is not an FSEQ or MP4. Also still in progress at last check: [45916719842](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45916719842) (`5a7ceb2`) and [45916691190](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45916691190) (`075b1fb`). Read `HELIX_NATIVE_REST_WAIT`. Do not cancel them. This arch commit will start another PR workflow wave.
3. Helix CI on the arch commit [45921322165](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45921322165) failed six tests that still required 256 populated addresses. The follow-up keeps the retired channels and updates those expectations to 252. It does not renumber the map. Nine-panel run [45921322115](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45921322115) died on that same `252 == 256` assertion before a movie. Phoneme [45921322221](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45921322221) is still the real gate: median_motion 0.375 < 0.65. Fresh band [45921322102](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45921322102) rendered, then failed closed because lead/harmony identity is unverified. Do not lower either gate.
4. Done in this change, not a native movie: canonical AC apex sections removed. 32 arch sections remain. No 16-strip tree was in `xlights_rgbeffects.xml`.
5. Ordinary-path sections: if `audio_analysis.json` already satisfies `timeline_from_audio_analysis`, feed it. If it does not, leave the synthetic seed and keep `synthetic_seed_only: true`.
6. Phoneme stage motion 0.374: inspect the retained diagnostic media before changing choreography. Do not lower 0.65.
7. Ask the owner for isolated lead/harmony, or written acceptance of ESTIMATED_REVIEW, before any release note claims singer verification.
8. After the gates above, and only with owner visual acceptance: tag, draft the prerelease, upload APK, EXE, checksums, this checklist, installation notes, and the new 16-panel MP4. Then write `WEBSITE_RELEASE_HANDOFF.md`.

## 8. Modified files this session

- `BETA_1_4_RELEASE_CHECKLIST.md`
- `MASTER_TODO.md`
- `tools/native_preview.py` — `rest_startup_timeout`, 30s wait log
- `tests/test_native_preview_resolution.py` — timeout bounds. Local run: 28 tests, 0 failures.
- `core/orchestration_balance.py` — role, lane, and section-cap functions. No `PlacementSession`.
- `core/physical_targets.py` — layout index plus `physical_placement_block`.
- `core/effect_engine.py` — `add_model` role/budget gate and `attempt_place_effect` shared-row gate. Budget counts a successful placement only.
- `tests/test_orchestration_balance.py`, `tests/test_physical_targets.py` — local direct-call pass. Not a native render.

- `xlights_rgbeffects.xml` — removed four apex models only. 252 circuits. Channels 133, 142, 151, and 160 unused.
- `tools/build_source_ac_review.py`, `tools/prepare_drive_ac_preview.py` — address checker matches the retired set. RGB still starts at 257.
- `tests/test_source_ac_review.py`, `tests/test_source_role_routing.py` — passed locally.
- `tests/test_preview_renderer.py` — polyline fixture moved to `Roof Top White`.
- `tests/test_source_drummer_3d.py`, `tests/test_prepare_drive_ac_preview.py` — expectations updated. The preview test was not executed on Python 3.10.

Draft baseline now also has the unsigned Windows portable ZIP. SHA-256 `864588c9545632b85c0bb190b8e197a2a53af850abb08a8c128ac1a986492b03`. Sites dashboard reporting was skipped: no session token, and none was created.
