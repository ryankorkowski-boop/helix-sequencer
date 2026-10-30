HELIX SEQUENCER — LIVE RECOVERY HANDOFF

Last updated: 2026-10-30T02:07:53.459618+00:00; user-facing date29October2026 (America/Chicago).
Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Current branch: codex/eight-hour-recovery-20261019
Current HEAD: dd73e36777d0a02c6d403245d03421d093bda0fd; this file's next metadata-only successor may be newer.
Last verified implementation SHA: dd73e36777d0a02c6d403245d03421d093bda0fd (58focused tests and full source-bound export parity; finalCI/device checks pending).
Last successful CI runs: source d52d234 fullCI40988081845 (Python3.11/3.12:2206tests+24subtests/6skips each), Windows40988090460. Source18a9762 fullCI40986962386 passes2203+24subtests/6skips each andWindows40986968903. These are explicitly previous implementation evidence.

CURRENT OBJECTIVE: finish existing beta and deliver exactly nine verified MP4s, without merge/publication.
CURRENT TASK: AND-01 / REG-01 / WIN-01 collect final-source results at dd73e367.
LAST COMPLETED TASK: MEM-03 global tuning workspace and DEP-01 numerical-runtime stabilization, locally verified and pushed.

COMPLETED AND VERIFIED:
- [x] REC-01 recovered remote45f17d69, PR188draft/unmerged, Issue199, complete existing inventory and native checkpoints. Current instruction is9videos; historical6/15/18counts are superseded.
- [x] MEM-03 / MEM-02 bounded long-file HPSS, pitch, centroid/width/flatness/contrast/flux, mel-bank FFTs and automatic CQT tuning. Whole-song tuning median/histogram and contrast dB floor are preserved; short paths remain compatible.
- [x] DEP-01 pinned desktop NumPy2.2.6/Numba0.61.2/llvmlite0.44.0 after a reproduced longfloat64 crash underNumba0.68.1. Android ABI pins/serial compatibility are unchanged. Official compatibility source is recorded in numerical_runtime_failure.json.
- [x]58focused tests pass,4warnings,80.16s on the pinned runtime, including exact float32/float64 tuning/chroma bins, frame/pitch/descriptor/flux/mel equality, HPSS boundaries, silence, tail, real drums, Android export/recovery and current Chronoflow/Helixualizer. Receipt: focused_memory_final.xml; exact file hashes: latest_status.json.
- [x]Same237.44s48kHz whole-song production sequencing/export: baseline1850908672bytes/142.832s -> tuned1024978944bytes/143.096s,44.6229%lowerpeak. BOTH43913effects, exact musical signaturefed5565412b36f5f48967eaf4e68572cd4b846b399d8f523161b094d31e2864c. production_tuned_comparison.json records scope/inputs. No material overall speedup claimed. Both paths reuse the same verified stems and exclude MP4. Linux Android-kernel bridge is not device proof. Baseline45f17d69 DSP modules were reconstructed on the same runner; raw GitHEAD fields are supplemented by explicit module identity/hash receipts.
- [x]Five prior layoutMP4s (04/05/06/07/09) and MP4-only ZIP recovered and SHA256 matched to passing full-decode/audio/QC receipts. No native rerender/reanalysis needed. Representative existing comparison frames inspected; full continuous playback not watched.
- [x]Persistent source/audio/stem engineering checkpoint saved, identity applied; no source music or large binaries committed.

IN PROGRESS:
- [ ]Final-source dd73e367 fullCI push40989578137 / PR40989590900.
- [ ]Android API30/API36 push40989578333 / PR40989590969; do not call queued/running passed. Previous18a/d52Android work was superseded by later necessary source pushes, not accepted.
- [ ]Windows portable40989591050.
- [ ]Current strict native producer40989590899 / finalband40989591017 / Phoneme40989590973 / collection40989590883. Known qualification blockers remain below.

