# Helix Beta Support Matrix

This document defines the supported surface for the beta version. Anything not listed here should be treated as experimental, legacy, or unsupported until tested and documented.

## Beta support summary

| Area | Beta support level | Notes |
|---|---|---|
| Primary OS | Windows | First-class target for early beta testing because the xLights workflow is expected to be Windows-heavy. |
| Secondary OS | Linux/macOS best effort | Useful for development and CI, but not the first beta packaging target. |
| Python | 3.11 or 3.12 | Pick one or both in CI and keep README aligned. |
| GUI | Tkinter launcher | `python gui_launcher.py` is the preferred day-to-day control center. |
| CLI | Supported for smoke/testing | `python main.py --list-profiles` and profile runs remain required. |
| Active profile | `master` | `master` currently resolves to the stable `v27.3` tuning. |
| Legacy profiles | Compatibility only | Keep available, but do not make them primary beta targets until tested. |
| xLights output | Required | Generated artifacts must be inspectable/importable in xLights or fail with clear logs. |
| AI bridges | Placeholder/opt-in only | Rule-based sequencing remains the default beta path. |

## Supported beta inputs

The beta path should support copied input files only. Testers should keep originals elsewhere.

| Input | Supported form | Notes |
|---|---|---|
| Audio | WAV first; MP3 best effort | WAV should be the clean smoke-test baseline. |
| Template | XSQ copy | Use a copied template file, not a production original. |
| Layout | `xlights_rgbeffects.xml`; XBKP best effort | XML layout is the main target. Backup projects can be documented later if supported. |
| Output directory | Empty or Helix-managed folder | The app should create timestamped run folders and avoid overwriting inputs. |
| Profile | `master` | Other profiles require explicit test coverage before being advertised. |

## Unsupported or experimental before beta readiness

- Production show deployment without manual xLights review.
- Training on user/tester layouts, templates, songs, or sequences.
- Marketplace/model scraping.
- Full legacy profile coverage.
- Large engine rewrites without wrapper tests.
- Claims of parity with expert hand-sequenced shows.
- Auto-overwriting existing layout/template/audio files.

## Minimum beta run expectations

A successful beta run should produce:

- A timestamped output folder under `outputs/beta/` or a user-selected equivalent.
- `run_manifest.json`.
- `command.txt`.
- `helix.log`.
- Generated xLights-compatible artifacts.
- Friendly error text when a run fails.

## Tester expectations

Beta testers should expect:

- Evaluation software, not production software.
- Bugs and incomplete output quality.
- A need to manually inspect and adjust results in xLights.
- A request to share logs/manifests instead of private source assets.

Beta testers should not expect:

- Fully unattended show creation.
- Guaranteed xLights import success for every layout.
- Automatic handling of every custom prop, submodel, or legacy file.
- Persistent learning from their private assets by default.

## CI expectations

CI should prove the documented support surface by running:

- Python compile checks.
- Unit tests.
- `python main.py --list-profiles`.
- A clean-room smoke run once fixtures exist.
- Optional Windows packaging smoke once packaging is ready.
