# v28.1 Legacy GUI Patch

This patch introduces the current Helix pipeline to the legacy GUI as the first v28 style lane.

## Naming

- `v28` = current Helix pipeline family
- `v28.1` = Style 1

## Already added

- `archive/legacy_versions/v28.1.py`
  - Thin adapter.
  - Delegates to `variant_engine.main_for("v28.1")`.
  - Does not copy or modify v27.3 logic.

## Required launcher registry edit

In `archive/legacy_versions/sequencer_launcher.py`, add this immediately after the existing `v27.3` `VariantOption`:

```python
    VariantOption(
        "v28.1",
        "Style 1",
        "Current Helix pipeline exposed through the legacy GUI as the first v28 style lane.",
        "Helix v28",
    ),
```

Then add this `StyleTypePreset` near the top of `STYLE_TYPE_OPTIONS`, ideally before `Customer Ready` so the new current pipeline is easy to select:

```python
    StyleTypePreset(
        label="Style 1",
        note="Current Helix pipeline default style lane exposed as v28.1.",
        versions=("v28.1",),
        density=1.00,
        speed=1.00,
        randomness=0.10,
        energy=0.70,
        palette_label="Workspace Match",
    ),
```

## Validation checklist

Run from the repository root:

```bash
python -m py_compile archive/legacy_versions/v28.1.py
python -m py_compile archive/legacy_versions/sequencer_launcher.py
python -m pytest
```

Manual GUI check:

```bash
python archive/legacy_versions/sequencer_launcher.py
```

Expected GUI result:

- `v28.1` appears as `Style 1`
- group label is `Helix v28`
- selecting Style Type `Style 1` selects only `v28.1`
- v27.3 remains unchanged

## Guardrail

Do **not** describe v27.3 as manual-placement-based. This patch only exposes the existing/current pipeline as v28.1.
