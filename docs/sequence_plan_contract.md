# Sequence Plan Contract

Status: Slice 1 contract  
Behavior change: none  
Purpose: define the intermediate planning target between audio analysis and effect rendering

## Concept

Helix output quality improves when the engine plans the show before rendering effects. The sequence plan is a source-agnostic, legal-safe summary of musical structure, desired intensity, prop emphasis, color intent, and restraint rules.

This contract does not replace the current renderer. It gives `core.sequence_builder` / `core.effect_engine` a future data shape to consume or emit incrementally.

## Minimal Shape

```json
{
  "version": "0.1",
  "source_audio": "LightsOutTheme.mp3",
  "fps": 40,
  "duration_seconds": 180.0,
  "style": "showcase",
  "sections": [],
  "prop_groups": [],
  "restraint": {},
  "cues": [],
  "scoring_targets": {}
}
```

## Fields

### `version`

Contract version. Start with `0.1` until the renderer consumes it.

### `source_audio`

Display name or relative path for the analyzed audio. This is metadata only. Do not store copyrighted audio content inside the plan.

### `fps`

Target frame rate for preview/render scheduling.

### `duration_seconds`

Known or estimated sequence duration.

### `style`

High-level output style or quality mode. Examples: `general`, `showcase`, `vendor`, `classic_christmas`, `edm`, `rock`, `ballad`, `comedy`.

### `sections`

Ordered musical regions. Sections are the backbone of contrast and restraint.

```json
{
  "name": "chorus_1",
  "kind": "chorus",
  "start": 45.0,
  "end": 72.0,
  "target_intensity": 0.88,
  "primary_groups": ["mega_tree", "roofline"],
  "secondary_groups": ["arches", "mini_trees"],
  "palette": "classic_christmas_bright",
  "motion_intent": "wide_sweeps_and_spirals",
  "density": "high"
}
```

Recommended `kind` values:

- `intro`
- `verse`
- `pre_chorus`
- `chorus`
- `bridge`
- `solo`
- `breakdown`
- `drop`
- `finale`
- `outro`
- `unknown`

### `prop_groups`

Advisory layout groups and roles. This can be generated from model names or user configuration.

```json
{
  "name": "snowman_band",
  "role": "character",
  "members": ["snowman_singer", "snowman_drummer", "snowman_guitarist", "snowman_bassist"],
  "best_for": ["vocals", "percussion_hits", "call_and_response"],
  "energy_capacity": "medium"
}
```

Recommended `role` values:

- `centerpiece`
- `outline`
- `accent`
- `character`
- `singer`
- `percussion`
- `background`
- `foreground`
- `strobe`
- `fill`

### `restraint`

Rules that keep the render from becoming cluttered.

```json
{
  "max_whole_house_hits_per_section": 4,
  "min_seconds_between_major_hits": 2.0,
  "max_simultaneous_dominant_groups": 3,
  "allow_strobe": true,
  "strobe_requires_intensity_at_least": 0.85,
  "protect_manual_effects": true
}
```

### `cues`

Optional explicit timing events. Cues should be sparse at first. The renderer can fill around them.

```json
{
  "time": 72.5,
  "kind": "section_peak",
  "confidence": 0.92,
  "target_groups": ["whole_layout"],
  "effect_family": "burst",
  "intensity": 0.95,
  "locked": false,
  "source": "planner"
}
```

Recommended `kind` values:

- `beat`
- `downbeat`
- `vocal_entry`
- `drum_hit`
- `section_start`
- `section_peak`
- `transition`
- `silence`
- `manual_lock`

### `scoring_targets`

Targets for explainable candidate selection.

```json
{
  "timing_alignment_min": 0.9,
  "section_contrast_min": 0.75,
  "palette_consistency_min": 0.8,
  "density_penalty_max": 0.2,
  "prop_coverage_min": 0.7,
  "finale_strength_min": 0.85
}
```

## Legal-Safe Use

The sequence plan may store Helix decisions, measured structure, generated score metrics, and generated sequence context. It must not store copied choreography from third-party/vendor sequences or persistently learn from unapproved source material.

## Slice 1 Acceptance

This file is accepted when:

1. The contract documents a minimal sequence plan shape.
2. A sample JSON file exists.
3. Existing render commands do not need to change.