BLOCKED:
- [ ]CAN-01: exact approved fully modeled3D drummer/band identity is not established. Retained V3 is planar source art. Review3DScene is unapproved. Need actual approved asset or identifying reference/commit; do not relabel a substitute.
- [ ]VOC-01: UVR/MDX/KARA/Silero candidate lanes do not establish independent singer ownership or lexical phoneme timing. Original E14 remains unqualified. Need genuine source-bound acoustic/lexical evidence; no transcript or singer identity may be fabricated.
- [ ]VID-01:4missing files:01_Canonical_Snowman_Band.mp4,02_Lead_and_Harmony_Vocals.mp4,03_Drummer_and_Instruments.mp4,08_Full_Helix_Showcase.mp4. Do not create HELIX_FINAL_BETA_APPROVAL_MP4S.zip until all9qualify.
- [ ]Physical Samsung/controller acceptance and explicit owner artistic approval remain open.

FAILED ATTEMPTS:
- Original AndroidAPI30 run40836353439 killed foreground Helix at752236KiB RSS during offline processing. Instructions/Band recreation had passed. Earlier bounded stem separation alone did not fix all full-song spectra.
- Per-block spectral_contrast changed63rest samples by up to0.233dB. Rejected; corrected pinned peak/valley reduction applies one whole-song dB floor. Strict exact-array test now passes. Do not restore local dB floors.
- Classifier-only improvement (1.60GB->414MB) and mel-only improvement (1.35GB->306MB) did not by themselves remove the overall peak. Actual remaining stack was Chronoflow automatic CQT tuning -> full-song piptrack. production_trace.json records it. Corrected whole-source result is44.62%lowerpeak.
- Original and candidate longfloat64 piptrack segfaulted underNumba0.68.1/LLVM0.50 withbothNumPy2.3.5 and2.5.4. Matching newer NumPy alone did not fix it. Supported NumPy2.2.6/Numba0.61.2/LLVM0.44 passes the unchanged assertions. Dependency pins preserve this evidence; do not remove the regression or merely skip the test.
- Previous native source18a producer40986968812 failed independent vocal qualification; finalband40986968930 failed producer dependency; collection40986968962 lacked pilot evidence; Phoneme40986968843 motion0.425<0.65. Failure excerpts retained. These are not new-source results and no gate was reduced.
- Initial synthetic3sfixture had out-of-range test strikes; fixed fixture, reran all tests. No production behavior was changed for that fixture error.

ARTIFACTS ALREADY AVAILABLE:
- Authoritative9-file inventory, exact file hashes, source identities and links: evidence/beta_completion/artifact_manifest.json.
- Five-MP4 ZIP: https://chatgpt.com/library?file_id=libfile_3082a9295984819189352b8b63ddb5ec&account_id=personal ;275032669bytes;SHA2568f12c88b1cdb3703ddb5d75993bbb32a1de9a8345d9a410850a66ac42416b6e8.
- 04AC/RGB:libfile_3a1bf5ca007c81919fe63a0fd9500284;05six-layout:libfile_ee16c166488c8191bcc4e2235c384e67;06technical:libfile_78f3c8c5c63c8191a04cef9080eb3fda;07helix:libfile_a47c3b032e688191bec7eb35f8d6c585;09sampler:libfile_c8a2dea840a881918e403b0e242d4e8d.
- Native checkpoints:libfile_047ff812c6888191baa9a2d6cbc95dfa (319292814bytes,SHA256b7968227aa926b3ca546ad50989ace33608086546a3580daa7919e10702ee9b6);libfile_e3a0d03004888191a477e14bf2188285 (383475507bytes,SHA256815921854dbe6de6e7aa0e36d531e07546dd1bc64f69a3668a356c9800d2ba45).
- New audio/stem/performance checkpoint:libfile_fcf68c0edd7481918e7892adbd8def38 ;120781146bytes;SHA2566b25b139e307db1b09930a561163b98a34f1ed0a1d2e08a6985db2259f4e0580. Contains22entries,0MP4s, source full-song.wav,4stems and prior exact export receipts. Restore its relative paths into WORK. Latest tuned/trace receipts live in Git; do not resave duplicate music. This engineering ZIP is NOT an owner approval bundle.
- Local root:/workspace/scratch/1ed7281f6b64; checkout:helix-sequencer; verified movies:verified-layout-mp4s; native resources:WORK; profiling inputs:full-song.wav,memory-profile/stems; outputs:offline-memory/tuned. These local paths may disappear; durable counterparts above remain.

