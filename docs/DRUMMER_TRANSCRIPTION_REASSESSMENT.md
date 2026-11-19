# Drummer transcription reassessment — 2026-10-07

**User rejected #218 / 73bb80b. This supersedes the historical recovery candidate. New candidate remains pending human listening and explicit approval.** Start with MASTER_TODO.md and DRUMMER_RECOVERY_CHECKLIST.md. Approved artwork, geometry, lighting and strike poses are unchanged.

## What other programs taught us

Primary sources inspected:

- [xlight-autosequencer stem routing](https://github.com/bobbyfriday/xlight-autosequencer/blob/main/docs/stem-separation.md): separates full mixes with Demucs and routes algorithms to appropriate stems. Useful separation/routing design; generic onset/beat tracks do not by themselves identify individual kit instruments.
- [ADTOF original authors](https://github.com/MZehren/ADTOF): a model trained using real music/chart data. [PyTorch inference port](https://github.com/xavriley/ADTOF-pytorch) provides five independent family activations; simultaneous families can coexist. This is substantially different from selecting one family using a few spectral ratios.
- [ADTOF Plus](https://github.com/xavriley/adtof_plus_drum_transcription): separates the drum bus and its individual components, transcribes, then estimates articulation/dynamics from stems.
- [Demucs](https://github.com/facebookresearch/demucs): full-mix drum isolation. [LarsNet](https://github.com/polimi-ispl/larsnet): five individual drum stems. Their separation errors remain a limitation, not a reason to treat every separated transient as truth.
- [Omnizart drum API](https://music-and-culture-technology-lab.github.io/omnizart-doc/drum/api.html): its standard output collapses to three written instruments, inadequate for this kit contract without further identity work. Not installed.
- [ADT_STR](https://github.com/pier-maker92/ADT_STR), [model bundle](https://huggingface.co/Pierfrancesco/adt-str): a newer generative model with detailed instrument identities. Tested directly on mix and drums. The mixed-audio 21.2–23.76s probe predicts many weak auxiliary/tom notes absent from the clearer drum stem. Stem input markedly improves that probe, but the first 51.2s run still invents weak floor toms at independently supported snares (11.48/12.45s), duplicates kicks, and stalls in later decoding. Full inference stopped after 20/93 chunks. It was not adopted merely because it is newer.

ADTOF was run on the SAME full source and Demucs drum stem, using the published thresholds without a sweep. Individual normalized LarsNet stems were also tested as model input; isolated hat/cymbal prediction lost much of the activity. That route was rejected. No beat snapping, generated grooves, target quotas, or artificial bus distribution.

## Concrete evidence and resulting candidate

Rejected recovery: 1182 placements — kick188/snare36/hat202/cymbal749/tom7.
ADTOF original mix: raw kick346/snare264/hat464/cymbal225/tom54.
ADTOF separated drums: raw kick349/snare227/hat416/cymbal18/tom47.
Selected separated-drums candidate: **1022 placements** — kick349/snare227/hat416/cymbal18/tom12. These counts describe change and are not acceptance criteria. Separation reduces some metal detections; quiet hats and ride/crash activity require particular human scrutiny.

Signal views establish the basis for preferring separated drums over the mixed model's early extra body hits. The strong 15.56s attack appears in the isolated snare waveform and is absent from the isolated kick waveform; rejected recovery called it kick. At 11.48/12.45s it similarly assigns cymbal while both model inputs and snare traces support snare. At 22.08,23.38,24.69s the candidate preserves separate snare+hat events; recovery chose one principal family. Around 21.4–40s recovery produced 78 cymbal placements and 16 hats; the independent mix model shows a steady hat lane, while the drum/family stems support discrete attacks rather than repeated crashes.

Twelve toms use measured post-attack resonance in the isolated tom stem, stable in two overlapping body windows, against explicit recording-specific reference modes HIGH137.3/MID94.2/FLOOR78.1Hz. The references derive from the signal evidence, not a target coverage goal; they are provisional until reviewed by ear. Generic five-family output cannot identify tom height. Without supplied calibration, all tom identities abstain. With it, 35/47 still abstain for insufficient/unstable/ambiguous/out-of-range resonance. No tom cycling. The physical counts happen to include high7/mid4/floor1; that is not a test quota.

Drum timestamps come directly from each learned 100fps family activation peak; no full-mix waveform relocation or quantization. Per-instrument isolated attack RMS estimates velocity; 95th-percentile normalization within each family preserves relative accents. This is not ground-truth MIDI velocity. The unchanged scheduler and approved compositor consume the imported events.

All nine earlier independent **provisional** signal anchors match within their tolerances. They are not newly invented from model output and still lack human auditory review. This is engineering evidence only. Available tools do not provide auditory perception; no listening claim is made.

## Implementation and reproduction

`audio/drum_transcription.py`: vendor-independent polyphonic event import, strict original-audio SHA identity, finite timestamp/score validation, unsupported-family/unknown-tom abstention and per-event trace.
`tools/transcribe_drummer_adtof.py`: external package API, strict pretrained weight loading (missing/incomplete weights cannot silently produce random inference), published peak picker, optional measured identity/dynamics evidence.
`tools/integrate_drummer_v3_into_xsq.py --drum-events`: normal production mapping/export with verified transcription input; source engine is recorded in all native effects. Legacy HPSS remains the rejected comparator/default for callers that omit this flag; it is not musically approved. Broader application default promotion is deferred until this performance is approved, rather than silently deploying another unreviewed detector everywhere.
`evidence/drummer/helix_adtof_stem.json`: cached inferred performance for the exact song, **not an expected-test fixture or human annotation**. CI exports this candidate, checks source identity/structure, and renders actual-song proof. It does not claim to independently rerun/train the model. No external model code or weights are vendored into Helix.

Research source revisions:
ADTOF-pytorch `85c192e78f716ea0b111cc8a5ee4a8f6a3a4f8a9`;
Demucs `e976d93ecc3865e5757426930257e200846a520a`, htdemucs `955717e8-8726e21a.th`;
LarsNet `17d631fd18e77ee2f1d23ee7b3fc0fb46ae629e2`;
ADT_STR `77dbef225e7029478ebfb916f20c7a00274f0f12`, HF weights revision `a33c5c6b191a4ca1e0f6dc22140947485eb36ce8`, setting-tau-0.8.
Runtime: Python3.12, torch/torchaudio2.5.1 CPU, ADTOF public inference API (ADTOF Plus reviewed but not installed); model/stem SHA provenance is recorded in the event file. ADTOF weights are CC-BY-NC-SA4.0; LarsNet weights CC-BY-NC4.0. The PyTorch port has no license file. These are externally installed evaluation dependencies, not commercial redistribution clearance. Demucs is MIT; ADT_STR is CC-BY-SA4.0. No model/weight packaging changes.

```sh
# External research environment: install CPU torch/torchaudio and pinned model repositories separately.
# Demucs upstream dependency pin predates Python3.12: tested with torchaudio2.5.1 via no-deps install.
OMP_NUM_THREADS=2 python -m demucs.separate -n htdemucs --two-stems drums --shifts 0 --segment 7 --overlap .25 -j 1 -o test_runs/drummer_transcription/separated 'Helix Audiolights.mp3'
PYTHONPATH=. python tools/prepare_drummer_stems.py 'Helix Audiolights.mp3' --output test_runs/drummer_transcription --larsnet-code /path/to/external/larsnet
PYTHONPATH=. python tools/transcribe_drummer_adtof.py 'Helix Audiolights.mp3' --analysis-audio 'test_runs/drummer_transcription/separated/htdemucs/Helix Audiolights/drums.wav' --family-stems test_runs/drummer_transcription/lars_full --tom-reference-hz 137.3,94.2,78.1 --output test_runs/drummer_transcription/stem_transcription.json
PYTHONPATH=. python tools/integrate_drummer_v3_into_xsq.py template.xsq 'Helix Audiolights.mp3' --drum-events evidence/drummer/helix_adtof_stem.json --output test_runs/drummer_transcription/Helix_Drummer_TRANSCRIPTION.xsq --report test_runs/drummer_transcription/transcription_report.json
PYTHONPATH=. python tools/export_drummer_only_xsq.py test_runs/drummer_transcription/Helix_Drummer_TRANSCRIPTION.xsq --output test_runs/drummer_transcription/Helix_Drummer_TRANSCRIPTION_ONLY.xsq --audio 'Helix Audiolights.mp3'
```

## Artifacts and validation

`test_runs/drummer_transcription/`: 25s/full MP4 with ORIGINAL song audio, isolated XSQ, source/candidate/mix event files and CSV, before_after_summary.json, complete report, isolated instrument and activation plots, diagnostic clicks, decoded frames and soundtrack correlation evidence. No geometry/art/compositor changes. 110 relevant tests passed; focused changed-module checks repeated after audit changes. Encoded 25s soundtrack correlation to original source: .99621464. Decoded idle/kick/snare+hat frames preserve dim body and target-specific lighting/poses.

Human final gate: review actual-song MP4, especially hat rhythm, cymbal losses after separation, tom fills and quiet snare events. Native xLights playback and manual audible labels remain unverified. If this candidate is still wrong, isolate timestamp-specific failures with the original mix, separated stems and model activations; do not celebrate counts or green CI.
