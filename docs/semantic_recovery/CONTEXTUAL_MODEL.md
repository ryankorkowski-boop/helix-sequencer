# Contextual model: review-only after failed actual-language gates

The pinned local cross-encoder/nli-deberta-v3-small at revision
fa2804872c3b4bd748f38c0185cc85775361e735 supplies review candidates only.
It cannot change production concepts, emotion, motifs or visual direction.

Actual run [39162615351](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39162615351)
missed a contextual relationship metaphor (focus .635; context .644, below .80)
and proposed unsupported fear/travel for ordinary snow and reconciliation text.
Six of seven narrowly checked target cases passed, but that score hid false
positive concepts. This is an unsuitable production semantic model at present.
The fixture tool now checks specified unsupported concepts as well as the target
and separately asserts that review candidates leave production direction exact.
The capability gate must remain failed until the underlying problem is solved.

Experimental [context videos](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39161979412)
passed native export/timing checks but are **rejected semantic proofs**.
Their extra effects are not verified artistic improvements. New review-only
comparisons must equal conservative source direction; probabilities are retained
for diagnosis, without interpreting their magnitude as calibrated lyric accuracy.

HELIX_SEMANTIC_NLI=1 enables this review metadata. It requires
requirements-contextual.txt plus CPU PyTorch. Missing dependencies preserve rules.
Pinned safetensors, trust_remote_code=False, local inference and disabled runtime
telemetry remain in force. No lyric text is sent to a hosted inference API.
No model weights are redistributed.

The production rule path still supports scoped negation, selected idiom
abstention, confidence-weighted emotion, repeated motifs and changing context.
It does not provide arbitrary metaphor, irony or human-level narrative inference.
The existing intent graph, instrument clocks, palette and native compiler remain.

The spectrogram optimization separately hoists an unchanged global maximum out
of the pitch frame loop. Known note clocks and pitches plus a linear scan-budget
regression test cover this exact transformation.

Sources:
- https://huggingface.co/cross-encoder/nli-deberta-v3-small
- https://huggingface.co/cross-encoder/nli-deberta-v3-small/resolve/main/config.json

Independent singing annotations, broader semantic calibration, full-band acting,
richer spatial effects, native LMS/device acceptance and visual review remain open.
