# Helix master completion roadmap

Updated 2026-10-18. Owner directive supersedes earlier completion claims when
visual acceptance is absent. Release: **NOT READY; draft only**. No merge,
application publication, or music distribution authorized.

This is the current acceptance ledger. `MASTER_TODO.md` remains the preserved
historical implementation/evidence ledger; its unchecked entries below remain
open. Historical checkmarks are not proof of current release acceptance.
Owner for implementation rows: Codex; artistic approval and device access: owner.

## Keyboard motion validation slice — 2026-10-18

R06 **IMPLEMENTED — UNVERIFIED**: PR #180 now includes dedicated authored
keybed/short-link/velocity/acceleration/real-key-contact regression checks,
plus independent silence and unreachable-note assertions. Arm geometry is a
candidate, not artistically approved. Required dependencies: focus suite,
native MP4, verified source notes and owner visual review. Existing seven
cast and approved guitarist/drummer untouched. No release merge.

## Current drummer regression mismatch and remedy — 2026-10-18

Prior PR #180 full audit run 39192406726: 1,806 pass,
2 fail, 6 skipped. Both failures were tests accidentally
treating foot-only HI_HAT as a drumstick target. Fixed the test
setup on codex/keyboard-arm-proportions-20261018 while preserving explicit foot-pedal assertions.
Production drummer remains unchanged. Mark IMPLEMENTED —
UNVERIFIED until both 3.11 and 3.12 full CI pass. Native
showcase acceptance still BLOCKED separately.

## Current recovery and integration evidence

- Inspected PR175 head `13a833e9b71dbacefb340654a44f5707b162888e`.
- Default branch is `feature/restructure-core`, not main. PR175 is stacked on
  PR172; PR173/174 and the opt-in PR171 composer have separate heads. Their
  presence in open PRs does not prove integration. No branches merged.
- Run 39114244696 completed with failure in video QA, after a completed render.
  Artifact 12130964463 was downloaded and decoded. Five-frame global mean delta
  was 1.10–1.79, below the old threshold 3. Actual stage-only decoded samples
  showed 142/143 moving transitions. Fixed-camera false failure is reproduced.
- Its original drum report: 234 source tags, 131 hi-hat foot cues, 36 arm hits,
  67 rejections. These are not 234 verified drum contacts. Kick classification
  and transit rejection accounting remain to be audited.
- E14 has four scheduled mallet contacts and unverified instrument identity;
  it is not a qualified mallet feature. Full-band reviews may retain silence.
- Local recovery uses pinned GitHub files and checksum-verified original PNG;
  the older default-branch ZIP is NOT treated as current source. Full local
  checkout/dependency installation is unavailable through current network.

## Acceptance ledger

Every row includes priority/dependency, state, owner, reference, acceptance,
evidence and remaining defects. `verified` means the specific row only.

