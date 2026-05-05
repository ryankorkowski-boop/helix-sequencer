# Helix Spatial Abstraction

Helix now uses one spatial intelligence layer for flat, layered, and true 3D layouts.

## Core Rules

- Model geometry is normalized into a shared scene model before routing.
- `center_xyz` and `extents_xyz` are the master truth whenever depth exists.
- `projected_xy` is the front-view fallback used by renderers and flat-layout routing.
- 2D and 3D do not use separate engines. The same primitives and router adapt by layout capability.

## Layout Capability Detection

Helix classifies a parsed layout into one of three capabilities:

- `2d`: no meaningful depth span and no meaningful volumetric props.
- `2.5d`: depth layers exist, but the scene is still mostly planar or facade-like.
- `3d`: the scene has meaningful volumetric depth or dense multi-layer depth structure.

The detector looks at:

- scene-wide `x`, `y`, and `z` span
- how many models occupy distinct depth layers
- how many models have real `z` extent instead of just a center point

## Normalized Scene Model

Every model is normalized into a scene node with:

- `center_xyz`
- `extents_xyz`
- `projected_xy`
- `tags`
- `groups`

Groups are also normalized so routing can fall back from model names to group names without reparsing the layout.

## Front-View Projection

Helix uses a front-view projection for shared 2D consumers such as preview rendering and flat-layout routing:

- horizontal axis: `x`
- vertical axis: `y`
- depth axis: `z`

In other words, front-view projection keeps `x` and `y` visible and flattens depth out of the routing plane when a consumer needs 2D coordinates.

## Shared Spatial Primitives

The spatial layer exposes four reusable primitives:

- `radial_field`
- `directional_wave`
- `proximity_activation`
- `path_travel`

Effect families are routed onto those primitives instead of branching into separate 2D and 3D implementations.

## Fallback Table

| Effect family | 3D / 2.5D route | 2D route |
| --- | --- | --- |
| wave propagation | `directional_wave` using XYZ ordering | `directional_wave` on projected front-view X |
| radial burst | `radial_field` using XYZ distance | `radial_field` on projected XY |
| height mapping | `directional_wave` on real Y | `directional_wave` on projected Y |
| proximity activation | `proximity_activation` using XYZ distance | `proximity_activation` on projected XY |
| trajectory travel | `path_travel` using XYZ path spacing | `path_travel` on projected XY |
| orbit / rotation | `path_travel` over an XZ orbit order | `path_travel` over a projected XY orbit order |
| depth sweep | `directional_wave` on real Z | front-view height mapping on projected Y |

## What Changed In Practice

- Layout ingestion now builds a reusable `SpatialScene`.
- Spatial coordinate lookup reads `projected_xy` from that scene instead of reparsing ad hoc.
- Preview rendering uses the same front-view projection rules as the router.
- Orbit and wave-oriented placement modes can reorder pool models through the shared spatial router.

## Why This Preserves Existing Behavior

- Flat layouts still route intentionally because projected ordering remains deterministic.
- Existing 2D sequences still behave like front-view staging instead of random remaps.
- Depth-aware layouts get real XYZ distance where the capability detector says it is safe to use.
- The routing logic stays modular: one scene layer, one fallback table, one set of primitives.
