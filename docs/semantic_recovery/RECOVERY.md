# Historical recovery and semantic integration — 2026-10-18

Preserved production reference: `9522b19b660ebef537e195397e7e8ca6c64354bf`
(PR175). Default branch merge base: `1f66f5dfa09b3173f5cdfd33d28ab1b4421e11ad`.
Development only. No release merge or owner artistic approval is implied.

## Scope and reproducible evidence

The audit fetched all 224 advertised remote branches, available tags and all
125 PR heads, including merged and closed PRs. It inspected 2,432 reachable
commits from the April 14 modular baseline through the October 18 production
head. Six root histories include five orphan media histories. A connectivity
fsck also exposed 158 locally available dangling commit heads; recovery refs
preserve them. They did not increase the final reachable commit count because
the fetched refs already covered their histories. GitHub cannot supply objects
which have been permanently deleted and are not referenced or locally present.

The automated content pass read **2,924 unique source blobs**, not just commit
messages. It found 451 lyric-related, 162 emotion-related, 422 musical-analysis,
356 choreography, 469 export/render and 23 bypass-related blobs. Categories
overlap; matches are discovery evidence, not proof that a feature works.
`history_audit.json` retains refs, root commits, every target version and the
content inventory. `historical_inventory.csv` is the filterable source inventory.
`feature_provenance.json` records origins, production presence, imports and the
limits of historical performance evidence for the relevant module families.

Commands used: `git log --all --full-history --name-status`, per-path
`git log --follow`, content pickaxe `git log -S` / `git log -G`, `git diff`,
`git blame`, `git merge-base`, `git fsck --connectivity-only --no-reflogs`,
`git rev-list --objects --all`, and streaming `git cat-file --batch`.
All distinct historical versions of the ten requested modules were compared
against the preserved production blobs. Nine have one unique implementation;
`tools/helix_cli.py` has six. There was no hidden advanced alternate version of
the nine modules to restore. Existing advanced engines remain present.

## Feature provenance matrix

| Feature | Origin / evidence | Production gap | Recovery decision |
| --- | --- | --- | --- |
| Modular architecture / versioned effect engines | `9a9097c3` April 14; original README and retained legacy wrappers | Older wrappers are archived, not evidence of a superior missing analyzer | Preserve active engine and archives |
| Whisper words / optional Moises | `a0a65089`, `a8b7b446`, `0090604d`; `core/audio_intelligence.py` | Missing probabilities received high defaults; phrase timing looked like word alignment; local filtered residuals fed ASR | Shared confidence gate, explicit unknown spans, genuine isolated stems only or original mix; missing backend returns no text |
| Configurable lyric interpreter | `558db5ac` May 1; blob `436245917` | Isolated lexicon hits, no narrative state | Preserve interpreter; contextual director consumes phrase relationships separately |
| Vocal emotion / timeline | `18474b68` April 24, reintroduced identically by `5127bb53` May 1 | Even word/phone allocation and peak-generated `vocal_hit` text; mood labels overstate evidence | Evidence-aware production timeline, continuous confidence/provenance, restrained delivery |
| Seven-mouth grapheme contract | `a6c57042` May 10 | Graphemes do not establish pronunciation or acoustic boundaries | Preserve model contract; reuse recovered CMU pronunciation; explicit aligned-phone input supported |
| Dictionary pronunciation / sung syllables | Historical `tools/align_snowman_lyrics.py`; production source preserved in provenance JSON | Showcase-only helper imports torch and hardcodes workspace/model paths | Move exact pronunciation rules to `core/lyric_pronunciation.py`; old tool reuses them |
| Independent singer evidence | `music/vocal_roles.py`, PR153 | Mixed-bus classifier/peak windows can still activate legacy background faces | Keep duplicate rejection and independent voice routing; evidence-aware engine suppresses unsupported background windows |
| Shared context / learning features | `18474b68`, `cdf0468b`; SequenceContext and feature extractor | Semantic meaning absent from synchronized representation | Preserve interfaces; add source-timed unified event stream and plan metadata |
| Emotion palette | `a515c985`, `4531e636` April 24 | Discrete palette helper alone cannot tell a story | Reuse palette helper for scoped scenic layers; confidence limits intensity |
| Timing-track adapter | `55e6ab0a` May 5 | Analyzer discovery never names actual `analyze_audio_file`; ignores dataclass results and millisecond fields | Restore callable/result adaptation and explicit unit conversion |
| Helper CLI / shadow plan | `a515c985`, `79f58f96`, `fe66d731`, `726e7a5b` | Explicit `enable_lyrics=False`; no demonstrated dependency/performance rationale in introducing diffs | Analyze and plan sidecars enable lyrics with `--no-lyrics` escape; old generic placement helpers remain instrumental pending rendering validation |
| Cinematic / narrative engines | Adaptive storytelling, scene engine, intent graph, multi-pass orchestration and sequence memory | Section labels stand in for lyrical narrative; no language model implementation found | Reuse canonical intents and layer expander, add conservative contextual state; do not replace those engines |
| Native exports / video | Existing native XSQ adapter, FSEQ reader, NativeSongView and preview verifier | Full-song semantics had no production connection or comparison | Append explicit scenic RGB layers only; baseline/native sample parity and soundtrack/decode gates |