| ID / priority / dependency | State / owner | Reference | Exact acceptance | Evidence / remaining defects |
|---|---|---|---|---|
| R01 P0 none: recover run | verified / Codex | PR175, run39114244696 | Read actual logs, download artifact, distinguish render and QA | Actual render completed; QA false freeze reproduced; not artistic approval |
| R02 P0 R01: integration audit | in progress / Codex | PR168–175, MASTER_TODO | Compare all seven-day commits, tests and usable artifacts | Open heads/base chains inspected; full branch ancestry and remaining issues still incomplete |
| R03 P0 R02: preserve artwork | in progress / Codex | PR175 original V3 | Authored PNG/xModel/spec hashes unchanged; all eight components present | Source PNG matches 643e1bfb…; fixed source artwork retained; all-platform regression pending |
| R04 P0 R03: snare articulation | in progress / Codex | animation/articulated_source_drummer.py | Constant two-link lengths and outward/down snare elbow across every source frame; exact contact preserved | Fixed right skeleton replaces mixed-length elbow blend; deterministic transitions pass; run39115813867 source preflight passes, render ongoing |
| R05 P0 R04: drum timing and feet | in progress / Codex | PR175 | Every hi-hat note drives pedal/foot at source time, no sticks; kick retained; all rejected transitions logged | 17 focused tests pass; source-art foot/pedal recovery now inside visible crop; kick tags separated from arm rejections; physical kick and real-film approval incomplete |
| R06 P0 R03: keyboard motion | in progress / Codex | models/keyboard_motion_plan.py | No debounce; bounded speed/acceleration; stable shoulders; valid reach; real-note contact accounting | Eight deterministic patterns pass; no idle-target bouncing; real-source contacts and visual acceptance pending |
| R07 P0 R06: keyboard analysis | pending / Codex | music/review_score.py | Confidence, stable pitch, onset/off, source-specific note filtering; numerous credible real contacts | Explicit low-confidence rejection added; source separation and pitch ground truth unverified; anticipation incomplete |
| R08 P0 R02: mallet source detection | pending / Codex | PR175, pitched_roles | Find numerous credible pitched-percussion events, preserve uncertain identities | Current E14 four contacts is insufficient; no fabricated notes or mallet feature claim |
| R09 P0 R08: mallet articulation | pending / Codex | unified_mallet | Correct alternating contact/rebound/bar mapping; frame contacts equal schedule | Full chain and frame-level counting incomplete |
| R10 P1 R02: guitar | pending / Codex | preserved guitarist | Verified lead passage, fret/pick/string sustain and contact | Original motion preserved; genuine solo isolation and feature incomplete |
| R11 P1 R02: bass | pending / Codex | preserved bassist | Independent pitch/pluck/sustain; contact visible | Fresh independence/contact validation incomplete |
| R12 P0 R02: vocal roles/phonemes | pending / Codex | PR153/175 | Ten controls, silence closures, defensible separate voices, restrained mouth | Existing evidence router retained; source phonemes and harmony not verified |
| R13 P0 R03: purple neutral singer | in progress / Codex | PR175 | Purple across every renderer/preset/export/platform; neutral geometry | Current scene preflight checks purple and neutral geometry; cross-path regression incomplete |
| R14 P0 R06: fixed review camera | in progress / Codex | original-v3 workflow | All seven visible, stable scale, no camera cuts, complete decode | Prior frame shows seven; stage-only motion gate passes prior artifact; new render pending |
| R15 P0 R04–R14: source metrics | pending / Codex | contact reports | Detected/accepted/rejected/missed/false events, timing, pitch provenance; frame-confirmed contacts | Keyboard source/contact frames separated; independent ground truth and per-event rendered contact audit incomplete |
| R16 P1 R15: audio/excerpt ranking | pending / Codex | Drive Helix Music Mix | Full-song instrument-specific ranking, hashes and unique recordings, 15–42s selected windows | Historical ranking retained; fresh multi-song selection incomplete |
| R17 P1 R15: full-band and B–F features | pending / Codex | review package | 36–42s band and genuine keyboard/mallet/guitar/drum/vocal clips; original audio; all decode | No new approval-quality feature package claimed |
| R18 P1 R17: highlights | pending / Codex | PR174 | 90–150s verified multi-song assembly, source-identification and audio alignment | Advertisement tooling is separate open PR; new film incomplete |
| R19 P1 R15: layouts | pending / Codex | PR153/171/173 | Distinct AC256/experimental RGB, helix rungs, special props, depth/dynamics; synchronized comparisons | Historical native evidence retained; integration and fresh comparison incomplete |
| R20 P1 R19: standalone models | pending / Codex | PR153, #160/163 | Seven independent xModels, native 3D import, <=16 AC circuits each, distinct pixel count | Historical counts 10/9/11/15/15/14/14; current source/native import not rerun |
| R21 P1 R20: controller selection | pending / Codex | #157/162 | Explicit/detected 16/32/64 AC, pixels/mixed config reaches engine; no ownership inference | Configuration router historically implemented; end-to-end hardware unverified |
| R22 P1 R20: dual export | pending / Codex | #154–156/163 | One real run makes XSQ+LMS; native import/timing validates both | Universal default orchestration and LOR native validation incomplete; current owner directive authorizes implementation, distribution still held |
| R23 P1 R22: Windows | blocked / owner + Codex | PR150 | Existing EXE launches, audio/generation/preview/export/settings/error smoke | Historical build success only; no Windows runtime/device here |
| R24 P1 R22: Android | blocked / owner + Codex | PR150 | APK install/launch, long job, preview/share/settings on supported device | Historical build success only; no Android device/emulator here |
| R25 P1 R15: profile/cache | pending / Codex | #165 | Per-stage timing/memory; deterministic hash-bound cache; no dropped events | No comprehensive fresh profile |
| R26 P0 R17–R24: release gates | pending / Codex | final acceptance | Full suite, native imports, all-frame/contact/video/audio gates, packaging/legal/docs | Focused tests only; all outstanding rows block release |
| R27 P1 R26: packaging/docs | pending / Codex | #164/166 | Direct verified links, provenance, channel maps, troubleshooting, release report | No final deliverable package yet |
| R28 P0 R26–R27: owner approval | blocked / owner | release hold | Explicit approval of current films and final release candidate | NOT approved; no merge/release/distribution |

