# GUI Quality Options Contract

Status: Slice 10 contract helper  
Behavior change: none unless GUI code explicitly imports and uses it

## Purpose

The GUI should eventually expose Helix output-quality controls without overwhelming the user or bypassing safe rollout. Slice 10 defines a validated options shape before any launcher or GUI internals are modified.

`tools/build_helpers/gui_quality_options.py` provides safe defaults and a future CLI-mapping contract for quality-related controls.

## Safe Defaults

Default options:

```json
{
  "quality_preset": "showcase",
  "style_preset": "general",
  "enable_prop_roles": true,
  "enable_density_restraint": true,
  "enable_section_identity": true,
  "enable_palette_discipline": true,
  "enable_motif_memory": true,
  "enable_manual_locks": true,
  "report_only": true
}
```

## Quality Presets

Supported quality presets:

- `general`
- `showcase`
- `vendor`

## Style Presets

Supported style presets:

- `general`
- `classic_christmas`
- `edm`
- `rock`
- `ballad`
- `comedy`
- `spooky`
- `patriotic`

## Report Modules

Supported report modules:

- `prop_roles`
- `density_restraint`
- `section_identity`
- `palette_discipline`
- `motif_memory`
- `manual_locks`

## Important Boundary

This module does not:

- modify GUI files
- render effects
- write XSQ data
- mutate layout files
- call the active engine
- guarantee all CLI args are already supported by the current runner
- change current output by default

It only normalizes GUI-facing options and documents the intended future mapping.

## Manual Lock Safety

Manual locks remain report-only in Slice 10. The helper refuses a configuration where manual locks are enabled while `report_only` is false.

This preserves the rollout order:

1. Load options.
2. Generate reports.
3. Validate reports.
4. Later, wire enforcement after explicit review.

## Example

```python
from tools.build_helpers.gui_quality_options import normalize_gui_quality_options

options = normalize_gui_quality_options({
    "quality_preset": "vendor",
    "style_preset": "classic_christmas",
    "enable_motif_memory": False,
})

print(options.as_dict())
print(options.enabled_report_modules())
print(options.cli_args())
```

## Future CLI Mapping

The helper can produce future-facing CLI-style arguments such as:

```text
--quality-gate-preset showcase
--helix-style-preset general
--quality-report-only
--enable-quality-report-module prop_roles
--enable-quality-report-module density_restraint
```

GUI code should only pass arguments that the active command actually supports. This method is a documented mapping target, not proof that every argument is already implemented in `core.sequence_builder` or the current GUI launcher.

## Validation

Run:

```bash
PYTHONPATH=. pytest tests/test_gui_quality_options.py
```

Recommended combined validation for Slices 2-10:

```bash
PYTHONPATH=. pytest tests/test_prop_roles.py tests/test_restraint.py tests/test_section_identity.py tests/test_palette_discipline.py tests/test_motif_memory.py tests/test_manual_locks.py tests/test_explainable_variant_scoring.py tests/test_regression_snapshots.py tests/test_gui_quality_options.py
```

## Future Wiring Rule

Wire this into the GUI only after the active command-line/reporting path supports the corresponding options. The first GUI integration should be report-only and should not silently alter generated output.
