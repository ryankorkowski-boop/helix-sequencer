# Helixville4 Snowman Female Singer Vocal Performance Spec

## Goal

Upgrade the Helixville4 female singer from a static harmony vocalist placeholder into an expressive harmony/call-response performer with lyric-reactive mouth, bow detail, microphone interaction, hand gestures, body sway, and harmony glow.

The female singer should visually communicate harmony phrase starts, phoneme movement, emotional moments, call-and-response gestures, chorus/belt moments, sustained harmony notes, and complementary interaction with the lead singer.

## Approved Visual Direction

The approved sheet shows a female snowman singer with a bow, scarf, scarf tails, vintage microphone and mic stand, open-mouth vocal states, eyelash/expression states, hand raise, point-out, hand-to-heart, both-hands-up, and soft/normal/power/harmony/call-response states.

## Required Submodels

- HX_SNOWMAN_SINGER_FEMALE_HEAD
- HX_SNOWMAN_SINGER_FEMALE_FACE
- HX_SNOWMAN_SINGER_FEMALE_EYES
- HX_SNOWMAN_SINGER_FEMALE_EYELASHES
- HX_SNOWMAN_SINGER_FEMALE_CARROT_NOSE
- HX_SNOWMAN_SINGER_FEMALE_MOUTH
- HX_SNOWMAN_SINGER_FEMALE_BOW
- HX_SNOWMAN_SINGER_FEMALE_SCARF
- HX_SNOWMAN_SINGER_FEMALE_SCARF_TAIL_LEFT
- HX_SNOWMAN_SINGER_FEMALE_SCARF_TAIL_RIGHT
- HX_SNOWMAN_SINGER_FEMALE_MIC_STAND
- HX_SNOWMAN_SINGER_FEMALE_MICROPHONE
- HX_SNOWMAN_SINGER_FEMALE_TORSO_UPPER
- HX_SNOWMAN_SINGER_FEMALE_TORSO_LOWER
- HX_SNOWMAN_SINGER_FEMALE_LEFT_ARM
- HX_SNOWMAN_SINGER_FEMALE_RIGHT_ARM
- HX_SNOWMAN_SINGER_FEMALE_LEFT_HAND
- HX_SNOWMAN_SINGER_FEMALE_RIGHT_HAND
- HX_SNOWMAN_SINGER_FEMALE_BUTTONS
- HX_SNOWMAN_SINGER_FEMALE_PLATFORM
- HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW
- HX_SNOWMAN_SINGER_FEMALE_STAGE_GLOW

## Required Performance States

1. READY_IDLE
2. SING_START
3. HAND_RAISE
4. POINT_OUT
5. EMOTE_CLOSE
6. HEART_FEEL
7. SWAY_GROOVE
8. BIG_VOCAL
9. BOTH_HANDS_UP
10. HIT_HOLD

## Required Vocal Style States

- SOFT_WHISPER
- NORMAL_SING
- POWER_BELT
- HARMONY_OOH
- CALL_RESPONSE

## Reactive Animation Behaviors

### Harmony Phrase Start

At harmony phrase starts, the microphone, mouth, and vocal glow should pulse together.

### Phoneme / Mouth Animation

Mouth regions should support closed/rest, small open, wide open, rounded/ooh, and smile/hold.

### Harmony Glow

Harmony passages should use HX_SNOWMAN_SINGER_FEMALE_VOCAL_GLOW with softer sustained shimmer than the lead singer.

### Call and Response

Call-response lyrics should use point-out, hand raise, and head-turn style states, alternating with lead singer states.

### Emotional Emphasis

Emotional lyric moments should use hand-to-heart, closed-eye/eyelash emphasis, and scarf/body glow.

### Big Vocal / Chorus

High-intensity vocal moments should trigger wide mouth, both-hands-up, mic glow, vocal glow, and stage glow.

## Helix Mapping Concepts

- harmony onset -> microphone + mouth + vocal glow pulse
- syllable timing -> mouth state changes
- sustained vowel -> harmony shimmer
- call/response phrase -> gesture state and stage glow
- chorus intensity -> big vocal state
- emotional lyric -> heart feel / eyes close / softer glow

## Implementation Requirements

The finished exporter must create a real xLights custom model with non-placeholder dimensions, export all required submodels, include mouth and harmony glow regions, include microphone and mic stand regions, preserve readable stage placement, and include regression tests against placeholder/stick-figure output.

## Validation Requirements

Tests should fail if HX_SNOWMAN_SINGER_FEMALE is exported as a 12x12 placeholder, if mouth/microphone/vocal-glow/bow/scarf-tail regions are missing, if fewer than 18 submodels are exported, or if animation-state metadata is missing.

## Status

Specification accepted. Exporter implementation pending.
