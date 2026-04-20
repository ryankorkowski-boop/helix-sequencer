# Dream Sequence Weaver

Dream Sequence Weaver is the active one-click xLights auto-sequencer in this workspace. The maintained `master` profile is still powered by the proven `v27.3` core inside [core/effect_engine.py](/C:/Users/User/Desktop/414/core/effect_engine.py), but the pipeline now continues past raw effect placement into audit, polish, multi-variant generation, and automatic winner selection.

## What Changed

- `core/effect_engine.py` remains the placement engine and base tuning source.
- `core/audit.py` adds a super-audit pass for overlap control, intensity balance, section coverage, and musical coherence.
- `core/polish.py` adds post-generation cleanup and enhancement for breathing fades, hook lifts, micro-timing, and color-flow transitions.
- `tools/build_helpers/` now exposes promoted runtime helpers for neighbor flow, all-models coverage, and variant shortlisting.
- `core/sequence_builder.py` and `main.py` still provide the modular entrypoint, but the CLI now supports `--polish`, `--variants`, `--auto-shortlist`, and `--learn-from-my-xsqs`.

## One-Click Workflow

1. Put `template.xsq`, your current `xlights_rgbeffects.xml` or `xlights_rgbeffects.xbkp`, and the target audio file in the workspace.
2. Optionally place favorite high-scoring `.xsq` files in the workspace history folder so the engine can learn preferred palettes and prop behavior.
3. Run the maintained master profile:

```powershell
python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist --learn-from-my-xsqs
```

4. Review the exported `.xsq`, `.report.json`, and `.sequence_notes.txt` in the output family folder.
5. Open xLights only when you want optional artistic tweaks or a final confidence check. Manual cleanup is no longer the default workflow.

## Vendor Quality Achieved

The new success bar is show-ready output in the first pass for the overwhelming majority of runs. The engine now aims for:

- musical storytelling with hooks, builds, drops, breathing space, and call-response,
- lower overlap and clutter through audit-backed conflict cleanup,
- stronger spatial flow through neighbor-aware reactions,
- template and workspace learning from proven prior sequences,
- stem-aware layering with local or Moises-powered source separation when stems are available,
- multi-variant comparison with an optional auto-shortlist winner.

## Command Examples

List profiles:

```powershell
python main.py --list-profiles
```

Run the strongest maintained profile:

```powershell
python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist
```

Run the explicit `v27.3` compatibility profile:

```powershell
python main.py --profile v27.3 -- --template template.xsq --audio song.wav --no-prompt --polish
```

Launch the GUI:

```powershell
python main.py
```

## Output Guarantees

Each run now produces:

- a sequenced `.xsq`,
- a `.report.json` with quality, audit, coverage, neighbor-flow, and shortlist data,
- a `.sequence_notes.txt` file describing readiness and polish actions,
- optional alternate variants when `--variants` is greater than `1`.

If `--auto-shortlist` is enabled, the best-scoring variant is promoted to the canonical output automatically.

## Immediate Verification

Run the test suite:

```powershell
python -m unittest discover -s tests
```

Run a real sequencing pass:

```powershell
python main.py --profile master -- --template template.xsq --audio song.wav --no-prompt --polish --variants 3 --auto-shortlist --learn-from-my-xsqs
```
