# Saved-XSQ quality metrics (Phase 1)

This opt-in diagnostic harness measures original, general engineering criteria.
It does not change effects, profiles, drummer timing, learning memory, or inputs.
Existing intent scorers keep their current behavior. No external sequence data
is used for calibration. Metrics are diagnostic warnings, not release approval.

## API and command

```python
from tools.quality import score_sequence
report = score_sequence(xsq_path, layout_path, audio_features)
```

The function reads the two supplied XML files and returns a JSON-serializable
dictionary. It writes nothing, changes no RNG state, and includes no timestamps
or machine-specific paths. Identical inputs produce identical reports.

After a run has finished:

```bash
python -m tools.quality score path/to/run_dir
```

The directory must contain `run_manifest.json` and `audio_features.json`.
XSQ is selected from manifest artifacts with `kind: xsq`, or a single local
`*.xsq` if none are recorded. Layout comes from manifest `layout_path`.
Relative recorded paths may resolve from the run directory or launch working
directory; ambiguous paths fail. Runs with multiple variants require an explicit
choice. Overrides use paths relative to the command's working directory:

```bash
python -m tools.quality score path/to/run_dir \
  --xsq output.xsq --layout xlights_rgbeffects.xml --features features.json
```

The command prints the report and atomically replaces only the manifest's
`quality` field. Other fields, run status, and success/failure remain unchanged.
Malformed input exits 2 without modifying the manifest. Scoring is post-run:
running it while RunManager is still writing the manifest is unsupported.
This phase does not add automatic feature extraction or run-completion hooks.

## Feature contract

All times are milliseconds; energy is normalized to [0, 1]. Times must be finite.
Energy samples must be strictly increasing, sections ordered/nonoverlapping,
and section ids nonempty and unique. Features must correspond to the exact XSQ
audio clip, including its offset and duration. A mismatch is rejected.

```json
{
  "duration_ms": 4000,
  "onsets_ms": [0, 1000, 2500],
  "energy": [
    {"time_ms": 0, "value": 0.25},
    {"time_ms": 4000, "value": 0.8}
  ],
  "sections": [{"id": "intro", "start_ms": 0, "end_ms": 4000}],
  "intentional_restraint": [{"start_ms": 3000, "end_ms": 3500}]
}
```

Duration may come from `head/sequenceDuration` (seconds) if omitted. Missing
onsets/energy yield null metrics with warnings; empty/constant series never
receive fabricated perfect correlation. No sections yields an overall report
and a warning. Preserve feature provenance alongside these fields. The CI
fixture supplies synthetic features, not detected events from a real recording.

## Definitions and initial diagnostic thresholds

The same definitions apply overall and within each section. Effect-start
metrics use starts inside the section; coverage and peak metrics also include
effects carried over its boundary. Intervals are half-open [start, end).

| Metric | Definition | Initial warning threshold |
| --- | --- | --- |
| Onset latency | Next visible effect start at/after each onset, at most 500 ms away; median and linearly interpolated p95 of matched latencies | p95 >100 ms or match fraction <0.8 |
| Effect diversity | Shannon entropy in bits of effect names per layout model class; group members count once each | Descriptive; no universal minimum for AC On-only shows |
| Energy tracking | Pearson correlation of interpolated energy with occupancy at fixed 100 ms bin midpoints; no extrapolation | Correlation <0.5; missing/constant data warns separately |
| Repetition | Identical effect name, normalized settings and palette on the same target/layer; adjacent count and count recurring within 5 seconds, divided by eligible transitions | Rate >0.5 |
| Dead air | Exact intervals with no potentially visible effects; split at declared restraint boundaries | Unintentional interval >=1000 ms |
| Peak simultaneous effects | Exact event sweep, excluding Off/zero-intensity/black-only effects; ends precede starts at shared timestamps | Descriptive; layout dependent |
| Focal-point count | Sampled physical model count with estimated intensity >=80% and >=90% of current maximum | Peak >2 |
| Palette consistency | Fraction of visible effect starts using the modal enabled-color set | Fraction <0.5 |

Values are rounded to six decimal places. Thresholds are versioned in the
report and `tools/quality/scoring.py`. They are initial engineering heuristics,
not learned aesthetic standards. Compare reports using the same feature inputs,
layout, schema, sampling, and thresholds. Match fraction must accompany latency:
a sparse sequence must not look successful just because one onset matches.

## Estimation limits and verification gate

Native saved-XSQ EffectDB/palette references and inline settings are supported.
Timing markers are excluded. On start/end levels and static brightness are
evaluated. Groups expand recursively and deduplicate physical model names.
Invalid references, unknown targets, cyclic groups, invalid intervals, and
non-finite data fail rather than silently improving a score.

Channel occupancy uses positive explicit `ChannelCount` or `channels` per model
when every model has one. Otherwise it uses equal model weights and reports a
warning. These explicit counts must describe nonoverlapping physical channels.
This phase does not infer native controller addressing or channel counts from
model geometry. It cannot deduplicate two models sharing physical channels.
Nested SubModel layers conservatively occupy the full parent model and warn.

Non-On effects are an occupancy upper bound. Value curves, blend modes, masks,
render order, gamma, transitions and per-pixel colors are not rendered. Their
light output, darkness and focal hierarchy may differ substantially. Missing
or unsupported palettes warn. A palette score does not prove visual coherence.

Reports always state `structural_estimate_not_native_render` and
`native_render_verified: false`. A score never certifies xLights import,
controller safety, visual quality, or real-song detector accuracy. Phase 1 is
implementation-tested but remains native-verification-pending until the project
gate in MASTER_TODO.md is satisfied with native XSQ/MP4 and human review.

## Reproduce the deterministic benchmark

`tests/fixtures/quality/` contains clean-room XSQ, layout, features and the golden
report. Beta CI runs `tests/test_quality_metrics.py` and exercises the CLI on
these files. An integration test also scores the existing Birdsong exporter;
unsupported curves/effects must produce explicit warnings.

```bash
python -m flake8 tools/quality tests/test_quality_metrics.py
python -m mypy --strict --explicit-package-bases --follow-imports=silent tools/quality
python -m pytest -q tests/test_quality_metrics.py
```

The benchmark deliberately contains a late onset and repeated ramp: tests must
detect those defects. Its constructed energy correlation of 1.0 verifies metric
arithmetic only. Phase 1 establishes a baseline; it makes no before/after claim
about sequencing improvements. Native rendering is still an external gate.