FILES MODIFIED:
- core/bounded_audio.py:bounded DSP workspace with unchanged global statistics.
- core/audio_intelligence.py:bounded harmony analysis/HPSS, avoid duplicate stem spectrum.
- core/effect_engine.py:bounded harmonic and multiband workspace/global tuning.
- core/chronoflow.py:source-equivalent whole-song tuning without full pitch workspace.
- core/helixualizer.py:bounded long float64mel FFTs.
- audio/drummer_v3.py:bounded HPSS/descriptors; typed events, unknown-tom abstention and thresholds retained.
- xlights/xsq_writer.py:bounded long pitch/centroid work and timely spectral cleanup.
- requirements.txt,requirements-windows-portable.txt:verified desktop numerical pins.
- tests/test_bounded_audio.py:strict source/parity and long-tuning regressions.
- tools/profile_android_full_song_memory.py:reproducible baseline/current performance and peak-stack tracing; refuses overwriting outputs.
- MASTER_TODO.md, live handoff and evidence/beta_completion:continuous source-bound progress, receipts and exact9-file inventory.

TEST RESULTS:
- Current code dd73e367:58focused pass/4warnings/80.16s; exact module/dependency hashes retained. FullCI/platform results must be collected from exact runs above.
- Previous d52 fullCI2206+24subtests/6skips eachPython3.11/3.12 andWindowssuccess; previous18a2203+24/6each. Do not substitute these for a changed implementation.
- Pinned graph longfloat32/float64 isolated2pass/18.87s before whole58-test run; counts overlap, do not sum.

RENDER RESULTS:
- No newly qualified band media. All5existing native-layout MP4 bytes unchanged; H264/AAC1920x1080/20fps, source-bound original soundtrack, prior full decode/readability/blank/frozen/sync checks pass. Display gamma correction is declared and raw dimness failures remain separate.
- All native source shows/FSEQ/audio clocks preserved. No canonical/vocal ground-truth or full playback claim.

NEXT THREE ACTIONS:
1. Collect exact dd73e367 fullCI, Windows and both Android API results (including full-song preview/export). IfAPI30fails, inspect actual process/buffers; do not increase RAM, shorten the song, skip the test or weaken gates.
2. Resolve CAN-01 with a genuinely identifying approved model/reference; preserve original assets until identity is established.
3. Resolve independent vocal/lexical/percussion qualifications, render missing01/02/03/08, verify every actual MP4, then create exactly9MP4-only finalZIP and deliver immediately.

EXACT RESUME COMMANDS:
```bash
git fetch origin codex/eight-hour-recovery-20261019
git checkout codex/eight-hour-recovery-20261019
cat MASTER_TODO.md
cat docs/BETA_COMPLETION_LIVE_HANDOFF.md
cat evidence/beta_completion/latest_status.json
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_bounded_audio.py tests/test_audio_analysis_reuse.py tests/test_bounded_fallback_stems.py tests/test_audio.py tests/test_drummer_v3_real_audio.py tests/test_drummer_v3_analysis.py tests/test_android_offline.py tests/test_android_recovery.py tests/test_helixualizer.py tests/test_chronoflow.py
# Restore the saved internal checkpoint into a fresh WORK directory only if needed.
# Existing measurements already pass; do not rerun unchanged analysis without a reason.
python -m tools.profile_android_full_song_memory WORK tuned
```
For Actions reads use the authenticated GitHub connector with exact run IDs above. Shell git reads work; shell push lacks a credential. Publication succeeded via create_tree/create_commit/expected-head update_ref, with tree identity checked; no force push. Metadata-only evidence successors use [skip ci] and retain the tested implementation SHA explicitly.

OWNER APPROVAL STATUS: NOT APPROVED.
BETA RELEASE STATUS: HELD; PR188draft/unmerged; public beta unpublished; nine-video collection incomplete (5verified,4missing).
