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

List active sequencing profiles:

```powershell
python main.py --list-profiles
```

Run the active master profile and pass through engine arguments:

```powershell
python main.py --profile master -- --template template.xsq --audio 13.wav --no-prompt
```

Launch the simple GUI (default when no args are passed):

```powershell
python main.py
```

The launcher UI opens as **Helix Sequence Helper** and now includes:
- live activity logs streamed directly from the sequencing engine,
- automatic preference for `allmodels/xlights_rgbeffects.xml` when available,
- optional one-click MP4 rendering after sequence generation,
- helix animation playback while tasks are running (when `helix_twist.mp4` is present).

Legacy version IDs still work as explicit compatibility fallbacks:

```powershell
python main.py --profile v27.3 -- --template template.xsq --audio 13.wav --no-prompt
```

## Packaging

Build the packaged Windows executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Build and sign using an installed code-signing certificate (auto-detected from cert store):

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -Sign
```

Build and sign using a PFX file:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -Sign -PfxPath "C:\path\codesign.pfx" -PfxPassword "your-password"
```

Create a customer bundle in `release/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_customer_bundle.ps1
```

Each bundle now includes:
- `release_checksums.txt` with SHA256 hashes for included files.
- `RELEASE_NOTES_TEMPLATE.md` prefilled with bundle date/version/commit placeholders.

Run release gates (tests + build + smoke checks):

```powershell
powershell -ExecutionPolicy Bypass -File .\release_audit.ps1
```

Run release gates with an end-to-end sequencing smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\release_audit.ps1 -IncludeEndToEnd
```

Run strict release gates that require a valid Authenticode signature:

```powershell
powershell -ExecutionPolicy Bypass -File .\release_audit.ps1 -RequireSignature
```

## Notes

- The active maintained entrypoint is the `master` profile, currently backed by the stable `v27.3` tuning inside `core/effect_engine.py`.
- Legacy wrappers and experimental scripts were moved instead of deleted.
- The current restructure is intentionally conservative: proven engine code was promoted into the new folders with minimal behavioral changes.
- AI bridges are placeholders by design. Rule-based sequencing remains the default path.
