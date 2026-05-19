# Codex Roadmap: Birdsong Engine v2 Integration

This roadmap is the handoff for continuing GitHub Issue #2: **Implement Birdsong Engine (Phrase-Based Generative Sequencing Upgrade)**.

Repository: `ryankorkowski-boop/helix-sequencer`  
Working branch: `feature/birdsong-engine-v2`  
Base branch: `feature/restructure-core`  
Primary goal: safely evolve Helix Sequencer from the current v27.3 reactive engine into a generative, phrase-aware, spatially coherent sequencing pipeline without breaking the existing v27.3 fallback path.

---

## 0. Current State

This branch is an experimental Birdsong v2 integration branch. It is **not ready for review** and should remain draft until smoke tests and Birdsong-specific tests pass after the branch is updated against `feature/restructure-core`.

The branch now includes both isolated Birdsong v2 modules and runtime wiring in `core/effect_engine.py`.

Current implementation pieces:

```text
core/birdsong_generative.py   # FeatureState, PhraseEngine, SpatialMap, EnergyWave, BehaviorEngine, RenderEvent
core/birdsong_cognitive.py    # cognitive Birdsong behavior layer
core/beat_grid.py             # musical subdivision helpers
core/choreography.py          # role-based event transforms
core/color_system.py          # deterministic palette/color selection
core/show_director.py         # macro section/intensity direction
core/effect_engine.py         # Birdsong v2 overlay helpers and runtime wiring
tests/test_*birdsong*         # isolated and integration-adjacent Birdsong coverage
```

Important correction from the original handoff: Birdsong v2 is no longer only isolated module work. `core/effect_engine.py` now contains `place_birdsong_v2_overlay(...)` plus runtime calls that can add `birdsong_v2` placements when the existing Birdsong enable/auto confidence gate allows it. Future work must treat this as runtime-affecting code, not documentation-only work.

The older `core/birdsong_engine.py` still exists and must not be deleted; it remains the older bird-call overlay layer used by current paths.

---

## 1. Non-Negotiable Constraints

Do all work incrementally. Do not attempt a full rewrite.

Preserve these behaviors:

- Existing v27.3 profile must keep working.
- `core/sequence_builder.py` dispatch system must remain compatible.
- Existing `core/birdsong_engine.py` must not be removed.
- Existing rule-based/direct-trigger output must remain available as fallback.
- Birdsong v2 must be opt-in or confidence-gated and fallback-safe until proven stable.
- A non-Birdsong/default run must not change stable output behavior.

Architecture constraints:

- Max 5 motifs only: `wave_sweep`, `spiral`, `pulse_cascade`, `orbit`, `sparkle_field`.
- No unconstrained randomness.
- Prioritize temporal coherence over effect variety.
- Prefer deterministic scoring and stable ordering.
- Avoid large monolithic commits.
- Keep systems small, typed, and testable.

---

## 2. Files to Inspect Before Coding

Start here:

```text
core/effect_engine.py
core/birdsong_engine.py
core/birdsong_generative.py
core/birdsong_cognitive.py
core/beat_grid.py
core/choreography.py
core/color_system.py
core/show_director.py
core/sequence_builder.py
core/engine_profiles.py
tests/test_birdsong_engine.py
tests/test_birdsong_generative.py
tests/test_birdsong_cognitive.py
tests/test_beat_grid.py
tests/test_choreography.py
tests/test_color_system.py
tests/test_show_director.py
```

In `core/effect_engine.py`, inspect these symbols before editing:

```text
RuntimeTuning
BirdsongV2Result
birdsong_v2_should_enable
place_birdsong_v2_overlay
build_birdsong_v2_features
birdsong_v2_dynamic_mix
birdsong_v2_event_limit
add_model
main_for
MultiBandAnalysis
```

Important current guard behavior:

```text
birdsong_v2_should_enable(enabled=tuning.birdsong_enabled,
                          auto=tuning.birdsong_auto,
                          confidence=birdsong_result.confidence,
                          min_confidence=tuning.birdsong_min_confidence)
```

That means v2 is currently tied to the existing Birdsong flags/auto-confidence gate. Before review, confirm this is intentional and safe, or add a separate explicit v2 flag/config so v1 Birdsong and v2 Birdsong can be tested independently.

