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
