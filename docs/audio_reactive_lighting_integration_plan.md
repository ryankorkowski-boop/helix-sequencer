# Audio-Reactive Lighting Integration Plan

## Scope

This plan records quick, safe ways to adapt ideas from open-source and adjacent audio-reactive lighting tools into Helix without replacing the current core engine. The preferred path is to add small rule-based modules that consume `AudioAnalysisResult.feature_state_frames` and `beat_feature_timeline`, then feed existing effect placement and preview systems.

## Dependency Status

- `madmom` 0.16.1 source was downloaded to `tmp/audio_tool_downloads/madmom-0.16.1.tar.gz`.
- `madmom` install is blocked on this Windows Python 3.12 machine by native C extension build requirements: Microsoft Visual C++ 14.0 or greater is required.
- `essentia` and `essentia-tensorflow` have no matching pip distributions for this Python 3.12 Windows environment.
- Current safe baseline remains `librosa`, `numpy`, `scipy`, and the optional fallback wrapper in `helix_sequencer.audio_pipeline`.

## Fast, Safe Integrations

### 1. LedFx-style effect registry

LedFx is useful as an architecture model: audio input is transformed into real-time effects for multiple LED devices, with selectable effects and device configuration. For Helix, copy the pattern, not the GPL code.

Safe integration:
- Add a small `core/audio_reactive_effect_catalog.py` with metadata-only effect definitions.
- Fields: `name`, `family`, `required_features`, `energy_band`, `beat_gate`, `density`, `conflicts`, `preferred_models`.
- Feed this catalog into `core.effect_engine` placement mode selection.
- Keep it rule-based and deterministic.

Quick win:
- Start with 8 effects: `bass_pulse`, `mid_sweep`, `treble_sparkle`, `downbeat_flash`, `energy_wave`, `quiet_shimmer`, `build_ramp`, `drop_burst`.

### 2. p5.js FFT band model

p5.sound exposes simple FFT concepts: waveform, frequency bins, smoothing, named bands such as bass/mid/treble, and centroid. Helix already has equivalent data in `feature_state_frames`.

Safe integration:
- Add named band helpers: `bass`, `low_mid`, `mid`, `high_mid`, `treble`.
- Derive those from existing spectral features instead of adding browser dependencies.
- Use smoothing values similar to p5 defaults for stable effect intensity.

Quick win:
- Convert `low/mid/high` in `feature_state_frames` into effect parameters:
  - low -> scale, brightness, bass props
  - mid -> motion width, arches, house outlines
  - high -> sparkles, stars, snowflakes

### 3. QLC+ audio-trigger routing

QLC+ audio triggers map volume and spectrum bars to DMX channels, functions, virtual console widgets, sliders, and cue-list steps. Helix can use the same idea as a sequencer routing layer.

Safe integration:
- Add an `audio_trigger_routes` section to profile/config data.
- Route feature thresholds to existing effect actions rather than direct low-level writer changes.
- Example route: `high > 0.70` triggers sparkle layer on stars; `low > 0.75` triggers whole-house pulse.

Quick win:
- Build a `core/audio_trigger_routes.py` module with pure functions and unit tests.

### 4. OpenLightShow weighted rotation and conflict rules

OpenLightShow’s best transferable idea is not the rendering itself. It is weighted effect selection, presets, and conflict prevention.

Safe integration:
- Add effect weights and conflict groups to Helix style profiles.
- Prevent mutually noisy effects from stacking, such as strobe plus full-house flash plus high-density sparkle.
- Use `beat_feature_timeline` to select effects per segment or phrase.

Quick win:
- Add conflict groups:
  - `full_intensity`: strobe, drop_flash, full_house_white
  - `dense_texture`: sparkle_storm, snow_noise, starburst
  - `large_motion`: sweep, spiral, chase_wave

### 5. MusicBeam / projector-laser geometry ideas

MusicBeam uses a projector like an RGB laser and is written for simple contribution of new effects. Its useful ideas are geometric primitives: beams, tunnels, fans, scanners, and radial patterns.

Safe integration:
- Translate geometry primitives into xLights model groups, not raw projector rendering.
- Add pattern descriptors: `fan`, `tunnel`, `scanner`, `radial_burst`, `beam_pair`.
- Map them to existing house props using spatial coordinates.

Quick win:
- Add 2D pattern planner functions that output target groups and timing, then let the existing XSQ writer place actual effects.

### 6. ASLS JSON show-file discipline

ASLS emphasizes plain JSON show files and editable cue/effect structure.

Safe integration:
- Export a Helix intermediate show plan JSON before XSQ writing.
- Keep it non-destructive and schema-versioned.
- Use it as a debug/preview/audit layer.

Quick win:
- Add `outputs/<run>/helix_show_plan.json` with sections, triggers, chosen effects, target groups, confidence, and reasons.

### 7. vvvv / dataflow graph model

vvvv’s transferable idea is dataflow: audio features feed transform nodes, which feed visual/output nodes.

Safe integration:
- Do not add a visual programming dependency.
- Represent Helix decisions as a simple internal graph:
  - audio feature node
  - section node
  - rule node
  - effect candidate node
  - placement node
  - writer node

Quick win:
- Add optional debug graph output to explain why an effect was placed.

### 8. projectM / MilkDrop preset inspiration

projectM parses presets, analyzes PCM with beat detection/FFT, and renders shader visuals. Helix should not directly absorb shader code, but the preset idea is useful.

Safe integration:
- Create Helix preset formulas using a tiny safe expression subset or plain Python functions.
- Inputs: `time_s`, `beat_phase`, `energy_smooth`, `low`, `mid`, `high`, `centroid`.
- Outputs: color, intensity, motion rate, density.

Quick win:
- Add formula-free presets first as data tables, then consider expressions after tests.

### 9. Capture-style visual validation

Capture is primarily a visualizer/preprogramming reference. The useful Helix adaptation is preview confidence, not integration.

Safe integration:
- Improve preview renderer audit scoring:
  - blank-frame detection
  - over-brightness detection
  - prop coverage by section
  - motion density per phrase

Quick win:
- Add a `preview_quality_report.json` next to MP4 renders.

## Recommended Implementation Order

1. Add `core/audio_trigger_routes.py` with threshold-to-action routing.
2. Add `core/audio_reactive_effect_catalog.py` with 8 deterministic effect definitions.
3. Add conflict groups and weights to style/profile selection.
4. Emit `helix_show_plan.json` before XSQ writing.
5. Use `beat_feature_timeline` inside placement scoring.
6. Add preview quality scoring.
7. Only after the above works, revisit optional `madmom` via a Python 3.10/3.11 tool environment or Windows C++ Build Tools.
8. Treat Essentia as a later external extractor, probably via a sidecar environment or command-line extractor, not a required import.

## Guardrails

- Do not copy GPL code from LedFx, QLC+, ASLS, or projectM into Helix core.
- Use observed ideas and public APIs only.
- Keep all new behavior optional behind profile flags until previews and tests prove value.
- Prefer pure rule-based modules before AI calls.
- Keep output deterministic for the same audio/layout/profile inputs.
