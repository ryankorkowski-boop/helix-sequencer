# Drummer target strikes — engineering handoff, 2026-10-06

Read `MASTER_TODO.md` first. That ledger holds the running checklist and acceptance status.

Branch: `fix/drummer-target-strikes`.
Rollback baseline: `87c4b51bab45fb80b630288ef82f29c3da5e0014` on `fix/drummer-independent-illumination`.
The baseline branch was not rewritten. No merge is authorized by this handoff.

## What changed

Six source-derived strike poses replace shared raised-stick geometry for snare, three toms, and two crashes. Each pose carries an explicit contact point and source-shaft transform. The floor arm is reposed so its stick reaches the visible floor-tom upper rim rather than disappearing behind the mid tom. Surface windows were corrected against actual source pixels: the previous MID/HIGH masks captured neighboring green parts, and the kick window clipped the ring.

The source image is unchanged. Idle is 30%, instrument gain is 1.45, and hi-hat pedal supplemental gain is 32%. All review layers, preview masks, and native xmodel projections use one exact-geometry extraction path. Native actuators are partitioned into neutral arm and gold wood nodes with median source colors, retaining exactly eight public musical components. Re-injection retires obsolete generated generic-arm layers while preserving unrelated layers.

Production analysis now lives in `audio/drummer_v3.py`. Both `audio/drum_detection.py` and XSQ integration delegate to it. Prior implementations are retained under `audio/archive/`; `core/drummer_v3_analysis.py` is an explicitly archived feature-only compatibility adapter. Classification thresholds were preserved, not retuned from hit totals. Unknown tom classes and ambiguous drum_bus events do not emit in mapping or animation.

## Reproduction

Use Python 3.12 and the dependencies in `.github/workflows/drummer-ground-truth.yml`. Set `PYTHONPATH=.`.

```bash
python tools/build_drummer_v3_assets.py --overwrite
python tools/review_drummer_v3_poses.py --output test_runs/corrective
python tools/integrate_drummer_v3_into_xsq.py template.xsq 'Helix Audiolights.mp3' --output test_runs/corrective/Helix_Drummer.xsq --report test_runs/corrective/events.json
python tools/audit_drummer_v3_events.py test_runs/corrective/events.json --output test_runs/corrective
# Inspect pose sheet/video before proceeding to music.
python tools/render_drummer_v3_preview.py test_runs/corrective/Helix_Drummer.xsq --audio 'Helix Audiolights.mp3' --output test_runs/corrective/Drummer_Song_Proof_9.5-34.5s.mp4 --start 9.5 --duration 25 --fps 24
```

Run the focused suite listed in the workflow, plus `tests/test_drummer_v3_analysis.py` and `tests/test_drummer_v3_guitar_rejection.py` for archived API compatibility. Current evidence: **76 passed, no xfails**, two preexisting ElementTree warnings in `tools/build_helpers/helixville4_full_band.py:363`. Asset rebuild compared SHA-256 hashes of 14 xmodel/layer/sheet files and was byte-identical. `git diff --check` and workflow YAML parsing passed.

## Inspected evidence

Nine isolated encoded pose states were inspected: idle, kick, snare, hi-hat, HIGH, MID, FLOOR, left crash, right crash. The slow video holds each state for two seconds. Six explicit tip-to-contact tests also check visible actuator pixels and proximity to actual instrument pixels. The sheet retains the source screenshot's numbers/resting sticks; they are not new geometry.

The 25-second song proof starts at source time 9.5s and contains 600 frames at 24 fps. Decoded frames inspected at source times 9.75, 11.00, 18.82, 20.82, 21.82, 27.84, 28.63, 29.79, and 29.96s cover idle, first kick, both crashes, hat, snare+hat, MID tom, and kick+hat. Decoded AAC-to-source PCM correlation is 0.9967868 at the intended offset. This establishes audio identity/alignment, not musical classification correctness.

Full-song counts remain kick 54, snare 142, hat 154, tom 23, cymbal 82 (455 total). No hits occur before 10s; first hit is 10.990s. The first 61 seconds after the nominal entrance contain 122 typed events, 46 with confidence below 0.45 and 18 simultaneous onsets. Maximum rolling one-second counts: snare 5, cymbal 3, kick 3, hat 4, tom 2. No impossible dense bursts were found by the stated broad sanity ceilings.

Every accepted event is logged with timestamp, type, confidence, velocity, spectral band ratios, centroids, HPSS percussive ratio/flatness, decay evidence, scheduled status, and physical component. `Drummer_Event_Timeline.png` displays 10–30s; the CSV and JSON contain all events.

## Remaining work — do not mark final acceptance complete

1. Listen to and annotate 10–71s, starting with the sparse 11–18s region and low-confidence snares/crashes. Compare actual audible hits to CSV timestamps. No auditory ground-truth labels were produced in this pass. Confidence is onset/percussive support, not calibrated class confidence. The 142 snare count remains a review flag, not proof of overclassification.
2. Retune only `audio/drummer_v3.py` against labeled false positives/negatives. Do not add another exporter classifier, fabricate bus hits, or cycle unclassified toms. Preserve simultaneous body+metal hits and the intro rejection gate.
3. Obtain user visual/musical approval of the supplied proof. Source-derived static contact poses are not full skeletal animation. Simultaneous events sharing a hand can show multiple stick poses.
4. Import the generated xmodel/XSQ in xLights and inspect native idle lighting, node/palette appearance, and playback. Native 96x72 nodes and median palettes approximate the full-resolution source preview. Native import/playback was not performed here.
5. Review compatibility implications before merging: `audio.drum_detection` now uses conservative V3 events; only onset_delta from the old config is honored. Unknown toms intentionally become non-emitting.

Do not equate this engineering pass, passing CI, or source-aligned rendering with final musical approval. Preserve the rollback commit and this ledger.
