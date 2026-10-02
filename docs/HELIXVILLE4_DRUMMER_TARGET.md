# Helixville4 Snowman Drummer Target

## Goal

The production Helixville4 drummer must match the approved snowman drummer visual reference and behave like a physically readable drummer rather than a generic light bank.

## Approved Physical Kit

The kit has exactly:

- one kick
- one snare
- three toms: left, right, and floor
- one hi-hat
- left and right crash cymbals

There is **no fourth tom** and no extra far-right drum.

## Contact / Motion Rules

- **Kick:** drum lighting only; no stick.
- **Hi-hat:** hi-hat plus foot/pedal action; no stick contacts the hi-hat.
- **Snare:** the struck snare includes the appropriate arm/stick contact.
- **Left/right/floor toms:** each tom hit includes the appropriate arm/stick contact.
- **Left/right crash:** each crash includes the appropriate arm/stick contact.
- Arms, sticks, and the hi-hat pedal remain geometry/submodels, but they are not independent sequencing channels.

## Production Sequencing Targets

Helix sequences exactly eight physical hit composites:

- HX_SNOWMAN_DRUMMER_HIT_KICK
- HX_SNOWMAN_DRUMMER_HIT_SNARE
- HX_SNOWMAN_DRUMMER_HIT_HI_HAT
- HX_SNOWMAN_DRUMMER_HIT_TOM_LEFT
- HX_SNOWMAN_DRUMMER_HIT_TOM_RIGHT
- HX_SNOWMAN_DRUMMER_HIT_TOM_FLOOR
- HX_SNOWMAN_DRUMMER_HIT_CYMBAL_LEFT
- HX_SNOWMAN_DRUMMER_HIT_CYMBAL_RIGHT

Generic detected tom hits rotate deterministically left -> right -> floor. Generic cymbal hits alternate left -> right.

## Visual Requirements

- Use the approved drummer background/reference artwork as the visual baseline.
- Preserve a large readable snowman silhouette and stage platform.
- Keep each drum/cymbal visually distinct.
- Only the physically active component/contact motion should light for an ordinary hit.
- Avoid whole-kit illumination except an explicitly authored special accent.
- Preview rendering must visibly show the floor tom and the hi-hat pedal action.

## Audio Integration

The production mapping consumes the stem-aware drum detector:

**audio -> cached htdemucs_6s -> isolated drums -> fused transient evidence -> drum family events -> physical hit composites -> XSQ**

The physical model contract is independent of detector tuning; audio changes must not reintroduce a fourth tom or a stick-driven hi-hat.

## Validation Requirements

Tests should fail if:

- a fourth tom appears;
- the floor tom disappears;
- the hi-hat composite contains a stick;
- the kick composite contains a stick;
- snare/tom/cymbal composites lose their arm/stick contact geometry;
- the production XSQ emits noncanonical drummer hit targets;
- the drummer regresses to placeholder geometry.
