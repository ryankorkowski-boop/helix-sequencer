# Helix Legacy AC

Clean-room starter engine for the GP/Greg-style 256-channel legacy AC layout.

Goal:

```text
input audio/timing plan -> legacy 256-channel effect plan -> xLights-friendly XSQ skeleton
```

This package is intentionally isolated from the larger Helix research code so it can later be moved into a new repo such as `helix-legacy-ac`.

## Current scope

- Deterministic 256-channel legacy model registry.
- Named model groups for canes, arches, snowflakes, stars, megatree, rooflines, boulevard, garage trees, and line trees.
- Candy-cane note mapping for the player-piano idea.
- Simple beat-plan generator that emits ON/OFF AC-safe effect events.
- Minimal XSQ XML writer skeleton for quick testing.
- Tests that prove channel uniqueness, 256-channel bounds, note mapping, and deterministic output.

## Run

```bash
python -m legacy_ac.generate_legacy_ac --output outputs/legacy_ac_demo.xsq
```

## Test

```bash
python -m pytest tests/test_legacy_ac.py -q
```

## Design rule

This module should stay boring, predictable, and power-safe. No learning engine, no repo-wide side effects, no vendor-sequence copying. The first milestone is reliable structure and timing placement, not flashy output.
