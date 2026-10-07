# Uploaded dry drum test and cymbal lighting

Read `MASTER_TODO.md` first. The user reports false hi-hat hits in the Helix preview and requests the drummer workflow on their uploaded recording. They are unsure whether or where that recording contains real hats. This run provides a diagnostic preview, not approved percussion labels or a claimed hi-hat fix.

## Exact uploaded source and workflow

`evidence/drummer/dry_drum_test.wav` is the unchanged uploaded **Dry Drum Test.wav**: 38.32 seconds, stereo, 48 kHz PCM16; SHA256 `4cd9ee35b65d359aa44ac4c9e01a256bbcaf3297458340fc512084bae1463913`.

Actual pretrained inference was run locally on both the original audio and the Demucs drum bus. The selected route is the current Helix candidate: Demucs htdemucs → LarsNet family stems for dynamics evidence → ADTOF independent family activations → source-bound import → existing scheduler and eight-target mapper. External model revisions and licenses remain those in `DRUMMER_TRANSCRIPTION_REASSESSMENT.md`; no model code or weights are bundled. The dry-test transcription records model/stem hashes and published thresholds.

| Input | Kick | Snare | Generic tom | Hi-hat | Cymbal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original dry audio | 68 | 55 | 33 | 147 | 14 |
| Separated drum bus | 67 | 53 | 34 | 138 | 17 |

Counts describe inferred candidates, not true hits or acceptance targets. The separated route schedules 275 placements. All 34 generic tom predictions abstain: this recording has no measured HIGH/MID/FLOOR calibration. Reusing the Helix song's reference pitches or cycling tom destinations would fabricate identity.

`evidence/drummer/dry_drum_test_adtof.json` is cached inferred evidence, explicitly pending human review. The GitHub workflow verifies its original-source hash, imports it, exports reports and drummer-only XSQ, renders the complete recording at 60 fps, and decodes eight review frames. CI does not independently rerun the external ML models.

## What signal inspection shows about hats

The original and separated model inputs both predict substantial hat activity; changing only the input did not resolve the complaint. The nominal LarsNet hat stem has substantial body leakage. In the 60 ms attack window from −10 to +50 ms around the 2.04 s candidate, approximately 94% of its Hann-windowed spectral power is below 1 kHz and less than 1% above 5 kHz; the 3.29 s candidate is approximately 96% below 1 kHz and less than 1% above 5 kHz. Both currently receive estimated velocity 1.0. These findings implicate broadband stem RMS as a source of exaggerated native XSQ hat accents, but do not prove that no simultaneous hat was played. The existing MP4 compositor uses the same bright 90 ms hat pulse for all accepted hat notes; it does not currently reproduce per-note hat velocity. No such behavior is changed in this baseline test run.

Nearby weaker candidates at 1.72 and 1.89 s have about 98% and 97% of their nominal hat-stem power above 5 kHz. Blanket removal of quiet notes, every snare-coincident hat, or all uncertain hats could delete real playing. No global threshold or transcription/scheduler change is made in this pass. The false-hit issue remains open for review of the actual audio and corresponding preview. There is no auditory perception tool in this session; signal inspection is not called listening. `evidence/drummer/dry_drum_test_signal_inspection.json` records these measurements for all 138 candidates, tied to both original-source and nominal-hat-stem hashes; it is evidence, not expected events.

Local evidence is in `test_runs/drummer_dry_test/`: original/stem activations and transcripts, source manifest, isolated-stem energy plots, report, event CSV, full MP4 and XSQ, decoded frames and soundtrack identity evidence. The full encoded soundtrack's zero-lag source correlation is .9959113596. The CI artifact is named `drummer-dry-audio-test` and includes the exact WAV, cached transcript, exported report/CSV/XSQ and MP4.

## Cymbal shimmer and decay

Only the left/right cymbal surfaces receive a 1.8-second fade. Each hit restarts its own cymbal's fade. Two lit warm-gold levels, with a 15% difference, alternate at sequence-frame cadence; this is subtle shimmer without black/off strobing. Strike arms/sticks retain their original 320 ms cue. Hi-hat, pedal, kick, snare, toms, body keepalive, clean idle background, complete strike overlays and alternating snare hands retain their existing behavior.

`animation/cymbal_lighting.py` shares the fade/peak calculation; `tools/render_drummer_v3_preview.py` applies it to source-art surfaces. `tools/integrate_drummer_v3_into_xsq.py` exports stock xLights **On** effects with `E_TEXTCTRL_Eff_On_Start`, `E_TEXTCTRL_Eff_On_End`, `E_TEXTCTRL_On_Cycles=1`, `E_CHECKBOX_On_Shimmer=1` and two enabled gold palette entries. Fields and shimmer behavior were checked against [xLights OnEffect.cpp](https://github.com/xLightsSequencer/xLights/blob/master/src-core/effects/OnEffect.cpp). A retrigger clips the previous effect at its remaining fade level rather than accelerating its decay.

The Helix report's entire `analysis` and `event_audit` match the previous visual-polish report exactly: all 1,022 events, timestamps, families, velocities, confidence and destinations are unchanged. The 25-second original-song preview and decoded attack/decay frames are in `test_runs/drummer_cymbal_shimmer/`; soundtrack correlation .9962146413. Four focused regressions check attack, decay, shimmer, retriggers, idle body, inactive instruments, short strike poses and native/preview event agreement; the complete relevant suite passed 120 tests. Native xLights playback remains unverified. The 1.8 s decay is an authored lighting envelope, not measured cymbal sustain, and native frame quantization may differ by one frame.

## Reproduce the uploaded-audio preview

```sh
# Use the separately installed, pinned external model environment for inference.
PYTHONPATH=. python tools/prepare_drummer_stems.py evidence/drummer/dry_drum_test.wav --output test_runs/drummer_dry_test/stems --larsnet-code /path/to/larsnet
PYTHONPATH=. python tools/transcribe_drummer_adtof.py evidence/drummer/dry_drum_test.wav --analysis-audio test_runs/drummer_dry_test/stems/separated/htdemucs/dry_drum_test/drums.wav --family-stems test_runs/drummer_dry_test/stems/lars_full --output test_runs/drummer_dry_test/new_inference.json
# Cached source-bound inference reproduces the reviewed export without installing models.
PYTHONPATH=. python tools/integrate_drummer_v3_into_xsq.py template.xsq evidence/drummer/dry_drum_test.wav --drum-events evidence/drummer/dry_drum_test_adtof.json --output test_runs/drummer_dry_test/Helix_Drummer_DRY_TEST.xsq --report test_runs/drummer_dry_test/report.json
PYTHONPATH=. python tools/export_drummer_only_xsq.py test_runs/drummer_dry_test/Helix_Drummer_DRY_TEST.xsq --output test_runs/drummer_dry_test/Helix_Drummer_DRY_TEST_ONLY.xsq --audio evidence/drummer/dry_drum_test.wav
PYTHONPATH=. python tools/render_drummer_v3_preview.py test_runs/drummer_dry_test/Helix_Drummer_DRY_TEST_ONLY.xsq --audio evidence/drummer/dry_drum_test.wav --output test_runs/drummer_dry_test/Helix_Drummer_DRY_TEST.mp4 --fps 60
```
