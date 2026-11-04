# Repository audit

Date: 2026-11-04. Scope: static reachability, caller search, and a pytest baseline. This change does not alter sequencing behavior.

The beta roadmap still applies. Do not rewrite `core/effect_engine.py` before the beta safety work. Prefer a wrapper, a staged extraction, or a documented deferral over a deletion that the GUI or CLI might still reach.

## How this was measured

| Check | What it can show | What it misses |
|---|---|---|
| `scripts/repo_reachability_audit.py` | AST imports, including imports inside functions; `import_module("literal")`; `Path / "file.py"` joins; `if __name__ == "__main__"` scripts. Archive is excluded from the graph and counted separately. | Imports built from variables. `tools/core_sandbox.py` loads `core.{name}` from `config/core_feature_flags.json`. `tools/pr14_stem_intelligence_adapter.py` and `tools/audio_intelligence_adapter.py` import modules by string. |
| Name search | A top-level function whose name never appears as a `Name` or `Attribute` anywhere outside archive. | Calls through `getattr`, and functions that are only referenced from inside a dead branch (those still count as referenced). |
| `vulture --min-confidence 80` on `core/`, `xlights/`, `ai/`, and the three entry scripts | Three unused locals, listed below. | Almost all structural dead code. Public names and cross-module imports look "used" to vulture. |
| `python -m pytest` | Whether the tree imports and the unit tests agree with current code. | Real-song XSQ import and rendered MP4 quality. The suite finished in about 18 seconds. |

Re-run the graph with:

```bash
python scripts/repo_reachability_audit.py --json /tmp/repo_audit.json
```

Confidence labels in the findings mean:

- **High:** the cited source shows the behavior, and a repo-wide name search found no other caller.
- **Medium:** static search is clean, but a string import or an external command could still load the module.
- **Low:** not used below. Where a dynamic loader exists, the finding says so.

## Test baseline

Python 3.12.3. Installed for the run: pytest, numpy, PyYAML, Pillow, librosa, scipy, soundfile, scikit-learn. `imageio` and `imageio-ffmpeg` were not installed. `openai-whisper` was not installed.

```text
905 passed, 24 failed, 5 skipped, 1 xfailed, 1 collection error in 18.22s
```

Command: `python -m pytest -q --tb=line -p no:cacheprovider --continue-on-collection-errors`.

The collection error is `tests/test_drum_mapping.py`: it imports `assign_hand` from `animation/drummer_motion.py`. That function does not exist. Hand choice is inlined in `build_drummer_motion` (`"L"` / `"R"`), while the test still expects `"foot"` / `"left"` / `"right"`. **High.** Recommendation: **leave** the motion function; update the test when drummer work resumes. Do not restore `assign_hand` just to satisfy the import.

Failures that are this environment, not product logic: preview and mux tests import `imageio` or `imageio_ffmpeg` (`tests/test_preview_mux.py`, `tests/test_render_xsq_skeleton_preview.py`, and the helix-flow export tests that shell out to the skeleton preview).

Failures that are contract drift, and should not be "fixed" by deleting the newer code:

- Drum classifier tests expect `kick` and `snare`; the code returns `drum_bus`. That matches the confidence gate already recorded in `MASTER_TODO.md`.
- Band geometry and Helixia prop tests disagree on model name sets. `core/snowman_band.py` raises `KeyError: 'composite_submodels'` in one snowman test.
- `tests/test_xsq_validation_tool.py` fails with `No Element entries found in effects container`.

`docs/core_dependency_graph.md` is stale. It says it analyzed 16 core files and that `self_improving_scoring` and `spatial_mapping_engine` are absent. Both modules exist. Regenerate that note from the script after Phase 5, or mark the doc historical. Do not treat it as the current graph.

## What the GUI and CLI actually reach

Counted Python, excluding `archive/`: **630 files, about 96,700 lines.** Archive adds **50 files, about 9,000 lines**, and nothing outside archive imports it.

Operator seeds are `main.py` and `gui_launcher.py`, plus imports and subprocess script paths found from those files. That closure is **94 modules**.

```text
gui_launcher.py
  -> main.py
    -> core.sequence_builder.run_profile
         1. core.effects_orchestration_bridge
              -> core.effects_orchestrator_bridge
              -> helix_intent placement / contract / xsq writer
              -> core.multi_pass_orchestration_director
                   -> timeline, memory, storytelling, cinematography,
                      spatial, show identity, audience energy,
                      iterative convergence, masterpiece evaluator
         2. core.effect_engine_beat_grid.main_for
              -> core.effect_engine.main_for
                   -> xlights.xsq_writer (library + its own unused CLI)
                   -> audio analysis, birdsong_engine, snowman_band,
                      matrix, polish, hardkor, chronoflow, helixualizer
```

