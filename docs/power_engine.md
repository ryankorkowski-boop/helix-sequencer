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
- (later integration) `core/effect_engine.py` report payload wiring

## Risks
1. Incomplete or missing circuit metadata can hide real risk.
2. Correction policy can damage musical intent if applied too aggressively.
3. Spike smoothing window must not blur rhythmic accents.
4. Integration order: keep this module isolated until report quality is stable.

