# Helix V2 Audio + GUI Development Plan

## Development boundary

This work lives on `helix-v2-audio-gui-lab`. The known-good full-length
256-channel + drummer output remains the regression baseline and is not
modified by this branch until a replacement passes the same checks.

Baseline reference:
- workflow run: 35501245067
- commit: e78d67dca84b7f69760de7c5c5819d7042c98094
- expected output: complete XSQ and complete preview-capable sequence

## Audio analysis goals

Build an independent analysis layer that can combine several detector families:

- beat and tempo estimation
- downbeat/bar candidates
- transient/onset candidates
- low-frequency energy and bass events
- spectral energy bands
- pitch and melodic candidates
- harmonic/chord candidates
- vocal/activity cues
- optional stem-derived event streams
- confidence and provenance for every event

External software may be studied for documented behavior and interoperability,
but Helix will implement its own interfaces, algorithms, identifiers, and
documentation. Do not reproduce distinctive product-specific labels, names,
phrases, or source code from another project.

The analysis result must be consumable by the existing SequencePlan layer.

## GUI goals

Extend the existing GUI rather than replace it. Add a workflow-oriented analysis
area for:

1. Select audio
2. Analyze
3. Inspect timing/event streams
4. Choose analysis components
5. Build sequence
6. Validate
7. Export XSQ

The GUI should expose progress, detector status, warnings, and the location of
generated artifacts. Analysis must run off the UI thread.

## Integration rules

- Keep SequencePlan as the single downstream contract.
- Do not create a second effect-placement pipeline.
- Existing AC-safe output behavior remains the compatibility target.
- Every new detector gets unit tests and deterministic fixtures where practical.
- Preserve legacy implementations; archive rather than delete.
- No external project's distinctive naming is to be adopted merely because it
  appears in that project's UI, source, or documentation.

## First implementation slices

### Slice A — contract
Create the event/feature data model and adapters.

### Slice B — detector adapters
Wrap existing Helix detectors behind the contract. Add additional independent
detectors where they improve timing accuracy.

### Slice C — timing fusion
Combine candidates using confidence, temporal proximity, and detector
agreement. Keep raw streams available for diagnostics.

### Slice D — GUI
Expose analysis controls and a timeline/event summary in the current desktop
GUI.

### Slice E — regression
Generate the baseline XSQ and compare structural invariants before allowing
the new analyzer to become the default.

## Acceptance criteria

A change is not considered ready to replace the baseline unless:

- full song duration is preserved;
- XSQ opens in xLights;
- 256-channel mapping remains intact;
- drummer channels remain present;
- no unexpected always-on channels are introduced;
- sequence-plan validation passes;
- the GUI can run the analysis without freezing;
- analysis provenance is recorded.
