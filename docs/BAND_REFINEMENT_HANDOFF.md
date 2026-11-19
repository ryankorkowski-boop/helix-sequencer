# Helix band refinement handoff — 2026-10-12

Canonical continuation ledger: `MASTER_TODO.md`. Task checklist: `docs/BAND_REFINEMENT_CHECKLIST.md`.
Working branch: `feature/band-musical-refinement-20261012`, based on `4aca41c5ae83a9f4c838e69393380f1dd0817ae6`.
No primary-branch merge. Current code is an opt-in review path, retaining previous approved assets and compositors.

## Implemented

- `animation/articulated_source_drummer.py`: original body/surfaces/gold shaft artwork, new connected two-link neutral-wire sleeves, fixed-length sticks, anticipation/contact/rebound/recovery, continuous fast passages, explicit same-hand travel constraints, configurable idle/strike brightness. Detection families stay polyphonic. Physically unplayable motions are recorded; surface events remain preserved. Snare hand reassignment is an explicit review-only physical schedule change.
- `models/band_motion_refinement.py`: deterministic source-owned alternating gesture envelopes, bounded fretting transitions, fixed-link IK, strict mallet provenance/range handling.
- `models/refined_band_scene.py`: preserved readable bass/guitar designs and warmer independent strings; dedicated literal MIDI60–84 mallet bars/player using the existing snowman aesthetic. The original piano remains a separate performer.
- `tools/refined_band_performance.py`: retained bass/guitar stem events, stable supported dominant guitar contact, bass pitch transitions, alternating artistic strokes, smaller single-note guitar picking, isolated measured mallet-peak candidates with conservative acoustic screens, no piano leakage or octave-folded bars, connected mallet travel/contact/recovery.
- `tools/render_refined_helix_band.py`: actual Helix GL and source-art renders on original audio; full dry comparison/test and six18-second real-song excerpts; source and pose evidence. CLI brightness controls.
- `tools/package_refined_band.py`: combined C/E reels; normalized concatenation filter fixes differing input time bases.
- `tools/export_refined_band_matrix.py`, `tools/audit_refined_band_native.py`: explicit portable virtual-matrix XSQs, actual xLights2026.18 render and per-frame pixel comparison. This is NOT an individual stationary-performer prop export.
- Focused counterexample tests in `tests/test_band_motion_refinement.py` and `tests/test_refined_band_native_export.py`.

## Reproduction

Use Python3.12 with the repository preview dependencies, ffmpeg, CPU torch and cmudict for the broader suite. GL rendering uses Mesa/EGL. Restore the SHA-pinned input ZIP described in `evidence/band_instrument_review/remote_render_request.json`; extract at repository root, then run:

```bash
python -m tools.rebuild_band_logic_review
# This legacy helper writes one historical evidence JSON; restore that file
# after saving any needed comparisons. Never overwrite prior delivered media.
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 LP_NUM_THREADS=2 python -m tools.render_refined_helix_band --dry
for job in 0 1 2 3 4 5; do
  OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 LP_NUM_THREADS=2 python -m tools.render_refined_helix_band --job "$job"
done
python -m tools.package_refined_band --montages --exports
python -m tools.audit_refined_band_native --binary /absolute/path/xLights --display 109
python -m tools.audit_refined_band_output
python -m pytest -q tests/test_band_motion_refinement.py tests/test_refined_band_native_export.py tests/test_readable_band_instruments.py tests/test_band_logic_reassessment.py tests/test_drummer_shoulder_revision.py
python -m pytest -q tests
```

For brightness: add `--idle-brightness 0.72 --strike-brightness 1.35` to the renderer. Values must be within0–2.
On this sandbox, Xvfb must use a TCP display with `-listen tcp -nolisten unix -ac`; a stale display lock can prevent startup. The native auditor manages a fresh display. The pinned xLights AppImage SHA256 is `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`.

## Validation and current risks

Initial baseline focused checks:18passed. New motion checks:18passed. Full suite after dependencies:1266passed/12failed/5skipped; all12failures reproduce on untouched baseline in `evidence/band_refinement/baseline_failure_comparison.log`. Initial collection lacked torch; installing torch and cmudict resolved those environment gaps. Export/mixed-FPS regressions:2passed. Final output/native/soundtrack evidence is under outputs/Band_Refinement_20261012; the user-facing report is Helix_Band_Refinement_Report.md.

Actual output review exposed weak mallet bar definition, an occluded mallet grip, rapid drummer wrist discontinuities, and a mixed-FPS montage time-base defect. These were corrected; earlier pilots and native render proofs are superseded and excluded from delivery. Do not reuse old FSEQs after replacing their MP4 media.

Generation/evidence: `outputs/Band_Refinement_20261012/` and `evidence/band_refinement/`. Raw separated WAV stems are absent from the recovered render ZIP. Accepted source-hash-bound inference caches were retained rather than inventing replacement detections. No listening-based verification, human-labeled precision/recall, verified xylophone identity, exact finger identity, recovered guitar upstroke, or native physical-controller proof is claimed.

## Remaining work

1. Final renders, native checks, audio-cut checks and decoded review are complete:7,747MP4frames/6,981native frames/40decoded screenshots;38focused checks pass. Save the delivery files and record the commit/publication receipt.
2. Publish the code on the dedicated branch, with no primary merge, and record the actual commit receipt in the final report.
3. Obtain the original six separated WAV stems and independent manual event labels before tuning drum-family thresholds or reporting musical accuracy.
4. Validate pitched-percussion identity/fundamentals before promoting the diagnostic mallet estimates as confirmed xylophone notes.
5. Build a separate native stationary-prop pose/channel export and verify on user hardware; the current delivered native route is a virtual matrix with required video/audio media.
6. Review limits of monophonic peak candidates, ghost notes, hi-hat articulations, slide evidence, detailed guitar finger/chord poses, and physically unplayable same-hand schedules.
7. User artistic/musical approval remains pending. No merge until the user's preview review.