`launch_sequencer_app.cmd` does not start `gui_launcher.py` when `gui_launcher_drummer.py` is present. It prefers the drummer GUI. That adds four modules to the closure: `gui_launcher_drummer`, `tools.generate_drummer_ground_truth`, `tools.export_drummer_ground_truth_xsq`, and `tools.validate_xsq_structure` (imported by the export script). The drummer checkbox on that GUI does not add a sequencing module. See finding F2.

Of **114** modules directly under `core/`, **61 are outside** that operator closure. They are tests, one-off tools, or unreferenced. Reachable is not the same as "changes the XSQ". On a default GUI run the orchestrator cluster writes a sidecar sequence. `effect_engine` writes the sequence the user is meant to import. Findings F1 and F4 separate those two outputs.

Profiles: `core/engine_profiles.py` advertises one profile, `master`, implemented as style `v27.3`. `available_profiles()` returns only that profile, so `python main.py --list-profiles` hides the catalog. `resolve_profile()` still accepts any key in `effect_engine.VARIANTS`, and `core/engine_style_catalog.py` defines about **77** `version=` rows from `v2.1` through `v27.3`. Those rows are not separate engines. They are `VariantStyle` records passed into the same `effect_engine.main_for`. **High** that the GUI cannot select them (`values=["master"]`). **Medium** that no external script passes an old `--profile`: the only in-repo callers of `resolve_profile` tested here are `master` and `v27.3`. Recommendation: **document** that beta supports `master` only, and **leave** the catalog until Phase 5. Deleting rows changes CLI behavior for anyone who already passes an old version id.

## Prioritized findings

### F1. Default run writes two sequences, and only one follows the audio

**Recommendation: document now, wrap later. Do not merge the two writers before beta.**

`core/sequence_builder.py` `run_profile` calls `run_effects_orchestration` unless `--no-effects-orchestrator` is present. The GUI never passes that flag.

`core/effects_orchestrator_bridge.py` `build_seed_graph` does not read the audio file. It builds five fixed sections over 30 seconds unless the args contain `--duration` or `--seconds`, which the GUI does not pass. It then writes `{audio}.orchestrated.xsq` on layer `AUTO_Helix_Orchestrated` (`helix_intent/xsq_template_writer.py`).

`effect_engine` then writes the audio-driven XSQ on layer `AUTO_DreamSequenceWeaver_v27_3` (`core/effect_engine.py` around the `auto_layer_name` assignment in the main generate function).

Promotion into the engine template happens only when `--promote-orchestrated-template` is present (`_orchestrator_template_promotion_enabled`). The GUI does not pass it. So the orchestrated file is a sibling, not the engine input.

`RunConfig.promote_orchestrated_template` defaults to `True` in `core/run_spine.py`, but `to_engine_args()` omits the positive flag and `sequence_builder` does not read that field. The dataclass default does not turn promotion on. **High.**

If promotion is switched on later, the engine clears its own auto layer (`CLEAR_MODE = "layer"` in `xlights/xsq_writer.py`) and does not clear `AUTO_Helix_Orchestrated`. The imported file can then contain the synthetic layer and the audio layer together. **High** on the layer names. **Medium** on every effect surviving, because layout sync can still drop rows that do not match the layout.

Risk of deleting the orchestrator: tests and the default CLI both call it. Risk of leaving it: a tester can import `*.orchestrated.xsq` and judge the wrong file.

### F2. The Windows launcher's drummer checkbox does nothing

**Recommendation: document, then fix the GUI wrapper in Phase 2. Do not invent an injection path inside `effect_engine` for beta.**

`launch_sequencer_app.cmd` sets the script to `gui_launcher_drummer.py` when that file exists. `HelixDrummerGui` adds "Enable Drummer V3 in generated 256-channel XSQ" (`drummer_var`, default `True`) and the comment says injection happens in `_run_sequence_with_drummer`. That method is not defined. `_run_sequence` either runs the ground-truth tool chain or calls `HelixGui._run_sequence`. `drummer_var` is never read. **High.**

