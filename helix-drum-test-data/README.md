# Helix drum ground-truth benchmark

Small, deterministic benchmark harness for Helix drum detection. Third-party audio and source annotations are **not committed** to Helix; they are acquired locally under the provider's license terms.

## Legal/data-use policy

The benchmark uses datasets only under their published terms and keeps source archives out of the repository. IDMT-SMT-Drums V2 is hosted by Fraunhofer IDMT on Zenodo; verify the record's current Rights field before redistributing any extracted audio. GMD is CC BY 4.0, so selected local copies require attribution. MDB must be treated according to the license/terms attached to the exact MDB release being used. Do not package third-party audio into a Helix release unless its license expressly permits that redistribution.

## Current state

- Harness calls Helix's existing `audio.drum_detection.detect_drum_event_streams_from_file` path.
- Ground truth uses `kick`, `snare`, `hihat`, `tom`, `cymbal`.
- Matching is one-to-one within a configurable tolerance; class mismatches are reported as confusion.
- Default tolerance is 60 ms.
- Synthetic fixtures provide a no-download smoke/regression test.
- Third-party datasets are acquired locally and are never copied into git by the benchmark scripts.

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

## Run

From the Helix repository root:

```bash
python helix-drum-test-data/scripts/make_synthetic_drums.py --output helix-drum-test-data
python helix-drum-test-data/scripts/run_helix_drum_test.py \
  --helix-root . \
  --ground-truth helix-drum-test-data/ground_truth \
  --tolerance-ms 60 \
  --output helix-drum-test-data/benchmark-result.json
```

The runner resolves paths from either the Helix root or benchmark directory and **fails immediately** if required audio is missing. This prevents false zero-metric runs.

## Third-party tiers

1. **IDMT-SMT-Drums V2** — highest-priority onset benchmark. Zenodo reports 608 mono WAV files with manually annotated kick/snare/hi-hat onsets and isolated tracks for selected subsets. Download locally from the official Zenodo record; do not commit the archive.
2. **Groove MIDI Dataset (GMD)** — human-performed MIDI with velocity and style metadata. Google publishes the MIDI-only archive at 3.11 MB under CC BY 4.0. Selected MIDI may be rendered locally for detector testing.
3. **MDB Drums** — mixed real-music tier. Use only a specific release whose terms permit the intended local testing/use; keep source audio outside git unless redistribution is clearly permitted.

### IDMT

```bash
python helix-drum-test-data/scripts/prepare_idmt.py \
  --idmt-root /path/to/IDMT-SMT-DRUMS-V2 \
  --output helix-drum-test-data \
  --per-subset 2
```

### GMD

```bash
python helix-drum-test-data/scripts/prepare_gmd.py \
  --gmd-root /path/to/groove-midi \
  --output helix-drum-test-data \
  --count 5
```

If audio is needed, render the selected MIDI locally with the separately installed FluidSynth/soundfont:

```bash
python helix-drum-test-data/scripts/render_gmd.py \
  --midi-root helix-drum-test-data/annotations/gmd \
  --soundfont /path/to/drums.sf2 \
  --output helix-drum-test-data/audio/gmd
```

## Ground truth

```json
{
  "track_id": "example",
  "audio_path": "audio/synthetic/example.wav",
  "events": [
    {"time": 0.500, "drum": "kick", "velocity": 0.85}
  ]
}
```

Velocity is normalized to 0..1. Finer tom labels can be added in a future schema revision while retaining aggregate `tom` metrics.

## Evaluation

- Same-class event within tolerance: TP.
- Nearby wrong-class event: FP for predicted class + FN for reference class + confusion entry.
- Unmatched prediction: FP.
- Unmatched reference: FN.
- Timing error: prediction minus reference for matched events.

The synthetic set is a smoke/regression fixture only. The first meaningful detector assessment should use IDMT isolated/mixed loops, followed by GMD and MDB.
