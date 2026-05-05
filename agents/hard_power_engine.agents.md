# Helix Hard Power Engine Agent

## Mission
Implement a hard power simulation and constraint engine for Helix.

Helix must become electrically aware. It should predict and constrain real-world power draw before final render so generated sequences are beautiful, safe, and practical.

---

## Core Objective

Create a post-process power engine that can:

1. Read layout/prop/circuit metadata.
2. Estimate watts and amps over time.
3. Detect overloaded circuits.
4. Apply smart correction without destroying musicality.
5. Output adjusted sequence data plus a power report.

Do not integrate into generation yet. Build this as a separate safe module first.

---

## Required Module

Create:

```text
core/power_engine.py
```

Optional supporting files:

```text
docs/power_engine.md
tests/test_power_engine.py
```

---

## Electrical Model

Each prop should support metadata like:

```yaml
prop_id: megatree_1
pixels: 1200
voltage: 12
watts_per_pixel_full_white: 0.3
circuit_id: circuit_A
priority: focal
```

Each circuit should support:

```yaml
circuit_id: circuit_A
breaker_limit_amps: 15
safe_utilization: 0.8
voltage: 120
```

Safe circuit limit:

```text
safe_amps = breaker_limit_amps * safe_utilization
```

Power estimate per prop per frame:

```text
prop_watts = active_pixel_fraction * intensity_fraction * pixels * watts_per_pixel_full_white
```

Circuit current estimate:

```text
circuit_amps = circuit_watts / circuit_voltage
```

---

## Correction Priorities

When overloaded, preserve artistry in this order:

1. Preserve beat accents.
2. Preserve vocals/focal props.
3. Preserve major phrase transitions.
4. Reduce background props first.
5. Reduce washes before accents.
6. Reduce non-focal props before focal props.
7. Compress brightness before deleting effects.
8. Smooth spikes over short windows when visually acceptable.

---

## Required Features

### 1. Per-Frame Power Log
For every frame/time slice, output:

- timestamp
- watts per prop
- watts per circuit
- amps per circuit
- safe limit per circuit
- overload amount if any

### 2. Overload Detection
Flag:

- hard overloads
- repeated near-limit events
- full-white spikes
- simultaneous heavy-prop events
- risky circuit concentration

### 3. Smart Compression
If a circuit exceeds safe amps:

- Compute required reduction.
- Reduce lowest-priority props first.
- Avoid reducing accents unless absolutely required.
- Maintain relative motion and timing.
- Keep color ratios where possible.

### 4. Peak Smoothing
For short spikes:

- Smooth over a configurable 50–150ms window.
- Avoid shifting musical hits noticeably.
- Preserve perceived impact.

### 5. Report Output
Generate a structured report:

```json
{
  "max_amps_by_circuit": {},
  "overload_events": [],
  "corrections_applied": [],
  "frames_adjusted": 0,
  "safe_after_processing": true
}
```

---

## Testing Requirements

Add tests that prove:

1. Under-limit sequences remain unchanged.
2. Over-limit sequences are reduced.
3. Focal props are preserved before background props.
4. Circuit max amps stay under safe limit after correction.
5. Reports include overload events and corrections.
6. Peak smoothing reduces spikes without deleting events.

---

## Non-Goals For First Pass

Do not:

- Rewrite the main generation engine.
- Change layout builders.
- Alter timing logic.
- Modify musical analysis.
- Merge with HSS scoring yet.
- Assume Greg’s exact electrical setup unless metadata exists.

---

## Final Output Required

End with:

```text
POWER ENGINE REPORT

Files created:
- ...

Tests added:
- ...

Validation commands run:
- ...

Known limitations:
- ...

Next integration step:
- ...
```
