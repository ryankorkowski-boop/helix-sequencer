# Helixville4 Snowman Drummer Target

## Goal

Replace the current Helixville4 placeholder/stick-figure drummer implementation with a fully realized xLights-ready snowman drummer model based on the approved infographic concept frames.

This document is now the authoritative visual direction for the Helixville4 drummer.

## Required Visual Features

- Large readable snowman silhouette
- Full drum kit
- Animated drum sticks
- Distinct cymbal zones
- Kick/snare/tom separation
- Neon-style LED outline readability
- Strong front-view readability in xLights layout preview
- Stage platform/base
- Vendor-quality visual density

## Required Submodels

Minimum required exported xLights submodels:

- HX_SNOWMAN_DRUMMER_HEAD
- HX_SNOWMAN_DRUMMER_FACE
- HX_SNOWMAN_DRUMMER_HAT
- HX_SNOWMAN_DRUMMER_HAT_BAND
- HX_SNOWMAN_DRUMMER_SCARF
- HX_SNOWMAN_DRUMMER_TORSO
- HX_SNOWMAN_DRUMMER_BUTTONS
- HX_SNOWMAN_DRUMMER_LEFT_ARM
- HX_SNOWMAN_DRUMMER_RIGHT_ARM
- HX_SNOWMAN_DRUMMER_LEFT_STICK
- HX_SNOWMAN_DRUMMER_RIGHT_STICK
- HX_SNOWMAN_DRUMMER_KICK
- HX_SNOWMAN_DRUMMER_KICK_RIM
- HX_SNOWMAN_DRUMMER_SNARE
- HX_SNOWMAN_DRUMMER_SNARE_RIM
- HX_SNOWMAN_DRUMMER_TOM_LEFT
- HX_SNOWMAN_DRUMMER_TOM_RIGHT
- HX_SNOWMAN_DRUMMER_HI_HAT
- HX_SNOWMAN_DRUMMER_CYMBAL_LEFT
- HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT
- HX_SNOWMAN_DRUMMER_STANDS
- HX_SNOWMAN_DRUMMER_PLATFORM

## Animation Targets

Required animation states:

1. Idle/ready
2. Kick hit
3. Snare hit
4. Hi-hat pulse
5. Tom fill
6. Cymbal crash
7. Stick accent
8. Both arms up
9. Downbeat impact

## Integration Requirements

The current implementation path in tools/build_helpers/helixia.py uses placeholder custom models and placeholder submodel ranges.

The replacement implementation must:

- Export real custom model geometry
- Export real xLights submodels
- Remove placeholder line0="1-4" usage
- Use actual geometry/node segmentation
- Preserve readable layout positioning in 3D
- Support future Helix sequencing automation

## Validation Requirements

Tests should fail if:

- The drummer regresses to a placeholder/stick figure
- The exported model dimensions are tiny placeholder dimensions
- Fewer than 16 real submodels are exported
- Cymbal/kick/snare zones disappear
- Animation zones collapse into shared node ranges

## Notes

The infographic concept approved by the user is considered the visual target baseline for the Helixville4 drummer implementation.
