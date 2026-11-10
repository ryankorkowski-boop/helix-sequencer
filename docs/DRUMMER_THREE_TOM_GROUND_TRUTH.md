# Drummer Ground Truth — Three Tom Canonical

**Status: authoritative**

This document resolves the drummer-spec conflict that accumulated across older V3 assets.

## Canonical physical kit

The snowman drummer has exactly:

- Kick
- Snare + contacting stick geometry
- Hi-hat + contacting stick geometry
- **High Tom + contacting stick geometry**
- **Mid Tom + contacting stick geometry**
- **Floor Tom + contacting stick geometry**
- Left cymbal + contacting stick geometry
- Right cymbal + contacting stick geometry

There is **no fourth tom**.

## Sequencing contract

There are exactly **8 sequenced components**:

`KICK`, `SNARE`, `HI_HAT`, `TOM_HIGH`, `TOM_MID`, `TOM_FLOOR`, `CYMBAL_LEFT`, `CYMBAL_RIGHT`.

Sticks and arms are visual geometry only. They are never independent sequencing targets.

A hit event is one physical component event. For example, a snare hit illuminates the snare and the contacting stick at the same timestamp; it does not emit a separate stick event.

## Historical evidence

The repository's older deterministic ground-truth audio generator already encoded the intended three-tom musical vocabulary as `tom_low`, `tom_mid`, and `tom_high`. That is consistent with the current High/Mid/Floor contract. The later four-tom V3 pose specification was a geometry/spec drift and is explicitly superseded by this document.

The known-good drummer behavior commit remains the regression oracle for timing/behavior, but its historical V3 physical naming must not be interpreted as permission to add a fourth tom.

## Implementation rule

Any future agent touching drummer code must:

1. Read this document and `docs/DRUMMER_COMPONENT_CONTRACT.md` first.
2. Preserve simultaneous events.
3. Never introduce `TOM_4`.
4. Never introduce independent stick or arm sequencing targets.
5. Validate High/Mid/Floor mapping with explicit tests before accepting a render.
