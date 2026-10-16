# Structural quality benchmark

These XSQ, layout, and feature fixtures are original Helix test data. There is
no sampled audio, external sequence, or imitation of a show. The fixture uses
the saved-XSQ EffectDB/palette reference form. Its features are synthetic inputs
for testing metric arithmetic, not evidence of real-song detection accuracy.

Two physical props have declared channel weights 1 and 3. Nested groups include
a duplicated member to test union coverage. Effects include an On ramp,
repetition, a shared boundary, a group accent, an Off interval, and intentional
restraint covering only part of a dark interval.

`expected_quality.json` locks deterministic metric output. Its ideal energy
correlation is constructed for arithmetic verification; it is not a musical
quality claim. No fixture here has a native xLights import/render approval.
