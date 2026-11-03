# Helix Unified Intelligence — integration audit and optimization handoff
Date: 2026-11-03
Audited source: 28072eda15c09b6d5c93dac92a9942cc33d8be8e
Optimization PR: #205 (codex/core-facade-optimization-20261031)
Status: assessment and CI retry only; no source edits or merge made in this pass.

## Executive assessment
The repository has useful specialized engines and a measured core-facade/audio-cache extraction, but they are not yet a single authoritative musical pipeline. The safe direction is an incremental, contract-driven integration; do not rewrite the effect engine or change musical defaults until parity and ground-truth tests are green.

## Verified strengths
- `core.engine_runner`: typed lazy facade routes existing CLI/GUI path and multi-layout sampler entry.
- `core.audio_features`: extracted shared feature seam; optional content/version/code/library-bound NPZ cache behind HELIX_AUDIO_CACHE_DIR.
- `core.drum_pipeline`: extraction of percussion mark assembly and canonical drum cue mapping while preserving mapper/motion/effect owners.
- `core.stage_metrics`: opt-in inclusive stage timing and process lifetime peak RSS via HELIX_PROFILE_OUTPUT.
- Existing benchmark receipt claims exact baseline/refactor/cache-off XSQ parity: 42,305 model effects, matching SHA, snowman-band export; 68-event/eight-target canonical drummer oracle matches.
- Python 3.12 and 3.11 retries not yet green as at audit. Beta, Birdsong, Windows, Android, license workflows had successful runs on the audited commit.

## Verified blockers
1. Both Python full-regression jobs failed with the same three tests in tests/test_bounded_audio.py:
   - long partial-block chroma reference [1], [61], [509]
   - tolerance remains rtol=0, atol=1e-7
   - worst observed mismatch 2.66020723e-7
   Do not loosen tolerances. Reproduce under pinned dependency and fix chunk-boundary / normalization parity.
2. Native phoneme review failed visible_stage_motion. Recorded medians: bright fraction 0.08007, luma 13.466, motion 0.425, visible height 0.644, width 0.681.
3. Fresh native-band workflow rejected the supplied source: no independently resolved lead and backing vocal tracks. Do not create synthetic harmony to pass.
4. Exact-commit accepted-native consumer failed because its native producer failed.
5. Existing Birdsong hook in core/sequence_builder.py currently creates a 20-second, 10-fps synthetic energy/centroid sequence after the master engine run. This is demonstration scaffolding, not production audio integration. Do not call it production-ready.
6. Sequence Plan v0.2 is emitted by tools/emit_sequence_plan.py in shadow mode (renderer_changed=false); it is not yet consumed as the authoritative render input.
7. Effects orchestration bridge seeds five generic sections from a nominal duration (default 30 seconds) and generic motion/palette rules. Promotion is opt-in and generated XSQ may be built from the generic intent graph. It must not be promoted as the universal musical source until it consumes source-bound audio/performance events and proves parity/quality.

## Target cohesive architecture
AudioSource/AnalysisCache
  -> Shared MusicalClock and typed EventLedger
       beat/downbeat, section, onset, harmony, note, vocal, percussion, silence, phrase
  -> PerformancePlan (one deterministic, source-bound plan)
       confidence/provenance, humanization seed, performer intents, rests and phrase arcs
  -> Resource/LightingPlan
       layout capability inventory, group role, AC/RGB constraints, ownership, priority,
       collision resolution, intensity/flash limits, explicit no-op/explainability
  -> Render adapters
       canonical xLights XSQ/FSEQ; snowman-band/performance animation; Birdsong; AC/LOR
  -> Shared validators and scorecard
       event truth, timing, overlap, coverage, section contrast, visual motion, brightness,
       XML contracts, original audio hash, deterministic signatures, runtime/memory profile.

No engine should independently re-decode source audio, infer its own clock, or write conflicting effects without registering ownership and priorities in the plan.

## Integration work, ordered
P0 Regression recovery:
- Fix the three bounded-chroma parity tests without relaxing tolerance.
- Re-run both Python 3.11/3.12 complete suites; add fixture coverage around partial final windows and multiple BLAS/library combinations.

