# Drummer V3 audio analysis

Active detector: `audio/drummer_v3.py`, `v3_historical_hpss_onset_classifier`.
The user rejected #217's conservative detector. That implementation is archived
in `audio/archive/drummer_v3_rejected_217.py` and can be replayed by
`tools/audit_rejected_drummer_217.py` for forensic comparison.

The active path restores b27e8d77's native-rate mixed-song analysis, HPSS margin
1, 2048 FFT / 512 hop, onset delta .045 / wait 1, original overlapping bands,
original attack/tail decay features, and one principal family per onset. The
original transient grid is retained. Full-mix waveform attack relocation and
whole-song short/context consensus vetoes have been removed.

A harmonic-dominated candidate (percussive RMS fraction below .16), ambiguous
bus, clear literal waveform cutoff, or unresolved tom pitch does not emit.
An opening strong body candidate (.40 percussive fraction) supported by another
typed transient establishes a generic entrance, with an 80 ms preroll for coincident opening metal, and no song timestamp. After
that entrance, quieter onsets remain eligible. No beat can create a hit.

The historical kick band overlapped tom bodies. Clear 160–700 Hz body dominance
with almost no metal and a low-band centroid above 185 Hz resolves that overlap
as tom. A tom's post-attack source resonance above the preceding background supplies relative HIGH/MID/FLOOR
identity; HPSS attenuates sustained tom partials, so its residual alone is not a
reliable pitch estimate. Diffuse resonance or a sub-110 Hz body abstains.
This heuristic does not establish the actual kit's tuning. Unknown toms never
cycle. Cymbal-side alternation remains a deterministic physical convention,
not evidence that a recording's left/right cymbal can be identified in mono.

Each candidate carries its frame/index, spectral evidence, quality, principal
family, rejection reason, and downstream scheduler/target decision in the XSQ
report. The scheduler keeps the historical 24 ms merge / 70 ms clutter / four
hits / repeat-attenuation policy. Simultaneous independently supplied events
can coexist; the historical detector itself emits one family per onset.

The exact eight targets, source artwork, dim body keepalive, strike overlap,
three-tom geometry, no kick/hat sticks, and 32% supporting pedal are preserved.
Signal-inspected sparse anchors are provisional and explicitly await human
listening. Neither this benchmark, synthetic tests, historical event agreement,
nor CI establishes musical correctness. User MP4 approval remains open.
