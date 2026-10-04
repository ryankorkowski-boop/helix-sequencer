# Helix drum ground-truth benchmark

Small, deterministic benchmark harness for Helix drum detection. The benchmark intentionally keeps third-party datasets out of git; `audio/` and source annotations are populated locally from the dataset providers listed in `manifest.json`.

## Current state

- Harness is wired to Helix's existing `audio.drum_detection.detect_drum_event_streams_from_file` path.
- Ground truth schema is normalized to `kick`, `snare`, `hihat`, `tom`, `cymbal`.
- Matching is one-to-one within a configurable time tolerance; class mismatches are counted as confusion rather than silently becoming false positives.
- Default tolerance is 60 ms.
- Synthetic MIDI generation is included so the benchmark can run without any downloaded dataset.
- IDMT and GMD acquisition instructions are recorded in the manifest. MDB is retained as a mixed-real-world tier.

## Layout

```text
helix-drum-test-data/
├── audio/{idmt,gmd,mdb,synthetic}/
├── annotations/{idmt,gmd,mdb,synthetic}/
├── ground_truth/
├── scripts/
├── manifest.json
└── README.md
```

## Ground-truth schema

```json
{
  "track_id": "example",
  "audio_path": "audio/synthetic/example.wav",
  "events": [
    {"time": 0.500, "drum": "kick", "velocity": 0.85}
  ]
}
```

`velocity` is normalized to 0..1. Helix's detector currently exposes the five typed classes plus a `drum_bus` fallback; the benchmark evaluates only the five canonical classes unless `--include-drum-bus` is requested.

## Run the benchmark

From the Helix repository root:

```bash
python helix-drum-test-data/scripts/run_helix_drum_test.py \
  --root helix-drum-test-data \
  --ground-truth helix-drum-test-data/ground_truth \
  --tolerance-ms 60
```

The runner imports `audio.drum_detection` from the current checkout, so it tests the detector actually present in the branch being evaluated.

## Convert source annotations

```bash
python helix-drum-test-data/scripts/convert_to_helix_gt.py \
  --format gmd \
  --source annotations/gmd/example.mid \
  --audio audio/gmd/example.wav \
  --output ground_truth/example.json
```

IDMT XML/SVL and MIDI conversion are supported. MDB conversion is intentionally adapter-based because MDB releases can differ in annotation-file layout; use `--format mdb` with a CSV/TSV/JSON annotation containing time + class columns.

## Synthetic regression set

Generate three tiny WAV+JSON pairs without external samples:

```bash
python helix-drum-test-data/scripts/make_synthetic_drums.py \
  --output helix-drum-test-data
```

The renderer uses simple deterministic synthesized drum voices. These are regression fixtures, not a substitute for acoustic recordings.

## Dataset sources

1. **IDMT-SMT-Drums V2** — highest-priority acoustic/sample/synth isolation tier. The public release contains 608 mono WAV files, manually annotated kick/snare/hi-hat onsets, and isolated tracks for selected subsets. Download the 287.1 MB archive from the Zenodo record rather than committing the archive to this repository.
2. **Groove MIDI Dataset** — human-performed MIDI with velocity and style metadata. The MIDI-only archive is only 3.11 MB and is the preferred symbolic source. Render selected sequences locally when audio is needed.
3. **MDB Drums** — mixed real-music excerpts with drum annotations. Keep only 2–3 short excerpts locally.

Respect each dataset's license and attribution requirements. Do not redistribute source archives from this repo.

## Evaluation notes

- A prediction and reference of the same class within tolerance = TP.
- A prediction within tolerance but with another class = class confusion; it increments FP for predicted class and FN for reference class.
- Unmatched predictions = FP.
- Unmatched references = FN.
- Timing error is `prediction_time - reference_time` for matched same-class events; report mean absolute and signed error.
- Matching is greedy by smallest absolute time difference within each class, which is deterministic and adequate for short onset benchmarks.

## Suggested first benchmark set

Select 6–8 IDMT loops across RealDrum, WaveDrum and TechnoDrum, 4–6 GMD short beat/fill MIDI sequences across contrasting styles, and 2–3 MDB excerpts. Prefer 2–8 second clips with enough repeated hits to expose systematic errors. Keep the complete local package under 300 MB.
