# True 3D Render Pipeline

Helix now has a renderer-facing bridge over the canonical `SpatialScene`.

## Data flow

`xLights WorldPos XYZ -> SpatialScene -> SpatialRenderScene -> 3D camera/light-field renderer`

The 3D preview consumes the same leaf-model intensities parsed from the XSQ. It does not invent a second coordinate system.

## Modes

`tools/preview_hq.py` accepts `--spatial-mode auto|2d|3d`.

- `auto`: use the perspective 3D renderer when the layout is detected as true 3D; otherwise retain the existing 2D renderer.
- `3d`: require a true 3D layout and fail instead of silently flattening it.
- `2d`: retain the legacy 2D renderer.

The existing `xlights` quality preset remains 1920x1080 at 30 FPS. The first 3D renderer uses perspective projection, depth sorting, individual light cores, bloom, and a restrained nighttime ground/horizon treatment.

This is intentionally a first renderer stage. Future work can preserve full model geometry points, add camera paths, and feed spatial effect fields directly into the renderer.
