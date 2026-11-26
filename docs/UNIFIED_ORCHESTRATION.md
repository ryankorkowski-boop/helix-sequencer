# Unified orchestration

## Execution paths at baseline

Base commit `3683449`. The CLI and Android call `sequence_builder.run_profile`. The desktop launcher also runs the CLI. The builder creates a run manifest and invokes the effects bridge before the audio has been analyzed. The bridge creates five synthetic sections, sends the intent graph through the multi-pass director and placement planner, and writes a sidecar XSQ when a template is available. Only explicit template promotion feeds it to the renderer.

The main sequence takes a separate path through `effect_engine_beat_grid.main_for` and `effect_engine.run_variant`. The variant loads a copy of the template and layout, analyzes audio, chooses compatible template timing tracks or detected beats and onsets, builds song parts, extracts stems, notes and optional lyrics, and runs the existing feature-specific passes. These passes call `add_model` to select effects and palettes, snap and retry timing, and serialize accepted placements. The timeline validator and audit/polish passes run before XSQ export. Explicit beat-grid postprocessing can modify the exported timing. Native xLights import/render is a separate verification step.

The director and the exporter use seconds and milliseconds, respectively. A separate beat-grid postprocess can move an effect again. Within the exporter the overlay and flash budgets were charged before cooldown, snapping, and placement checks. Unplaceable proposals could exhaust the budget and the eventual window could differ from the one charged. The timeline also removed a lower-priority effect before checking whether the incoming effect passed prop rules. Several analysis outputs are exported for inspection and have no direct effect on live placement.

## Engine responsibilities and maturity

| Existing subsystem | Live input and output | Baseline participation and interaction |
| --- | --- | --- |
| `xlights.xsq_writer`, `core.audio_intelligence` | Audio to envelopes, timing, optional stems and lyric events | Active analysis. Legacy base and stem loaders have separate decoding paths. |
| `rhythm_intelligence`, beat-grid modules | Selected beats/onsets to rhythm diagnostics and optional quantization | Rhythm insights are report-only. Live snapping and final explicit beat-grid postprocessing are separate. |
| `spatial_scene`, `spatial_mapping_engine`, `spatial_choreography_engine` | Layout geometry and spatial motion vocabulary | Scene and spatial chase are live. The standalone mapper is a separate path. Graph spatial choreography runs in the director. |
| `style_engine`, `style_engine_v2_adapter` | Style and intent decisions | Profile, runtime style and palette logic are live. The V2 adapter has its own test path. |
| `adaptive_emotional_storytelling_engine`, `show_identity_engine`, `visual_cinematography_engine`, `live_audience_energy_engine` | Intent graph to section, motif, motion and focal adjustments | Director passes on the seeded sidecar. Audience energy is a heuristic, independent of live audience input. |
| `matrix_intelligence` | Layout and musical marks to matrix plans/cues | Flagged live path with layout gating. |
| `effects.piano_effect` and polyphonic/keyboard functions in `effect_engine` | Harmonic analysis to notes, specialist plan, and keyboard or yard placements | Live placement and diagnostic plan are separate consumers. Piano role preference preserves no-piano fallback. |
| `core.drummer_v3_analysis`, `snowman_band`, `band_sync` | Drum streams and music timeline to performer cues and band planning | Band plan is live diagnostic/export input. Specialized drummer integrations also have dedicated scripts and render workflows. |
| `lyric_interpreter`, `lyric_phoneme_mapper`, vocal and band-face modules | Optional timed words, peaks and phonemes to lyric and face effects | Live routing is conditional. Native face export also has a separate path. |
| `birdsong_engine`, `birdsong_issue2_runtime` | Spectral and note data to accent phrases; optional runtime manifest | Live feature-gated accent path and separate optional hook. |
| `chronoflow`, `helixualizer` | Analysis and layout to trajectory, timing, visualizer exports and piano-neighbor hints | Active via Chronoflow; stereo and piano-roll analysis may decode or analyze independently. |
| `hardkor_engine` | Profile-specific rhythmic groups to effects | Active when its mode is selected. Preserve its effect vocabulary. |
| `effect_layering_engine`, `EffectTimeline` | Candidates to compatible layers | Standalone planner has tests. Live placement uses EffectTimeline and prop rules. |
| `self_improving_scoring`, `sequence_memory_engine` | Runtime report or intent graph to scoring and motif memory | Live scoring and optional persistence are separate from in-run graph motif memory. |
| `autonomous_masterpiece_evaluator`, `autonomous_render_validation_engine`, `choreography_correction_loop` | Graph to scores, readability findings and deterministic edits | Masterpiece and correction run in the director. Readability simulation evaluates intents and cannot validate native renders. |

## Baseline verification

The focused baseline suite for orchestration balance, bridge and promotion, correction, intent graph, palettes, and band sync passed 34 tests. The clean-room beta fixture produced an eight-effect XSQ and a runtime quality score of 81.0 using the default Master profile and its three-model layout. The real-audio baseline uses the repository's existing workflow fixture `Helix Audiolights.mp3` and checked-in Helixville4 layout for local rendering and comparison. The repository's native renderer was unavailable in this environment.
