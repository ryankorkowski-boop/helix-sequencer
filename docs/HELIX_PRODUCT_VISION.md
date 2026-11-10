# Helix Product Vision

Status: Directional source-of-truth  
Scope: Helix Sequencer, Helixia, layout intelligence, and source-safe automatic sequencing

## 1. Core Identity

Helix is an automatic sequencing engine for holiday light shows.

Its promise is simple:

> Audio in. Lights out.

Helix should turn audio, layout data, user intent, and safe internal rules into original xLights-ready sequencing output.

Helix is not a clone of any vendor sequence, YouTube show, tutorial, or creator style. Helix is its own sequencing system. It should generate original shows from lawful inputs, deterministic analysis, layout understanding, musical structure, and user-controlled creative direction.

## 2. What Helix Should Become

Helix should become a practical sequencing copilot and automation engine that can:

1. Analyze an audio file.
2. Detect musical sections, beats, accents, energy changes, stems, lyrics, and useful timing cues.
3. Read an xLights layout.
4. Infer prop roles from model names, geometry, groups, submodels, and user notes.
5. Build a role-aware visual plan.
6. Generate source-safe original effect placements.
7. Validate quality, readability, safety, power impact, and layout coverage.
8. Export artifacts that can be inspected, tested, and imported into xLights workflows.

Helix should feel less like a random effect generator and more like a director that understands the stage.

## 3. Design Philosophy

Helix should prioritize:

1. Musicality over noise.
2. Readability over raw density.
3. Structure over randomness.
4. Originality over imitation.
5. User control over black-box magic.
6. Repeatable tests over vibes.
7. Legal/source hygiene over speed.
8. Layout-aware sequencing over generic effects.

The best Helix sequence should feel intentional, emotionally paced, and physically aware of the display it is controlling.

## 4. Source-Safe Learning Boundary

Helix must not ingest, summarize, imitate, or preserve questionable third-party materials.

Forbidden guidance sources include:

1. Paid sequence files without explicit rights for the intended use.
2. Vendor previews or marketplace listings used as style training material.
3. YouTube timing patterns, creator-specific show structure, or tutorial recipes.
4. Private groups, login-only content, scraped forums, transcript dumps, or unclear-rights notes.
5. Any source that forbids scraping, AI training, redistribution, or derivative use.

Allowed guidance sources include:

1. Official xLights documentation for tool behavior.
2. User-authored notes.
3. User-supplied files with explicit confirmation and provenance.
4. Helix-generated experiments.
5. Internal tests, previews, metrics, and user ratings.
6. Open-license examples where terms clearly permit the intended use.

Helix should learn from its own generated outputs and user feedback, not from copied third-party choreography.

## 5. The Three Core Engines

### 5.1 Audio Intelligence

Audio intelligence should transform music into useful structure:

- tempo
- beats
- bars
- sections
- phrase boundaries
- drops
- fills
- vocal/lyric timing
- transient events
- energy curves
- stem-like cues where available
- mood and density estimates

Audio intelligence does not decide the whole show by itself. It feeds the visual director.

### 5.2 Layout Intelligence

Layout intelligence should understand the show as a stage:

- prop names
- model families
- groups
- submodels
- coordinates
- depth/layering
- render order
- channel and controller constraints
- power limits
- AC versus pixel behavior
- character props and performer props

Layout intelligence should infer roles but allow user override.

### 5.3 Visual Direction

Visual direction should convert audio and layout knowledge into original sequencing choices:

- focal target selection
- section-level scene identity
- palette planning
- motion grammar
- density budgets
- prop-family call/response
- character moments
- finale escalation
- darkness/rest usage
- safety and power restraint

Visual direction should produce an inspectable plan before or alongside generated effects.

## 6. Helixia

Helixia is the canonical testing and demonstration layout for Helix.

Helixia should be a playful but serious proving ground:

- houses/lots with different sequencing personalities
- a snowman band
- cactus and tubeman performer props
- traditional holiday props
- matrices and trees
- rooflines, windows, arches, outlines, and accent props
- AC and pixel examples
- simple and advanced layouts for regression testing

Helixia should test whether Helix understands prop roles, staging, depth, character moments, and 2D/3D readability.

## 7. User Experience Goal

The eventual Helix workflow should feel like this:

1. Choose an audio file.
2. Choose or import a layout.
3. Choose a style or direction profile.
4. Run Helix.
5. Review the generated plan, quality report, warnings, and preview artifacts.
6. Export to xLights-compatible files.
7. Iterate with user feedback.

The system should be powerful, but the user should never need to understand every internal module to get a useful result.

## 8. Quality Standard

Helix output should be graded against source-agnostic engineering criteria:

- musical phrase alignment
- focal clarity
- motion coherence
- prop role consistency
- palette discipline
- use of darkness and contrast
- layer control
- section escalation
- layout coverage
- flash safety
- power awareness
- export reproducibility

The quality standard should be implemented through tests and reports, not references to third-party shows.

## 9. Implementation Rule

Every major Helix feature should include:

1. A clear purpose.
2. A small deterministic test.
3. A sample input or fixture.
4. A report field or artifact proving what happened.
5. Source-hygiene compliance.
6. A rollback-safe implementation path.

No feature should be merged only because it sounds cool.

## 10. North Star

Helix should become the system that lets a normal person create a complex, musical, original light show without hand-sequencing every moment.

It should respect artists, respect source rights, respect hardware limits, and still feel magical.

Audio in. Lights out.
