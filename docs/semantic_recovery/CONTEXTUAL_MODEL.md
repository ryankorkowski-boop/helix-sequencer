# Contextual interpretation expansion — development only

The first Wires in the Garland native comparison passed timing/export checks but
contained only one rule-derived imagery intent. That fails the requested visual
storytelling coverage. A first technical MP4 is not artistic completion.

An optional local NLI provider now evaluates complete lyric passages and their
neighbouring context using the pinned cross-encoder/nli-deberta-v3-small model,
revision fa2804872c3b4bd748f38c0185cc85775361e735. It does not generate lyrics.
A concept requires independent support in the focus passage and in context;
neighbour-only imagery is rejected. Contradiction/neutral scores, emotion
disagreement and possible irony lower confidence or cause abstention.

The existing intent graph, motion vocabulary, palettes, native compiler, musical
events and whole-song motif state remain active. Contextual inference can
identify non-literal relationship/hope/conflict themes without an isolated word
match. Every interpretation remains a model hypothesis. Model probabilities
are not calibrated on lyrics, metaphor, humour or sarcasm; no accuracy claim.

A high-confidence contextual emotion can drive a restrained emotional-transition
cue when literal imagery is unsupported. This expands emotion/palette direction
without inventing a physical story object. Repeated motifs and changing valence
still retain their source clocks and development state.

Set HELIX_SEMANTIC_NLI=1 and install requirements-contextual.txt plus CPU PyTorch.
Absent dependencies/model files fail back to the recovered rule path. Downloads
use pinned safetensors and trust_remote_code=False. Inference is local; no lyric
text is sent to a hosted inference API. ONNX/Hugging Face telemetry is disabled
before initialization. The optional model is Apache-2.0 according to its model
card and is not redistributed in Helix binaries.

The context-proof workflow reuses the already source-verified musical baseline,
original decoded audio and transcript from run 39160681079. It re-renders actual
native FSEQ and comparisons, comparing channel values outside explicit scenery.
It does not repeat source separation or invent a new instrument performance.

A separate performance repair hoists the invariant full-spectrogram pitch
maximum out of the frame loop. The denominator is exactly unchanged; the fixture
checks known note onsets, durations, pitches and one whole-matrix normalization
scan. Existing older native comparison outputs retain their original commit
provenance. The '[semantic-context-stage]' commit marker runs the revised tests
and dedicated contextual proof instead of restarting the full eight-song baseline
matrix. This is a scoped development validation choice, not a release waiver.

Primary model/config sources:
- https://huggingface.co/cross-encoder/nli-deberta-v3-small
- https://huggingface.co/cross-encoder/nli-deberta-v3-small/resolve/main/config.json

Pending: actual-model inference results, semantic coverage/artistic review,
independent word/phone annotations, full-band acting, model-wide visemes, native
LMS/device gates and direct YouTube viewing. No release approval is inferred.
