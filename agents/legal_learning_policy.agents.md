# Helix Legal Learning Policy Agent

## Mission
Build Helix sequencing intelligence from lawful, generalized learning — not copied source material.

This policy applies to all Helix docs, rulebooks, prompt files, tests, examples, generated sequence logic, and PR work.

## Core Principle
Helix may learn general public ideas, methods, and best practices, but must not copy, store, reproduce, or closely imitate protected expression, proprietary sequence files, paid content, forum dumps, tutorial transcripts, or vendor-specific implementations.

Use this model:

- Learn ideas.
- Rewrite in Helix’s own words.
- Generalize into source-agnostic rules.
- Validate with Helix’s own tests and generated outputs.

Do not build Helix from copied source material.

---

## Allowed Learning Sources

Helix may be informed by:

- Public xLights documentation.
- Publicly available tutorials watched or studied normally.
- Public forum discussions read and summarized in original words.
- User observations and handwritten notes.
- The user’s own sequences, layouts, tests, and renders.
- Open-license examples, only when the license clearly allows the intended use.

---

## Forbidden Inputs

Do not scrape, bulk download, mirror, ingest, or preserve:

- YouTube transcripts or captions.
- Tutorial scripts.
- Forum threads or comment dumps.
- Paid course material.
- Vendor sequence files.
- Proprietary LMS/XML sequence logic.
- Downloaded libraries of someone else’s effects.
- Exact timestamps from tutorials.
- Creator-specific “do this like X” recipes.
- Source-specific examples that reveal copied structure.

---

## Forbidden Output Patterns

Do not create rules like:

- “Xtreme Sequences does this at 1:23, so Helix should do the same.”
- “Copy this exact chase/fan/burst/timing pattern.”
- “Recreate this vendor’s chorus look.”
- “Use the same model layout and timing from this tutorial.”
- “Here is a transcript-derived rule set.”

These are not acceptable for Helix.

---

## Safe Transformation Standard

Bad:

> Xtreme uses a red/green chase across arches at 0:43.

Good:

> During high-energy rhythmic phrases, directional motion across linear props may reinforce momentum.

Bad:

> The tutorial says to put this exact shimmer on the mega tree during the vocal phrase.

Good:

> Vocal-forward phrases should preserve visual focus by limiting competing effects and prioritizing face, lyric, or focal props.

Bad:

> A forum user said to use these exact values.

Good:

> Parameter ranges should be tested against layout scale and adjusted to avoid clutter, flicker, or over-saturation.

---

## Required Rule Style

Every Helix rule should be:

- Original.
- Generalized.
- Source-agnostic.
- Testable.
- Not traceable to one tutorial, vendor, forum post, or sequence.
- Written in Helix terminology.
- Capable of being evaluated by validators or scoring systems.

Preferred format:

```yaml
rule_id: phrase_palette_limit
category: visual_clarity
description: Limit dominant colors per phrase to preserve readability.
check: dominant_colors_per_phrase <= 4
severity: medium
fix_strategy: reduce palette using phrase-level color clustering
```

---

## Legal Learning Checklist

Before committing any rule, doc, test, or prompt, confirm:

- Did we write this in our own words?
- Is this a general principle rather than a copied example?
- Does it avoid creator/vendor names unless discussing source hygiene?
- Does it avoid timestamps and tutorial-specific references?
- Does it avoid copied wording?
- Does it avoid proprietary sequence structures?
- Could the rule apply broadly across many layouts and songs?
- Could we explain it as Helix’s own design principle?

If any answer is no, quarantine and rewrite.

---

## Required Documentation

Create or maintain:

- `docs/legal_learning_policy.md`
- `docs/source_hygiene_checklist.md`
- `docs/helix_master_rulebook.md`

These docs must reinforce that Helix learns generalized principles, not copied protected expression.

---

## PR Gate

Before merge, scan for:

- `Xtreme`
- `xLights tutorial`
- `transcript`
- `caption`
- `YouTube`
- `forum dump`
- `scrape`
- `crawl`
- `vendor`
- `timestamp`
- `paid`
- `proprietary`
- `LMS`
- `copied`
- `clone`
- `imitate`

If any are found, review manually before merge.

---

## Required Response When Risk Is Found

If questionable material is found:

1. Stop the merge.
2. Identify the file and line range.
3. Classify risk as low, medium, or high.
4. Remove copied/source-specific content.
5. Rewrite only as generalized Helix-original rules.
6. Re-run tests.
7. Report whether history cleanup is needed.

No questionable source material may remain in tracked files.
