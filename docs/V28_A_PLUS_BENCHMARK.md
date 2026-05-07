# V28 A+ Benchmark Targets

This note captures the current evidence from the legacy 256 grade-only benchmark and defines the next measurable path from the current v28.9 A- result to an A+ candidate.

## Current longer benchmark result

Command:

```bash
python tools/run_v28_legacy_256_previews.py \
  --versions v28.7 v28.8 v28.9 \
  --duration-seconds 20 \
  --max-layers-per-prop 1 \
  --skip-render
```

Result summary:

| Variant | Score | Grade | Effects | Validation issues | Sequence OK |
|---|---:|---|---:|---:|---|
| v28.7 | 74.1 | C | 3,749 | 0 | yes |
| v28.8 | 64.4 | D | 4,389 | 0 | yes |
| v28.9 | 91.1 | A- | 4,388 | 0 | yes |

## Main conclusion

v28.9 is the correct foundation for the next A+ candidate. It beats v28.8 despite having almost the same effect count because it adds stronger scene, role, and showcase intent.

The next improvement should not blindly add more effects. The improvement should make the existing density more professional through stronger staging balance, section contrast, and role hierarchy.

## What v28.9 is already doing well

The longer run showed v28.9 producing these high-value placement families:

- `role_scene_arrival=187`
- `showcase_scene_arrival=187`
- `showcase_vocal=49`
- `role_vocal_focus=17`
- `role_foreground=19`
- `spatial_chase=17`
- `validation_issues=0`

These are the signals that likely pushed v28.9 into A- territory.

## A+ blockers to address

### 1. Role staging is too thin outside scene arrivals

The longer run showed:

- `role_foreground=19`
- `role_midground=1`
- `role_background=2`
- `role_scene_arrival=187`
- `role_vocal_focus=17`

This means v28.9 is strong at scene arrival events but weak at continuous professional staging. An A+ candidate should have visible foreground, midground, and background intent throughout the sequence.

### 2. The synthetic benchmark audio is too simple

The current 20-second benchmark uses three sine tones. It is useful for repeatability, but it does not exercise real song structure well enough.

Observed audio-analysis shape from the run:

- `kick_events=0`
- `snare_events=0`
- `tom_events=1`
- `hihat_events=65`
- `bass_peaks=173`
- `vocal_peaks=80`

A better CI-safe benchmark should include section changes and percussive events so Helix can prove kick, snare, bass, melody, and scene-change behavior.

### 3. Section contrast needs a stronger test

The current benchmark identified only:

- `INTRO:0.0-8.0s`
- `VERSE:8.0-20.0s`

An A+ gate should exercise at least four sections, such as intro, verse, chorus/drop, bridge/breakdown, and finale.

## A+ candidate requirements

A future v28.10 or equivalent candidate should meet all of these before it is considered A+ ready:

- `quality_score >= 95.0`
- `validation_issues == 0`
- `sequence_ok == true`
- `effects_total` should not exceed v28.9 by more than 25% unless justified by better staging metrics
- foreground, midground, background, scene arrival, and vocal-focus role families should all be present
- at least four detected or intentionally generated sections should be exercised in benchmark audio
- no single role family should dominate the whole sequence
- the grade improvement should come from role/stage balance, not raw density only

## Recommended implementation slice

Build a v28.10 candidate from v28.9 with:

1. Stronger midground/background role assignment.
2. Section-aware contrast rules:
   - intro: restrained
   - verse: controlled motion
   - chorus/drop: broader scene arrival
   - bridge/breakdown: lower density, texture, anticipation
   - finale: highest-but-safe density
3. Improved musical routing:
   - kicks to impact/foundation props
   - snares to accents and scene punctuation
   - hats to small shimmer/twinkle props
   - bass to trees, megas, and foundation lanes
   - vocal/melody to foreground notes, stars, arches, and lead lanes
4. A CI-safe structured synthetic benchmark audio generator.
5. A grade-only benchmark that compares v28.9 against the next candidate without rendering MP4s.

## Why not use v28.8 as the base?

v28.8 produced 4,389 effects but only scored 64.4 / D. v28.9 produced 4,388 effects and scored 91.1 / A-. That proves effect volume is not the deciding factor. v28.8 may contain useful energy ideas, but any borrowed behavior should be filtered through v28.9's role hierarchy and validation discipline.
