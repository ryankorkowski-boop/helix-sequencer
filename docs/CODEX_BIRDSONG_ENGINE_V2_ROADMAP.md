# Codex Roadmap: Birdsong Engine v2 Integration

This roadmap is the handoff for continuing GitHub Issue #2: **Implement Birdsong Engine (Phrase-Based Generative Sequencing Upgrade)**.

Repository: `ryankorkowski-boop/helix-sequencer`  
Working branch: `feature/birdsong-engine-v2`  
Default/base branch at time of handoff: `feature/restructure-core`  
Primary goal: safely evolve Helix Sequencer from the current v27.3 reactive engine into a generative, phrase-aware, spatially coherent sequencing pipeline without breaking the existing v27.3 fallback path.

---

## 0. Current State at Handoff

A new module has been added:

```text
core/birdsong_generative.py
```

It currently contains the first-pass implementation of the generative architecture:

```text
audio features
 → FeatureState
 → PhraseEngine
 → Motif system
 → EnergyWave propagation
 → SpatialMap
 → EffectScoringEngine
 → BehaviorEngine
 → RenderEvent output
```

This module is intentionally isolated and not yet wired deeply into `core/effect_engine.py`. Do not delete or overwrite the older `core/birdsong_engine.py`; that file is the older bird-call overlay layer and may still be used by current engine paths.

The current `core/sequence_builder.py` dispatches profiles into `core.effect_engine.main_for(...)`, and existing profile dispatch must remain intact.

---

## 1. Non-Negotiable Constraints

Do all work incrementally. Do not attempt a full rewrite.

### Preserve these behaviors

- Existing v27.3 profile must keep working.
- `core/sequence_builder.py` dispatch system must remain compatible.
- Existing `core/birdsong_engine.py` must not be removed.
- Existing rule-based/direct-trigger output must remain available as fallback.
- The new Birdsong v2 path must be opt-in until tests prove it is stable.

### Architecture constraints

- Max 5 motifs only:
  - `wave_sweep`
  - `spiral`
  - `pulse_cascade`
  - `orbit`
  - `sparkle_field`
- No unconstrained randomness.
- Prioritize temporal coherence over effect variety.
- Prefer deterministic scoring and stable ordering.
- Avoid large monolithic commits.
- Keep new systems small, typed, and testable.

---

## 2. Files to Inspect Before Coding

Start here:

```text
core/sequence_builder.py
core/engine_profiles.py
core/effect_engine.py
core/birdsong_engine.py
core/birdsong_generative.py
tests/test_sequence_builder.py
tests/test_birdsong_engine.py
```

Then search for these symbols in `core/effect_engine.py`:

```text
RuntimeTuning
birdsong_enabled
birdsong_auto
birdsong_intensity
add_model
main_for
MultiBandAnalysis
build_neighbor_graph
spatial_awareness
```

Important observation: `RuntimeTuning` already includes fields for Birdsong-style behavior:

```python
birdsong_enabled: bool = False
birdsong_auto: bool = False
birdsong_intensity: float = 1.0
birdsong_min_confidence: float = 0.45
birdsong_profile: str = "wild"
```

Do not assume these are fully wired everywhere. Verify before modifying.

---

## 3. Desired Final Pipeline

The target Issue #2 pipeline is:

```text
audio
 → feature extraction
 → state engine
 → phrase engine
 → behavior engine
 → spatial renderer
 → xLights output
```

The current implementation candidate is:

```python
from core.birdsong_generative import BirdsongPipeline, SpatialMap

spatial_map = SpatialMap.from_model_names(all_model_names)
pipeline = BirdsongPipeline(spatial_map)

events = pipeline.update(features, current_time_s)
for event in events:
    add_model(event.model, event.start_ms, event.end_ms, "birdsong_v2", eff=event.effect)
```

Do not paste this blindly. Locate the real model-name list, real feature frame object/dict, and real `add_model` helper in `core/effect_engine.py`.

---

## 4. Implementation Plan by Milestone

### Milestone 1 — Tests for isolated generative module

Goal: prove `core/birdsong_generative.py` is importable and deterministic before integration.

Add tests in a new file:

```text
tests/test_birdsong_generative.py
```

Minimum tests:

