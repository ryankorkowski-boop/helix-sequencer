# Optimized native layout review — 29 October 2026

Five fresh layout review movies are delivered. The requested nine-video beta approval collection is incomplete; canonical and vocal gates remain open.

Implementation: `76c0176d3c2c3776d5f9e9abd5e98c004f379021`. Sequencing changes: `c39028db34a6e76b58908bf1c6f0e20a59634f27`. The renderer is pinned xLights 2026.18, upstream 839c0f5, patch 93bedae. Exact hashes are in `evidence/optimized_beta_20261029/pinned_renderer.json`. Metadata-only successors do not change these media bytes.

## Videos

[MP4-only ZIP: five movies, 275,032,669 bytes](https://chatgpt.com/library?file_id=libfile_3082a9295984819189352b8b63ddb5ec&account_id=personal)

|Video|Content|Duration|
|---|---|---|
|[04_Residential_AC_RGB_Comparison.mp4](https://chatgpt.com/library?file_id=libfile_3a1bf5ca007c81919fe63a0fd9500284&account_id=personal)|Traditional 256 AC and a separate AC + RGB copy; alternating views|120 s|
|[05_Six_Layout_Synchronized_Comparison.mp4](https://chatgpt.com/library?file_id=libfile_ee16c166488c8191bcc4e2235c384e67&account_id=personal)|Six layouts sharing the same original audio and time|120 s|
|[06_Advanced_Technical_Showcase.mp4](https://chatgpt.com/library?file_id=libfile_78f3c8c5c63c8191a04cef9080eb3fda&account_id=personal)|Helix, moire and forced perspective|60 s|
|[07_Double_Helix_and_Musical_Direction.mp4](https://chatgpt.com/library?file_id=libfile_a47c3b032e688191bec7eb35f8d6c585&account_id=personal)|Literal 88-key pitch rungs and section-driven structures|120 s|
|[09_Starred_Music_Sampler.mp4](https://chatgpt.com/library?file_id=libfile_c8a2dea840a881918e403b0e242d4e8d&account_id=personal)|Four Starred songs, with 30 seconds from each|120 s|

All five files fully decode as H264/AAC at 1920×1080 and 20 fps. They pass the unchanged presentation brightness, motion and framing thresholds, with no blank interval of one second or frozen interval of two seconds. Four interior/tail soundtrack windows each measure zero lag; correlation with the original audio is at least 0.998. Representative final encoded frames were inspected. Full playback was not watched.

Raw native dimness failures remain separate from the declared RGB display correction. The curves preserve black, and create no musical events. This is technical media verification, not owner artistic approval or acoustic ground truth.

## Changes and measured results

- Matrix Bars effects no longer fill short source rests or sustain across section changes. Summed unsupported coverage across props falls from 24,827 ms to zero on the retained source plan.
- Hash-verified vocal clocks are decompressed once per collection invocation. Original notes, pitches, clocks, assets, 256 AC addresses, fixed colors and exporters remain intact.
- Presentation and segment caches require matching source, code, encoder and decoded-output hashes. The same five movies take 430.66 seconds cold and 2.53 seconds for verified reuse, with five cache hits. This measures presentation only.
- Sequential montage cuts and bounded decoder threads recover the observed 8 GiB memory failure. The completed encoder child peak is 559,084 KiB RSS; no new OOM kill occurred.
- Native mux cleanup errors no longer mask verified publication or the original media error. The moire movie was recovered through independent checks; perspective was rerendered alone.

## Tests and open gates

Final focused JUnit: 48 passed and one existing opt-in integration skip. Exact-source full CI [40836343857](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40836343857) passes Python 3.11 and 3.12: each has 2,199 tests and 24 subtests passed, with six existing skips. Windows [40836353435](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40836353435) passes. Android run 40836353439 completed: API 36 passes, while API 30 fails when Android kills the foreground Helix process for low memory during offline audio/export. The API 30 Instructions and persisted Band recreation tests passed before the crash. Exact log evidence and instrumentation XML are retained in `android_final_status.json` and `android_api30_failed_instrumentation.xml`. This is a memory-stability blocker, not the historical APK overwrite issue. Physical Samsung and controller acceptance remain open. Historical APK overwrite migration is not reopened.

Videos 01, 02, 03 and 08 are blocked. The exact approved fully modeled 3D drummer asset/reference remains unresolved; retained V3 is planar artwork. UVR/MDX/KARA candidates do not establish independent singer identity or lexical phoneme boundaries. No replacement is approved.

Strict producer 40836353360 rejects unqualified E14 vocal lanes; final-band 40836353456 fails its dependency. Collection 40836353448 lacks supported pilot evidence, and Phoneme 40836353485 retains motion 0.425 below the unchanged 0.65 threshold. Failed gates are not reduced or counted as passes.

No owner approval, PR #188 merge or public release occurred. `HELIX_OPTIMIZED_BETA_APPROVAL_MP4S.zip` has not been created. The separately named five-movie layout ZIP is complete and verified.

## Continuation

Read `MASTER_TODO.md` and `evidence/optimized_beta_20261029/delivery_status.json` first. Do not repeat separation or analysis. Internal native checkpoints are `libfile_047ff812c6888191baa9a2d6cbc95dfa` and `libfile_e3a0d03004888191a477e14bf2188285`; both saves and identity application succeeded. Restore their relative paths into WORK. Use `optimized-native-restore.json` to restore repeated media from `optimized-production/media`. The original sampler/stems checkpoint remains `libfile_a4f25fecbed881919a61725b9f227f74`.

Native FSEQ, configurations, assets, source plans, clocks and validated movies are retained. Adjust only WORK locators in `review_config.json`, retaining its hashes. `python -m tools.assemble_beta_review WORK/review_config.json WORK/optimized-review-movies` reproduces presentation without native rerendering. Runtime artifacts 12562415032 and 12706746779 retain pinned resources and the compiled renderer.

Resolve the approved model reference and independent acoustic/lexical evidence before producing the four missing band videos. Preserve six default performers, seven opt-in and literal keyboard mapping. Refresh Android results; keep post-beta work deferred. Merge and release require explicit owner authorization.