Historical tests and reports exist but do not establish independently measured
historical musical performance. The matrix explicitly marks that metric unknown.
No historical implementation was discarded because a simpler replacement was
easier to write.

## Confirmed gaps repaired

1. Low-confidence/no-speech/repetitive ASR output cannot become semantic text.
2. No recognizer or instrumental mode yields no invented words/phonemes.
3. Timed phrases stay phrases; reliable source words keep their exact clocks.
4. Supplied phone alignments are validated within words. Dictionary phones are
   explicitly estimated and have capped confidence; no acoustic accuracy claim.
5. Source-bound user correction JSON has a required audio SHA256, explicit
   millisecond intervals, and declared word/phrase timing granularity.
6. English contextual rules handle scoped negation, selected literal/figurative
   distinctions, mixed mood, recurring imagery and emotionally transformed motifs.
7. Emotion exposes valence, arousal, tension and intensity with separate
   confidence and provenance. Missing acoustic evidence has zero confidence.
8. One ordered event stream retains beats, estimated bar positions, notes,
   drum events, sections, words, phonemes and semantic phrases. The 4/4 bar
   assumption is explicit; beat phase and meter are not asserted as verified.
9. Semantic direction uses recovered ChoreographyIntent / IntentLayerExpander.
   Instrument times remain authoritative; semantic scenery uses separate layers.
10. `--semantic-target` selects scenic RGB roots in the engine. Performer names,
    submodels, unknown models and non-RGB/control fixtures fail closed. Existing
    XML layers remain unchanged. A separate `.semantic.json` describes the
    semantic overlay; the older musical report still describes original lanes.
11. Optional CPU ASR uses a tested dependency set. PyAV 19 broke the recognizer's
    `metadata_errors` argument; optional requirements pin PyAV 15.1.0.

## Current limits and remaining acceptance gates

This is a conservative rule-based extension, **not complete human-level song
understanding**. Arbitrary metaphors, sarcasm, story causality, automatic source
identity, robust harmony separation and audio-aligned phone boundaries remain
open. A single mixed vocal track does not establish multiple singers. Existing
ten-viseme review models and seven-mouth legacy exports coexist; this work does
not pretend all models support the same mouth inventory.

The semantic XSQ compiler currently uses native On envelopes and ordered scenic
prop traversal. Particle imagery, shaders, richer per-concept spatial composition
and full band semantic acting remain future work. It never labels an On effect
as a meteor, fire shader, snow particle or measured singer gesture.

The completed conservative native benchmark covers exact owner Drive recordings: instrumental
Bells of Mathmas, Phoneme Test Hook, Wires in the Garland, Let It Glow, Glass
Under Skin, Ghost In The Grid, Festivus and North Pole Overdrive. Genre/emotion
categories are hypotheses until listening and annotation confirm them. The
fixture tests verify clock/contract correctness, **not ASR WER or acoustic phone
accuracy**. Independent labels for those measurements remain required.

All eight conservative native renders finished; all movies fully decoded,
original soundtrack zero-lag correlation exceeded .9988, original XML layers and
non-scenic samples matched, and the instrumental samples matched exactly.
See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md). This establishes these technical
gates only. The original requirements were: zero-lag original
audio correlation must exceed .98, pre-existing XML layers must compare exactly,
non-scenic native samples must match, and instrumental native samples must be
identical. Full-band, native LMS import, Windows, Android, physical controllers,
and owner artistic review remain separate gates. No release completion claim.

## Running

`python -m tools.helix_cli analyze-audio SONG.mp3 --output analysis.json`

`python -m tools.emit_sequence_plan --audio SONG.mp3 --layout LAYOUT.xml --output plan.json`

Use `--no-lyrics` for explicit instrumental runs, or `--lyric-corrections` for a
source-bound timed JSON. Engine CLI accepts repeated `--semantic-target NAME`
alongside the existing layout and audio options. Missing recognition degrades to
the existing instrumental sequence. Invalid correction sources/targets fail.

`tools/benchmark_semantic_recovery.py` runs the immutable baseline in a separate
process, compiles current semantic overlays, renders both with xLights 2026.18,
compares native samples and exports synchronized full-song comparison MP4s.
The dedicated development workflow automates the same steps without release writes.

## Actual contextual model failed acceptance

The optional local NLI provider is review-only after actual fixtures exposed
unsupported concepts and missed a contextual metaphor. It cannot change production
concepts, emotion, motifs or direction. See [CONTEXTUAL_MODEL.md](CONTEXTUAL_MODEL.md).
The two earlier experimental context videos are rejected semantic proofs.
