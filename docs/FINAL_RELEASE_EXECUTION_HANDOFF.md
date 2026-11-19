# Final release execution handoff — 2026-10-23

Release status: **IN PROGRESS**. No merge of PR #188 or public beta publication
is authorized until release gates pass and the owner approves a fresh canonical
band movie. Post-beta roadmap work remains deferred. See MASTER_TODO.md first.

## Current source

Branch: `codex/eight-hour-recovery-20261019`. Verified starting HEAD:
`8c61452713bd06273e94e8607a828c8341ada9f3`. PR:
https://github.com/ryankorkowski-boop/helix-sequencer/pull/188 (open, draft).
The commit containing this file is an implementation checkpoint, not evidence
that its renderer/platform builds have completed.

| Task | Status | Evidence / cause / exact next action |
|---|---|---|
| True branch/PR state | COMPLETE | Remote fetched; PR #188 open/unmerged at starting SHA. No older ZIP used. |
| Original owner audio | COMPLETE | `fixtures/audio/Phoneme_Test_Hook.mp3`, 802902 bytes; SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. Recovered original Library upload and verified exact bytes; full decoded duration 34.8799791667s. |
| Reliable ingestion | IN PROGRESS | `tools/phoneme_source.py`: retained fixture default, optional HTTPS/auth override, exact hash, bounded download, redacted diagnostics, source receipt before DSP install. Workflow no longer requires audio/show URLs or prepared show ZIP. Run committed workflow and inspect completed result. |
| Analysis bottleneck | IN PROGRESS | Existing one-variant/no-orchestrator defaults preserved. Reuse magnitude/power STFT for default onset mel and centroid; vectorized argmax pitch. Exact numerical/onset/beat equivalence across 22050/44100/48000 Hz passes. `tools/benchmark_audio_analysis.py` compares trusted baseline SHA to candidate on full recording. |
| Production singing-face binding | IN PROGRESS | Found generated `lead_singer_full` / `helixville4_harmony_singer_full` style hints were being treated as imported faceInfo names. Generated hints bind only one unambiguous real definition on the same target. Explicit face selections remain strict (b418efe retained). Native lead now appears in lead cycle. Test explicit/ambiguous/other-target refusal and generated binding. |
| Full-song XSQ | IN PROGRESS | First real current-source production run completed in 73.49s with 1861 effects and 34.88s header. Six existing Review3DScene-derived models, no xylophone. First run omitted opt-in lyric sync; corrected builder rerun is required. Generated show uses current source, no external ZIP. |
| Genuine native render | IN PROGRESS | Pinned xLights 2026.18 AppImage hash verified `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`. Actual native headless FSEQ: 74643 channels, 697 frames, 6854540 nonzero samples. Native GUI exported 248x442; strict HD gate correctly rejected it. Local openbox lacked theme search path; retry with extracted theme data in XDG_DATA_DIRS, then inspect real-canvas resize and full decode. No accepted full-resolution MP4 yet. |
| Canonical appearance | BLOCKED | Existing native geometry recovered; no new placeholder design authored. It remains an unapproved candidate. Need owner comparison with approved references and actual rendered frames; code labels do not prove approval. |
| Independent backing vocals | BLOCKED | Source is mixed stereo; classifier estimates are not independent vocal ground truth. `vocal_lane_diagnostic.json` keeps this false. Obtain isolated lead/backing source or defensible separated/validated vocal lanes; never manufacture events. Existing E14 native producer independently fails because its retained backing lane is empty. |
| Instrument musical acceptance | NOT STARTED | Current production show is diagnostic; native FSEQ activity and effect counts do not prove instrument identity, shoulder/contact continuity, independence or string/key accuracy. Preserve original algorithms; review source-timed per-role evidence. |
| Windows latest starting SHA | IN PROGRESS | Run39924409615 reported success at starting SHA; inspect binary/start/clean-host evidence before distribution. New changes require a new build. |
| Android API30/API36 | IN PROGRESS | Run39924409507 was in emulator instrumentation at inspection; Gradle build already succeeded, installation not yet verified. Read completed run, signing/install reports and device evidence. |
| Full Python3.11/3.12 CI | IN PROGRESS | Earlier starting-SHA push Beta CI39924402290 passed; PR jobs were still running. Do not claim all completed. New checkpoint needs fresh completed CI. |
| Licensing | COMPLETE | No license/legal policy changed in this checkpoint; retain noncommercial/homeowner and paid commercial vendor requirements. Existing compliance run39924409519 reported success at starting SHA. |
| Merge/publication | BLOCKED | All release gates plus owner MP4 approval required; no merge or publication performed. |

