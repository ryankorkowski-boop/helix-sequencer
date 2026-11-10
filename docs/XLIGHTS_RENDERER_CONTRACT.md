# xLights Renderer Contract

Status: Active implementation contract  
Scope: how Helix placement plans become xLights-renderable output safely

## 1. Purpose

Helix must not jump directly from high-level intent to final sequence XML without an inspectable contract.

The renderer contract exists to make the pipeline auditable:

```text
VisualIntent
→ PlacementCandidate
→ PropEffectIntent
→ PlacementValidationReport
→ PlacementQualityReport
→ RenderPermissionReport
→ xlights_effect_contract.json
→ future xLights sequence writer
```

The current implementation intentionally emits a JSON sidecar first. A true `.xsq` writer should only be added after the exact supported file shape is confirmed with safe sample files or official xLights behavior.

## 2. Contract File

The current sidecar is:

```text
xlights_effect_contract.json
```

Schema:

```text
helix.xlights_effect_contract.v1
```

The contract contains:

- render permission result
- supported render families
- skipped unsupported effect families
- deterministic effect placements

Each effect placement contains:

- `start_time`
- `end_time`
- `target_model`
- `effect_name`
- `render_style`
- `brightness_cap`
- `source_visual_intent_id`
- `source_effect_family`

## 3. Supported First-Pass Families

The first renderer pass supports only conservative, reviewable effect mappings:

| Helix effect family | xLights-style effect name | Purpose |
| --- | --- | --- |
| `soft_wash` | `Color Wash` | background/mood wash |
| `outline_pulse` | `On` | roofline/window/structure pulse |
| `energy_wave` | `Bars` | hero/energy movement |

Unsupported families are skipped and reported instead of guessed.

This is intentional. It avoids accidental nonsense output and preserves a safe escalation path.

## 4. Render Permission Rule

A renderer must not emit renderable output unless:

1. placement validation passes
2. placement quality score meets the configured threshold
3. render permission says `allowed: true`

Warnings may be allowed, but they must be carried forward into reports.

## 5. Required Safety Behavior

The renderer must:

- preserve target model names exactly
- preserve source visual intent IDs
- preserve effect family provenance
- respect brightness caps
- keep start/end times ordered
- skip unsupported effect families with a report
- avoid inventing target models
- avoid broad all-model rendering unless explicitly planned
- produce deterministic output for deterministic input

## 6. What The Contract Is Not

The current contract is not yet the final `.xsq` sequence writer.

It does not claim to be importable as a finished xLights sequence. It is the stable intermediate artifact that the future writer will consume.

## 7. True Writer Requirements

Before adding a true `.xsq` writer, the repo must have one of these:

1. a safe user-supplied sample `.xsq` with permission to inspect structure
2. a Helix-generated minimal sample confirmed in xLights
3. a tested writer/reader fixture for the exact XML shape being emitted

The writer must have tests proving:

- XML parses
- required root elements exist
- model/effect references match the layout
- timing order is stable
- unsupported effect families are skipped or mapped explicitly
- generated output round-trips through the repo parser or a fixture validator

## 8. Recommended Next Implementation Steps

1. Validate `xlights_effect_contract.json` before use.
2. Add CI tests for contract validity.
3. Add a minimal dry-run writer that produces a `helix_sequence_plan.xml` review artifact, not a final `.xsq`.
4. Confirm a safe `.xsq` sample structure.
5. Add the true writer behind a feature flag.
6. Only then allow real xLights sequence output.
