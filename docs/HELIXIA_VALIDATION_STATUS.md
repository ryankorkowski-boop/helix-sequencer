# Helixia Validation Status

## Implemented Systems

- `helixville4/helixia_manifest.json`
- `helixville4/xlights_rgbeffects.xml`
- Helixia layout generator: `tools.build_helpers.helixia.build_helixia_layout`
- xLights XML generator: `tools.build_helpers.helixia_xlights.build_helixia_xlights_layout`
- Layout parser: `core.model_parser.parse_layout`
- Layout health checks: `helix_layout.layout_health.build_layout_health_report`

## Tested Systems

- Manifest generation.
- Required special lots.
- Fibonacci tree lot constraints.
- Native model type coverage.
- House style metadata and cost estimates.
- Parser-valid xLights XML generation.
- Required model family coverage.
- Complex prop submodel coverage.

## Parser-Valid Evidence

- `helixville4/xlights_rgbeffects.xml` parses with `xml.etree.ElementTree`.
- `core.model_parser.parse_layout` parses current Helixia XML.
- Temp regeneration produced byte-identical `xlights_rgbeffects.xml`.
- Current parser counts match temp-regenerated parser counts.

## Current Counts

- Houses: 12
- Special lots: 11
- Fibonacci trees: 13
- Root models: 105
- Groups: 49
- Submodels: 345
- Total parsed models including submodels: 450

## Remaining Validation Gaps

- xLights GUI import has not been recorded as validated.
- Production controller/channel-output validation has not been recorded.
- Visual review remains separate from parser validity.
- Manifest embeds the absolute `output_layout` path, so temp-regenerated manifests differ only by environment path.

## Validation Levels

- Parser-valid: XML is syntactically valid and accepted by the repo parser.
- xLights import-validated: XML has been opened/imported successfully in xLights and any import warnings are recorded.
- Production-ready: parser-valid, xLights import-validated, visually reviewed, channel-safe, and regression-protected.

Current status: parser-valid, not yet recorded as xLights import-validated or production-ready.
