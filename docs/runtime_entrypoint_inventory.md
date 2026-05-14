# Runtime Entrypoint Inventory (v1)

## Objective

Track executable/runtime entrypoints and classify them into:

- ACTIVE
- LEGACY
- SKELETON

This document is intended to support safe consolidation and deletion planning.

---

# ACTIVE (Canonical Direction)

These systems are considered part of the current intended production runtime.

## Sequencing Runtime

ACTIVE:
- `run_helix_beta.py`
- ChronoFlow execution path
- TimingTrackSet execution path
- structured sequencing pipeline
- XSQ export pipeline
- validation pipeline

## Deployment Runtime

ACTIVE:
- XSQ validators
- deployment validation tooling
- geometry validation tooling
- CI gates
- xLights deployment path

---

# LEGACY (Archive Candidates)

These systems may retain historical or migration value.

## Runtime Compatibility

LEGACY:
- legacy GUI adapters
- compatibility wrappers
- migration bridges
- transitional runtime layers

Recommended action:

```text
archive first
```

---

# SKELETON (Probable Removal Candidates)

These systems are currently suspected of being duplicate or abandoned infrastructure.

## Duplicate Launchers

SKELETON CANDIDATES:
- duplicate executable launchers
- thin runtime wrappers
- obsolete launcher shims

## Experimental Runners

SKELETON CANDIDATES:
- abandoned experimental runners
- isolated sequence generators
- sandbox planners

## Duplicate Timing Systems

SKELETON CANDIDATES:
- isolated beat analyzers
- duplicate phrase planners
- abandoned onset systems
- disconnected timing planners

## Generated Artifact Noise

SKELETON CANDIDATES:
- stale XSQ exports
- duplicate MP3 outputs
- duplicate MP4 previews
- obsolete build artifacts

---

# Required Next Enumeration Pass

The repo still requires a deeper filesystem/runtime audit to:

1. Enumerate all executable scripts
2. Enumerate all launchers
3. Enumerate all timing systems
4. Enumerate all standalone runners
5. Determine true runtime references
6. Identify dead/unreferenced systems

That phase should precede any destructive cleanup.
