# Helix Training Policy

## Purpose

This document defines persistent-learning and reinforcement boundaries for Helix systems.

## Allowed Persistent Learning Sources

Persistent learning systems may only retain long-term learning signals derived from:

- Helix-generated outputs
- internally generated metadata
- authenticated Helix watermark outputs
- internally generated scoring telemetry

## Restricted Sources

The following sources must NOT be ingested into persistent training datasets, reinforcement memory, model tuning pipelines, or long-term scoring archives without explicit licensing rights:

- copyrighted music
- marketplace sequences
- third-party templates
- vendor choreography
- externally authored XSQ projects
- shared xLights community sequences
- licensed visual/audio assets
- proprietary sequencing packs

## Operational Runtime Usage

Third-party assets may still be used for:

- rendering
- previews
- interoperability
- temporary runtime transformations
- user-requested sequencing workflows

provided usage remains consistent with the applicable licenses.

## Enforcement Guidance

Persistent-learning systems should reject:

- unwatermarked content
- externally authored sequence archives
- unknown provenance data
- vendor marketplace assets

unless explicit authorization exists.
