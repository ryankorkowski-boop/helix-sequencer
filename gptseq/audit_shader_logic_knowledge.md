# Shader Logic Knowledge Audit

Date: 2026-04-22

## Shader Corpus
- Shader files analyzed: 68
- Keyword frequency snapshot: [('vec4', 1024), ('vec3', 583), ('vec2', 495), ('dot', 366), ('fract', 118), ('noise', 100), ('mix', 63), ('uv', 45), ('sin', 25), ('time', 9), ('smoothstep', 3), ('cos', 3)]

## Learned Logic Patterns
- Strong vector-math core: heavy `vec2/vec3/vec4` + `dot` usage for spatial transforms.
- Texture/motion basis: frequent `fract`, `noise`, `uv`, and `time` patterns for procedural movement.
- Blend discipline: most effective stacks keep a base layer + detail layer + accent transient layer.
- Coordinate-first control matters more than raw color logic for musically coherent mapping.

## Implemented in Helix
- Added `core/shader_layering.py`:
  - compatibility scoring
  - coordinate uniform hints (`u_focus_x/u_focus_y/u_slice_z/u_path_speed`)
  - dynamic layer stack recommendation based on audio context
- Integrated section-level shader layering output into matrix intelligence planning.

## Next Improvements
1. Add runtime export from matrix plan to GLSL uniform timeline file.
2. Add per-prop shader suitability gating by model geometry (matrix vs tree vs arch).
3. Add contrast-driven strobe guardrails to avoid visual overload.
