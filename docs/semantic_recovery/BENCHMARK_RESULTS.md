# Historical semantic recovery: measured development results

Status: **release not ready**. No branch was merged.

History coverage: 224 advertised branches, 125 PR heads, 158 preserved dangling
heads, 2,432 reachable commits and 2,924 unique source blobs searched by content.
See feature_provenance.json (56 modules), historical_inventory.csv and
history_audit.json. Nine requested modules have one distinct historical source
implementation; the helper CLI has six. Historical performance is not measured
merely because old tests or reports exist. Unadvertised, unreachable server
objects cannot be guaranteed recoverable.

## Full-song conservative native comparisons

[Run 39160681079](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079)
used recovery commit a5a9e29be577606548be847ce7b30b38edf8fc97 and immutable
production baseline 9522b19b660ebef537e195397e7e8ca6c64354bf.
Each original source passed its recorded SHA256 check. Native xLights 2026.18
was checksum-pinned. These are actual native FSEQ channel samples drawn at prop
coordinates, **not the xLights House Preview or a full-band performance**.

| Recording | Seconds | Accepted ASR words | Imagery intents / effects | Original audio correlation | Download |
|---|---:|---:|---:|---:|---|
| Bells of Mathmas | 155.96 | 0 | 0 / 0 | 0.999183 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12149196410) |
| Phoneme Test Hook | 34.88 | 38 | 0 / 0 | 0.999031 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12149220580) |
| Wires in the Garland | 214.96 | 87 | 1 / 2 | 0.999579 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12148203993) |
| Let It Glow | 199.00 | 27 | 0 / 0 | 0.998875 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12148373774) |
| Glass Under Skin | 294.72 | 0 | 0 / 0 | 0.998860 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12149685414) |
| Ghost In The Grid | 262.44 | 0 | 0 / 0 | 0.998882 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12149427250) |
| Festivus Remastered | 111.48 | 42 | 0 / 0 | 0.999004 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12148729161) |
| North Pole Overdrive | 238.20 | 0 | 0 / 0 | 0.999191 | [MP4 + XSQ + FSEQ](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39160681079/artifacts/12149074107) |

All eight MP4s fully decoded. All original XML effect layers and non-scenic native
channel samples matched exactly. Bells of Mathmas had zero words/cues and every
native sample matched exactly. Correlation is measured at zero lag; threshold .98.
For vocal rows the instrumental-only equality field is not applicable.

Total source duration: 25.19 minutes.
The seven zero-intent outputs show limited semantic recall. Abstention prevents
invented scenic interpretations but does not fulfill the requested visual-story
coverage. Zero accepted words in a recording does not prove it has no vocals.
ASR WER, phone boundary accuracy, singer identity and genre/mood labels are not
independently measured. Visual review is pending for every movie.

The linked Actions bundles contain full-song MP4, XSQ, FSEQ, layout, source-bound
analysis and QA evidence and expire October 25, 2026. After local execution
recovered, all eight archives passed their artifact digests and all eight MP4s
passed their recorded movie hashes. Each full-song MP4 and a combined native
sequence/provenance evidence ZIP were separately saved as direct deliverables.
Reports, source hashes and movie hashes are also preserved in this repository.

Sampled visual inspection covered three frames per recording (24 total), including
the Wires semantic cue at 74.9 seconds, plus its full-resolution frame. Real native
scenic pixels are visible, but composition is sparse and the difference is small.
No performers are depicted. This is insufficient artistic/storytelling evidence;
full-song visual and listening review remain open.

## Actual contextual model: rejected for production direction

Run [39162615351](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39162615351)
found unsupported fear/travel candidates and missed a contextual relationship
metaphor. See actual_language_failure.json. A narrow six-of-seven target score
was insufficient because it ignored those spurious concepts.
NLI is now review-only, with regressions requiring exact production direction,
emotion and motif preservation. The optional model cannot create visual cues.

Two earlier [experimental full-song contextual renders](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39161979412)
passed technical gates but are rejected semantic proofs. More effects are not
evidence of better understanding. Fresh quarantine-path native proofs both passed in
[run 39166061779](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39166061779),
commit e81471f4117cd9c988c91b5b4673c08ceb219dd8. The model evaluated 12 Wires
and eight Let It Glow passages but changed no production direction. Wires retained
one imagery intent/two effects; Let retained zero. Original layers, non-scenic
native samples, soundtrack correlation and complete decode gates passed.
These prove candidate isolation, not improved semantic recall.

The stricter actual-model run39166061721 passed only three of seven authored
capability cases, while all seven production-safety comparisons passed. It remains
a failed capability gate and must not be presented as calibrated lyric accuracy.

## Tests and remaining gates

At commit 7f2062074798bd59cadbf82430874864dbc67061, run 39161979246 passed
127 focused tests with one optional native-manifest skip. The earlier separate
instrument batch passed 39 tests with three absent real-fixture skips; these
counts overlap and must not be added as unique tests.
Final provider-confidence/quarantine regressions: **135 passed, one optional
native-manifest skip**, run [39165828231](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39165828231),
commit 9a462494c0c5f7319d6e757cdf42049ab8a965cf. One audioop deprecation warning.
These are focused regressions, not an entire-repository clean CI claim.

Open: independently labeled word/phone accuracy, source-separated harmony
identity, nontrivial metaphor/irony/narrative calibration, richer spatial
choreography, full-band semantic acting and native/device/LMS visual acceptance.
Public YouTube playback was blocked by CAPTCHA; public metadata/creator source
notes are not a watched-video review or a global popularity ranking.