The ground-truth button is a separate path: `tools/generate_drummer_ground_truth.py`, `tools/export_drummer_ground_truth_xsq.py`, then `tools.render_xsq_skeleton_preview`. It does not call `main.py`. **High.**

README tells operators to run `gui_launcher.py`. The Windows cmd file does not. **High.**

### F3. Several GUI controls do not change the sequence

**Recommendation: document, and correct the GUI command in Phase 2 with tests. Do not change `effect_engine` defaults in the same patch.**

| Control | Default in the GUI | What the engine does | Confidence |
|---|---|---|---|
| Matrix Intelligence off | Checkbox only appends `--matrix-intelligence` when on | `parse_args` sets `matrix_intelligence=True`. Off does not pass `--no-matrix-intelligence`, so the engine stays on. | **High.** `gui_launcher.py` `_run_sequence`; `effect_engine.py` `set_defaults`. |
| Auto Shortlist off while Vendor Bar is on | Vendor Bar defaults on and passes `--vendor-bar` | `main_for` forces `auto_shortlist = True`, `polish_enabled = True`, `variant_count >= 3`, and workspace history on. | **High.** |
| Learn From My XSQs | Defaults on, passes `--learn-from-my-xsqs` | The flag is stored and logged. No branch reads it. `scan_workspace_preferences` sets `learned_from_user_xsqs=False` unconditionally. The help text already says the flag is deprecated. Workspace history still runs because it defaults on, and Vendor Bar forces it on. It only considers XSQ names containing `,v` with a Helix report beside them. | **High** that the checkbox itself is a no-op. **High** that history scanning is a different switch. |
| Birdsong profile, intensity, confidence | Passed through | `effect_engine` reads them and calls `birdsong_engine.place_birdsong_engine`. These do take effect. | **High.** |
| Variants | Passed as `--variants` | Honored, capped at 8 by `self_improving_scoring.plan_variations`. | **High.** |
| Polish off | Passes `--no-polish` | Honored, unless Vendor Bar forces polish back on. | **High.** |

`config/core_feature_flags.json` is read only by `tools/core_sandbox.py` (`importlib.import_module(f"core.{name}")`). It does not affect `gui_launcher.py` or `main.py`. Turning `spatial_mapping_engine` off in that file does not remove it from the product, because the product never imports it. **High.** Recommendation: **document** the file as a sandbox switch. **Leave** `core/spatial_mapping_engine.py` (tests and the sandbox import it dynamically).

### F4. Prime BeatGrid is computed, recorded, then removed before the engine

**Recommendation: document. Do not delete the beat-grid modules. Do not stop stripping flags until a test defines the intended XSQ.**

`run_profile` calls `_apply_prime_beat_grid_defaults`, which prepends `--snap-grid` / `--snap-bpm` for `master` / `v27.3`. The manifest command is built from those args. If the user did not pass a snap flag, `_strip_beat_grid_args` removes them before `effect_engine_beat_grid.main_for`. The GUI never passes snap flags, so the default run strips them. **High.**

`effect_engine.py` has no `beat_grid` or `--snap-` handling. The wrapper's `postprocess_beat_grid_outputs` edits JSON reports and snowman sidecars only, and only when a `BeatGrid` was parsed (`subdivision` required). It does not call `xlights.beat_grid_timing.snap_xsq_timing_tracks`. **High.**

`core/beat_grid_output_postprocess.py` does snap timing tracks (not model effect rows) and skips `*.orchestrated.xsq`. The only production importer found is `tools/beat_grid_validation.py`, a standalone script. **High** that the GUI/CLI do not call it. **Medium** that an operator runs the tool by hand.

`core/sequence_builder_beat_grid.py` is an alternate CLI (`python -m` would work; it has `__main__`). No file imports it. If someone did run it, the snap flags would be explicit and would survive the strip. **High** that the GUI and `main.py` do not use it. Recommendation: **leave** until Phase 5, then either point `main.py` at it or archive it. Do not delete while the flag semantics are still split across three modules (`prime_beat_grid`, `effect_engine_beat_grid`, `beat_grid_output_postprocess`).

`prime_beat_grid_args` is called with `output_root=Path(".")`, not the run's output directory, so BPM discovery looks at the process cwd. Those args are stripped anyway. **High.**

### F5. Birdsong runs twice, and the second run ignores the song

**Recommendation: wrap. Keep both libraries. Stop the synthetic hook from looking like a second sequence.**

With the GUI default, `--birdsong` is passed.