---

## 3. Current Runtime Direction

Target Issue #2 pipeline:

```text
audio → feature extraction → state engine → phrase engine → behavior engine → spatial renderer → xLights output
```

Current branch direction:

```text
FeatureState → PhraseEngine → Motifs → EnergyWave → SpatialMap → EffectScoringEngine → BehaviorEngine → RenderEvent
```

Current `effect_engine.py` overlay direction:

```text
Birdsong enable/auto confidence gate
 → v2 feature snapshot
 → phrase/director/color/choreography update
 → quantized overlay events
 → timing metadata
```

---

## 4. Immediate Readiness Blockers

Do not mark PR #62 ready until all are true:

1. `feature/birdsong-engine-v2` is updated/rebased onto current `feature/restructure-core`.
2. The required smoke gate passes:

```bash
python scripts/ci/run_required_checks.py
```

3. Birdsong-specific tests pass:

```bash
python -m pytest -q \
  tests/test_birdsong_generative.py \
  tests/test_birdsong_cognitive.py \
  tests/test_birdsong_engine.py \
  tests/test_beat_grid.py \
  tests/test_choreography.py \
  tests/test_color_system.py \
  tests/test_show_director.py
```

4. Canonical xLights contract tests still pass.
5. Default/non-Birdsong output path is proven unchanged.
6. Birdsong v2 runtime failures degrade to skipped/metadata-only behavior, not a failed sequence build.
7. The PR body and docs continue to match actual `core/effect_engine.py` behavior.

---

## 5. Recommended Next Codex Step

Focus only on making the existing Birdsong v2 runtime wiring safe and tested. Do not broaden the feature set.

Recommended prompt:

```text
Update/rebase feature/birdsong-engine-v2 onto current feature/restructure-core. Then inspect core/effect_engine.py, especially birdsong_v2_should_enable and place_birdsong_v2_overlay. Do not add new features. First prove that a default/non-Birdsong run is unchanged, and that Birdsong v2 is either explicitly opt-in or safely gated. Run python scripts/ci/run_required_checks.py and the Birdsong-specific pytest command from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Fix only failures required to make the existing v2 wiring fallback-safe.
```

If a separate v2 flag is added, keep defaults conservative and update tests so:

- old Birdsong v1 flags still behave as before;
- Birdsong v2 remains off unless explicitly enabled or intentionally auto-enabled;
- runtime exceptions in v2 do not break sequence generation;
- metadata records skipped/error state clearly.

---

## 6. Acceptance Criteria for Closing Issue #2

Issue #2 should not be closed until all are true:

- FeatureState smoothing/history works.
- PhraseEngine groups audio into 2–8 second phrases.
- Only five motifs are available and used.
- EnergyWave propagation creates spatially coherent effects.
- SpatialMap assigns model roles/coordinates and adjacency.
- Effect selection uses weighted scoring:

```text
score = energy_match * 0.35 + spatial_fit * 0.25 + novelty * 0.20 + continuity * 0.20
```

- BehaviorEngine orchestrates phrase + waves + spatial + scoring.
- v27.3 fallback remains available.
- New path is opt-in or blend-controlled.
- Tests cover isolated modules and key integration points.
- A 20-second Helixville test sequence can be generated without crashes.
- Output subjectively flows rather than simply reacts.

---

## 7. Current Known Risks

The biggest risk is `core/effect_engine.py` complexity. It is large and runtime-critical. Do not edit it unless the change is small, test-backed, and directly tied to preserving fallback behavior.

Second risk: `add_model(...)` may not accept all future parameters such as `color`. The current branch introspects color support before passing `color=`, but this must remain covered by tests.

Third risk: multiple Birdsong systems now exist:

```text
core/birdsong_engine.py       # older bird-call overlay
core/birdsong_generative.py   # new Issue #2 architecture
```

Keep names explicit: use `birdsong_v2` or `birdsong_generative` when referring to the new architecture.

Fourth risk: the branch is behind `feature/restructure-core`; failures may be caused by drift against the cleaned-up smoke-gate base. Update the branch before interpreting final CI status.
