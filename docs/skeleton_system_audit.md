# Skeleton System Audit (v1)

## Objective

Identify legacy, duplicate, abandoned, or structurally obsolete systems that are no longer part of the canonical Helix runtime path.

---

# Canonical Production Direction

Current intended production runtime:

```text
lyrics/audio
→ ChronoFlow
→ TimingTrackSet
→ structured sequencing
→ XSQ emission
→ validation
→ xLights deployment
```

Any runtime path outside this flow must justify its existence.

---

# Runtime Classification Categories

## ACTIVE

Definition:
- participates in current runtime/export stack
- participates in CI
- participates in deployment validation
- participates in current sequencing path

Examples:
- ChronoFlow
- TimingTrackSet
- XSQ emitter
- validation tooling
- geometry systems

---

## LEGACY

Definition:
- historical value retained
- may still be useful for comparison/migration
- not canonical production runtime

Examples:
- old GUI adapters
- compatibility wrappers
- transitional migration systems

Recommended action:

```text
archive first
```

---

## SKELETON

Definition:
- duplicate execution path
- abandoned experimental runner
- obsolete launcher shim
- unreferenced runtime
- duplicate timing planner
- stale build/output system

Strong indicators:
- not covered by CI
- not referenced by canonical runtime
- not used in export pipeline
- no deployment validation integration

Recommended action:

```text
archive → parity validation → delete
```

---

# High-Confidence Skeleton Candidates

## Launcher / Runtime Shims

Candidates:
- thin launcher wrappers
- duplicate executable entrypoints
- deprecated runtime adapters

Likely status:

```text
SKELETON
```

---

## Experimental Standalone Runners

Candidates:
- isolated sequence generators
- sandbox execution paths
- abandoned experimental planners

Likely status:

```text
SKELETON
```

---

## Duplicate Timing Pipelines

Candidates:
- beat-only planners
- abandoned onset planners
- duplicate phrase schedulers
- isolated timing analyzers

Likely status:

```text
LEGACY → SKELETON
```

---

## Stale Generated Outputs

Candidates:
- stale XSQ exports
- duplicate MP4 previews
- duplicate MP3 outputs
- abandoned generated artifacts

Likely status:

```text
SAFE DELETE
```

---

## Obsolete Executables

Candidates:
- old Dream Sequence Weaver builds
- superseded Helix executables
- obsolete packaged builds

Likely status:

```text
ARCHIVE
```

---

# Required Next Audit Phase

1. Enumerate every executable runtime path
2. Enumerate every timing-analysis system
3. Enumerate every launcher/adapter
4. Enumerate every standalone runner
5. Mark:
   - ACTIVE
   - LEGACY
   - SKELETON
6. Validate canonical runtime parity
7. Remove obsolete systems safely