1. `effect_engine` calls `birdsong_engine.place_birdsong_engine` and can write an "AUTO Birdsong" timing track into the XSQ.
2. After that returns, `sequence_builder._run_birdsong_hook` builds 20 seconds of sine-wave energy, calls `birdsong_issue2_runtime.plan_birdsong_runtime`, and writes `birdsong_runtime_manifest.json`. Nothing in the repo reads that file back into an XSQ. The hook does not modify the engine XSQ. **High.**

The other birdsong modules (`birdsong_phrase_engine`, `birdsong_motion`, `birdsong_xsq_export`, and the rest of that set) are outside the operator closure. Tests import them. **High** that `main.py` does not. **Medium** for deletion, because Issue 2 tools may call them by path. Recommendation: **leave** the test-only modules; **document** the hook as a demo sidecar.

### F6. Audio hits are classified, then replaced

**Recommendation: document the precedence. Do not delete the first classifier before beta; it is the fallback when stem lists are empty.**

In `effect_engine` `main_for`'s generate path:

1. `xlights.xsq_writer.analyze` supplies beats, onsets, and spectral curves. This is on the live path (`base.analyze(audio_path)`).
2. Template timing tracks replace those beats, bars, and onsets when `timing_marks_usable` says the template marks cover the song.
3. Spectral centroid then sorts onsets into hats, snares, and kicks.
4. `audio_intelligence.build_stem_analysis` replaces bass peaks, vocal peaks, kicks, snares, and hats when the corresponding stem list is non-empty.

`audio_intelligence` imports `audio.drum_detection`, which imports `audio.drum_classification`. That is how the drum classifier is reachable even though `effect_engine` does not import it directly. **High** on the order of the four steps. The centroid split is not dead; it remains when stem detection returns an empty list.

There is a second full sequencer inside the library the engine uses. `xlights/xsq_writer.py` defines `_legacy_sequence_one_song` (about line 1077), `_v8_2_sequence_one_song` (about line 1442), `sequence_one_song` (about line 1782), `_legacy_main` (about line 2221), and `main` (about line 2293). Repo search finds callers only inside this file. `_legacy_main` and `_v8_2_sequence_one_song` have no callers at all. `main` calls `sequence_one_song` only when the file is executed as a script. `archive/legacy_versions/v1.py` repeats the same three sequencers. `effect_engine` uses `analyze`, `discover_layout`, `load_xsq`, and the XML helpers from this module, so the file cannot be deleted. **High.**

Recommendation: **leave** until Phase 5. The extraction plan should move `_legacy_sequence_one_song`, `_v8_2_sequence_one_song`, `_legacy_main`, and the script `main` / `sequence_one_song` behind a library facade. Risk of editing the file now: **high**, because a syntax error breaks every sequence.

### F7. Identical functions are defined twice in `sequence_builder`

**Recommendation: delete the first copy. Risk: low. Do it in its own small PR with the existing sequence-builder tests, not inside an engine change.**

`core/sequence_builder.py` defines these twice, with identical AST bodies:

| Function | First (dead) | Second (the one Python keeps) |
|---|---|---|
| `_artifact_search_roots` | 162 | 330 |
| `_unique_paths` | 171 | 339 |
| `_snapshot_known_artifacts` | 183 | 351 |
| `_record_changed_artifacts` | 194 | 362 |
| `_known_artifact_paths` | 210 | 378 |
| `_is_known_artifact` | 219 | 387 |
| `_artifact_kind` | 224 | 392 |

The same script reports the bodies identical. **High.** Deleting lines 162–229 does not change behavior. A later edit to only the first copy would also not change behavior, which is why the duplicate is worth removing.

`core/effect_engine_beat_grid.py` has its own `_artifact_search_roots` with the same idea. **Leave** that one; it is a third copy in a different module and is the one the wrapper uses.

### F8. Unreferenced names on otherwise live modules

**Recommendation: leave the large ones until Phase 5. The small API leftovers can be deleted after a grep gate.**

Vulture, 80% confidence, only reported:

- `core/model_parser.py:1078` unused variable `mtime_ns`
- `core/run_manager.py:48` unused variable `exc_type`
- `core/spatial_scene.py:625` unused variable `mtime_ns`

The AST name search (zero references outside archive, including tests) found these on the operator path or in `xlights`. **High** that nothing calls them by name. **Medium** if a future `getattr` list is added; none was found.

