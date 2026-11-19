# Dry Drum Test: missing high-tom roll

The user identifies the missed 32–34 second passage as a high tom or timpani sound. At `c58364b`, the network had already detected its attacks but exported generic `tom` without a physical identity. Import rejected them all as `unresolved_tom_identity`, so no target reached the XSQ or video. This was not an onset timing or renderer masking failure.

Original-source attack/body spectra show roughly 500 Hz ringing modes and multiple brighter/quiet articulations in the reviewed passage. The previous isolated pitch search used 60–400 Hz; LarsNet can also lose the original body. Extending that search alone would still lack an appropriate recording calibration. A diagnostic ADT_STR experiment disagreed with the user's listening and changed labels with clip boundaries. Its snare/hat/auxiliary guesses were rejected, not adopted.

The optional `--drum-calibration` input names source-bound, user-labelled attack/body exemplars. It compares existing unresolved candidates against all three physical tom alternatives using separate normalized log-frequency spectra. Similarity and a separation margin are required. It never creates attacks, changes family/timing/velocity/confidence, rotates toms, or touches accepted events. Raw inference and every original rejection remain in the audit. The three first-fill identities still come from the prior sparse review.

Ten previously rejected attacks from 32.36 through 33.77 seconds now resolve to `TOM_HIGH`. The brighter attacks stay in this user-reviewed tom passage; no hi-hat notes are added. The exact-source scope is 32.3–34 seconds. The lower-pitched change near 33.93 seconds remains ambiguous and unassigned; this is not a claim that every tom in the recording is solved.

Rapid same-target tom hits also need a visible retrigger. Their former 165/175 ms holds could overlap notes about156ms apart and display one static contact pose. Only those holds are shortened to leave50ms of rest, preserving strike times and all artwork. This applies to native XSQ and MP4. Isolated holds, other instruments and all detected musical events remain unchanged.

The seven new benchmark anchors use independent original-waveform attack rises and the user's passage-level family judgment. They are held out from the timbre exemplar timestamps. The suite also protects source identity, the earlier descending fill, original family/dynamics, unknown high/mid abstention, other rejection gates, and separate repeat strikes. It does not turn a green test into listening approval.

Reproduce:

```sh
PYTHONPATH=. python tools/integrate_drummer_v3_into_xsq.py template.xsq evidence/drummer/dry_drum_test.wav --drum-events evidence/drummer/dry_drum_test_adtof.json --drum-review evidence/drummer/dry_drum_test_tom_review.json --drum-calibration evidence/drummer/dry_drum_test_source_calibration.json --output test_runs/drummer_dry_ending/Helix_Drummer_DRY_ENDING.xsq --report test_runs/drummer_dry_ending/report.json
PYTHONPATH=. python tools/export_drummer_only_xsq.py test_runs/drummer_dry_ending/Helix_Drummer_DRY_ENDING.xsq --output test_runs/drummer_dry_ending/Helix_Drummer_DRY_ENDING_ONLY.xsq --audio evidence/drummer/dry_drum_test.wav
PYTHONPATH=. python tools/render_drummer_v3_preview.py test_runs/drummer_dry_ending/Helix_Drummer_DRY_ENDING_ONLY.xsq --audio evidence/drummer/dry_drum_test.wav --output test_runs/drummer_dry_ending/Helix_Drummer_DRY_ENDING.mp4 --fps 60
```

Local report/CSV/XSQ/MP4, source plots, rejected probes, before/after JSON and decoded strike/rest frames live under `test_runs/drummer_dry_ending/`. CI publishes the same current performance in `drummer-dry-audio-test`, including a six-second ending clip. Master progress and limitations: `MASTER_TODO.md`.

The physical contract remains eight targets and three toms, dim visible body, complete target-specific strikes, no kick/hat sticks, subtle pedal, alternating snare hands/full shell, transparent kick and independent cymbal shimmer. Native playback and user approval remain open. Earlier false hi-hat behavior outside this passage is not repaired by this change.
