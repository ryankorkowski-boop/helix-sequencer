# True 3D Render Pipeline

Helix now has a renderer-facing bridge over the canonical `SpatialScene`.

## Data flow

`xLights WorldPos XYZ + model geometry -> SpatialScene -> SpatialRenderScene -> perspective 3D renderer`

The preview uses the same leaf-model intensities parsed from the XSQ. It does not invent a second coordinate system. The bridge also carries the model's native XYZ geometry (with bounded sampling for performance), so arches, trees, canes, stars, matrices and other multi-point models render as shapes rather than isolated center lights.

## Modes

`tools/preview_hq.py` accepts `--spatial-mode auto|2d|3d`.

- `auto`: use the perspective 3D renderer when the layout is detected as true 3D; otherwise retain the existing 2D renderer.
- `3d`: require a true 3D layout and fail instead of silently flattening it.
- `2d`: retain the legacy 2D renderer.

The existing `xlights` quality preset remains 1920x1080 at 30 FPS. The 3D renderer uses perspective projection, depth sorting, native model geometry, individual light cores, bloom, and a restrained nighttime ground/horizon treatment.

## Geometry handling

The renderer first tries the model parser's explicit `geometry_points`. If a model does not provide those, it falls back to its virtual pixel map. Geometry is bounded to a maximum of 160 points per model for preview performance while retaining the overall shape.

This is still a preview renderer rather than a replacement for xLights' effect engine. The next natural stage is camera-path control and direct spatial effect-field visualization while keeping this same canonical geometry source.
