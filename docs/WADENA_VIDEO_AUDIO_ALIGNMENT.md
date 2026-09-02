# Wadena Direct-Video Audio/Visual Alignment Calibration

Date: 2026-09-02

## Source

Direct camera recording supplied by the project owner:

- `XRecorder_20260901_06.mp4`
- measured video: 230.514 s / 7,186 frames / 31.174 fps
- embedded audio: mono AAC, 44.1 kHz; extracted to 22.05 kHz WAV for analysis

This is the first calibration pass using the actual recording rather than a YouTube page. It therefore provides frame-addressable visual evidence.

## Visual analysis

A 2-second frame-state scan produced the following strongest visual state-change candidates:

`8.0, 32.0, 38.0, 58.0, 80.0, 98.0, 110.0, 154.0, 162.0, 220.0, 226.0 s`

These are computer-detected visual transitions, not claims about individual LOR channel changes. They should be used as candidate section boundaries for human/automated frame inspection.

A previous 0.5-second calibration scan also identified broad changes around 37-38 s, 56-60 s, 78-85 s, 154-162 s, and 224-225 s.

## Audio analysis

The embedded audio was extracted and onset strength was computed. The first strong onset candidates include:

`0.25, 1.00, 1.75, 2.75, 3.50, 4.25, 5.00, 5.75, 7.25, 8.00, 8.75, 9.75, 10.50, 11.75, 13.75, 18.50, 19.75, 20.75, 21.75, 22.75, 24.00, 25.00, 31.25, 32.50, 33.50, 37.00, 39.75, 41.00, 41.75, 43.50, 44.50, 45.50, 46.75, 48.25, 49.25, 50.25, 51.00, 52.50, 54.00 s`

The fact that strong audio events occur near several visual transition candidates (for example ~8, ~32, ~37-38 s) supports using joint audio/visual alignment rather than treating visual transitions as arbitrary.

## Important limitation

The supplied professional Nutrocker LMS is 246.93 s on a 50 ms grid, while this direct recording is approximately 230.5 s. Do **not** time-stretch the video to the LMS duration. A synchronization offset/segment correspondence must first be established from shared musical landmarks.

## Engineering implication

The calibration pipeline should become:

```text
video frame state
      +
embedded audio onset / phrase state
      ↓
joint section candidates
      ↓
physical landmark choreography observations
      ↓
WadenaSpatialGraph gesture examples
      ↓
SpatialIntent calibration
      ↓
existing AC-safe effect engine
      ↓
XSQ + MP4 proof
```

The direct recording should be treated as behavioral calibration evidence, not as a source for copying exact channel programming. The goal is to learn spatial choreography habits: propagation, center-out expansion, perimeter traversal, sectional hero use, punctuation, and layered background activity.

## Next calibration pass

1. Inspect narrow frame windows around each joint audio/visual candidate.
2. Label the visible landmark(s) involved.
3. Classify the gesture: impulse, sweep, propagation, center-out, out-to-center, oscillation, expansion, contraction, or sustained field.
4. Measure approximate lead/lag between musical onset and visible response.
5. Only after those labels exist, correlate against the 246.93 s LMS reference where a defensible musical correspondence exists.
