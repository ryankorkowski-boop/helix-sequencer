# Canonical Snowman Drummer Component Contract

## Purpose

This is the canonical sequencing contract for the Helix snowman drummer. It replaces the abandoned four-tom / stick-driven-hi-hat contract and keeps motion geometry inside physically meaningful hit composites.

## Eight sequenced hit composites

1. `HX_SNOWMAN_DRUMMER_HIT_KICK`
2. `HX_SNOWMAN_DRUMMER_HIT_SNARE`
3. `HX_SNOWMAN_DRUMMER_HIT_HI_HAT`
4. `HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT`
5. `HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT`
6. `HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR`
7. `HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT`
8. `HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT`

## Physical kit truth

- Exactly three toms: **left, right, floor**.
- No fourth tom and no extra far-right drum.
- Kick has **no stick**.
- Hi-hat is activated by **foot/pedal**, with **no stick contacting the hi-hat**.
- Snare, each tom, and each crash include the appropriate arm/stick contact geometry.
- Arms, sticks and pedal may exist as geometry submodels, but are never independent sequencing channels.

## Mapping behavior

- Generic tom detections rotate deterministically left -> right -> floor.
- Generic cymbal detections alternate left -> right.
- Compatible simultaneous hits remain simultaneous.
- Ambiguous `drum_bus` events must never be silently converted into duplicate raw-kick placements.
- Audio-detector tuning must not change the physical kit contract.

## Canonical implementation

Production truth is defined by:

- `mapping/drum_mapper.py`
- `tools/build_helpers/helixville4_full_band.py`
- `tools/render_drummer_v3_preview.py`
- `docs/HELIXVILLE4_DRUMMER_TARGET.md`
- `fixtures/band_geometry/drummer_v3_pose_spec.json`

The old checked-in `HX_SNOWMAN_DRUMMER_V3.xmodel` is a historical asset and is explicitly noncanonical.

## Acceptance criteria

A production drummer change is correct only if:

- emitted sequencing targets are a subset of the eight IDs above;
- the exported layout contains all eight composite submodels;
- kick composite contains no stick/arm contact;
- hi-hat composite contains pedal geometry and no stick;
- floor tom exists;
- no fourth tom exists;
- snare/tom/cymbal composites include contact arm/stick geometry;
- simultaneous hits remain simultaneous;
- a real-audio full-song XSQ and drummer MP4 are generated for visual validation.
