# Runtime Consolidation Inventory (v1)

## Objective

Identify the canonical Helix execution/runtime path and classify legacy or overlapping systems.

---

# Protected Systems (KEEP)

These systems are considered core production infrastructure and should not be removed.

## Core Runtime / Export Stack

KEEP:
- `feature/restructure-core`
- deterministic sequencing pipeline
- XSQ emitter pipeline
- deployment validation pipeline
- geometry manifest pipeline
- band runtime catalog
- export validation tooling

## Validation / CI

KEEP:
- XSQ validators
- geometry status tooling
- V28 benchmark gates
- source hygiene gates
- CI deployment validation

## Active Sequencing Systems

KEEP:
- `run_helix_beta.py`
- ChronoFlow systems
- TimingTrackSet systems
- structured sequence builders

---

# Archive Candidates

These systems likely still contain historical value but should eventually move to archive-only status.

## Legacy Runtime Paths

ARCHIVE CANDIDATES:
- legacy launcher shims
- deprecated GUI adapters
- experimental standalone runners
- duplicate timing planners

## Old Builds / Outputs

ARCHIVE CANDIDATES:
- obsolete EXEs
- duplicate preview renders
- stale generated XSQ exports
- redundant MP3 outputs
- redundant MP4 outputs

---

# Delete Candidates

Delete only after parity validation.

## Safe Delete Targets

DELETE CANDIDATES:
- superseded temporary exports
- stale generated artifacts
- duplicate rendered previews
- abandoned scratch outputs

---

# Canonical Runtime Direction

Current intended production direction:

```text
lyrics/audio
→ timing analysis
→ ChronoFlow
→ TimingTrackSet
→ structured sequencing
→ XSQ emission
→ validation
→ xLights deployment
```

---

# Required Next Audit Phase

1. Enumerate every runtime entrypoint
2. Enumerate every timing-analysis pipeline
3. Enumerate every launcher/GUI shim
4. Determine canonical execution path
5. Move uncertain systems to archive
6. Validate CI parity
7. Remove obsolete systems
