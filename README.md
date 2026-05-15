# xLights Auto Sequencing Core

This workspace has been restructured around a smaller active surface:

- `core/` contains the sequencing engine, audio analysis, model parsing, and build orchestration.
- `xlights/` contains the legacy-derived XSQ writer helpers and the effect catalog cache.
- `tools/` contains shared utilities and preview rendering.
- `ai/` contains explicit opt-in bridge stubs for future model integrations.
- `archive/legacy_versions/` preserves older wrappers, lab scripts, and legacy entrypoints.

## Active Structure

```text
core/
ai/
xlights/
tools/
tests/
archive/legacy_versions/
main.py
README.md
requirements.txt
AGENTS.md
TASKS.md
ROADMAP_BETA_TODO.md
```

## Beta Readiness

The current beta-readiness plan is tracked in:

- `ROADMAP_BETA_TODO.md` — autonomous beta-version roadmap and task order.
- `TASKS.md` — short entrypoint for humans and coding agents.
- `docs/SUPPORT_MATRIX.md` — supported beta platforms, inputs, and boundaries.
- `docs/BETA_POLICY.md` — data-use, learning, and asset-safety policy.

Beta expectations:

- Use copies of layouts, templates, and audio inputs.
- Treat generated output as beta-quality until manually reviewed in xLights.
- Do not commit private tester files, songs, layouts, templates, screenshots, or generated outputs unless explicitly approved.
- The near-term goal is a safe, inspectable beta GUI path, not perfect production-quality auto-sequencing.

## Running The Builder

Launch the maintained GUI control center (preferred day-to-day workflow):

```powershell
python gui_launcher.py
```

or use:

```powershell
launch_sequencer_app.cmd
```

List active sequencing profiles:

```powershell
python main.py --list-profiles
```

Run the active master profile and pass through engine arguments:

```powershell
python main.py --profile master -- --template template.xsq --audio 13.wav --no-prompt
```

Legacy version IDs still work as explicit compatibility fallbacks:

```powershell
python main.py --profile v27.3 -- --template template.xsq --audio 13.wav --no-prompt
```

## Helixville Layout Builders

Build or refresh the dedicated Helixville 3D test show folder from your allmodels / GP baseline:

```powershell
python tools/build_helixville_layout.py
```

Output is written to `helixville/`, including:

- `helixville/xlights_rgbeffects.xml`
- `helixville/xlights_rgbeffects.xbkp` (when source backup exists)
- `helixville/helixville_manifest.json`

Build the aligned legacy-256 based Helixville3 layout with lyric/singing-face groups:

```powershell
python tools/build_helixville3_layout.py
```

Output is written to `helixville3/`, including:

- `helixville3/xlights_rgbeffects.xml`
- `helixville3/helixville3_manifest.json`
- `helixville3/HELIXVILLE3_LAYOUT_NOTES.txt`

Legal source notes:
- `docs/helixville3_legal_sources_2026-04-23.md`

## hardKor AC Placement

Enable the AC-first hardKor placement machine:

```powershell
python main.py --profile v27.3 -- --template template.xsq --audio 13.wav --hardkor --ac-lights-only --no-prompt
```

hardKor rules and source references:
- `docs/hardkor_rulebook_2026-04-23.md`

## AAATEST Variant Pack

Generate a multi-variant comparison pack (`.xsq` + `.mp4`) using `13.wav`:

```powershell
python tools/generate_aaatest_pack.py
```

Outputs are written to `aaatest/`.

## Notes

- The active maintained entrypoint is the `master` profile, currently backed by the stable `v27.3` tuning inside `core/effect_engine.py`.
- Legacy wrappers and experimental scripts were moved instead of deleted.
- The current restructure is intentionally conservative: proven engine code was promoted into the new folders with minimal behavioral changes.
- AI bridges are placeholders by design. Rule-based sequencing remains the default path.

## Learning Policy

Helix scoring memory is limited to Helix-generated sequence reports that carry the internal Dream Sequence Weaver watermark metadata. It does not learn from copyrighted songs, licensed third-party sequences, template files, imported third-party XSQs, or arbitrary user-provided sequence folders. Audio analysis may guide a one-time render, but persistent learning stores only Helix decisions, generated-score metrics, and generated sequence context.
