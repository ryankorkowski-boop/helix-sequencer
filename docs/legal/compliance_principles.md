# Helix Legal Compliance Principles

Status: policy and engineering guardrail  
Applies to: showcase parity, quality scoring, benchmark design, and any future learning or biasing work

## Core Rule

Helix may learn sequencing principles, measurable structure, and user-approved heuristics. Helix must not memorize, reproduce, scrape, or clone copyrighted/proprietary creative works without permission.

The goal is sequencing grammar, not sequence mimicry.

## Allowed Sources

High-confidence allowed inputs include:

- user-authored rules and notes
- user-created sequences and layouts
- sequences where the user has explicit permission to analyze/use them
- public tutorials describing general sequencing techniques
- public documentation for tools and algorithms
- licensed/open datasets whose terms permit the intended use
- aggregate metrics derived from authorized material
- music/audio files the user legally possesses for one-time render analysis

## Disallowed Sources and Behaviors

Do not:

- download or commit copyrighted YouTube videos for training
- scrape YouTube or public videos into a choreography dataset
- clone creator/vendor timing/effect placements
- commit proprietary vendor sequence packs or derived timelines
- build a named-creator emulator
- store raw copyrighted media unless licensed or explicitly permitted
- store recognizable choreography extracted from a specific copyrighted show
- bypass platform terms or paywalls

## Public Inspiration Boundary

Public videos and tutorials may be used for human observation and high-level design inspiration. They must not become training data unless the license/permission clearly allows it.

Allowed:

- "Top shows often use restraint before a drop."
- "Choruses should generally have higher breadth and intensity than verses."
- "Finales should usually exceed earlier peaks."

Not allowed:

- "Copy this creator's exact effect timing."
- "Recreate this display's choreography."
- "Train on downloaded public videos without permission."

## Derivative-Only Storage

When analyzing permitted sources, Helix should store only audit-safe derived data:

- aggregate scores
- anonymized statistical summaries
- manually reviewed general heuristics
- normalized metric distributions
- source metadata and permission status

Helix should not store:

- raw copyrighted media
- raw third-party sequence files
- frame-by-frame third-party choreography
- effect timelines from unlicensed sources
- vendor model packs without permission

## Source Registry Requirement

Every external source used for benchmarking, analysis, or heuristic extraction should have registry metadata including:

- source id
- title/description
- source type
- license/permission status
- storage permissions
- whether derived metrics are allowed
- reviewer
- review notes

See:

```text
docs/legal/source_registry_contract.md
```

## Engineering Rollout Rule

All quality-intelligence systems must follow this order:

1. Document policy and source permissions.
2. Implement report-only metrics using synthetic/user-permitted data.
3. Add explainable reports.
4. Add soft bias only behind opt-in flags.
5. Add hard enforcement only after benchmark/human validation.

## Audit Requirements

A PR that introduces learning, benchmarking, or showcase-parity behavior should state:

- what sources were used
- whether any copyrighted media was stored
- whether any vendor/proprietary data was used
- whether output behavior changes by default
- how the change remains report-only or feature-flagged

## Recommended PR Checklist

- [ ] No copyrighted media committed
- [ ] No downloaded YouTube assets committed
- [ ] No proprietary/vendor sequence files committed without permission
- [ ] No direct third-party choreography copied
- [ ] Source registry entries included for new external sources
- [ ] Tests use synthetic or user-authorized data
- [ ] Default renderer behavior unchanged unless explicitly intended

## Project Position

Helix should become an original cinematic sequencing engine that uses legal, auditable principles:

```text
Audio -> structure analysis -> staging heuristics -> original choreography -> quality report -> render
```

Not:

```text
Audio -> copied creator dataset -> imitation
```
