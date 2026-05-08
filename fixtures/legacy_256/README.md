# Legacy 256 Fixture

This fixture folder defines the legacy 256-channel proving ground for Helix calibration.

The source LMS file is expected to be local-only unless permission explicitly allows committing it.

Expected local paths:

```text
local_fixtures/legacy_256/source_lms/*.lms
local_fixtures/legacy_256/audio/*
```

Committed fixture paths may include converted xLights files only when permission allows:

```text
fixtures/legacy_256/converted/template.xsq
fixtures/legacy_256/converted/xlights_rgbeffects.xml
```

Use this fixture to test whether Helix can produce disciplined, original output on a constrained legacy layout.
