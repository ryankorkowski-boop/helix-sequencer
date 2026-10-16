# Opt-in section composer (Phase 3)

```bash
python main.py --profile master -- --section-composer \
  --template template.xsq --audio original.wav --layout-file layout.xml \
  --no-prompt --no-workspace-history --no-learning-memory
```

The flag is off by default. Existing fixed planners in
`helix_music/section_planner.py` and `helix_intent/section_planner.py` remain
unchanged. `core/section_composer.py` derives a separate measured plan from
the audio already loaded by the effect engine. There are no new downloads,
AI services, external sequences, creator styles or random choices.

Analysis pools chroma and 13 MFCCs into 500-ms frames (larger for long audio),
normalizes descriptor families and builds a self-similarity matrix. Local
checkerboard novelty peaks define boundaries, selected deterministically
by novelty and time with a four-second minimum on both sides. The matrix
has at most 2048 frames, about 32 MiB. Clips shorter than the minimum form
one section with a warning. Boundaries cover the whole signal without gaps
or overlaps. IDs are chronological index/start-time IDs, stable for repeated
analysis of the same samples and settings; they are not persistent edit IDs.

Each section records measured RMS energy normalized against the song peak,
energy/brightness budget, density ceiling, original palette, allowed effect
families and a build/drop/steady marker. These markers describe changes in
measured section energy, not semantic verse/chorus or drop recognition.
Later sections with higher measured energy must have higher budgets; the
plan and Phase 1 quality report warn about violations. Near-absolute silence
creates intentional-restraint windows. A quiet verse is not labeled silence.

`core/section_placement.py` applies the plan inside the existing engine's
successful-placement path, including Birdsong calls and the existing
`energy_wave` route. It does not replace their selectors or add an effect
generator. Expanded group/submodel root unions count against conservative
50-ms density slots. Effects stop at section/restraint boundaries. Failed
placements do not reserve slots. Reservations can remain conservative after
later conflict replacement. Density is a fraction of root props, not a
channel-weighted guarantee for unequal pixel models.

Static palette brightness is capped. RGB targets receive the section
palette; AC/single-color targets retain their source colors. Active template
brightness curves are rejected with a recorded placement reason because a
static slider cannot bound them reliably; bounded curve support is deferred
to Phase 5. Drum-stem requests and performer models/groups bypass these caps,
preserving their timing. Thus total-show occupancy may exceed the budget
when protected performers are active or existing template effects remain.
The engine report includes `section_composer` and placement counters only
when enabled. Existing default reports/XSQ are unchanged.

## Evidence and reproduction

```bash
python -m tools.section_composer_benchmark test_runs/sections
for variant in baseline composed; do
  xvfb-run -a python -m tools.native_preview "test_runs/sections/$variant" \
    --xsq "test_runs/sections/$variant/benchmark.xsq" \
    --audio test_runs/sections/original.wav --xlights /path/to/xLights
done
python -m tools.section_composer_benchmark test_runs/sections --verify-native
HELIX_SECTION_COMPOSER_BENCHMARK=test_runs/sections \
  python -m pytest -q tests/test_section_composer.py
```

The 24-second original synthetic benchmark isolates the existing energy_wave
action builder/placement function and the same budget policy used in the
engine. Native table serialization expresses its actual On placements; it
does not approximate frames. Eight monochrome one-channel nodes represent
the AC target. Baseline and composed runs share audio, actions and geometry.
No whole-band or real-song showcase is implied.

| Measurement | Baseline | Composed |
| --- | ---: | ---: |
| Phase 1 energy/occupancy correlation | 0.273532 | 0.340514 |
| Actual native lit-channel correlation | 0.265961 | 0.338588 |
| Native nonzero channel samples | 612 | 558 |

Both correlations remain below the unchanged 0.5 threshold. The quality
warnings, including the quiet intro's dead air, remain visible. This is a
measured incremental improvement, not professional-quality approval.

`--rgb` generates a separate palette-routing experiment. Its model-presence
correlation improves (0.265961 to 0.338588), while literal lit-channel
correlation decreases (0.265961 to 0.256274): some palette colors set channels
to zero. Structural occupancy estimates must not be presented as native
channel occupancy. RGB palette quality needs separate human/native review.

Native proof uses official xLights 2026.18: 480 frames at 50 ms; H.264/AAC
streams last 24 seconds and start at zero. The first six seconds deliberately
retain the existing route's low-energy threshold behavior. The preview is a
sparse technical fixture. An actual v27.3 engine run also records the plan
and caps. A flag-off run is byte-identical to the parent implementation
(XSQ SHA256 `0c76f81274e02ae79a94f021b0034264a818c91087de83d5cb4603367397b7c6`).

The whole legacy engine's inline settings/palette export retains the native
format limitations documented in Phase 1; this phase does not claim that
every profile now imports natively. The native benchmark covers the actual
isolated placement path. A pre-existing snowman planning `composite_submodels`
error occurred in the separate minimal engine fixture; no full-band proof,
drummer-oracle render approval, human visual approval or controller safety
is established here. Broader existing test/lint/type failures are unchanged.
