# Helix Watermark Policy

## Purpose

This document defines provenance verification guidance for Helix-generated outputs.

## Recommended Metadata

Persistent-learning eligible outputs should contain embedded metadata similar to:

```json
{
  "helix_generated": true,
  "helix_version": "x.y.z",
  "generation_timestamp": "ISO8601",
  "watermark_signature": "signature-or-hash"
}
```

## Validation Requirements

Persistent-learning systems should:

1. verify watermark presence
2. validate watermark authenticity
3. reject unknown provenance
4. reject externally authored sequences
5. maintain provenance audit logs

## Recommended Enforcement

Long-term learning pipelines should refuse:

- externally sourced marketplace sequences
- community sequence archives
- vendor choreography
- copyrighted show packages
- unverified imports

unless explicit licensing rights exist.

## Goal

The goal is to preserve:

- provenance integrity
- licensing boundaries
- dataset traceability
- reproducible compliance behavior
