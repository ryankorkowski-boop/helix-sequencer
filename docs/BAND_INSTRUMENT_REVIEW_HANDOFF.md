# Band instrument review and movie delivery

The canonical continuation ledger is [MASTER_TODO.md](../MASTER_TODO.md). Work is on `feature/band-instrument-readability`, based on the published natural-shoulder drummer revision `f0aca51`. This report is updated at delivery; the fresh batch is currently being verified.

## Historical input audit

The earlier player-piano implementation is commit `d94c4ec047d64843bec0142688a208d1827ddb83`; `core/effect_engine.py` contains `choose_player_piano_pool` and `place_player_piano_sequence`. Its literal note pools also support `canes_combo`, `north_canes` and `south_canes`, which connects the candy/cane keyboard idea to this implementation. The recovered history dates to April/May 2026; a separately named year-old candy-keyboard asset was not recovered.

Reusable measured-note semantics are `music/note_events.py` (pitch, start/end, velocity), `render/keyboard_geometry.py` (ordered real keys), `render/piano_renderer.py`, and the May floor-piano/string specifications and adapters. Decorative beat fallback, cue skipping, randomized playing delays, coarse pitch-to-string bins and softened every-thirteenth accents are intentionally excluded from this source-driven review.

Every current member was examined: the drummer retains the original XSQ target/hand/hold schedule; singers retain screened lyric/wordless visemes and authored duet lanes; bass and guitar use their separate six-stem outputs; the keyboard combines piano notes with separately screened mallet notes from `other`, checking vocal leakage. Authored duet casting is not automatic gender or singer identity separation.

## Changes and concrete defects fixed

- `models/band_instrument_logic.py`: canonical NoteEvent compiler, velocity/hold/release, source attack phases, detuning-aware harmonic-template pursuit, maximum-cardinality distinct playable string assignment. Guitar chord notes no longer overwrite each other on a string. Octave folding is explicit; impossible low-register chords report omitted note frames.
- `tools/analyze_band_instruments.py`: source-hashed per-stem note events and separate screened mallet provenance. Harmonics and detuned single notes are tested against false chord creation. No absent guitar is fabricated from the `other` bus.
- `models/readable_band_scene.py`: wider, thicker independent bass/guitar strings with source-gated segmented resonance; thicker guitar neck and frets with verified string clearance; head/torso groove; literal key depression. The visible wave is an artistic resonance envelope, not acoustic-frequency vibration.
- `tools/readable_band_performance.py`: source onset gestures replace free-running sine picking; bass left-hand height is monotonic with the original measured pitch (lower toward sky, higher toward ground); right hand follows the active physical string; guitar fretting follows the actual neck; keyboard hands contact the lit literal keys with independent velocity.
- `tools/render_intricate_band_samplers.py`: optional shaders/camera hook, leaving its historical defaults intact.
- `tools/audit_band_instrument_inputs.py` and `tools/render_readable_band.py`: independent source/event checks, actual pose checks, and encoded own-channel checks against an instrument-muted counterfactual. Surrounding layout activity cannot satisfy an instrument check.

The drummer uses the shared source-art compositor and latest v7 outward/lower torso shoulders. Its kit surfaces and tagged song schedules remain preserved; it is a planar physical prop mounted in the intricate 3D stage, not a replacement 3D kit. Original audio and historical native shows/movies remain preserved.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m tools.analyze_band_instruments
OPENBLAS_NUM_THREADS=2 python -m tools.audit_band_instrument_inputs
python -m pytest -q tests/test_readable_band_instruments.py tests/test_intricate_band_scene.py tests/test_band_sampler_logic.py tests/test_drummer_shoulder_revision.py
LIBGL_ALWAYS_SOFTWARE=1 EGL_PLATFORM=surfaceless LP_NUM_THREADS=3 python -m tools.render_readable_band --group 01
```

Analysis requires the retained original six stems under `outputs/Snowman_Ensemble/stems/htdemucs_6s`. Rendering alone uses the pinned 29,719,264-byte input ZIP at media commit `a8f7e9ed3973774874d9f719cd0a7b38a245cc2a`, SHA256 `ac7c36b1a749aedf09d2de20681163e3ede052d2062466474f228919bdc6b2ec`. The render request and all 21 windows are in `evidence/band_instrument_review/`. The five-job workflow is `.github/workflows/render-readable-band.yml`.

## Validation, downloads and remaining scope

Seventeen focused regressions pass. Final full-HD pilots, full-source actual-pose audit, remote batch, archive verification and immutable links are being recorded here before delivery.

Separated stems, inferred pitches and mallet classification are estimates, not a verified musical score. Guitar can legitimately remain quiet in weak passages; targeted close-ups use stronger source windows. The shortest phoneme-test song cannot supply a 42-second movie and is excluded. New stage native xLights/controller playback and automatic singer identity separation remain deferred. Do not claim exhaustive audible-hit/note ground truth from detection and routing tests. Future work must retain source binding, independent string routing, literal key geometry and the current drummer shoulders.
