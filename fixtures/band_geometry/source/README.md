# Drummer v3 image input

The approved Drummer v3 background PNG lives here as `drummerbg.png`.

The Drummer v3 layer builder reads that image, creates transparent event overlays, and writes a contact sheet for visual review.

`drummerbg.png.b64` is the repo-safe encoded copy used by `tools/build_drummer_v3_assets.py` to restore the PNG deterministically when needed. The lower-level PNG layer builder still exits clearly when a custom source PNG is missing.
