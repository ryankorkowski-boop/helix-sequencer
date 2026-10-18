# Snowman Band — verified release blockers (2026-10-17)

This is a live, evidence-bound execution checklist. **Do not merge/release** until the owner approves actual seven-member performance footage.

## Evidence
- Native geometry workflow: [run 39073887694](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39073887694) **passed**; pixel/AC16 model coordinates and Android PNG previews are source-derived.
- Full-band acceptance workflow: [run 39073891184](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39073891184) **failed**.
- Its artifact `native-proof-acceptance.json` says `valid_zip=true`, `showcase_mp4s_verified=0`, and reports:
  1. `full_song_showcase_complete` is not true.
  2. Complete-band verification is not true.
  3. No non-diagnostic MP4 is present.
- Only included MP4 is `Physical_Drummer_Diagnostic/Native_Physical_Channel_Diagnostic.mp4`.
- `Final_Band_Output_Diagnostic/verification.json` identifies an **authored fixture**, not an original-song transcription. Its 12-performer diagnostic covers two six-performer stages and **does not prove** a real-song seven-member Snowman Band.

## Blocking implementation checklist

- [x] Export audited native pixel and AC16 coordinates for seven performers.
- [x] CI regression for drummer's independent hits and ten distinct singer mouth circuits.
- [x] Generate Android PNG/SVG inspection previews from native geometry.
- [ ] **P0:** Select actual source audio and record SHA-256, exact excerpt start/end, and analysis provenance.
- [ ] **P0:** Generate a source-bound performance for the **seven native HX_SNOW performers**, not a legacy 256-light layout, unrelated stage, or authored diagnostic.
- [ ] **P0:** Produce an Android-playable MP4 of native seven-performer light states against that audio; validate full ffmpeg decode, duration, synchronization, exact native model IDs, and provenance in machine-readable JSON.
- [ ] **P0:** Include that MP4 and proof in the native-proof archive; do not mark `full_song_showcase_complete` or complete-band verified without real evidence.
- [ ] **P0:** Re-run the full-band acceptance workflow and resolve its actual failed assertions **without lowering acceptance criteria**.
- [ ] **P1:** Owner visually reviews the real-song nighttime MP4 and explicitly approves or requests changes.
- [ ] **P1:** Verify physical LED spacing, hardware channel mapping, mounting geometry and real-world scale; only then generate construction/drilling templates.
- [ ] **P1:** Integrate PR #172 only after required tests and owner approval.

## Invariants
- Do not equate model point count with physical bulb count.
- Do not infer real LED brightness, diffusion, colors, or physical dimensions from point projections.
- Do not call a generated still, a diagnostic fixture, or a different layout an exact nighttime performance.
- Preserve the full-song and complete-band acceptance gates.
