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
