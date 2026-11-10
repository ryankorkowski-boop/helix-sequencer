# Helixville4 Visual Reference Manifest

This manifest records approved visual targets for the Helixville4 snowman band.

The source images/GIFs were generated during design review and are treated as visual specification references for future xLights custom model/export work.

## Approved References

### Drummer

- Status: approved visual target
- Spec: docs/HELIXVILLE4_DRUMMER_TARGET.md
- Motion target: neon LED drummer with full drum kit, 23+ submodels, kick/snare/tom/cymbal/stick animation states

### Bassist

- Status: approved reactive-string direction
- Spec: docs/HELIXVILLE4_BASSIST_REACTIVE_STRINGS.md
- Motion target: standup/upright bass with individual E/A/D/G string pulses, traveling note energy, left-hand neck tracking, pluck-zone impact, and bridge/body resonance

### Guitarist

- Status: approved reactive-string direction
- Spec: docs/HELIXVILLE4_GUITARIST_REACTIVE_STRINGS.md
- Motion target: electric guitar with strum sweeps, chord energy, neck slides, pick attack flashes, pickup/bridge pulses, and sustain shimmer

### Lead Singer

- Status: approved visual target
- Spec: docs/HELIXVILLE4_SINGER_VOCAL_PERFORMANCE.md
- Motion target: expressive lead vocalist with microphone, phoneme/mouth states, vocal glow, hand gestures, body sway, and lyric-reactive performance states

### Female Singer

- Status: pending visual target
- Motion target: harmony/call-response vocalist with bow/hair detail, microphone, harmony glow, expressive hand gestures, and complementary lead-singer interaction states

## Repository Rule

Future layout/export work should not claim a band member is finished unless:

1. The visual target is recorded here.
2. A dedicated spec exists in docs/.
3. The generated xLights XML includes a real custom model with non-placeholder dimensions.
4. Named submodels exist for the performance zones described by the spec.
5. Tests guard against placeholder/stick-figure regression.
