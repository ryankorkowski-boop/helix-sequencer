# CTB16PC drummer and chorus export

This optional physical kit uses ten drum circuits and six backing-vocal mouth
poses on one 16-output controller. It is separate from the existing twelve-string
drummer with two idle arm circuits. Do not interchange their wiring maps.

Run from the repository root:

```bash
python -m tools.export_ctb16pc_sequence cues.json --source-lms my-controller.lms --unit-id 0A --output new-kit-export
```

Supply the actual controller Unit ID in two-digit hexadecimal. The source LMS
must contain exactly that controller's sixteen distinct circuits. The exporter
uses their original channel identities and track references, leaves the source
untouched, and requires a new output directory.

Example classified cue input (seconds, velocity from zero to one):

```json
{
  "duration": 3,
  "audio_filename": "my-song.wav",
  "hits": [
    {"time": 0.2, "target": "kick", "velocity": 0.9},
    {"time": 0.4, "target": "snare", "side": "left"},
    {"time": 1, "target": "cymbal_right", "tail_fps": 40,
     "tail_amplitudes": [1, 0.8, 0.6, 0.3, 0.1, 0]}
  ],
  "vocals": [
    {"start": 1, "end": 1.2, "phoneme": "AH", "chorus": true, "vocal_layers": 2},
    {"start": 1.2, "end": 1.4, "phoneme": "OH", "vocal_layers": 3}
  ]
}
```

Accepted drum targets: kick, snare with explicit left/right hand, hi_hat/hihat,
tom_high, tom_mid, tom_floor/tom_low, cymbal_left and cymbal_right. The existing
HX_SNOWMAN_DRUMMER_V3_HIT_ prefix is accepted. Unknown/ambiguous hits are rejected.
The detector's unresolved bus/tom events must be reviewed before this export.

The mouth poses are AH, EE, OH, MBP, FV and L. REST/silence leaves all six off.
Mouths activate only on an explicit chorus or more than two confirmed vocal
layers. These inputs must come from observed analysis; the exporter does not
separate voices or infer a chorus from a mixed recording. Contradictory overlapping
mouth poses fail. A 10 ms grid preserves the supplied rapid hits with a release
gap; repeated contacts below 20 ms fail because distinct flashes cannot be
represented at this resolution.

Cymbals spike at their accepted attack and follow the supplied measured cymbal
tail. Without a measured tail, the output is a short contact flash. Supply only
accepted cymbal-specific energy, not broadband song loudness. Sample rates below
16 Hz cannot represent the default 8 Hz shimmer. No song audio is copied.

The new folder contains the editable legacy LMS, matching intensity XSQ,
synthetic channel-grid layout, actual wiring CSV, source/cue hashes, export
reports, and the shared front-view construction contract for flat and dimensional
builds. Depth and bucket shells do not change its front positions or addresses.
The historical five outlines plus one mallet-player asset are also integrated
for front-projection planning. These construction contracts are not surveyed
fabrication geometry or hardware proof.

Automated acceptance checks compare every centisecond in the reimported LMS
against the compiled intensity timeline, retain all original addresses, and
compare actual xLights FSEQ output with all 4,800 diagnostic intensity values.
The native diagnostic uses synthetic cues/audio and cannot establish original-song
recognition. Licensed LOR application import, controller load/dimming behavior,
physical build parity and listening remain separate acceptance gates. Modern
LOREDIT output is not supported by this exporter.