P1 Canonical event/time contracts:
- Define immutable typed event envelope: event_id, source_id/hash, source_clock, timestamp_ms/frame, duration_ms, kind, target, confidence, provenance, parent/related event IDs, seed.
- Require every engine to emit or consume this contract. Preserve existing drum mapper's eight-target oracle and native geometry.
- Make one timebase conversion utility authoritative (audio samples <-> ms <-> frame); eliminate local rounding drift.

P2 Shared analysis:
- One decoded audio object and one feature cache per source+parameter/version identity.
- Consumers take typed feature/event references, not perform fresh independent analysis.
- Cache entries validate shapes, dtypes, sample clocks, decoder/DSP version and code fingerprints; cache is opt-in until final full cache-hit parity is proven.

P3 SequencePlan / PerformancePlan:
- Extend SequencePlan with event ledger references, performance roles, constraints, provenance and scorecard.
- Convert current shadow-only emitter to produce inspectable plans first; then implement a plan consumer in a separate opt-in render adapter.
- Preserve canonical engine path as control; promotion requires exact deterministic parity or documented expected musical delta with owner acceptance.

P4 Engine adapters:
- Drummer: retain independent percussion evidence/stem precedence; prohibit guitar/melody spectral events from being mislabeled as drum events; preserve kick/snare/hat/cymbal/tom mapping and eight-target oracle.
- Birdsong: consume actual source frames/features; no synthetic 20-second fallback in production. Demo mode must be separately explicit and visibly labeled.
- Vocals: do not animate independent lead/backing roles without source-bound vocal separation/phoneme confidence. Silence must remain silence.
- Melody/harmony: bind note events to source clocks and allowed prop ranges; prevent pitch events from feeding drums.
- Effects/orchestration: derive section/energy/motion from actual plan and layout; seed intents from source events rather than fixed five-section generic graph.
- AC/LOR: enforce channel capability constraints at planning time; omit unsupported effects before renderer; preserve source LMS/wiring and AC-safe effects.

P5 Resource arbitration:
- One deterministic per-frame/per-prop scheduler with exclusive/priority ownership, merge rules, max simultaneous dominant groups, protected manual layers, AC-safe family and output bounds.
- Record every rejected/suppressed request with reason; no silent collision or stale always-on channels.

P6 Objective optimization:
- Use profile stage timings and peak RSS to choose hot spots. Avoid speculative Numba rewrites.
- Compare baseline, cache-off, cold-cache, warm-cache with alternating execution order and same audio/layout/template.
- Require XSQ musical signature parity, duration/timing integrity and drummer oracle parity before accepting speed changes.

P7 Native/visual acceptance:
- Fix visible stage movement independently from singer-source qualification.
- Only accept exact-SHA native MP4 after full decode, soundtrack correlation, representative-frame visibility and exact source/layout provenance.
- Re-run native consumer after producer succeeds. No hardware/device claims without real hardware.

## Shared acceptance gates
- Same input audio SHA and layout/template hashes recorded in every run.
- All events within source duration; all frame conversions monotonic and bounded.
- Deterministic same-seed plan and output hashes.
- No unsupported output effects per target capability.
- No event-kind leakage (e.g. guitar notes -> drum hits; vocal noise -> backing vocalist).
- Canonical drummer oracle remains exactly 68 events / eight targets for the existing fixture.
- Baseline vs cached XSQ musical signature and audio identity unchanged where the change is intended to be behavior-preserving.
- Strict full suite passes Python 3.11 and 3.12.
- Native preview quality, independent vocal source and visual/hardware approvals remain separate gates.

## Run references
- PR #205: https://github.com/ryankorkowski-boop/helix-sequencer/pull/205
- Audited commit: https://github.com/ryankorkowski-boop/helix-sequencer/commit/28072eda15c09b6d5c93dac92a9942cc33d8be8e
- Python full CI run: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/41181696928
- Real source profiling workflow: https://github.com/ryankorkowski-boop/helix-sequencer/actions/workflows/real-sequence-profile.yml

## Execution truth
This audit triggered a retry of the failed Python 3.12 full-regression job (job ID 124480245902; accepted by GitHub, new job queued). It did not modify source code, dispatch a new workflow, produce a fresh MP4, or alter/merge PR #205. The Python 3.11 retry in the same run remained failed at the time of the audit.
