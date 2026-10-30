HELIX SEQUENCER — LIVE RECOVERY HANDOFF

Last updated: 2026-10-30T01:28:35.129715+00:00 (29 October client date)
Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Current branch: codex/eight-hour-recovery-20261019
Current HEAD: 45f17d69fac91d7683984cc22c54bb701eb2226e (recovered source; checkpoint commit follows)
Last verified implementation SHA: 76c0176d3c2c3776d5f9e9abd5e98c004f379021
Last successful CI runs: 40836343857 (Python3.11/3.12),40836353435 (Windows); Android40836353439 API36 passes/API30 fails

CURRENT OBJECTIVE: finish existing beta and exactly nine verified MP4s; no merge/publication.
CURRENT TASK: MEM-01 profile full-song harmony classifier after reproduced post-drum low-memory kill.
Before expensive operation: source ../full-song.wav (237.44s48kHz stereo decoded original repository Helix Audiolights.mp3); command ../venv/bin/python ../profile_memory.py; outputs ../memory-profile/{stems,before.json,after.json}; resume by reusing stems, never repeating unchanged separation.
LAST COMPLETED TASK: REC-01 restore exact source, native checkpoints and five-media ZIP.

COMPLETED AND VERIFIED:
- [x] REC-01 remote HEAD verified via git and PR; draft/unmerged.
- [x] Five source76c0176 layout MP4s recovered, ZIP SHA2568f12c88b1cdb3703ddb5d75993bbb32a1de9a8345d9a410850a66ac42416b6e8 matches.
- [x] Native checkpoints restored under WORK; exact identities/hashes in artifact_manifest.json.
- [x] No unchanged separation/analysis/render repeated.

IN PROGRESS:
- [ ] MEM-01 reproduce/profile 237.44s source analysis/export and identify memory peak.

BLOCKED:
- CAN-01 approved fully modeled3D drummer identity not established. V3 is planar, Review3DScene unapproved.
- VOC-01 independent singer acoustic ownership and lexical phonemes unqualified.
- VID-01 missing01_Canonical_Snowman_Band.mp4,02_Lead_and_Harmony_Vocals.mp4,03_Drummer_and_Instruments.mp4,08_Full_Helix_Showcase.mp4.
- AndroidAPI30 foreground process killed at752236KiB; physical Samsung/controller acceptance open.

FAILED ATTEMPTS:
- Prior full-song fallback HPSS chunking reduced Linux memory but latestAPI30 still fails. Do not merely rerun unchanged failing test, increase emulator RAM, skip test, reduce song or weaken gate.
- Do not repeat broad asset/separation search already documented, fabricate pilot acceptance or relabel planar source art as3D.

ARTIFACTS ALREADY AVAILABLE:
- See evidence/beta_completion/artifact_manifest.json for exact paths, SHA256 and durable links.
- Five-movie ZIP: https://chatgpt.com/library?file_id=libfile_3082a9295984819189352b8b63ddb5ec&account_id=personal
- Original native checkpoints: libfile_047ff812c6888191baa9a2d6cbc95dfa and libfile_e3a0d03004888191a477e14bf2188285.

FILES MODIFIED:
- MASTER_TODO.md: prepended active uniquely identified task ledger; historical evidence retained.
- docs/BETA_COMPLETION_LIVE_HANDOFF.md: this recovery file.
- evidence/beta_completion/latest_status.json: machine-readable task state.
- evidence/beta_completion/artifact_manifest.json: exact nine-file inventory and recovered hashes.

TEST RESULTS:
- No new implementation tests yet; prior source76c0176 CI2199tests+24subtests passed/6skips each Python3.11/3.12.
- Windows40836353435 passes; Android40836353439 API36 passes/API30 fails.

RENDER RESULTS:
- No new native render; five verified existing media preserved byte-for-byte.
- Full continuous playback not watched; prior automated checks/still inspection only.

NEXT THREE ACTIONS:
1. Profile Android equivalent full237.44s source using serial numerical bridge and capture stage/peak allocations.
2. Implement smallest effective memory correction; test output parity and same-workload before/after.
3. Commit/push source plus live files; collect exact-source Android/API30/API36 and CI results.

EXACT RESUME COMMANDS:
```bash
git fetch origin codex/eight-hour-recovery-20261019
git checkout codex/eight-hour-recovery-20261019
cat docs/BETA_COMPLETION_LIVE_HANDOFF.md
cat evidence/beta_completion/latest_status.json
python -m pytest tests/test_android_offline.py tests/test_android_recovery.py -q
```

OWNER APPROVAL STATUS: not approved.
BETA RELEASE STATUS: held; PR188 draft/unmerged; public beta unpublished.

CURRENT MEMORY IMPLEMENTATION CANDIDATE:
- Profiled237.44s48kHz source. Harmony classifier1.60GB->414MB (74.11% reduction), same12windows/every field;31.429->30.053s. Linux Android bridge only, not device acceptance.
- Focused tests running: ../venv/bin/python -m pytest -q tests/test_bounded_audio.py tests/test_bounded_fallback_stems.py tests/test_audio.py tests/test_drummer_v3_real_audio.py tests/test_android_offline.py tests/test_android_recovery.py --junitxml=evidence/beta_completion/focused_memory.xml; output ../focused-memory.log.
- Next full production comparison: ../venv/bin/python ../profile_offline_pipeline.py baseline then candidate; same original full-song.wav and generated hash-bound stems reused. Expected outputs ../offline-memory/{baseline,candidate}; inspect metrics.json and musical_signature without asserting Android acceptance.

