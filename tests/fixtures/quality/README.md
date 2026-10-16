# Structural quality benchmark

These XSQ, layout, and feature fixtures are original Helix test data. There is
no sampled audio, external sequence, or imitation of a show. The fixture uses
the saved-XSQ EffectDB/palette reference form. Its features are synthetic inputs
for testing metric arithmetic, not evidence of real-song detection accuracy.

Two physical props have declared channel weights 1 and 3. Nested groups include
a duplicated member to test union coverage. Effects include an On ramp,
repetition, a shared boundary, a group accent, a zero-intensity On interval, and intentional
restraint covering only part of a dark interval.

`expected_quality.json` locks deterministic metric output. Its ideal energy
correlation is constructed for arithmetic verification; it is not a musical
quality claim. The native fixture includes fixed-point millisecond timing,
DisplayElements, model geometry and channel starts. The one-channel red arch
and three-channel RGB star intentionally exercise different color routing.

Native xLights 2026.18 produced 80 frames at 50 ms. Inspection found 78 nonzero
channel samples, 49 nonzero frames, and lit fraction .24375. The structural
estimate is .4375 because effect presence is not the same as per-channel color
routing, and native ramp endpoints are quantized. `quality-native-check.yml`
repeats the native render and checks actual ramp/accent/rest channel bytes.
No human visual review or physical controller approval is claimed.