| Symbol | Note | Recommendation |
|---|---|---|
| `sequence_builder.available_versions`, `sequence_builder.run_version` | CLI uses `available_profiles` and `run_profile`. | **Delete** with F7, same PR. |
| `engine_profiles.active_profile` | `resolve_profile(None)` already returns the active profile. | **Delete** or **document** as the supported accessor and call it from `main`. Do not keep both patterns without a caller. |
| `effect_engine.build_keyboard_lane` | Body is `build_keyboard_lane_with_routes(...)`. The generate path calls the `_with_routes` function directly. | **Leave** until Phase 5. One-line wrapper, easy to delete later, not worth a monolith diff now. |
| `effect_engine.piano_lights_duration_scale` | Wrapper around `cue_duration_scale`. No callers. | Same as above. |
| `effect_engine.GENERATE_SHOWCASE = False` | The only call of `build_all_models_all_effects_sequence` is inside that `if`. Nothing assigns the flag. | **Leave.** Turning it on would write a second showcase XSQ. Do not delete the function until Phase 5; it is a large block in the monolith. |
| `xlights.xsq_writer` helpers `_name_lookup_keys` through `_collect_effect_elements` | Thin wrappers around `layout_sync` / `timing_tracks`. No callers by those private names. Public wrappers such as `sync_xsq_to_layout` are used. | **Leave** until the facade work. Deleting private wrappers is safe only after confirming no `base._name_lookup_keys` string is built dynamically. None was found. |
| `multi_pass_orchestration_director.MultiPassOrchestrationDirector.correction` | Constructed, never used. `IterativeQualityConvergence` builds its own `ChoreographyCorrectionLoop` and does call `run`. | **Leave** the class. A later cleanup can stop constructing the unused attribute. Risk of removing the class: tests call `ChoreographyCorrectionLoop().run`. |
| `spatial_scene.proximity_activation`, `directional_wave`, `path_travel`, `_scene_bounds` | Module is imported by the operator closure; these functions are not referenced. | **Leave.** They may be the intended spatial API. Deleting them does not speed up sequencing. |

### F9. Parallel packages are real code and are not on the default path

**Recommendation: document and leave. Do not delete for beta. Do not import them into `effect_engine` to "use" them.**

Static orphans (no importer, no `__main__` guard), **high** for "nothing in this repo imports them", **medium** where a tool uses `import_module`:

- `ai/chatgpt_bridge.py`, `ai/deepseek_bridge.py`. README calls `ai/` optional stubs. The bodies return a disabled message and do not call a network API. **Leave.** They are the advertised package, not dead runtime.
- `core/run_config_v2.py`. A second `RunConfig` that `core/run_config.py` does not use. The live one is `core/run_spine.py`, re-exported by `core/run_config.py`. **Delete** only after Phase 4 manifest tests still pass. Risk **low** if the grep stays empty. Not before the manifest work, in case a branch was about to switch to v2.
- `core/ac_band_event_compiler.py`, `core/adaptive_venue_intelligence_engine.py`, `core/autonomous_render_validation_engine.py`, `core/floor_piano_intent_adapter.py`, `core/gui_orchestration_diagnostics.py`, `core/helixville4_band_animation_map.py`, `core/style_governed_orchestration_personalities.py`, `core/temporal_continuity_intelligence.py`, `core/plan/__init__.py` (the package marker; `core/plan/sequence_plan.py` is imported by tests and tools).
- Package markers and unused submodules under `helix_composers`, `helix_intent` (`restraint_engine`, `section_planner`), `helix_knowledge` (`provenance`), `helix_layout` (`audience_readability`, `custom_model_analyzer`), `helix_mapping` (`model_migration_assistant`, `semantic_alias_mapper`), `helix_music`, `helix_preview` (`learning_memory`), `helix_render` (`render_cost_estimator`), `helix_spatial` (`field_sampler`, `music_to_space`, `tunnel_preview`), `helix_style` (`density_adapter`, `motif_memory`, `palette_engine`, `restraint_engine`), `helix/preview/*`, `legacy_ac`, `export/professional_intelligence_export.py`, `xlights/timing_tracks_xml_writer.py`, `tools/audio_intelligence_adapter.py`, `tools/phrase_motif_reuse.py`, and `tools/preview/` modules that are not launched as scripts.