## Commands and evidence

```
python -m tools.phoneme_source phoneme-work/input
python -m tools.prepare_phoneme_show --audio phoneme-work/input/Phoneme_Test_Hook.mp3 --output phoneme-work/show
HELIX_NATIVE_PREVIEW_WIDTH=1280 HELIX_NATIVE_PREVIEW_HEIGHT=720 xvfb-run -a -s '-screen 0 2560x1440x24' python -m tools.native_preview phoneme-work/show --xsq phoneme-work/show/Phoneme_Test_Hook_Helix.xsq --audio phoneme-work/show/media/Phoneme_Test_Hook.mp3 --xlights /absolute/path/to/xLights
python -m tools.finalize_phoneme_review phoneme-work/show
python -m tools.benchmark_audio_analysis fixtures/audio/Phoneme_Test_Hook.mp3 --baseline-ref 8c61452713bd06273e94e8607a828c8341ada9f3 --report benchmark.json
```

38 focused source/DSP/face/compiler/snowman/discovery/routing tests passed in
5.09s on Python3.12 locally. Full regression is not inferred. The new workflow
uploads the complete show, source, sequence logs, native logs, diagnostic report,
checksums and actual MP4 even if later acceptance blocks release. It resolves
`native_preview.mp4` from the renderer receipt rather than guessing a root path.

Historical failures verified:
- https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39924402434 — old Phoneme workflow failed before install because automatic push supplied no manual URLs.
- https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39921342070 — source qualification rejected original E14 empty backing lane before compile. Do not rerender unchanged E14 expecting two singers.

Remaining work is explicit above; queued, unverified or diagnostic work is never
marked complete. Update this file and MASTER_TODO.md with every next safe change.

## Verified local follow-up before first checkpoint

- Corrected full-song production rerun: **44.30s**, **1893 effects**; actual
  parent singer rows contain **22 lead Faces effects and 11 harmony Faces
  effects**. The prior zero-face export is repaired. Whisper is unavailable
  locally; cues are broad source-energy/classifier estimates, not verified
  lyrics/phonemes or independently isolated backing vocals.
- DSP full-source benchmark: warmed median 0.542879s baseline versus
  0.449600s candidate (1.20747x throughput; 17.18% elapsed-time reduction).
  All measured features and onset/beat/pitch clocks match exactly; original
  source bytes unchanged. Scope is initial analyze(), not whole engine.
  Receipt: `evidence/phoneme_recovery_20261023/audio_analysis_benchmark.json`.
- Generated shows record source commit, dirty-worktree flag and relevant
  module hashes. An uncommitted local run must not be described as the clean
  committed source. Workflow checkout will render the committed revision.

## Native export root cause confirmed and next repair

The unmodified AppImage did render an actual MP4 but **failed acceptance**:
248x602, black image at8s, even after real X11 canvas resize to1280x720. Exact
pinned `xLightsMain.cpp` reads cached getWidth/getHeight immediately after
SetSize; its saved3D camera is initialized before mode selection. Both defects
are already repaired by `tools/patch_xlights_native_export.py`. Do not repeat
unpatched exports or substitute an upscaled/black movie.

The Phoneme workflow now restores/builds the **existing source-patched pinned
renderer**, reinstalls cached wxWidgets libraries, checks ldd, saves the build
before export and uses HELIX_PATCHED_XLIGHTS. Automatic production uses the PR
trigger so it can read the existing PR-scope native build cache. Native runtime
and compiler logs are included even if downstream acceptance fails.

