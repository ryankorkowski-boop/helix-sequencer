# Source Hygiene Checklist

Date: 2026-05-01  
Status: Active

## 1. Intake Checklist

Before extracting any rule:

1. Confirm the source is public and rights are clear.
2. Classify source type: official, repository, community, user-owned, internal.
3. Capture URL/path and extraction date.
4. Confirm no paid/private/proprietary restrictions are violated.
5. Decide if the source provides authoritative behavior or practical heuristic only.

## 2. Transformation Checklist

For each extracted insight:

1. Rewrite fully in Helix language.
2. Remove source-specific names, timestamps, and choreography.
3. Convert examples into generalized engineering rules.
4. Add a technical check condition where possible.
5. Mark confidence and risk level.

## 3. Rule Quality Checklist

A rule is merge-ready only if:

1. It is testable or reviewable.
2. It does not require one specific creator sequence.
3. It can be applied to multiple layouts.
4. It does not leak protected expression.
5. It aligns with legal policy and repo rulebooks.

## 4. Conflict Resolution Checklist

When sources disagree:

1. Prefer official behavior documentation first.
2. Use repository code/docs second.
3. Treat community discussion as inference.
4. Run a focused reproduction test when uncertain.
5. Record final decision and rationale.

## 5. Automation And Script Hygiene

For scripting and automation guidance:

1. Use documented automation APIs and script interfaces.
2. Avoid undocumented destructive actions.
3. Keep commands idempotent where possible.
4. Require explicit validation after automated changes.
5. Store script intent and expected outputs.

## 6. Red-Flag Triggers

Stop and quarantine content if any are true:

1. Text appears copied or stylistically imitative.
2. Rule depends on a specific creator choreography.
3. Rights provenance is missing or ambiguous.
4. Content came from paid/private materials.
5. Output includes proprietary data structures from third-party sequences.

## 7. Pre-Commit Scan

Before commit:

1. Search changed files for indicators of copied/source-specific content.
2. Verify all findings were rewritten to generalized language.
3. Confirm no bulk-ingested raw source text exists in repo files.
4. Confirm legal and technical docs remain internally consistent.

## 8. PR Gate Output Template

Use this minimal gate report in PR notes:

1. `sources_checked`: count by source tier.
2. `blocked_sources`: list and reason.
3. `rules_added`: count and categories.
4. `community_inference`: count and labels.
5. `legal_risk`: low/medium/high with rationale.
6. `final_status`: pass/fail.