1. `FeatureState` smooths energy and keeps history maxlen 128.
2. `PhraseEngine` returns one of the five allowed motifs.
3. `SpatialMap.from_model_names(...)` assigns stable coordinates and categories.
4. `EnergyWave.update(...)` moves and decays energy.
5. `EffectScoringEngine.select(...)` returns deterministic choices.
6. `BirdsongPipeline.update(...)` returns a list of `RenderEvent` objects for high-energy onset input.

Suggested test feature dict:

```python
features = {
    "time_s": 1.0,
    "energy": 0.9,
    "onset": 0.8,
    "centroid": 0.7,
    "bands": [0.8, 0.4, 0.2],
    "beat_phase": 0.0,
}
```

Run:

```bash
python -m pytest tests/test_birdsong_generative.py
```

Then run broader tests:

```bash
python -m pytest tests/test_birdsong_engine.py tests/test_sequence_builder.py
```

Acceptance:

- New tests pass.
- Existing Birdsong and sequence builder tests still pass.

---

### Milestone 2 — Improve spatial role categories before integration

The current `SpatialMap.from_model_names(...)` uses rough categories:

- `center_ground`
- `high_vertical`
- `horizontal`
- `perimeter`
- `generic`

Normalize this to clearer role names while preserving backwards compatibility in scoring:

Preferred roles:

```text
ground
horizontal
vertical
perimeter
generic
```

Mapping hints:

```python
# ground / bass / drums
["bass", "kick", "drum", "snare", "sub", "floor", "low"]

# vertical / high / sparkle
["star", "flake", "sparkle", "snow", "roof", "top", "high"]

# perimeter / framing
["arch", "cane", "outline", "frame", "border", "perim"]

# otherwise
"horizontal"
```

Update `feature_anchor(...)` so:

```text
low-dominant audio  → ground anchor
high-dominant audio → vertical anchor
mid/default         → horizontal anchor
```

Acceptance:

- Existing tests updated.
- No category mismatch causing effect scoring to collapse.

---

### Milestone 3 — Add external trigger wave bridge

Goal: let existing kick/snare/hat style triggers spawn waves instead of directly adding effects when Birdsong v2 is active.

Add to `core/birdsong_generative.py`:

```python
def spawn_trigger_wave(trigger_type: str, state: FeatureState, spatial_map: SpatialMap) -> EnergyWave | None:
    ...
```

Suggested deterministic behavior:

```text
kick  → ground/low wave, high energy, mostly horizontal
snare → mid wave, upward/horizontal
hat   → high/vertical sparkle wave
```

Also add to `BehaviorEngine`:

```python
def inject_wave(self, wave: EnergyWave | None) -> None:
    if wave is not None:
        self.waves.append(wave)
```

Acceptance:

- Unit tests prove `spawn_trigger_wave("kick", ...)` returns a wave.
- Unknown trigger types return `None`.
- `inject_wave(None)` is safe.

---

### Milestone 4 — Add optional integration in `core/effect_engine.py`

Goal: wire Birdsong v2 into the engine behind a flag without changing default v27.3 behavior.

Do not start here until Milestones 1–3 pass.

Find the real generation loop and the real `add_model(...)` call path. Then add:

```python
from core.birdsong_generative import BirdsongPipeline, SpatialMap
```

Initialize once per sequence/run only when enabled:

```python
birdsong_v2_pipeline = None
if getattr(tuning, "birdsong_enabled", False):
    model_names = ...  # derive from real layout/pools/xsq index
    birdsong_v2_pipeline = BirdsongPipeline(SpatialMap.from_model_names(model_names))
```

Inside the real frame/event loop, after features are available:

```python
if birdsong_v2_pipeline is not None:
    events = birdsong_v2_pipeline.update(features, current_time_s)
    max_events = 4  # start conservatively
    for event in events[:max_events]:
        add_model(event.model, event.start_ms, event.end_ms, "birdsong_v2", eff=event.effect)
```

Critical fallback rule:

- If Birdsong v2 fails or returns no events, old v27.3 logic still runs.
- Do not disable existing direct triggers yet.

Acceptance:

- Default run without `--birdsong` or existing Birdsong flags is identical or functionally unchanged.
- Birdsong-enabled run produces additional `birdsong_v2` placements.
- No exceptions if model list is empty.

---

### Milestone 5 — Add deterministic blend control

Goal: prevent v27.3 and Birdsong v2 from fighting visually.

Add a local dynamic blend value instead of hard switching:

