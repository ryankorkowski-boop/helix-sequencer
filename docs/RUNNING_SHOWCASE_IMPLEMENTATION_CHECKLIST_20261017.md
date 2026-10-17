# Helix showcase and musical performance — running implementation checklist
Updated: 2026-10-17. Working branch: `codex/showcase-pilot-recovery-20261017` (PR #172).

**Status legend:** [x] code committed; [ ] unfinished or unverified. A checked code change does not imply tests passed or MP4 approved.

## P0 — correctness and native review blockers
- [x] Stop routing hi-hat-only events into stick-contact candidates (`models/review_3d_scene.py`).
- [x] Add separate animated hi-hat foot/pedal and include its moving geometry in native RGB pose capture.
- [x] Remove static hi-hat foot/pedal outlines from native pose-bank export, avoiding duplicated idle geometry (commit `0aedc7c`).
- [x] Add hi-hat foot-only regression (`tests/test_hihat_foot_pose.py`).
- [ ] Run hi-hat regressions and render native foot/pedal close-up; verify no stick strike, independent kick, release and repeated notes.
- [x] Correct keyboard black keys to the far side from the snowman (`models/band_performance_scene.py`); add orientation regression.
- [ ] Verify keyboard hand/key reach and correct perspective in all native stage/3D exports and video.
- [ ] Diagnose why the xylophone/mallet performer repeatedly disappears from rendered band videos: note source -> role -> curves -> mallet pose -> XSQ -> FSEQ -> MP4/camera. Fix proven root cause.
- [ ] Implement unified keyboard/mallet performer as requested, preserving backwards-compatible layouts, instrument exports and 16-channel AC limits.
- [ ] Implement evidence-gated fallback routing of unrepresented pitched melodies (trumpet/horns/woodwinds/strings/synth) to the keyboard; avoid duplicating bass/guitar/vocals and inventing notes.
- [ ] Verify bass fundamentals, octave, string/fret assignments, fretting, plucks, sustains and audio alignment against real songs.
- [ ] Verify guitar pitch/string/fret/chord/solo detection and performance against real songs.
- [x] Add native pixel export checks for nonempty disjoint `NOTE_MIDI_*` and `STRING_*` node sets; add tests for pixel versus AC16 addressing.
- [ ] Execute these tests, fix failures, inspect exported actual channel counts and prove key/bar/string events light correct native FSEQ channels and MP4 frames.
- [ ] Prove keyboard and mallet note-on/note-off/velocity/decay and actual per-note addressability, including simultaneous notes.
- [ ] Verify all musician models independently export to xLights 3D and 2D with front-on parity and <=16 AC circuits per physical model.

## P1 — source selection, music and show quality
- [x] Analyze seven Drive originals and commit reproducible excerpt shortlist (`docs/DRIVE_ACTIVITY_SHORTLIST_20261017.json`).
- [x] Replace three disappointing audio excerpts with Fractal Crown, Frosted Axes and Glitterquake Parade listening candidates.
- [ ] Obtain owner listening approval; reject slow Snowbound selection, poor-sounding Candy Cane Chaos selection and weak Wub Wub Wonderland selection.
- [ ] Select musically compelling, clean, source-verified 30–42s passages; not energy-only ranking.
- [ ] Check vocal/lead/harmony/background singer separation and phoneme mouth accuracy, avoid unsupported claims.
- [ ] Improve believable arm contact, independent instrument movement, cymbal shimmer/decay and balanced performer visibility.
- [ ] Verify double-helix MIDI rungs, spiral trees, 3D forced-perspective and moire features in six native layout variants.

## P2 — actual deliverables and integration
- [x] Prior recovery produced verified real-song native band/close-up/embedded/comparison MP4s (see `MASTER_TODO.md`), but these predate recent corrections.
- [ ] Run full unit/integration regression suite on latest branch, document pass/fail counts.
- [ ] Rebuild native source shows with all P0 fixes and inspect native FSEQ sample parity, 1080p decoded video, brightness, camera and original-audio synchronization.
- [ ] Deliver accessible final review MP4s: whole seven-member band, musician closeups, embedded stage, six-layout comparisons and ads, with SHA256/provenance manifests.
- [ ] Obtain explicit owner video/music approval before any release integration.
- [ ] After approval only: integrate approved work into desktop Windows EXE and Android APK; verify builds and real hardware/controller compatibility.
- [ ] After approval only: plan/implement free multiple-layout song variants and xLights XSQ plus Light-O-Rama LMS export on each Helix run; verify import compatibility and clear feature limitations.

## Current execution constraints and next actions
1. Finish hi-hat native-pose correctness and execute focused tests.
2. Trace xylophone omission and keyboard note source, then implement fallback/unified performance without breaking existing exports.
3. Verify pitch/string/key lighting at actual native channel/frame level, not just model definitions.
4. Render fresh native review clips; retain explicit release hold.

**Honesty gate:** This checklist is an implementation tracker, not proof of tests or video acceptance. The native xLights 2026.18 scratch renderer referenced in `MASTER_TODO.md` may not be available in this session; do not claim fresh native renders without actual verified files.


## P3 — benchmark and surpass commercial/community sequence quality (added 2026-10-17)
- [ ] Assemble a legally accessible reference set of at least 5 representative professional vendor previews and 5 freely shared community sequences, covering varied display sizes, singing faces, musical sections and model groups. Log URLs, licenses and evidence limits; do not redistribute paid sequences.
- [x] Implement validated weighted human-rating calculator and tests (`tools/sequence_quality_benchmark.py`, `tests/test_sequence_quality_benchmark.py`); rubric: synchronization 30%, choreography 25%, performance 20%, compatibility 15%, import 10%.
- [ ] Collect actual blind reviewer scores, execute the benchmark tests and compare against representative reference sequences; do not claim parity without evidence.
- [ ] Compare source-aligned kick/snare/cymbal, bass, lead melody, harmonies, lyric phonemes, transitions, build/release and finale to reference examples.
- [ ] Implement phrase-aware orchestration, coherent palettes, tasteful contrast and prop-group choreography; benchmark against static/repetitive and overbusy failure modes.
- [ ] Create small/traditional/mega-tree/band/advanced-3D/AC16 sequence variants per approved song, with explicit capability limits and preserved canonical source cues.
- [ ] Validate automatic model/group/submodel/face/lyric remapping to actual third-party layouts, including import failures and user correction paths.
- [ ] Verify full-song editable XSQ, valid LMS where supported, FSEQ, model xmodels, audio provenance, licensing, thumbnails, instructions and previews in each release package.
- [ ] Run native xLights open/import/render and Light-O-Rama compatibility tests, followed by owner review and a small independent community usability trial.
- [ ] Publish reproducible before/after reports and benchmark evidence; no blanket 'better than paid vendors' claim until validated across representative references.

External comparison discovery: xLights Hub sequence index, official xLights Resources and xLights Import Effects documentation (2026-10-17). These provide comparison and workflow targets, not proof of quality.


## 2026-10-17 — continuation after video-link request
- [x] Source MP3s and revised excerpt ZIP confirmed present in current working container.
- [x] Added bass/guitar routed-string illumination regressions and pitch/octave separation regression (`tests/test_source_instrument_light_curves.py`).
- [x] Clamp routed-string light intensity to native pixel range; never light an unrouted string merely because overall instrument energy exists (`tools/build_spatial_review.py`).
- [ ] Execute these regressions and native channel checks in a complete repository environment; do not claim pass before execution.
- [ ] Recover or provision native xLights rendering workspace, rebuild from latest commit, inspect new XSQ/FSEQ/MP4 and provide actual current-review links.
- [ ] Current published 2026-10-10 review MP4s remain **historical references**, not approval candidates for recent fixes.