Additional verification:98 native-preview/cast/artifact/patch/sequence-builder
checks passed,1 native-only integration skipped,10 subtests passed (4.23s).
Checkpoint3776d2a95bfce693239caccaa81d895daa35c382 is pushed. Its original
unpatched renderer workflow is superseded by this next targeted fix. Current
jobs and build/install results remain unverified until completed.

## Android evidence repair (local follow-up)

Starting-SHA Android run39924409507 **completed successfully on API30 and36**.
This includes instrumentation, offline sequencing/MP4 decode and same-key/same-
version reinstall. It does not verify the user's installed historical key.
The release variant is intentionally unsigned without the established owner
keystore; existing debug APKs may use a different historical CI certificate.
Do not promise an in-place update or erase user data to work around that.

Found two actual reporting defects: the inline report wrote a literal `\\n`
after JSON, and it equated certificate validity with installation. New
`tools/android_apk_compatibility.py` writes valid JSON, recognizes the real
`app-release-unsigned.apk` filename and requires an exact APK SHA256 plus fresh
install/launch device evidence before marking installability verified.
`run_android_device_smoke.py` now checks activity launch/live PID and binds its
install/reinstall receipt to the actual APK hash. Workflow invokes that module.
Original signing configuration/package ID and data-preserving update rules
are unchanged.23 Android reporting/offline/recovery tests passed locally;
Python3.10 grammar checked. New emulator execution remains IN PROGRESS.

Full local Python3.12 suite initially lacked torch during collection. Installed
CPU torch dependency, then restarted the unweakened full suite; result pending.
Patched native render run:
https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39927505584
at286307e091c0a9eab4485b9ff2b4785612c4b3ce. Source/preflight/production
steps passed and native build cache restore completed; installation/build was
still active at inspection. Do not claim successful native MP4 until completed
artifact verification.

## Source-separated vocal and mouth ownership repair

IN PROGRESS: direct XSQ inspection found native mouth submodel rows also received
Wave/On cues and whole singers received Strobe, which can light multiple mouths
at once despite valid Faces cues. Canonical show builder now opts into exclusive
phoneme ownership; generic placement rejects the whole face, mouth submodels and
containing groups. Actual imported face definitions and unflagged user layouts
remain unchanged. Native `rest` is emitted with xLights' correct lowercase alias.

Ran two real local separation models on the exact original: UVR-MDX-NET-Inst_HQ_3
then UVR_MDXNET_KARA_2 on the vocal estimate. Model and output hashes,100Hz clocks
and reproducible tool are retained under fixtures/audio/phoneme_vocal_separation.
Estimated lead/backing are not gain/delay copies; voiced estimates25.06s/21.55s.
These are source-separated estimates, not verified identities/lexical phonemes;
independent backing acceptance remains BLOCKED pending review/leakage validation.

`tools/phoneme_vocal_export.py` maps measured AH/EE/OH estimates through actual
native face definitions, inserts source-timed rest intervals, removes decorative
mouth overlays and uses authored BODY/BASE_DIM node colors for static nonmusical
illumination. Local export:339 non-rest lead cues+137 rests;334 non-rest backing
cues+160 rests; two distinct source fingerprints. No copied lane or manufactured
phoneme boundaries. Fresh complete prepare command rerun remains required after
mapping correction (EE->E etc).18 mouth/export/luma regressions pass.

Full local Python3.12 suite at the prior checkpoint passed2081 tests,6 existing
skips,16 subtests in349.37s. It is rerunning after the mouth ownership change.
Latest primary286307e Windows and Beta CI passed; full PR CI39927505413 passed;
Android still active at inspection. Separate retained-render sourceb1272664/run
39928972347 is active. Compact runtime transfer18b46b09 is an independent branch,
verifies the original archive/binary, strips only debug symbols and records both
hashes so the runtime can be transferred below the connector's512MiB limit.
No old movie is reused; no successful new native MP4 claimed yet.

## Verified latest local checks and renderer transfer

