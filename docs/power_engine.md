# Power Engine Plan

## Scope
Build a standalone electrical-awareness module that estimates per-frame watts/amps and reports overload risk before render/export integration.

## Initial Input Shape
- `PropPowerMeta`
  - `prop_id`
  - `pixels`
  - `voltage`
  - `watts_per_pixel_full_white`
  - `circuit_id`
  - `priority`
- `CircuitMeta`
  - `circuit_id`
  - `breaker_limit_amps`
  - `safe_utilization`
  - `voltage`
- `FrameInput`
  - `timestamp_ms`
  - list of per-prop states:
    - `prop_id`
    - `active_pixel_fraction`
    - `intensity_fraction`

## Initial Output Shape
- Per-frame log rows:
  - `timestamp_ms`
  - `watts_by_prop`
  - `watts_by_circuit`
  - `amps_by_circuit`
  - `safe_amps_by_circuit`
  - `overload_events`
- Summary report:
  - `max_amps_by_circuit`
  - `overload_events`
  - `corrections_applied`
  - `frames_adjusted`
  - `safe_after_processing`

## First Tests To Keep
1. Formula correctness for per-prop watt estimate.
2. Under-limit frame stays safe and applies no correction.
3. Over-limit frame reports overload with positive `overload_amps`.
4. Report schema keys exist and are stable for downstream export.

## Next Files To Touch
- `core/power_engine.py`
- `tests/test_power_engine.py`
- `core/effect_engine.py` report payload wiring

## First Integration
Sequence reports now carry a disabled-by-default `power` section. When a later pipeline step enables power analysis, `validate_report_payload()` fails the build if the power report is unsafe after processing, including residual overloads or missing circuit metadata.

## Metadata File
The sequencing CLI accepts `--power-metadata-file <path>` with JSON shaped as:

```json
{
  "schema": "helix.power.metadata.v1",
  "circuits": [
    {"circuit_id": "A", "breaker_limit_amps": 15, "safe_utilization": 0.8, "voltage": 120}
  ],
  "props": [
    {
      "prop_id": "roof",
      "pixels": 100,
      "voltage": 12,
      "watts_per_pixel_full_white": 0.3,
      "circuit_id": "A",
      "priority": "background"
    }
  ]
}
```

Use `--fail-on-power-risk` to turn metadata/report risk into a build failure. The current first pass validates prop-to-circuit metadata and records `analysis_status: metadata_only`; frame-level sampling remains the next integration step.

## Risks
1. Incomplete or missing circuit metadata can hide real risk.
2. Correction policy can damage musical intent if applied too aggressively.
3. Spike smoothing window must not blur rhythmic accents.
4. Integration order: keep this module isolated until report quality is stable.