A large second group is imported by tests and often also by `tools/*.py` scripts, and not by `main.py`. Examples: `core/style_engine.py`, `core/style_engine_v2_adapter.py`, `core/power_engine.py`, `core/spatial_mapping_engine.py`, the `core/wadena_*.py` set, `core/helix_flow_*.py`, `helix_knowledge` except `provenance`, `models/working_*.py`, `learning/*`. `tools/style_engine.py` is yet another style engine, used by `tools/run_full_helix_pipeline.py` and `xlights/style_xsq_bridge.py`, not by `effect_engine`. **High** that these are a parallel toolchain. **Low** confidence that every script is abandoned: 94 files have a `__main__` guard and are simply not called by the GUI. Recommendation: **document** them as research or operator tools. The beta support matrix already says archive, old variants, and experimental Helixville folders are unsupported unless intentionally included.

`effects_orchestration_bridge.py` is a re-export of `effects_orchestrator_bridge.py`. **Leave** the re-export. `sequence_builder` imports the shorter name. Deleting it is a rename, not a cleanup win.

Circular imports, static and lazy at runtime: `xlights.xsq_writer` imports `layout_sync`, `timing_tracks`, and `xml_io` at import time; those three import `xsq_writer` inside `_legacy()`. That is why import works. Recommendation: **leave** until the facade extraction. Untangling it without tests around `sync_xsq_to_layout` can drop models from the XSQ. `effect_engine` calls `base.sync_xsq_to_layout` twice in the generate path (once mid-run, once immediately before writing the file). The second call can remove rows the first placement added when names do not match the layout. That is deliberate sync, and it is also a later step that can undo earlier placement. **High** that both calls exist. **Medium** on how many effects a given layout loses. Do not remove the final sync as an optimization.

## Where one process muddles another

1. **Orchestrator sidecar vs engine XSQ** (F1). Same output directory, different files, different clocks (fixed 30s vs the song).
2. **Promotion, if enabled** (F1). Different layer names, so both stacks can remain in one XSQ. The engine then runs layout sync, which can delete rows that are not in the layout.
3. **Beat grid** (F4). Defaults are inserted, written into `command.txt` / the manifest command, then stripped. The recorded command is not the command `effect_engine` sees.
4. **Template timing vs detected beats vs stem hits** (F6). Each step overwrites the previous when its data is "usable" or non-empty. A template with its own beat track changes the sequence even if the audio analysis disagreed.
5. **Vendor Bar vs the other checkboxes** (F3). The engine overwrites shortlist, polish, variant count, and history after the GUI has encoded the opposite choice.
6. **Centroid drums vs `audio.drum_classification`** (F6). Two classifiers. The stem path wins when it returns events. Tests that still expect a raw kick/snare label are asserting the path that lost.
7. **`RunConfig` says promotion defaults on; `sequence_builder` defaults it off** (F1). A reader of the dataclass will predict the wrong pipeline.
8. **`xsq_writer.main` vs `effect_engine.main_for`** (F6). Two sequencers share one module. Running `python -m xlights.xsq_writer` does not run the GUI engine.
9. **Director's unused correction instance vs the convergence loop's live instance** (F8). Same class, two objects, one is called.
10. **Synthetic birdsong manifest vs birdsong timing track** (F5). Same flag, two artifacts, only one is in the XSQ.

## Quick wins vs larger refactors

Quick wins, each as its own PR, after the beta phase that owns that surface:

| Change | Kind | Risk if the tests for that file pass |
|---|---|---|
| Delete the first copy of the seven `sequence_builder` helpers, plus `available_versions` and `run_version` if still unreferenced | delete | Low |
| GUI: pass `--no-matrix-intelligence` when the box is off | wrap | Low. Changes output only for the unchecked case, which today matches the checked case. |
| GUI: when Vendor Bar is on, show that shortlist and polish are forced, or stop the engine force in one place | wrap | Medium. Changes sequences if operators had been unchecking shortlist and expecting it to stick. |
| Relabel or remove "Learn From My XSQs" | document or delete the checkbox | Low for XSQ bytes. The history scanner is a different flag. |
| Point `launch_sequencer_app.cmd` at the README entry, or make `drummer_var` do something real | wrap | Medium until the drummer injection has a test. Today the checkbox is already a no-op, so launching `gui_launcher.py` matches current behavior. |
| Mark `docs/core_dependency_graph.md` historical | document | None |
| Delete `core/run_config_v2.py` after one more grep | delete | Low, but wait until manifest work settles |

Not quick, and not pre-beta:

| Change | Kind | Why it waits |
|---|---|---|
| Facade `run_sequence_job` around `effect_engine.main_for` | wrap | Roadmap Phase 5. The wrapper should record effective args after the beat-grid strip, and should say which XSQ is canonical. |
| Split `xlights/xsq_writer.py` library vs legacy sequencers | wrap, then archive the sequencers | The live `analyze` path sits in the same file as the dead sequencers. |
| One beat-grid implementation | merge | Three implementations disagree about JSON vs timing tracks vs effect rows. |
| One birdsong path | merge | Engine path writes the XSQ. Issue 2 runtime writes a demo manifest. Phrase-engine modules are a third stack. |
| One style engine | merge | `engine_style_catalog` (live), `core/style_engine.py`, `core/style_engine_v2_adapter.py`, `helix_style/*`, `tools/style_engine.py`. |
| Import helix\_\* / wadena / learning into the product | do not | They are not dead, and they are not the beta path. Wiring them in is a behavior change. |
| Delete `archive/` or the 77 style rows | leave | Archive is the historical copy. Style rows are hidden CLI compatibility. |
| Extract `effect_engine.py` by feature | wrap first | Roadmap non-goal before beta. `GENERATE_SHOWCASE` and the keyboard wrappers are the safest internal cuts later, and they are still inside the monolith. |

## How this fits the beta roadmap

`ROADMAP_BETA_TODO.md` immediate order is still the right order. This audit does not insert a rewrite ahead of it.

| Roadmap step | What to do with these findings |
|---|---|
| 1–4. Tasks index, support matrix, beta policy, dependency/CI | Add one paragraph to the support matrix: beta profile is `master` only; `*.orchestrated.xsq` is not the audio sequence; BeatGrid does not move effect rows on the default run; the Learn checkbox does not train on user XSQs. Fix CI so `imageio` / `imageio-ffmpeg` are installed if those preview tests are part of the gate. The current failures in that area are missing modules. |
| 5. Clean-room smoke | Assert the canonical XSQ filename and that the run manifest command matches the args actually passed to `effect_engine.main_for`. That locks F1 and F4 without changing audio analysis. |
| 6. Run manifest | The manifest already exists (`core/run_manager.py` writes `outputs/.../beta/<stamp>/`). Record `orchestrator_promoted: false` and the stripped engine argv. Do not start copying the orchestrated XSQ into the beta folder as the primary artifact. |
| 7. GUI beta mode / dry check | F2 and F3 belong here. Dry check should print the canonical output filename and the flags that will be ignored (`--learn-from-my-xsqs`, matrix off, shortlist off while vendor bar is on). |
| 8–9. Beta README and packaging | Say which file to import in xLights. The Windows cmd file should match that README. |
| 10. Engine facade, only after the above | `docs/EFFECT_ENGINE_EXTRACTION_PLAN.md` (roadmap Phase 5.3) should name the seams this audit found: input validation, artifact names, manifest args, profile dispatch, the `xsq_writer` legacy sequencers, beat-grid postprocess, and the birdsong hook. Extract those as wrappers. Do not start by splitting the generate function. |

Non-goals before beta, repeated because the findings make them tempting: deleting `helix_*`, merging style engines, enabling orchestrator template promotion, turning on `GENERATE_SHOWCASE`, and rewriting drum classification so the red `drum_bus` tests go green. The drummer gate is a product decision already recorded in `MASTER_TODO.md`.

## Appendix: counts from the script

Latest local run of `scripts/repo_reachability_audit.py`:

- 630 Python files outside archive, 96,712 lines
- 50 archive files, 9,033 lines
- Operator closure: 94 modules
- Launcher extra beyond the operator closure: 4 modules
- Outside the operator path but imported by tests: 115 modules (76 of those are also reachable from a `tools/` or `scripts/` `main`)
- Standalone `__main__` scripts not reachable from the GUI/CLI: 94
- Modules with no importer and no `__main__`: 64
- Duplicate top-level function definitions: the seven in `sequence_builder` only
- Top-level functions with zero name references: 80, including test helpers and private wrappers; the ones that matter are in F8
- Import cycles: the three `xlights` pairs listed above

`core/` package line count is dominated by `effect_engine.py` (about 13,100 lines), `audio_intelligence.py`, `engine_style_catalog.py`, `chronoflow.py`, and `snowman_band.py`. `tools/` is the next largest tree (148 files) and is mostly scripts, not the GUI import graph.