Full unweakened local Python3.12 suite after the mouth/source changes:
**2093 passed,6 existing skipped,24 subtests passed in344.15s**.18 focused
mouth/export/luma checks also pass. Fresh prepare-v4 completed successfully:
55.00s production engine,1572 production effects before measured vocal/material
export; both source-bound estimate lanes and authored static body illumination
are serialized in the full34.88s XSQ. No generic Wave/On mouth rows retained.

Compact renderer transfer run39930592387 **completed successfully**;
artifact12491875007 is34.2MB, ZIP SHA2562523f06db9a556d7a3d624aaea22fb614ded07452ef63acd22efd251f9920ccf.
Downloaded and verified every original/derived binary/library hash locally.
Initial local GUI launch crashed(-6) in ColorPanel while mixing AppImage GTK
libraries with the compiled runtime; headless FSEQ succeeded. Retry now uses
system GTK/GLib, exact retained wx runtime and only six missing compatibility
libraries plus pinned AppImage share resources. No success claimed before retry.

Primary Phoneme workflow now falls back from a missing branch cache to the
validated retained renderer archive; archive/patch/binary mismatch fails closed.
An unavailable/expired artifact can still use the pinned-source compiler path.
The reproduction recipe, metadata/clock hashes and estimate limitations remain
part of this checkpoint. Native readiness, owner appearance/voice review and
new platform build/install results remain open.

## Native movie produced; white-only serialization cause repaired

Local native xLights2026.18 now exports actual1280x720/20fps/full-recording video
with the original34.88s soundtrack. Source audio correlation0.9968248 at zero lag;
full decode and unchanged brightness/motion thresholds pass. This is actual
House Preview export from matching FSEQ/XSQ, not a substitute renderer.

Visual inspection found the initial movie's white silhouettes even though
material metadata had authored colors. Root cause: inline `settings` and literal
`palette` strings were written without native EffectDB/ColorPalettes indices;
xLights consequently used defaults, including for native mouth definitions.
New shared xlights.xml_io serializer materializes actual tables/IDs without
retiming/changing targets; active engine writes and final Phoneme export invoke
it. Numeric native template references resolve on import. Original numeric table
order and duplicate entries are preserved. Missing palette attributes remain
available to the existing neon post-pass; implicit native white default is
preserved.24 focused serialization/palette/mouth tests pass; later combined
63 cast/artifact/serialization cases pass. Full prior serializer checkpoint:
2097 passed,6 skips,24 subtests; final import/staging checks still required.

The corrected native movie now shows authored hats/scarves/body colors and mouth
settings. Quantitative readability: median luma19.286, bright fraction0.12572,
motion1.55, width0.662,height0.444. Source staging still clipped the keyboard:
recovered existing native_source_pose_band six-cast positions into a reusable
helper, with unchanged node geometry/channel addresses and old pose-export
staging preserved. New prepared show uses those established non-overlapping
positions. Fresh render after final source commit remains IN PROGRESS.

Do not deliver earlier white-only, black, clipped or unpatched diagnostic movies
as final approval. New tests check native color/setting references and imported
template retention. No musical/source/owner acceptance gate has been relaxed.


## Execution interruption checkpoint — 2026-10-23

Current verified implementation: `5f60522b2d1a52e4c4a7efa918d4b255d50f39b8`
on `codex/eight-hour-recovery-20261019`, PR188 remains open/draft.
This checkpoint changes documentation only; all source-matched results below
refer to that implementation commit, not a later documentation SHA.

The execution environment became unavailable before final artifact saving.
Connected GitHub remains accessible. Do not claim the interrupted local
visibility patch, its tests, a downloadable local movie, or beta approval
completed. Do not discard any surviving local work.

