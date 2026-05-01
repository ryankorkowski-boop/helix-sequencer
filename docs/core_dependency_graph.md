# Core Dependency Graph

## Scope
- Analyzed `16` files under `core/` using static AST import parsing.
- Edges represent `core.*` import dependencies only.

## Import Graph (Module -> Imports)
- `audio_intelligence` -> lazy_imports, model_parser
- `audit` -> (none)
- `birdsong_engine` -> (none)
- `chronoflow` -> helixualizer, lazy_imports
- `effect_engine` -> audio_intelligence, audit, birdsong_engine, chronoflow, engine_style_catalog, helixualizer, lazy_imports, matrix_intelligence, model_parser, polish, rhythm_intelligence, snowman_band
- `engine_profiles` -> effect_engine
- `engine_style_catalog` -> (none)
- `feature_state` -> (none)
- `helixualizer` -> lazy_imports
- `lazy_imports` -> (none)
- `matrix_intelligence` -> (none)
- `model_parser` -> (none)
- `polish` -> (none)
- `rhythm_intelligence` -> (none)
- `sequence_builder` -> effect_engine, engine_profiles
- `snowman_band` -> (none)

## Topological Build Order (Least-dependent first)
1. `audit`
2. `birdsong_engine`
3. `engine_style_catalog`
4. `feature_state`
5. `lazy_imports`
6. `matrix_intelligence`
7. `model_parser`
8. `polish`
9. `rhythm_intelligence`
10. `snowman_band`
11. `helixualizer`
12. `audio_intelligence`
13. `chronoflow`
14. `effect_engine`
15. `engine_profiles`
16. `sequence_builder`

## Inferred Execution Order
main.py -> core.sequence_builder -> core.effect_engine
- effect_engine
- audio_intelligence
- lazy_imports
- model_parser
- audit
- birdsong_engine
- chronoflow
- helixualizer
- engine_style_catalog
- matrix_intelligence
- polish
- rhythm_intelligence
- snowman_band

## High-Risk Core Targets
- `effect_engine` imports: audio_intelligence, audit, birdsong_engine, chronoflow, engine_style_catalog, helixualizer, lazy_imports, matrix_intelligence, model_parser, polish, rhythm_intelligence, snowman_band
- `audio_intelligence` imports: lazy_imports, model_parser
- `self_improving_scoring` is not present on this branch.
- `spatial_mapping_engine` is not present on this branch.