## Preserved legacy backlog

Each historical unchecked task remains **pending, owner Codex, priority P2**
unless the acceptance ledger above assigns a higher priority/state. Dependency:
recovery R02; reference: exact file/line below. Acceptance is the quoted task,
with usable artifact/test evidence required. Evidence: none newly verified;
remaining defect: historical completion status must be reconciled. No task is
silently cancelled by creating this ledger.
- `MASTER_TODO.md:96` — - [ ] User reviews the four previews and supplies corrections/explicit approval.
- `MASTER_TODO.md:97` — - [ ] Obtain user video approval before final release integration.
- `MASTER_TODO.md:197` — - [ ] Receive user MP4 corrections/explicit acceptance. Unknown toms, mixed-bus
- `MASTER_TODO.md:214` — - [ ] Establish whether this is identical to the October 13 original six-song source; filename, MP4 size and decoded WAV hash differ from earlier original-sampler evidence. AAC padding must be handled explicitly for exact duration alignment.
- `MASTER_TODO.md:215` — - [ ] Generate source-bound musical analysis and native drummer XSQ for this exact uploaded audio. `tools/render_final_band.py` requires both, not just a WAV; no verified fresh band MP4 exists yet.
- `MASTER_TODO.md:216` — - [ ] Render and fully decode two six-member bands, six layouts and comparison movies; independently inspect kick, mallet and keyboard passages. Do not ship an unverified or fabricated video.
- `MASTER_TODO.md:217` — - [ ] Physical CTB16PC, Samsung/ARM64, final signing, song distribution and release gates remain open.
- `MASTER_TODO.md:766` — Checklist: [x] inspect source/previous band research and originals; [x] six-member/helix-face geometry; [x] all six source-bound analyses; [x] 11 native shows and full-audio movies; [x] exact mouth/arm/Faces/paired-drummer checks; [x] full decoding/audio comparisons/visual samples; [x] portable show rerender; [x] 48 focused tests/source preservation; [x] both ZIPs; [x] immutable artifact publication; [ ] user musical/artistic review (delivery remains available without this review).
- `MASTER_TODO.md:796` — Checklist: [x] inspect rules/ledger and stop-motion scope; [x]20 concept/principle/standout briefs; [x]10 paired hero/storyboard plates; [x] visually inspect images; [x] PNG/link/count/preservation checks; [x] mobile gallery and short summaries; [ ] explicit user selection; [ ] native pose geometry and held-frame cadence after authorization; [ ] actual motion/readability/loop/native verification after implementation.
- `MASTER_TODO.md:808` — Checklist: [x] inspect prior rules/ledger and derive geometry/visibility lessons; [x]20 distinct concept briefs; [x]10 paired visual plates; [x] visually inspect all plates; [x] PNG/link/count/preservation checks; [x] static mobile gallery and short summaries; [ ] explicit user selection; [ ] native geometry/viewpoint calibration for selected concepts; [ ] native/physical implementation and sequence verification after authorization.
- `MASTER_TODO.md:818` — Checklist/evidence: [x] read rules/ledger and identify saved artwork; [x] scope clarification; [x] all 22 geometry generators; [x] 45 focused native-grid/channel/reference/portability/drummer tests; [x] first two native renders (Arena/Pontoon) and decoded visual inspection; [x] full 22 native renders; [x] all 22 MP4 decode and visual checks; [x] durable native layouts, proof and direct-link inventory; [ ] remembered whale source located.
- `MASTER_TODO.md:832` — Checklist/evidence: [x] read rules/ledger and inspect native shows/drummer contract; [x] ask which visual set and which stages; [x] eight-target native connectivity render (80 × 50ms frames, 6,912 pixels / 20,736 channels, all eight exact canonical node sets); [ ] chosen native stage/visual builds; [ ] song-bound drummer performance; [ ] regenerated MP4s and six-layout comparisons. Existing Helix Audiolights/Dry Drum Test transcriptions cannot be reused on the five different showcase songs; new performance needs source-bound analysis.
- `MASTER_TODO.md:866` — Checklist: [x] corrected complete exports; [x] seven self-contained show copies with media; [x] native rendering, coverage, duration and control audit; [x] final ZIP relocation and source/favorite preservation checks; [x] local render-then-open launcher and cloud GUI proof; [x] focused regressions; [ ] laptop GUI launch and audio-device playback; [ ] user musical/artistic acceptance.
- `MASTER_TODO.md:875` — Checklist: [x] inspect rules/ledger and prior favorites; [x] pin all three existing favorite shows; [x] generate spatial01–06 and abstract07–12 plates; [x] generate themed13–22 plates; [x] document evidence-based 3D feasibility and a future small-module assessment; [x] offline Chromium filters/modal/shortlist/mobile checks; [x] final archives/link/image/favorite-byte checks; [x] save/push feature branch; [ ] user chooses concepts before implementation.
- `MASTER_TODO.md:885` — Checklist: [x] inspect pipeline/layouts and verify five uploads; [x] clean music templates and pilot native playback; [x] all requested full-song sequences; [x] all native renders and actual-audio previews; [x] native/frame/duration/audio and focused regression checks; [x] review gallery/packages and push; [ ] user musical/artistic review.
- `MASTER_TODO.md:896` — Checklist: [x] six artistic compositions; [x] native/channel/geometry and Aurora preservation tests; [x] comparison images/gallery and six packages; [x] native xLights import/render and RGB audit for every flavor; [x] six decoded lighting videos/browser review; [x] CI/push/delivery; [ ] user artistic review.
- `MASTER_TODO.md:910` — Checklist: [x] inspect native factory/serialization and legacy layout; [x] geometry/export; [x] images/video and portable bundle; [x] native GUI/headless load/render and decoded frames; [x] focused/existing layout and browser checks; [x] feature-branch commit/push, native artifact CI and downloaded ZIP verification; [ ] user artistic approval.
- `MASTER_TODO.md:923` — Checklist: [x] source/activation/rejection audit; [x] investigate and reject second-model family errors using user listening; [x] scoped source calibration and hold/rest fix; [x] source anchor/abstention/preservation tests; [x] before/after report, XSQ/full actual-audio MP4 and decoded strikes/rests; [x]140-test relevant suite; [ ] push/CI and downloaded artifact verification (final remote status in local HANDOFF/FINAL_VERIFICATION); [ ] user preview approval.
- `MASTER_TODO.md:934` — Checklist: [x] inspect source/stems and exact missing stage; [x] implement review overlay and fail-closed checks; [x] real-audio anchor/physical target tests; [x] new XSQ/full MP4 and decoded tom frames; [x] c58364b / CI #223 (134 tests), uploaded exact source/report/frame proof verified; [ ] user preview approval.
- `MASTER_TODO.md:944` — Checklist: [x] verify exact uploaded source; [x] original-mix and separated transcription; [x] isolated attack-energy and source-band plots; [x] source-bound XSQ/MP4; [x] inspect local proof; [x] CI #222 (122 tests) and downloaded exact source/report/decoded proof verified at c0e8bae; [ ] resolve false-hi-hat behavior using additional evidence/human review.
- `MASTER_TODO.md:954` — Evidence/checklist: [x] inspect current flash/source effect settings; [x] implement and test (six lighting regressions; final CI 122 tests passed); [x] exact identical event audit/analysis; [x] real-song 25 s MP4/XSQ plus eight decoded attack/decay frames, soundtrack correlation .9962146413; [x] c0e8bae / CI #222 and delivered full-song proof decoded, soundtrack correlation .9919693452; [ ] user approval.
- `MASTER_TODO.md:963` — Evidence/checklist: [x] inspect and implement; [x] exact event audit/analysis comparison; [x] complete native projection and both decoded snare hands; [x] isolated XSQ and original-song 25s MP4 (audio correlation .9962146413); [x]116 relevant tests plus61 final visual checks; [x] full237.44s MP4 and decoded snare/kick overlap (source correlation .9919693452); [x] pushed cd16a03 and CI#220 success (116 tests); uploaded report/native assets identical, decoded uploaded frames inspected; [ ] user preview approval. Evidence: `test_runs/drummer_visual_polish/`.
- `MASTER_TODO.md:1002` — - [ ] Regenerate the real-audio proof, inspect CI/artifacts, and obtain user visual approval.
- `MASTER_TODO.md:1013` — - [ ] GitHub CI + regenerated real-song artifact inspection pending this commit.
- `MASTER_TODO.md:1034` — - [ ] Auditory annotation and musical approval: detector thresholds intentionally unchanged pending evidence.
- `MASTER_TODO.md:1035` — - [ ] Native xLights import/playback validation and user visual approval.
- `MASTER_TODO.md:1075` — - [ ] Continue with Phase 0/1 execution in the exact order called out by the roadmap before moving into engine-facing refactors.
- `MASTER_TODO.md:1076` — - [ ] Keep this ledger updated as each beta phase completes.
- `MASTER_TODO.md:1116` — - [ ] User visual approval of the corrected real-song candidate.
- `MASTER_TODO.md:1117` — - [ ] Native xLights import/playback confirmation.
- `MASTER_TODO.md:1131` — - [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- `MASTER_TODO.md:1132` — - [ ] Validate detector against real-song audio and quantify false positives.
- `MASTER_TODO.md:1133` — - [ ] Generate real-song XSQ.
- `MASTER_TODO.md:1134` — - [ ] Render full-song MP4 with audio.
- `MASTER_TODO.md:1135` — - [ ] Human visual review of rendered drummer timing.
- `MASTER_TODO.md:1268` — - [ ] User visual approval and native xLights import/playback remain final acceptance gates.
- `MASTER_TODO.md:1274` — - [ ] Resume and verify remaining embedded-stage native films; require complete FSEQ and decoded video, original audio matching, and channel parity.
- `MASTER_TODO.md:1275` — - [ ] Complete six-layout comparison queue and ensure every pane is sourced from authentic archived native channels.
- `MASTER_TODO.md:1276` — - [ ] Finish longer advertisement cuts; verify PCM edit timing and reject AAC-concatenation offsets.
- `MASTER_TODO.md:1277` — - [ ] Package all verified MP4s, native source shows, source hashes, contact sheets, QA reports and reproducible commands in a delivery index.
- `MASTER_TODO.md:1278` — - [ ] Perform human musical/visual review and controller review before any production merge or public release.
- `MASTER_TODO.md:1279` — - [ ] Do not mark scratch-only production outputs as GitHub-persisted until independently uploaded and hash checked.


## 2026-10-18 — Owner-requested advertisement delivered for review

Produced Helix_Advertisement_96s.mp4: 96.000 seconds, 1920x1080 H264/AAC stereo,
3840 fully decoded frames at 40fps (20fps source poses duplicated, not interpolated).
SHA256 569e3fe90878d181f55edc82639066d764d7e5b5083d8f743ac9bca633f9544b.
New ten-shot edit uses PR175 d420807 original-art fixed-camera seven-snowman
render (run39115986624, artifact12132521933) plus explicitly reused Oct15
Holly Steel Run and Kaleidoscope Engine six-layout footage. Layout source commit
is unavailable; do not label all footage freshly rendered or all native xLights.
Assembly uses PR174 dbeb868 tool with PCM intermediate soundtrack and final AAC.
Full decode and zero blank-picture frames verified; every edit zero-lag source
audio correlation >=0.999872. Final contact sheet visually inspected.
Saved movie: libfile_cabe566db1208191b1695323da7bbc78; reproducible scripts,
edit manifest, original-band provenance and QA package: libfile_f5abad2503fc8191abe419affe294e84.
No synthetic musical events, no substituted music, no feature/compatibility or
release-completion claims. Development-preview captions retained. Owner visual
approval remains pending. Instrument solo package, true mallet-rich selection,
native imports, platform checks and every other release blocker remain open.
The advertisement does not satisfy those separate gates.

