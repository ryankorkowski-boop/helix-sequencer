# Helix Sequencer — Integration and Release Qualification Roadmap
Updated: 2026-10-31. Branch: `codex/eight-hour-recovery-20261019`. PR #188 remains unmerged.

## Operating rule
Inspect → implement a focused change → test → compare output → document exact source SHA → render real-audio/native media → verify → owner approval. Do not mark an implementation complete based only on a module existing or tests being authored. Never substitute a planar or newly invented drummer for the approved canonical reference. No xylophonist in the six-member default. Preserve 256-channel AC wiring, color mapping, exports, and deterministic event signatures.

## Work packages and acceptance gates

| ID | Priority | Work | Exit evidence | State |
| --- | --- | --- | --- | --- |
| DATA-01 | P0 | Trace production callers from audio, rhythm, song parts, vocals, and band cues into XSQ/FSEQ and native preview | Per-feature call sites, input provenance, output-event diff and enabled/disabled comparison | Open |
| OWN-01 | P0 | Propagate detected/estimated/fallback source ownership from actual stem events into band cue builder; enable strict routing only after verified source quality | Guitar/bass/keys source-separated test, no phantom keyboard, overlaps and rests, old/new real-audio render | Foundation committed; integration opt-in |
| ARR-01 | P0 | Build hierarchical section → phrase → effect arrangement with deterministic returning motifs, chorus expansion, solos, fills, rests and silence | Verse/chorus/bridge/solo/silence golden tests and visible 45-second A/B native comparison | Open |
| VOC-01 | P0 | Verify lead/harmony source identity, timing and lexical phonemes; confidence-gated fallback and silence | Acoustically labeled beginning/middle/end comparison, ten phoneme classes, independent source ownership | Open |
| CAN-01 | P0 | Validate canonical fully modeled native six-member band and original drummer geometry | Approved model provenance, native continuous render, drum positions/kick orientation, no xylophonist | Open |
| QUAL-01 | P0 | Connect measurable section, phrase, ownership, silence and motif metrics to candidate ranking | Same-song feature-off/on event and media deltas; repetitive beat-only candidate rejected | Evidence-gate foundation committed; producer wiring open |
| REG-01 | P0 | Verify final source and media | Full Python 3.11/3.12, Windows, Android 30/36, native XSQ/FSEQ and audio/video QA all tied to exact SHA | Open for new commits |
| ENG-01 | P1 | Extract one `run_variant` stage at a time behind stable facade | Exact legacy output/event hash parity and public CLI/GUI API parity | Open |
| PERF-01 | P1 | Benchmark decode, separation, feature extraction, plan, export and render; source-hash cache with bounded memory | CPU time, RSS, hit rate, elapsed time, same-source output parity | Open |
| CI-01 | P1 | Consolidate duplicate CI work and one machine-readable release receipt | SHA, runs, tests, native/video artifact hashes and open gates traceable from one manifest | Open |
| APP-01 | P1 | Physical Android and controller acceptance, Windows portable acceptance | Actual device/controller/user evidence | Open |
| UTIL-01 | P2 | Consolidate signal helpers, typed intermediate events and indexed timeline search after parity profiling | Import graph, edge-case tests, unchanged event output | Open |

## Immediate sequence
1. Run `pytest -q tests/test_source_ownership.py tests/test_keyboard_source_routing.py tests/test_musical_quality_gate.py`; then focused band and scoring tests. These tests have been authored but have NOT been executed in this connector session.
2. Inspect actual note-event constructors and wire provenance there; test strict routing against source-labeled real audio before changing the default.
3. Record the current `run_variant` musical-data call graph and establish an unchanged baseline event hash.
4. Implement section/phrase composition behind a feature switch; prove musical changes in native outputs.
5. Integrate storytelling metrics from measured output events, not arbitrary producer scores.
6. Qualify singers and canonical native drummer; keep unresolved gates explicit.
7. Profile and incrementally extract stages only after baseline parity.
8. Rerun all final-source CI, device, controller and native media checks. Produce exactly nine real-audio MP4s in one approval ZIP, then await explicit owner approval.

## Recovery / handoff
Authoritative checklist: `MASTER_TODO.md`. Live handoff: `docs/BETA_COMPLETION_LIVE_HANDOFF.md`. Machine status: `evidence/beta_completion/latest_status.json`. Artifact inventory: `evidence/beta_completion/artifact_manifest.json`. On resumption fetch branch HEAD, compare the four files and PR #188, collect latest CI, and update all receipts with actual results only. Never claim a new MP4 was produced unless its bytes and digest were verified.
