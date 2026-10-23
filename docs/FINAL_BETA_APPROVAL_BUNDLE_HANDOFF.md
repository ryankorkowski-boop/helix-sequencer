# Final beta approval bundle — execution checkpoint

Branch: `codex/eight-hour-recovery-20261019`; starting HEAD
`29f0fcae19cff99b555692d817d9662d9e9504e5`; draft PR #188.
Read MASTER_TODO.md for the full preserved ledger. No merge/public beta authorized.

| Status | Task | Evidence / next action |
|---|---|---|
| COMPLETE | Current source recovered | Cloned exact branch/HEAD, read AGENTS.md, master ledger and release handoff. |
| COMPLETE | Original recording recovered | Retained fixture matches SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. |
| IN PROGRESS | Solid-scene native integration | New canonical_native_band exports FinalBandScene surface geometry; six stable identities, purple harmony, restrained native mouth proportions, exact source drummer node ranges and semantic aliases. |
| COMPLETE | Vocal algorithm preserved | tools/phoneme_vocal_export.py and retained source-separated clocks unchanged. Model source revision 5f60522 is retained. Owner observed vocal-animation approval remains separate from source-separation identity uncertainty. |
| IN PROGRESS | Full-song canonical show | prepare_phoneme_show now uses canonical_native_band, not Review3DScene. First run correctly rejected duplicate REST aliases; adapter now emits only native viseme names. Fresh run canonical-show-v2. |
| IN PROGRESS | Native runtime recovered | GitHub compact artifact12491875007, stripped runtime SHA256 ea7cde8ae6ea4385dec1e835fa270c48a3c289769323891f1fb2e072db674930; pinned2026.18 AppImage for resources/compatibility only. |
| NOT STARTED | Verified canonical MP4 | Generate using actual xLights and inspect rendered frames before promotion. |
| NOT STARTED | Twelve layouts/comparisons/bundle | No missing file may be represented as generated. |
| NOT STARTED | Current Windows/Android validation | Prior evidence in FINAL_RELEASE_EXECUTION_HANDOFF.md is historical, not this candidate. |
| BLOCKED | Exact continuous solid geometry in native pixel preview | Native exports surface samples and stationary light poses; FinalBandScene uses original planar drummer art via compositor. Do not describe native pixels as continuously animated solid meshes. |
| BLOCKED | Owner visual approval/public beta | Owner must approve new band visuals; no public beta/merge. |

Reproduction:

```
python -m tools.prepare_phoneme_show --audio fixtures/audio/Phoneme_Test_Hook.mp3 --output /absolute/fresh-show
HELIX_NATIVE_PREVIEW_WIDTH=1280 HELIX_NATIVE_PREVIEW_HEIGHT=720 python -m tools.native_preview /absolute/fresh-show --xsq /absolute/fresh-show/Phoneme_Test_Hook_Helix.xsq --audio /absolute/fresh-show/media/Phoneme_Test_Hook.mp3 --xlights /absolute/patched/xLights
python -m tools.finalize_phoneme_review /absolute/fresh-show
```

Xvfb and the export command must share the same execution network namespace.
Use private extracted GUI dependencies when package installation is unavailable;
system GTK/GLib plus retained wx libraries, not the full mixed AppImage library path.

## Native collection follow-up

- COMPLETE — twelve distinct native layouts generated from one retained production band plan; AC budgets16/64/256, six-member native bands in7/8/12,88 literal helix rungs. No geometric rotation claimed.
- COMPLETE —36 focused tests passed, one environment-dependent native integration skip. New tests cover literal event clocks/omissions, unique model identities, channel allocation and source vocal counts.
- COMPLETE — actual native xLights exports produced at1280x720/20fps, source34.88s. Earlier diagnostic band frames failed luma/motion acceptance; not promoted.
- IN PROGRESS — all12 native movies, source soundtrack/decode checks, comparisons and packaging via tools/render_approval_collection.py. Render root: /workspace/scratch/b503538b9f0a/approval-layouts-final; delivery root: /workspace/scratch/b503538b9f0a/delivery. Log: render-all.log.
- IN PROGRESS — full unweakened local pytest suite.
- Exact source control/render changes additionally include models/approval_layouts.py, tools/canonical_band_cues.py, tools/build_approval_collection.py, tools/render_approval_collection.py and tests/test_approval_collection.py.
- Repairs: native parent DisplayElements retained after replacing musician rows; active/idle arm nodes separated; literal strings and keys receive retained source events; out-of-range keyboard pitches reported rather than transposed; idle key/string visibility only in event complements.
- First collection native attempt revealed missing parent musician rows, fixed before final collection. Earlier source preparation duplicate REST aliases and duplicate display rows were rejected, then repaired. Missing native GUI effectmetadata caused ColorPanel crash; resource share restored beside retained binary, preserving system GTK.
- Native image/audio results alone never imply owner artistic approval, independent vocal identity, instrument ground truth, hardware/controller tests or platform release acceptance. Post-beta work remains deferred.

