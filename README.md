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
```

## Running The Builder

List available effect-engine versions:

```powershell
python main.py --list-versions
```

Run a specific version and pass through engine arguments:

```powershell
python main.py --version-id v27.3 -- --template template.xsq --audio 13.wav --no-prompt
```

Run several versions with the same engine arguments:

```powershell
python main.py --version-id v24.3 --version-id v27.3 -- --template template.xsq --audio 13.wav --no-prompt
```

## Notes

- Legacy wrappers and experimental scripts were moved instead of deleted.
- The current restructure is intentionally conservative: proven engine code was promoted into the new folders with minimal behavioral changes.
- AI bridges are placeholders by design. Rule-based sequencing remains the default path.