```python
base_mix = getattr(tuning, "birdsong_mix", 0.35)  # add field only if needed
energy = feature_energy
intensity = getattr(tuning, "birdsong_intensity", 1.0)
dynamic_mix = clamp((base_mix * 0.55) + (energy * 0.30) + (intensity * 0.15), 0.0, 1.0)
```

If adding `birdsong_mix` to `RuntimeTuning`, default it low:

```python
birdsong_mix: float = 0.35
```

Usage:

```text
low mix  → old v27.3 dominates
mid mix  → hybrid
high mix → Birdsong v2 dominates selected regions/triggers
```

Start with density limiting only:

```python
max_events = int(2 + dynamic_mix * 6)
```

Only later gate specific old triggers.

Acceptance:

- Birdsong density scales smoothly with energy/intensity.
- No random gating.
- Default off still unchanged.

---

### Milestone 6 — Replace selected direct triggers with wave emitters

Goal: convert some kick/snare/hat events into wave injection when Birdsong v2 is sufficiently active.

Pattern:

```python
if kick_detected:
    if birdsong_v2_pipeline is not None and dynamic_mix > 0.40:
        wave = spawn_trigger_wave("kick", birdsong_v2_pipeline.feature_state, birdsong_v2_pipeline.spatial_map)
        birdsong_v2_pipeline.behavior_engine.inject_wave(wave)
    else:
        # existing v27.3 add_model path
        ...
```

Do this one trigger type at a time.

Recommended order:

1. Hats/high sparkle accents — lowest risk.
2. Snare/mid accents.
3. Kick/bass impacts — highest visual importance; do last.

Acceptance:

- Old triggers remain fallback.
- Waves visibly propagate from correct spatial zones.
- No uncontrolled event explosion.

---

### Milestone 7 — Show Director layer

Goal: add macro-level song shape so output has intro/build/drop/outro behavior.

Create:

```text
core/show_director.py
```

Minimal API:

```python
@dataclass
class DirectorState:
    intensity: float
    section: str

class ShowDirector:
    def update(self, time_s: float, energy: float) -> DirectorState:
        ...
```

Keep it deterministic and simple at first:

```text
intro: early/sparse
build: rising density
drop: high density
outro: decay
```

Use it to influence:

- `max_events_per_frame`
- phrase duration
- wave strength
- Birdsong blend

Acceptance:

- Director is optional and enabled only in Birdsong path.
- It does not require perfect song-section detection yet.
- It improves macro pacing without breaking low-level timing.

---

### Milestone 8 — BeatGrid timing polish

Goal: quantize starts/durations to musical subdivisions while keeping wave movement continuous.

Create:

```text
core/beat_grid.py
```

Minimal API:

```python
class BeatGrid:
    def __init__(self, bpm: float): ...
    def nearest_beat(self, time_s: float) -> float: ...
    def next_beat(self, time_s: float) -> float: ...
    def subdivision(self, time_s: float, division: int = 2) -> float: ...
```

Use real BPM if available from analysis, otherwise default safely to 120 only for tests/debug. Do not make the production output worse by assuming wrong BPM when better tempo data exists.

Apply quantization to:

- RenderEvent start times
- short accent durations
- trigger-wave spawn moments

Do not quantize internal wave movement each frame.

Acceptance:

- Starts align to beat/subdivision.
- Wave travel still feels smooth.
- Wrong/missing BPM fails gracefully.

---

### Milestone 9 — Color system

Goal: give motifs visual identity.

Create:

```text
core/color_system.py
```

Minimal API:

```python
@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

class ColorEngine:
    def update(self, phrase, intensity): ...
    def pick_color(self, model_name: str, energy: float) -> tuple[int, int, int]: ...
```

Motif-to-palette mapping:

```text
wave_sweep     → cool
spiral         → dream
pulse_cascade  → energy
orbit          → festive
sparkle_field  → warm/sparkle
```

Important: verify how `add_model(...)` expects color/palette arguments before passing `color=`. If `add_model` does not accept color, adapt through the existing xLights effect settings mechanism instead.

Acceptance:

- Color system does not crash if `add_model` lacks color support.
- Palette choice is deterministic by motif.
- Brightness scales with energy/intensity.

---

### Milestone 10 — Choreography layer for snowman band/model identity

Goal: make props behave like performers, not generic lights.

Create:

```text
core/choreography.py
```

Role inference from model names:

```text
drum/kick/snare → drummer
guitar          → guitar
bass            → bass
sing/face/mouth → lead
star/flake      → sparkle
```

