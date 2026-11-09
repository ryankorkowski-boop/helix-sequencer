## Final delivery and workflow receipt — 2026-10-25

**Code/render source:** b0f82813125254a91bbbb6f132f63e9eccfeb7ec.
This final follow-up changes only this handoff and MASTER_TODO.md; determine the
documentation receipt HEAD with `git rev-parse HEAD`. All executable source is
unchanged from b0f8281, the commit that generated and verified the delivered files.

**Fresh downloads**
- [Native full-band review MP4](https://chatgpt.com/library?file_id=libfile_f8fe1523ff70819186c279c4a034e66e&account_id=personal)
- [Native singer closeup and diagnostic timeline MP4](https://chatgpt.com/library?file_id=libfile_c7bc2cbbfb9081918dd245279f99376f&account_id=personal)
- [Four-video ZIP: native shows, source candidates and verification](https://chatgpt.com/library?file_id=libfile_993b995f93408191a14023fc7843ca91&account_id=personal)
- [Tested API36 fresh-install debug APK](https://chatgpt.com/library?file_id=libfile_7525e6668d5c8191a7db6aaa4dadee50&account_id=personal)
- [Download/status index](https://chatgpt.com/library?file_id=libfile_015e798373a481919556e10fcb29ed92&account_id=personal)
- [Windows Portable](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919520/artifacts/12590071546)
- [Android API36 full receipts](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919594/artifacts/12589618830)
- [Android API30 full receipts](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919594/artifacts/12589094752)

| Code-source workflow | Final result |
|---|---|
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919569 | PASS; Python3.11 and3.12 each2148 passed,6 skipped,24 subtests passed |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919520 | Windows Portable PASS; current worker receipts inspected |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919585 | Phoneme native verification PASS |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919594 | API30/API36 PASS: fresh installation, launch, real-source quick clips and full-song output |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919516 | FAIL: Full-band source lacks independently resolved lead and backing vocal tracks |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919542 | native-proof PASS; accepted-native-band FAIL downstream of producer |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40168919611 | FAIL: Pilot acceptance evidence missing: vocal timing and approved-reference identity gates remain open; do not scale to the full collection |

New docs-only receipt workflows, if automatically triggered, are not substituted
for the completed code-source results above. No unchanged failed job was manually
rerun. The published ZIP records Android still running at packaging time; this
receipt and linked index record its final success.

ZIP:134927478bytes,SHA25696f9bdaa8625fa5366f1446f7ae5997b038a83120c70a010b0cef1ffe00e82f7;
203 entries passed hashes and CRC. Both native camera exports have decoded-channel
SHA25649c18c72a3c551877a5aa5c5b34e9e638776326ea1205c02dca0b9eb6801efa1.
Native FSEQ697frames at50ms; video698frames at20fps. Both have increasing timestamps,
full decode, source correlation.996824804 and unchanged interior/EOF synchronization.
Lead323/backing80 non-rest frames; after32.82s both0, excluding shared closed-rest nodes.
These are light-activity measurements, not independent singer-identity verification.

API36 debug APK:144433366bytes,SHA256b75c4da20d316624a3ff7a1760493e99d1264cde41fb3f40c5ce36c56826b2b6.
Signer3217ea9b9a064922b86d92eab9882dc24ae27ea6f9b74b3e5c3eecb7996ade86
differs from historical code6. Thus **fresh installation only; old-beta update
compatibility remains blocked**. Full237.44s emulator source preview3562frames,
H264/AAC,0ms measured lag, soundtrack correlation.9957144538. No physical-phone
update/data-preservation proof, original key or signing lineage was established.
Keep the old app and verify exports before planning any reinstall. Unsigned release
APKs are excluded from the standalone download and cannot install.

Owner approval remains pending. Exact approved canonical3D likeness/original drummer,
independent singer evidence, musical/spatial artistic acceptance, final12/comparisons,
flagship and historical Android update remain open. Current footage retains a
source-surface band and planar drummer; it is not canonical visual restoration.
Personal-context and repository reference checks did not identify a specific approved
six-member visual source. No merge, release or public distribution was performed.

**Next executable review step (after materializing this checkpoint):**
`python -m tools.vocal_diagnostic CHECKPOINT/03_Vocal_Diagnostics/E14_Candidates/Source_E14.wav CHECKPOINT/03_Vocal_Diagnostics/E14_Candidates E14_REVIEW`.
Audition its matching source/candidates and establish independently defensible vocal
and visual-reference evidence. Do not promote candidate metadata flags or repeat
the unchanged producer expecting it to establish missing source truth.
Then follow the reproducible commands and remaining-gate sequence below.

---

# Helix release recovery — 2026-10-25

Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Branch: codex/eight-hour-recovery-20261019
PR: https://github.com/ryankorkowski-boop/helix-sequencer/pull/188
Inspected starting HEAD: 28210d2b31e5a82aaf46bb2dcc87f51166d711fe.
The implementation commit containing this report is the next checkpoint; use
`git rev-parse HEAD` and the delivery artifact's Source_Commit.txt for its exact SHA.
Read MASTER_TODO.md first. No PR merge or public release is authorized.

## Completed implementation and execution

- Generalized the already working offline two-stage UVR pipeline to any explicit
  checksum-bound owner source. No paid service; no configured Moises key.
- Preserved accompaniment, lead/backing candidates, speech VAD probabilities and
  source/model/derivative hashes. Actual inference networking was denied.
- Re-ran actual separation on the full34.88s Phoneme Test Hook and original36s E14.
  E14 archiveSHA256604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10;
  WAVSHA2568905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171.
  PhonemeSHA25619e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938.
- Added10ms CSV/JSON and exact static chart diagnostics. Speech probabilities are
  not singer identity or calibrated singing confidence; absent values stay blank.
- Prepared and freshly rendered the six-member native Phoneme pilot from the
  actual production sequencer. Matched editable XSQ/models and native FSEQ retained.
  Native video1280x720,20fps,698frames,H264/AAC; luma14.383,motion.702 pass.
  Appended timeline video1280x920 preserves the native stage and soundtrack.
- Actual representative temporal frames inspected. This remains a source-surface
  candidate with a planar drummer. Exact owner-approved3D fidelity is not verified.
-15 focused and189 separate regression tests passed (204 distinct tests).

## Current workflows at starting HEAD

| Run | Result / exact scope |
|---|---|
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116273 | Helix CI PASS |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116306 | Windows Portable PASS |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116297 | Android fresh-install/emulator packaging PASS; old update not verified |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116291 | Phoneme native verification PASS |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116344 | FAIL: Full-band source lacks independently resolved lead and backing vocal tracks |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116224 | Native-proof PASS; accepted-native-band FAIL downstream of producer |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116314 | Native pilot renders; FAIL: Pilot acceptance evidence missing: vocal timing and approved-reference identity gates remain open; do not scale to the full collection |

These are historical/current-starting-revision results, not new-commit green claims.
New workflow URLs/results belong in the delivery artifact's final status/index.
No unchanged failed job was manually rerun.

## Verified application artifacts

Windows: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116306/artifacts/12562847626
Android API30: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116297/artifacts/12562429956
Android API36: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40101116297/artifacts/12562844464

Downloaded Windows diagnostics show successful real-source LOR, xLights and native
FSEQ worker exits. Downloaded Android API30 receipts show fresh install, launch,
quick-clip processing and full237.44s original-source playback (0ms measured lag).
This is emulator evidence, not an owner-phone installation test.
Actual API30 debug APK SHA256d7a0dddefbe3e87b260b3f54a7ba57fbc23a913f4cdaa29593cd56e85b606318;
signer8fb94544d25f60f3d74eb11353a320f351640798c04512f05064345447ee7293.
Historical code6 signerb814ef47f37a86461008bdfbfbd812127b870d92586807078422c657cd09760b.
These signers differ. The unsigned release variant cannot install. Do not use it.
For a data-preserving update recover the legitimate historical private key or
valid lineage, then run tools.android_upgrade_preflight and an actual baseline
update test. Until then keep the old app installed and export shows/audio/layouts
through its Save/Share controls. A clean reinstall requires a separately confirmed
backup and does not prove preservation of its private settings/jobs. No uninstall
or data clearing was performed. See docs/ANDROID_STABILITY_REPORT.md.

## Reproduce (from repository root)

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMBA_NUM_THREADS=2 python -m pytest tests/test_vocal_diagnostic.py tests/test_offline_vocal_transform.py tests/test_phoneme_vocal_export.py tests/test_vocal_presence_screen.py tests/test_vocal_clock_conflict_audit.py -q
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMBA_NUM_THREADS=2 python -m pytest tests/test_canonical_native_band.py tests/test_approved_concepts.py tests/test_final_band.py tests/test_final_native_band_export.py tests/test_native_face_instructions.py tests/test_android_recovery.py tests/test_recovery_pilot_gate.py tests/test_native_vocal_source.py tests/test_prepare_vocal_roles.py tests/test_vocal_pipeline_integration.py tests/test_source_spatial_direction.py tests/test_recovery_string_geometry.py tests/test_review_musical_recovery.py -q
python -m tools.offline_vocal_candidates E14_SOURCE/sources/E14/audio.wav E14_CANDIDATES --models LOCAL_PINNED_MODELS --expected-sha256 8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171
python -m tools.vocal_diagnostic E14_SOURCE/sources/E14/audio.wav E14_CANDIDATES E14_DIAGNOSTIC
python -m tools.prepare_phoneme_show --audio fixtures/audio/Phoneme_Test_Hook.mp3 --output FRESH_SHOW
# Inside an owned Xvfb/openbox session with the verified pinned2026.18 runtime:
python -m tools.native_preview FRESH_SHOW --xsq FRESH_SHOW/Phoneme_Test_Hook_Helix.xsq --audio FRESH_SHOW/media/Phoneme_Test_Hook.mp3 --xlights PINNED_XLIGHTS
python -m tools.finalize_phoneme_review FRESH_SHOW
python -m tools.vocal_diagnostic fixtures/audio/Phoneme_Test_Hook.mp3 fixtures/audio/phoneme_vocal_separation FRESH_SHOW/vocal_diagnostic --native-video FRESH_SHOW/Phoneme_Test_Hook_Helix_Native.mp4
```

The compact native runtime from run40098615878 was downloaded and all manifest
hashes verified. Actual stripped binarySHA256b01c2d3b46a864ad12fb6225f5188f955906c32245bb677f625f2a7d31f7cbe2;
archiveSHA256274473fabee86d95dde74266147435ed80df9b94425861ce36fb2b35a87e8ea1.
It was not recompiled. Retain the associated AppImage resources.

## Remaining release gates and next action

1. Audition the source-bound E14 lead/backing WAVs and compare the10ms timeline
   against independent vocal evidence. There is now actual nonempty backing
   candidate activity (3.30s), but this is not independent validation. Search of
   accessible Drive files for backing/lead/stem found no separately supplied stems.
   Do not promote the candidate just by editing voice_roles metadata flags.
2. Establish an actual approved reference asset/revision and compare native frames.
   The retained six-member source-family adapter remains a sampled-surface model
   and planar source drummer. Do not scale this unaccepted pilot into the final12.
3. Once those evidence gates pass: run verify_recovery_pilot_gate, then
   build_approval_collection and render_approval_collection using the same analysis.
   Inspect all12, synchronized6/12 comparisons and the60–120s flagship.
4. Recover legitimate Android key/lineage or complete an explicitly documented,
   tested migration. No physical owner-phone installation success is claimed.
5. Require passing new-commit workflows and owner approval before merge/public beta.

Owner checklist: exact six-character appearance; original drummer/shoulders/contact;
independent singer timing including ending silence; visible strings/keys; distinct
instrument-led spatial effects; increasingly technical layouts; Android/Windows
on-device acceptance. All remain pending where unsupported by direct evidence.
