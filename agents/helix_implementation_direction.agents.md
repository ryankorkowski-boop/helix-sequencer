# Helix Implementation Direction Agent Rules

Status: Active  
Audience: Codex, repo agents, and human maintainers

## 1. Mission

Implement Helix as a source-safe automatic sequencing engine.

Do not chase large uncontrolled rewrites. Work in small, testable, reviewable slices.

Primary direction docs:

1. `docs/HELIX_PRODUCT_VISION.md`
2. `docs/HELIX_IMPLEMENTATION_ROADMAP.md`
3. `docs/HELIXIA_LAYOUT_DIRECTION.md`
4. `docs/legal_learning_policy.md`
5. `docs/helix_master_rulebook.md`

## 2. Non-Negotiable Source Rules

Do not add guidance, examples, fixtures, tests, data, or code derived from:

1. Paid sequence files unless explicit rights for the intended use are documented.
2. Vendor previews, marketplace listings, or commercial benchmark notes used as style material.
3. YouTube shows, creator-specific timing, tutorial recipes, or transcript dumps.
4. Private groups, login-only forums, Discord/Facebook scraping, or unclear-rights material.
5. Any material marked no-scraping, no-AI, no-training, no-derivatives, or unclear provenance.

Allowed implementation inputs:

1. User-authored requirements in this repo.
2. User-supplied files with explicit permission/provenance.
3. Official xLights documentation for tool behavior.
4. Helix-generated experiments and internal test fixtures.
5. Open-license material where the intended use is clearly allowed.

When uncertain, block the source and ask for provenance rather than preserving it.

## 3. Preferred Workflow

For each task:

1. Inspect current branch, changed files, and relevant tests.
2. Identify the smallest safe slice.
3. Make only the intended change.
4. Add or update tests.
5. Run targeted tests.
6. Report exact files changed, commands run, and results.
7. Do not merge broad or unrelated changes.

## 4. Current Recommended Slice

Start with Helixia and layout intelligence:

1. Strengthen or create Helixia layout tests.
2. Confirm generated XML is deterministic and parseable.
3. Add or verify prop-role metadata.
4. Confirm snowman band, cactus, tubeman, houses/lots, rooflines, matrices, trees, arches, and groups.
5. Emit or validate a layout intelligence report.

Do not add new effect-generation behavior until layout intelligence is proven.

## 5. Do Not Do These Yet

Do not start with:

1. A large GUI rewrite.
2. Full automatic sequencing end-to-end.
3. AI model training.
4. Scraping external sources.
5. Importing third-party sequence files.
6. Massive branch merges.
7. Renaming half the repo.
8. Replacing existing architecture without tests.

## 6. Validation Commands

Agents must inspect the repo before assuming exact commands.

Likely commands include:

```bash
PYTHONPATH=. python -m pytest
PYTHONPATH=. python -m pytest tests/test_helixia_layout.py
PYTHONPATH=. python -m pytest tests/test_professional_sequence_intelligence.py
```

If these tests do not exist or fail for unrelated reasons, report the exact issue and propose the next smallest correction.

## 7. Commit Rules

Good commit shape:

- one purpose
- small diff
- tests or docs included
- no unrelated formatting churn
- no generated file changes unless intentional

Commit message examples:

```text
docs: add Helixia layout direction
test: validate Helixia performer props
feat(layout): emit Helixia role metadata
fix(layout): stabilize generated group ordering
```

## 8. Required Reporting Format

At the end of an agent run, report:

1. Current branch.
2. Files changed.
3. Tests run.
4. Test result.
5. Risks or skipped items.
6. Exact recommended next step.

## 9. Source-Hygiene Pre-Merge Check

Before opening or merging a PR, search for risky retained guidance:

```text
training_mode
training_use
vendor benchmark
YouTube-grade
creator-specific
source-specific
paid sequence
transcript dump
scraping
no provenance
```

Protective policy references are allowed, but source-derived guidance is not.

## 10. Principle

Build the stage before the show.

For Helix, that means:

1. layout truth
2. metadata truth
3. audio truth
4. visual plan
5. effect placement
6. quality report
7. export
8. GUI polish