Minimal API:

```python
class ChoreographyEngine:
    def __init__(self, model_names): ...
    def transform_event(self, event, phrase=None): ...
```

Behavior examples:

- drummer: short, punchy events
- bass: longer ground pulses
- lead/singer: expressive waves, phrase emphasis
- sparkle: Twinkle/Shimmer, lower intensity
- guitar: flowing mid/horizontal motion

Important: `RenderEvent` in `birdsong_generative.py` is currently frozen (`@dataclass(frozen=True)`). If transforming events, either:

1. return a new `RenderEvent`, or
2. make a separate mutable event type in choreography.

Do not mutate frozen dataclasses directly.

Acceptance:

- Role assignment is deterministic.
- Transformed events preserve valid start/end/effect fields.
- Snowman band models gain stable behavioral identity.

---

## 5. Important Code Quality Notes

### Avoid token-limit failure

Codex should work milestone-by-milestone. At the end of each milestone, leave a short checkpoint comment in this roadmap or a small commit message stating:

```text
Completed:
- ...
Remaining:
- ...
Risk:
- ...
```

Do not attempt to implement Milestones 4–10 in one pass.

### Favor tests over guessing

Before editing `effect_engine.py`, inspect the function signatures and real call paths. This file is large and easy to break.

### Be careful with dataclass immutability

`RenderEvent` is currently frozen. Any event post-processing must create replacements rather than mutating.

### Keep deterministic behavior

If randomness is absolutely necessary, seed from stable inputs:

```text
audio filename + phrase start + model name
```

But prefer no randomness.

---

## 6. Suggested Codex Prompts

Use these prompts one at a time.

### Prompt 1 — tests only

```text
Read docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md and core/birdsong_generative.py. Implement only Milestone 1: add tests/test_birdsong_generative.py covering FeatureState, PhraseEngine, SpatialMap, EnergyWave, EffectScoringEngine, and BirdsongPipeline. Do not modify effect_engine.py. Run the relevant tests and fix only failures in the isolated module/tests.
```

### Prompt 2 — spatial roles + trigger bridge

```text
Continue from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Implement Milestones 2 and 3 only. Normalize SpatialMap categories to ground/horizontal/vertical/perimeter/generic, update feature_anchor and scoring compatibility, add spawn_trigger_wave and BehaviorEngine.inject_wave. Add or update tests. Do not wire into effect_engine.py yet.
```

### Prompt 3 — first safe integration

```text
Continue from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Implement Milestone 4 only. Inspect core/effect_engine.py and find the real feature loop, model list, and add_model call path. Wire BirdsongPipeline behind the existing birdsong_enabled flag so default v27.3 output remains unchanged. Add conservative density limiting and safe exception handling. Add tests if there is an existing integration-test pattern.
```

### Prompt 4 — blend and trigger conversion

```text
Continue from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Implement Milestones 5 and 6 incrementally. Add deterministic blend control and convert only one low-risk trigger type first, preferably hats/high sparkle accents, into spawn_trigger_wave injection with fallback. Do not convert kick until tests and generated output are stable.
```

### Prompt 5 — polish modules

```text
Continue from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Implement Milestones 7 and 8: ShowDirector and BeatGrid. Keep them optional and only used in Birdsong v2 path. Add tests. Do not introduce external dependencies.
```

### Prompt 6 — art direction + choreography

```text
Continue from docs/CODEX_BIRDSONG_ENGINE_V2_ROADMAP.md. Implement Milestones 9 and 10: ColorEngine and ChoreographyEngine. Verify add_model color support before passing color args. Because RenderEvent is frozen, transform events by returning replacements. Add tests for palette selection and role-based event transforms.
```

---

## 7. Acceptance Criteria for Closing Issue #2

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

## 8. Current Known Risk

The biggest risk is `core/effect_engine.py` complexity. It is large and already imports many subsystems. Do not edit it until the isolated module is tested. When editing it, use the smallest possible integration point and preserve old behavior.

Second risk: `add_model(...)` may not accept all desired future parameters such as `color`. Inspect before calling.

Third risk: multiple Birdsong systems now exist:

```text
core/birdsong_engine.py       # older bird-call overlay
core/birdsong_generative.py   # new Issue #2 architecture
```

Keep names explicit: use `birdsong_v2` or `birdsong_generative` when referring to the new architecture.