FOCUSED MEMORY RESULT:40passed,3deprecation warnings,62.34s. evidence/beta_completion/focused_memory.xml. The initial failed synthetic fixture was corrected; whole focused set rerun. Full production baseline still running at stem summary. Production profiler is now tracked as tools/profile_android_full_song_memory.py; use python -m tools.profile_android_full_song_memory WORK baseline|candidate with WORK/full-song.wav and WORK/memory-profile/stems retained. New Android/CI run URLs follow source publication.

PUBLISHED SOURCE:18a97623524ac8c5b37689c95553716163bd04b0 (remote tree matches tested local commitc89a58d). Initial live metadata remote bae67b655fd1bc625ae67c267d80ac029c5cf9e4. Shell Git push lacks credential; authenticated GitHub API atomic tree/commit/expected-head update succeeded; no force, merge or release.
ACTIVE EXACT-SOURCE RUNS:Android40986962515(push)/40986968908(PR); fullCI40986962386(push)/40986968934(PR); Windows40986968903; strict producer40986968812; finalband40986968930; Phoneme40986968843; collection40986968962. Queued/running is NOT passed. Full production baseline complete142.832s/1850908672bytes peakRSS/43913effects. Candidate is running serially with identical source/stems/config; outputs ../offline-memory/candidate. Do not repeat separation.

NEXT MEASURED MEMORY TARGETS (local work may proceed while18a9762CI runs):baseline full production stage peaks include initial analysis1.80GB and multiband1.53GB, so classifier savings alone are not a whole-pipeline guarantee. Bound per-frame pitch/descriptor and flux workspace without changing full-source frames/thresholds. Do not push again while current native/device work is unpreserved. Compare full237.44sXSQ signature to retained baselinefed5565412b36f5f48967eaf4e68572cd4b846b399d8f523161b094d31e2864c and43913effects.

FULL PRODUCTION RESULT:baseline142.832s/1850908672bytes vs18a9762candidate145.274s/1805361152bytes; same43913effects/exact musical signature. This excludes fresh separation and MP4 on BOTH paths. Main initial-pitch/multiband peak persists. Local MEM-02 now bounds these frame-local allocations; focused_memory_final.xml/log is running. Next command: ../venv/bin/python ../profile_offline_pipeline.py bounded (or tracked python -m tools.profile_android_full_song_memory WORK bounded). Output ../offline-memory/bounded. Source18a9762deviceCI remains active; no speculative pass.

FAILED LOCAL ATTEMPT:per-block spectral_contrast changed63rest-band samples up to0.233dB because power_to_db uses a global floor. Boundary parity test failed and rejected it. Corrected pinned band reductions apply global dB only after all peak/valley curves; descriptor/flux/pitch tests2passed exactly. Full51-test suite rerunning. ../offline-memory/bounded started with the rejected contrast reducer; preserve as diagnostic, do NOT count it. Once complete run ../profile_offline_pipeline.py bounded2 against stable corrected source, and compare to baseline. No source separation repeated.

ADDITIONAL MEASURED PEAK:Helixualizer3float64melbanks alone1346871296->305745920bytes (77.30% less),1.894->1.866s; every bank summary and dominance sample exactly equal. Evidence mel_memory_profile.json. New core/bounded_audio.py mel helper retains small mel grid; core/helixualizer.py keeps original short-file API. Shared long harmonic piptrack keeps required dense matrices but bounds temporaries. Source frozen now for final same-workload comparison; run ../profile_offline_pipeline.py final, output ../offline-memory/final. Final focused set includes bounded/audio/reuse/fallback/drums/android and helixualizer. Do not edit code during this profile.

FINAL FOCUSED RESULT:54passed,3deprecation warnings,62.48s; no failures. Every final memory module has focused parity coverage. Earlier18a9762fullCI40986962386now succeedsPython3.11/3.12 and Windows40986968903succeeds; these do NOT certify newer local MEM-02 changes. Android40986962515still active. Native18a producer40986968812fails original mixed vocal qualification; finalband40986968930fails producer dependency; collection40986968962fails missing pilot evidence; Phoneme40986968843fails motion0.425<0.65. Failure excerpts persisted; gates unchanged.

COMBINED SOURCE PUBLICATION CHECKPOINT:MEM-02 source frozen;54focused tests pass. tools/profile_android_full_song_memory.py now profiles initial analyze and Helixualizer/mel separately, retains all six source-module hashes and refuses overwriting an existing output directory. Pending profile output ../offline-memory/final. Previous18a9762CI passing counts2203+24subtests/6skips each3.11/3.12, Windowspass; these certify only18a code. Source publication below is required to start current platform/fullCI, while existing native failures are already preserved.
