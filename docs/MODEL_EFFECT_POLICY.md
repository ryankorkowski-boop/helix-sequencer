# Model-aware effect choices in production

The native effect engine now uses `core/helix_effect_adapter.py` when choosing automatic root-model effects. The recovered policy distinguishes trees, arches, lines, outlines, spinners, matrices, icicles, stars and floods. This provides a production route to Meteors on eligible icicles and Shader on sufficiently resolved matrices.

The production adapter requires both catalog support and an authored effect template. Shader also requires the referenced native `.fs` file to exist. Missing templates or files leave the existing selector in control. The adapter preserves template settings and buffer render style; the policy's suggested render style does not replace authored native settings.

Explicit event effects/templates, manual layer preferences, music-style preferences and learned family effects take precedence. AC models and targeted submodels keep their existing paths. Vocal/face timing remains with the dedicated face router. Small or uncertain models do not receive unsupported spatial effects.

Catalog membership and file existence are structural checks. `native_render_verified` remains false until a specific generated sequence is rendered and reviewed. Shader compilation, additional imported Shader resources and portability require native validation; do not treat a catalog-only decision as proof of visible output.

The original supplied policy/adapter tests are retained with package imports. Integration regressions cover missing resources, native templates, preserved overrides/AC/submodel/voice paths and actual editable effect XML. Tests also verify that explicit On and style-selected Wave take precedence over generic matrix defaults.