Reproduce collection from a completed clean prepared Phoneme show:
```
python -m tools.build_approval_collection /absolute/prepared-show /absolute/fresh-layouts
python -m tools.render_approval_collection /absolute/fresh-layouts /absolute/output --xlights /absolute/patched/xLights
```
Run Xvfb/openbox and renderer in the same execution namespace.

## Verified band checkpoint

- COMPLETE — pushed implementation2ba32e83872819a528dc830fa0e8cb1a0c56ba05.
- COMPLETE — full local Python3.12:2106 passed,6 skips,24 subtests in259.47s. Initial missing-torch collection error repaired by installing CPU dependency, no test exclusions.
- COMPLETE — canonical native band movie7 passed unchanged readability/motion gate: luma14.648, motion1.014, extent.812×.811. Soundtrack correlation.996824804, complete34.88s H264/AAC720p20fps decode. Actual frame inspected; six members and purple harmony visible. Native samples/two-pose limits remain.
- IN PROGRESS — bright native collection under approval-layouts-bright/, output delivery-bright/, log render-bright.log. Earlier obsolete collection was interrupted and must not be delivered as current.
- BLOCKED — simpler layouts still fail unchanged global luma gate. Do not call bundle complete.
- IN PROGRESS — source-specific Windows40007465634 and Android40007465179 queued; compliance40007465091 and GUI evidence40007465082 success at2ba32e8.
- New workflow final-approval-collection.yml saves complete zipped candidate plus explicit technical/owner gates without publishing beta.

## Full movie inventory and solid companion

- COMPLETE —12 native individual movies,6-panel3840x1440,12-panel3840x2160,3-panel band integration3840x720, native close-up and verification feature:17 native-derived MP4s. Original full soundtrack correlation and complete decode measured.
- COMPLETE — separate1280x72020fps FinalBandScene solid OpenGL visualization, clearly captioned non-native. Same retained vocal clocks/production plan; original planar drummer, unresolved toms omitted and cymbal/hand staging unverified.
- IN PROGRESS — explicit gamma2.2 presentation curve and final-file revalidation; prior failures retained. Source AC preview bulbs12px, actual channel budgets unchanged.
- BLOCKED —AC256 lacks dedicated spinner/singing-face circuit props; native drum localization/contact, exact solid native equivalence, geometric helix rotation, current platform/hardware validation and owner visual approval remain.
- Do not label the bundle release-complete even if final file acceptance passes. It contains a real full inventory plus an explicit incompleteness report.

## Final source repair checkpoint

- COMPLETE —37 focused checks pass,1 receipt-dependent native skip. Full suite rerunning.
- IN PROGRESS — native rerenders03/07/08/12 with explicit drum component clocks and completedAC256 spinner/two singing faces. Earlier missing-face/spinner item is superseded by this implementation; final rendered evidence pending.
- Corrected source body idle ownership so kit events can flash independently. Unresolved toms, source cymbal side and snare hands remain honest uncertainty.
- COMPLETE —Windows40009240809 at4cdd069 passed packaged engine/GUI/native-FSEQ checks; current final code still requires source-specific CI. Android pending.
- Final delivery after rendering: run finish_approval_presentation, inspect18 final MP4s, verify ZIP checksums, save ZIP + featured videos persistently, then append download identifiers/results here.
