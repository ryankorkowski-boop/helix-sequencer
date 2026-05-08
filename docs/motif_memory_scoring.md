# Motif Memory Scoring

Status: Slice 6 advisory helper  
Behavior change: none unless a caller explicitly imports and uses it

## Purpose

A professional sequence should feel composed. Visual ideas should return when the music returns, especially in repeated choruses, drops, refrains, and major hooks. Without motif memory, auto-sequencing can feel like unrelated effects stitched together.

`tools/build_helpers/motif_memory.py` provides advisory scoring for motif reuse, variation, coverage, and overfragmentation.

## What It Measures

Current report scores:

- `coverage_score`: whether motifs include useful section kind, effect family, and prop group data
- `identity_reuse_score`: whether repeated section kinds reuse recognizable visual identity
- `variation_score`: whether repeated motifs evolve instead of copy/pasting exactly
- `overfragmentation_score`: whether the plan avoids too many unrelated one-off motifs
- `score`: weighted combined advisory score

## Motif Identity

A motif identity is estimated from:

- effect/motif family
- palette
- primary prop group
- intensity range

Examples:

- chorus spiral on mega tree
- roofline sweep for verses
- snowman singer vocal motif
- drummer/percussion hit motif
- finale cascade motif

## Motif Families

Initial motif family names include:

- `spiral`
- `sweep`
- `pulse`
- `burst`
- `shimmer`
- `sparkle`
- `strobe`
- `wash`
- `chase`
- `vocal`
- `percussion`
- `call_response`
- `finale_cascade`

These are advisory names only. They do not create or render effects by themselves.

## What It Flags

Current findings include:

- no motifs provided
- motif missing section kind
- motif missing family
- motif missing groups
- no recurring motif sections
- weak motif reuse for repeated section kinds
- repeated motif without enough variation
- motif overfragmentation

## Why This Improves Output

Motif memory helps Helix reward:

- choruses that visually relate to each other
- drops that reuse a recognizable high-energy idea
- verses that keep supporting motion consistent
- finales that expand prior motifs instead of appearing from nowhere
- repeated ideas with tasteful variation

The target is not exact repetition. The target is recognizable identity plus growth.

## Example

```python
from tools.build_helpers.motif_memory import score_motif_memory

report = score_motif_memory([
    {
        "name": "chorus_spiral_1",
        "section": "chorus_1",
        "section_kind": "chorus",
        "family": "spiral",
        "palette": "classic_christmas_bright",
        "primary_groups": ["mega_tree"],
        "intensity_range": [0.72, 0.88],
        "variation": "base",
    },
    {
        "name": "chorus_spiral_2",
        "section": "chorus_2",
        "section_kind": "chorus",
        "family": "spiral",
        "palette": "classic_christmas_bright",
        "primary_groups": ["mega_tree", "roofline"],
        "intensity_range": [0.82, 0.96],
        "variation": "expanded",
    },
])

print(report.as_dict())
```

## Report Shape

```json
{
  "motif_count": 2,
  "recurring_section_kind_count": 1,
  "identity_reuse_score": 0.75,
  "variation_score": 0.9,
  "coverage_score": 1.0,
  "overfragmentation_score": 0.65,
  "score": 0.8,
  "findings": []
}
```

## Important Boundary

This module does not:

- render effects
- write XSQ data
- mutate layout files
- create motif effects
- replace `core.effect_engine.py`
- change current output by default
- promote or reject variants by itself

It only reports motif-memory quality for future scoring and explainability.

## Intended Future Use

Near-term integrations:

1. Run motif scoring against generated or inferred `sequence_plan` motif data.
2. Add the report to sequence quality artifacts.
3. Include motif reuse and overfragmentation in shortlist explainability.
4. Let `showcase` and `vendor` presets reward recurring visual identity.
5. Later, allow the planner to reuse motif families when repeated sections are detected.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_motif_memory.py
```

Recommended combined validation for Slices 2-6:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py
```

## Future Wiring Rule

When this gets wired into the active engine, it should appear in reports first. Only after reports are stable should it influence planning, shortlist scoring, or generated motif reuse.
