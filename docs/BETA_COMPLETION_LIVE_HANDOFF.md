# 31 October — active core optimization branch

Owner's current build request is being implemented on `codex/core-facade-optimization-20261031`, starting at recovery321cf85. Keep MASTER_TODO.md authoritative; historical release/media gates below remain open. Commits:14c9a2c(instrumentation),fc51c9e(typed facade),c7452c2(audio/percussion extraction). Full237.44s real-audio/master/256-channel layout baseline:218.3794s cold /168.5173s warmed; peakRSS1,386,229,760 /1,244,893,184bytes; both42,305effects with identical musical signature57c402d5b7857077f57fcd0d435a92a8a3f28e32c88e3c2e756bade5decff50c. Exact stage receipts are under docs/core_optimization_20261031.

Current work: validate cache-off final-source parity, then opt-in cross-process features (HELIX_AUDIO_CACHE_DIR), full regressions and canonical68-event/eight-target drummer oracle.94focused extraction tests and21cache/facade/metrics tests pass; all2250tests now collect after making offline Torch imports lazy. Final-source timing/suite/remote publication remain pending. No source algorithms, master intelligence flags, AC mapping, band assets or acceptance thresholds changed. Existing matrix intelligence remains at its established default to preserve exact master behavior; no unmeasured Numba kernel or broad placement rewrite.

Resume commands (fresh output directories required):
```bash
python -m tools.measure_engine_stages --audio "Helix Audiolights.mp3" --output tests/outputs/core_optimization/resumed-no-cache --runs 1
HELIX_AUDIO_CACHE_DIR=RenderCache/audio_features python -m tools.measure_engine_stages --audio "Helix Audiolights.mp3" --output tests/outputs/core_optimization/resumed-cache --runs 2
PYTHONPATH=. python -m pytest tests -q --junitxml=tests/outputs/core_optimization/full-tests.xml
```

# Helix live completion handoff — 30 October 2026

Current objective: owner reviews the delivered nine-video ZIP; finish remaining qualification without merging or publishing.

Review ZIP: https://chatgpt.com/library?file_id=libfile_513a651bf1bc819192ffe6cae9105de0&account_id=personal
Filename:HELIX_FINAL_BETA_APPROVAL_MP4S.zip;427,604,937bytes;SHA2568c6c8453f2d0736d87b7b583da5153ca17f8237657d7042db90118fca6687159;exactly9MP4s,CRC/entry hashes verified. Library identity applied locally. This is the requested review collection, not an assertion that the beta is accepted.

StartingHEAD54f2b118; first review implementation92d3c05. Final tested implementationc009595976a2b660bc4094b7302b9b284588c3c4; subsequent receipt commits may be metadata-only. Exact current module hashes are in current_owner_review_20261030.json. Code modifications: tools/render_owner_band_review.py (six default source-family performers, passedV3reference, fixed camera,88keys,bounded hands,separate source clocks,snare-only hand alternation,retained tom classes); tools/assemble_beta_review.py (bounded nine-panel cache and1080pvocal crops); models/approval_layouts.py andtools/build_source_ac_review.py (native preview bulbs only); core/audio_intelligence.py (constant bounded chroma window aligned to preserve float32 reference); focused tests. Original audio/events/ACwiring/colors/modelpositions/defaultsix/seventhoptional/exporters retained.

Media is complete and technically verified. Band is solid OpenGL/source-art; lighting is native xLights2026.18upstream839c0f5,patch93bedae,binary6d2dffb937b46c2dedd8a4a637c902b67d38584a90f62a9c1b2b371d13ee9db0. All9files1080p/20fpsH264/AAC; min audio correlation.9992593517,four0mslag windows per movie,readability/motion/framing/blank/frozen checks pass. All9native panels pass; source native2400-frame byte signatures are unchanged after bulb repair. Beginning/middle/end inspected, continuous playback not watched.

Tests:97review/source cases pass63.80s. Original12bounded cases including three new long-tail cases pass19.12s on pinned librosa0.10.2/NumPy2.2.6/Numba0.61.2. Coherent final pinned-runtime run:158tests pass137.31s,4existing warnings; receipt owner_review_pinned_regression_20261030.xml. Previous92d3CI41161111521:Python3.11passes,3.12fails retained chroma entropy parity(max1.995e-7);Windows41161111463andAndroid41161111415pass. Fix keeps1e-7assertions unchanged and introduces no events/tuning changes. Do not count prior results as final-source acceptance.

Open: independent acoustic/lexical singing proof; fully modeled/native continuous equivalence (retainedV3is planar); current final-source CI and physical device/controller acceptance; owner artistic approval. Lead/harmony clocks are distinct but their identity/lexical phonemes are estimates. No fake acceptance,merge or public release.

Durable inputs: native checkpoints libfile_047ff812c6888191baa9a2d6cbc95dfa andlibfile_e3a0d03004888191a477e14bf2188285; source/stems libfile_a4f25fecbed881919a61725b9f227f74; original passedV3video libfile_77110f489b048191b613ea0505cf01d3. These are engineering inputs; owner only needs the new single ZIP. Restore them with Library helpers if scratch disappears. Local root:/workspace/scratch/f17380732d07;repository:helix-sequencer;WORK contains raw shows/audio/receipts;approval-mp4s contains videos;finalZIP is at root.

Reproduce band (after restoring inputs):
```bash
python -m tools.render_owner_band_review WORK/optimized-production WORK/work/new-sampler-vocals REFERENCE.mp4 OUTPUT.mp4 --expected-sha256 50857fef6ac17197821bb6a9ce27f7ebd1c23b7eb8c82521345296bd22087677
python -m tools.build_approval_collection WORK/optimized-production WORK/new-layouts --audio-name Helix_Starred_New_Review.wav --expected-sha256 50857fef6ac17197821bb6a9ce27f7ebd1c23b7eb8c82521345296bd22087677 --vocal-fixture WORK/work/new-sampler-vocals --layouts 4 5 12 --full-keyboard
# Native preview requires the pinned renderer/resources and one owned Xvfb/display session per show.
python -m tools.assemble_beta_review evidence/beta_completion/owner_nine_review_config_20261030.json OUTPUT
```
The final assembly config contains old scratch locators. Update locators only when restored bytes match its hashes. A rerender with different bytes requires a fresh source receipt. Fresh display sessions fixed the interrupted traditional render; preserve the failed diagnostic. Restore native runtime12562415032/compiled12706746779,verify hashes and dependencies. Do not repeat unchanged separation or relabel source estimates as ground truth.

Next: collect final-source CI; qualify genuine independent acoustic/lexical sources; obtain owner review/physical acceptance, then request explicit approval before merge/publication. MASTER_TODO.md remains authoritative.

Final implementation current Actions:fullCI41163710718;Android41163710668;Windows41163710660;native41163710727. These werequeued/inprogress at receipt time,not accepted. Collect actual completions; source c009595976a2b660bc4094b7302b9b284588c3c4.
