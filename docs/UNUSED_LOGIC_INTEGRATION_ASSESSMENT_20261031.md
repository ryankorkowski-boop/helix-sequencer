# Helix unused-logic integration assessment — 2026-10-31

Branch: `codex/eight-hour-recovery-20261019`. Assessment of selected current modules, not a repository-wide exhaustiveness claim.

## Confirmed existing modules and production gaps

| Component | Existing implementation | Production gap | Safe next step |
| --- | --- | --- | --- |
| `core/source_ownership.py` | Confidence/origin-gated ownership and labeled-stem mapping | Main `core/effect_engine.py` harmonic NoteEvent source_owner is optional and usually unclassified | Produce identifiable per-stem NoteEvents from actual stems; benchmark strict-vs-legacy and do not enable global gating until parity evidence |
| `core/audio_intelligence.py` | StemAnalysis, NoteEvent, cached/bounded feature extraction | Stem-specific note conversion not yet confirmed in main `run_variant` | Introduce one shared analysis-result boundary and source hashes; ensure no redundant full-audio analysis |
| `core/snowman_band.py` | Both harmonic and stem-note schema adapters, opt-in strict keyboard routing | Main producer does not supply trustworthy instrument-separated notes by default | Wire provenance-bearing stem events behind an opt-in flag with tests; don't force guitar notes to keyboard |
| `core/musical_quality_gate.py` + `core/self_improving_scoring.py` | Five explicit storytelling metrics and opt-in acceptance wrapper | Missing verified event-derived evidence, so enabling strict gates would reject unknowns | Compute honest section, phrase, silence, ownership and motif metrics from real emitted events; retain legacy scores for comparison |
| `core/event_provenance.py` | Bounded event provenance JSON summary | Native XSQ debug metadata not yet supplied | Add non-destructive exporter metadata with source, origin and confidence while preserving native compatibility |
| `core/intent_layer_expander.py` + `core/band_intent_adapter.py` | Deterministic layer expansion and adapter | Adapter fans each intent out to all selected performers; it does not prove source-specific instrument behavior | Filter by instrument ownership and role only when backed by source events; prevent vocal mouth motion from generic motion intents |
| `models/helixville4_performer_runtime.py` + `core/band_performance_timeline.py` | Approved drummer states; reference assets and source-driven performer contracts | Guitarist, bassist, lead and harmony have empty runtime state tables, so a generic state compiler cannot animate them | Route these to approved source-driven paths; do not fabricate state tables or substitute planar assets for verified solid geometry |

## Small implemented safeguard

- `core/band_intent_adapter.py` now respects explicitly empty performer selections and validates unknown/duplicate IDs. Commit `31e6b48129a414719005326ec6e13733d5d62765`.
- `tests/test_band_intent_adapter_selection.py` provides five regression tests. Commit `c38aec88dbb66e7a9ae44793b22356626179206b`.
- These tests have been authored but **not executed** here. Do not claim integration is verified.

## Priorities

1. Run targeted tests and all Python/Windows/Android/native regressions. Capture actual CI outcomes.
2. Trace the current `run_variant` producer through per-stem analysis, ownership propagation, sequencing JSON, band plan and XSQ/FSEQ.
3. Connect true stem-derived note events opt-in, with provenance, confidence and unknown rejection. Compare event hashes and original drummer oracle before changing defaults.
4. Implement measurable source-specific lead/harmony mouth timing including rests and phrase drift. Prove independent source ownership; do not fabricate vocal separation.
5. Fix canonical 3D geometry/visual identity and synchronize instrument animation with actual source events.
6. Feed musical section/phrase evidence into the existing storytelling quality gate and optimize once observed.
7. Render a new native real-audio MP4; verify audio origin, harmony non-rest effects, canonical approved performers and native workflow acceptance. Owner visual approval remains independent.

## Guardrails

Preserve the approved V3 drummer oracle, exact legacy 256-channel AC wiring/colors, native xLights exports, six-member default band, optional seventh API, deterministic behavior and original audio. No xylophonist in default approval. Avoid sweeping monolith rewrite or introducing unvalidated prototype Helixville runtime into production. PR #188 must remain unmerged; no beta publication or false video acceptance.

## Resume

```bash
python -m pytest -q tests/test_band_intent_adapter_selection.py tests/test_source_ownership.py tests/test_keyboard_source_routing.py tests/test_audio_stem_ownership.py
python -m pytest -q
git status --short
git log -5 --oneline
```

Inspect the newest CI jobs and compare native outputs and drummer oracle before additional runtime wiring. Keep `MASTER_TODO.md`, `docs/BETA_COMPLETION_LIVE_HANDOFF.md` and evidence status updated after validation.