| Status | Work and evidence | Exact next action |
| --- | --- | --- |
| COMPLETE | Original MP3 recovered, SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`, 34.879979s, retained at fixtures/audio/Phoneme_Test_Hook.mp3. Automatic source ingestion no longer requires external URLs/show ZIP. | Preserve exact bytes and source verification. |
| COMPLETE | Shared STFT/vectorized pitch analysis, exact feature parity. Full-source warmed analyze() median .542879s -> .449600s (17.18% less elapsed time). | Keep benchmark receipt; this does not measure entire engine. |
| COMPLETE | Strict singer binding, native rest alias, exclusive mouth ownership, native EffectDB/ColorPalettes serialization and imported template reference handling committed. | Preserve b418efe explicit-definition guard. |
| COMPLETE | Full source-matched GitHub Helix CI39933547402 passed Python3.11 and3.12. Each full audit:2099 passed,6 existing skips,24 subtests. Python3.11 349.05s;3.12 217.63s. Beta CI39933547428 also succeeded. | No new source change is covered by these results. |
| COMPLETE | Windows39933547551 completed successful packaged GUI/engine/native FSEQ checks. Portable artifact12492078971,190494413 bytes, ZIP SHA256 `1522b45e037015e59f75cb195cc1202698c8c87fb62269673ae1c8ac31bfc340`. | Owner clean-device/saved-layout workflow review still required. |
| COMPLETE | Android39933538032 completed both API30 and36 emulator jobs, offline/native media checks, exact-APK fresh install/launch and same-key reinstall. Artifact IDs12493601569(API30),12492989347(API36). | Distribute verified signed debug APK, never unsigned release. Physical Samsung and old-installed-key update remain unverified. |
| COMPLETE | Compliance/license workflow39933547661 succeeded; no MIT relicensing was introduced. | Preserve homeowner/noncommercial and commercial vendor policy. |
| COMPLETE | Real local patched xLights2026.18 exported1280x720/20fps movie from full source, all audio/video decoded, original soundtrack34.88s zero-lag correlation .996824804. Final completed pre-idle render luma20.201/motion1.484 passed original thresholds; all six staged colored performers visible. | This is local execution evidence only. File could not be made available before environment loss; owner appearance/musical approval remains blocked. |
| IN PROGRESS | Primary Phoneme native workflow39933547485 remains in progress, last observed installing DSP/native dependencies, no artifact yet. | Inspect completed result/logs; verify actual MP4/XSQ/layout/source hashes, then supply artifact. Do not call it passed while active. |
| BLOCKED | Independent backing identity/lexical phonemes not verified. Real two-stage UVR estimates retained with source/model/clock hashes; lead25.06s and residual backing21.55s estimated voiced time. Export339 lead and334 backing non-rest estimated cues. Separation may leak lead/reverb/instruments. | Audition isolated estimates against source; obtain independently defensible backing evidence before changing acceptance status. |
| BLOCKED | Native producer39933547417 rejects retained E14 audio with no independently resolved backing lane. Final-band39933547374 native-proof job passed, accepted-native-band failed awaiting successful same-commit producer. | Qualify appropriate source-bound evidence, then rerun producer/consumer. Do not manufacture vocals, relabel old media or weaken strict gates. |
| IN PROGRESS | Last local patch adds dim nonmusical idle visibility only on keyboard/drum kit rest intervals; excludes drummer arm/contact/beater/pedal nodes. It is NOT committed or fully verified. | Restore execution, inspect git diff/tests and complete fresh prepare/render before committing. Preserve unchanged source events. |
| BLOCKED | Native movie owner approval, canonical visual identity/animation continuity, distinct instrument ownership and physical Windows/Samsung/controller checks remain open. | Deliver fresh matched movie for owner review after verification. |
| BLOCKED | APK unsigned release is not installable without established owner signing key. Cross-build old-beta certificate compatibility is not proven. | Use original key and test data-preserving update; do not uninstall user data to hide mismatch. |
| BLOCKED | Standalone APK extraction and final MP4/XSQ review-bundle saving interrupted with unavailable execution environment. | Recover environment or use completed GitHub artifacts. No public beta/tag/PR merge before owner approval and all release gates. |

### Source-specific URLs

- Full CI: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547402
- Beta CI: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547428
- Windows: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547551
- Windows download: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547551/artifacts/12492078971
- Android: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933538032
- Android API30 download: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933538032/artifacts/12493601569
- Android API36 download: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933538032/artifacts/12492989347
- Compliance: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547661
- Phoneme production (active, unverified): https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547485
- Strict older producer failure: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547417
- Strict final band failure: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39933547374

Android API36 debug APK SHA256 from successful install receipt:
`5791a07ff50df74a0e6b9ef0989e656014e18326d90151c790f0c90d54aedbae`.
Certificate SHA256:
`cbc9b3e79b206bb003cc807d0b21bfdac0e8bba564de653654de4393f2f2a8bb`.
Unsigned release SHA256:
`21ccadb83ccda1098c8b4d59f39fc9d23fb5beafb494fcf42c3b2a7e26f638d1`
is explicitly NOT verified installable.

### Recoverable local paths and exact reproduction

Workspace was `/workspace/scratch/0f96d341b9a8`, checkout `helix/`.
Exact original is also `audio/Phoneme Test Hook.mp3`.
Last completed movie was
`Phoneme_Test_Hook_Review/Phoneme_Test_Hook_Helix_Native.mp4`;
its actual native export was `native-preview-1goooeev/preview.mp4`.
Important: after this completed render, an idle-visibility experiment modified
the existing show's XSQ/layout in place. The old movie must NOT be presented as
matching that modified XSQ. Prepare a new clean show; retain old movie only as
diagnostic evidence.

Uncommitted work was in tools/native_source_pose_band.py,
tools/phoneme_vocal_export.py, tools/prepare_phoneme_show.py,
tests/test_phoneme_vocal_export.py and local checklist files. Idle changes
extract native_drummer_arm_cells(), create exact-node idle aliases after
production sequencing, subtract existing source-effect windows, and add30%
On only in rest complements, tagged nonmusical_instrument_visibility.
The provenance patch distinguishes tracked-tree cleanliness from untracked
incidental output. Inspect logs idle-visibility-tests.log and idle-final-tests.log.
Full committed-source test log was full-committed-source.log; its final local
result was not read before interruption. Completed GitHub audits above are
authoritative.

Fresh preparation, from repository:
`python -m tools.prepare_phoneme_show --audio ../audio/Phoneme\ Test\ Hook.mp3 --output ../Phoneme_Test_Hook_Final`

Validated retained executable:
`/workspace/scratch/0f96d341b9a8/compact-runtime/native-runtime/bin/xLights`.
Compact transfer run39930592387/artifact12491875007 records original and stripped
binary hashes; ZIP SHA2562523f06db9a556d7a3d624aaea22fb614ded07452ef63acd22efd251f9920ccf.
Use its wx libraries, extracted native-deps and only native-compat libraries
with system GTK/GLib. Full AppImage library mixing caused ColorPanel SIGABRT(-6);
unpatched AppImage exported black undersized video. Those paths are rejected.

Working local environment:
PATH native-deps/usr/bin followed by system PATH;
LD_LIBRARY_PATH compact-runtime/native-runtime/lib:
native-deps/usr/lib/x86_64-linux-gnu:native-compat;
XDG_DATA_DIRS native-deps/usr/share:/usr/local/share:/usr/share.
Paths are absolute under the workspace above.
Start owned Xvfb with2560x1440x24, TCP display, -ac -nolisten local; start openbox.
Use DISPLAY=127.0.0.1:<unused display>, HELIX_NATIVE_PREVIEW_WIDTH=1280,
HELIX_NATIVE_PREVIEW_HEIGHT=720, XL_NO_GPU_COMPUTE=1.
Run `python -m tools.native_preview <fresh-show> --xsq <fresh-show>/Phoneme_Test_Hook_Helix.xsq --audio <fresh-show>/media/Phoneme_Test_Hook.mp3 --xlights <validated-executable>`;
then `python -m tools.finalize_phoneme_review <fresh-show>`.
Inspect sample frames, full decode/source soundtrack/hash reports and all
instrument/singer behavior. Never substitute schematic or old footage.
Package only that matching final show and verified movie, diagnostics and checksums.

Release remains BLOCKED. No merge, release tag or public beta was performed.
