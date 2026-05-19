# Birdsong Engine Handoff and TODO

This document is an autonomous handoff and TODO list for continuing the Birdsong Engine implementation (Issue #2).

Files created in this commit:
- core/feature_state.py — lightweight FeatureState with temporal smoothing and history
- core/phrase_engine.py — phrase detection and motif assignment (minimal, deterministic)
- tests/test_feature_state.py — unit tests for FeatureState
- tests/test_phrase_engine.py — unit tests for PhraseEngine

Goal
----
Provide a minimal, fully autonomous starting point so another agent or a later run can continue the implementation with minimal manual intervention. This handoff includes next tasks, testing steps, merge guidance, and design notes.

Quick actions completed
----------------------
- Added a small FeatureState module that wraps raw audio features and keeps a time history.
- Added a small PhraseEngine that creates phrase objects on simple heuristics (onset threshold / energy trend).
- Added unit tests for both modules to validate basic behavior.

How to run tests (locally / CI)
------------------------------
1. Create a virtualenv and install project requirements if any.
2. From repo root:
   - python -m pip install -r requirements.txt  # if requirements exist
   - pytest -q

Files to review before merging
-----------------------------
- core/feature_state.py
- core/phrase_engine.py
- tests/test_feature_state.py
- tests/test_phrase_engine.py

Next prioritized tasks (handoff list)
------------------------------------
1. Integrate FeatureState into existing audio pipeline
   - Wrap existing audio extraction (core/audio_pipeline.py or similar) to call FeatureState.update() each frame.
   - Ensure feature dict keys match: energy, onset, centroid, low, mid, high, beat_phase.

2. Improve PhraseEngine heuristics
   - Replace naive thresholds with tunable config values (exposed via dataclass fields).
   - Use BPM to estimate phrase durations (2–4 bars). Pull BPM from audio pipeline.
   - Add deterministic motif selection mapped to existing motif catalog.

3. Implement EnergyPropagation (EnergyWave) engine
   - Add core/energy_propagation.py with EnergyWave and engine managing waves.
   - Unit tests for spawn/update/near queries.

4. Implement SpatialMap and adjacency graph
   - Add core/spatial_mapper.py reading layouts (helixville manifest) to produce SpatialModel objects.
   - Provide query(position, radius) to return model names.

5. Implement EffectScoringEngine hooking into core/effect_engine.py
   - Map effect properties (intensity, categories) from effect catalog.
   - Provide select_best_effect(context) to choose effect per model/wave.

6. Implement BehaviorEngine orchestrator
   - Use FeatureState, PhraseEngine, EnergyPropagation, SpatialMap, EffectScoring to output SequenceRows
   - Add integration tests generating a 20s sequence on helixville layout

7. CI and PR plan
   - Create a feature branch (recommend: feature/birdsong-engine-implementation)
   - Push changes, open PR, run CI (pytest)
   - Merge small incremental PRs rather than one huge PR. Suggested order:
     a) feature_state + tests
     b) phrase_engine + tests
     c) energy_propagation + tests
     d) spatial_mapper + tests
     e) effect_scoring + tests
     f) behavior_engine + integration tests

Design notes and rationale
--------------------------
- Keep modules small and testable. Each core concept has a dedicated module and tests.
- Avoid heavy external deps. Implement simple math to compute energy trends without numpy to keep CI lightweight.
- Determinism is important: motif selection uses only observed features and deterministic tie-breakers.

For the next AI or human picking this up
---------------------------------------
- Review unit tests included in this commit and run them first.
- Create the next module (energy propagation) following the same style and add tests.
- When integrating with audio pipeline and effect engine, prefer minimal adapter code that translates between interfaces.

Contact notes
-------------
- This handoff was generated autonomously by a GitHub Copilot Chat assistant.
- If anything fails in CI, attach pytest output and I can produce targeted fixes in the next run.


Detailed TODO checklist (actionable)
------------------------------------
- [ ] Merge these initial files to feature branch
- [ ] Integrate FeatureState.update into audio pipeline
- [ ] Add tuning config for PhraseEngine (dataclass)
- [ ] Implement energy_propagation.py + tests
- [ ] Implement spatial_mapper.py + tests
- [ ] Implement effect_scoring.py + tests
- [ ] Implement behavior_engine.py + integration tests (Helixville)
- [ ] Add docs: docs/birdsong_architecture.md summarizing data flow
- [ ] Create end-to-end sample job that consumes audio and writes XSQ (minimal)


End of handoff
--------------

This commit intentionally keeps implementations small and opinionated to maximize autonomy and minimize friction for a follow-up agent or developer.
