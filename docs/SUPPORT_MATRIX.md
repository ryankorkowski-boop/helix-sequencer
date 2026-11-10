# Support Matrix

This document outlines the supported platforms, versions, dependencies, and beta boundaries for Helix Sequencer.

## Operating Systems

| OS | Status | Notes |
|---|---|---|
| **Windows 10/11** | Supported for beta | Primary beta target and expected tester platform. |
| **macOS 12+** | Best effort | Community-supported unless a maintainer records validation evidence. |
| **Linux / Ubuntu 20.04+ / WSL** | Best effort | Useful for CI and developer smoke checks; xLights import should still be validated separately. |

## Python Versions

| Version | Status | Evidence |
|---|---|---|
| **3.11** | Supported for beta | Included in `.github/workflows/helix-ci.yml`. |
| **3.12** | Supported for beta | Included in `.github/workflows/helix-ci.yml`. |
| **3.10 and earlier** | Unsupported for beta | Not part of the declared CI matrix for the beta gate. |

## xLights Versions

| Version | Status | Notes |
|---|---|---|
| **2023.x** | Targeted | README lists this as supported, but beta claims still need artifact/import evidence. |
| **2024.x** | Targeted | README lists this as supported, but beta claims still need artifact/import evidence. |
| **Other versions** | Not promised | Treat as manual validation only until evidence is recorded. |

## Runtime Dependencies

Runtime dependencies are declared in `requirements.txt`. The table below records the declared minimums, not independent manual validation results.

| Package | Declared minimum | Purpose |
|---|---:|---|
| `numpy` | `>=1.26` | Numerical processing. |
| `scipy` | `>=1.11` | Signal/scientific utilities. |
| `librosa` | `>=0.10.2` | Audio analysis. |
| `soundfile` | `>=0.12.1` | Audio file I/O. |
| `numba` | `>=0.59` | Accelerated analysis paths used by audio dependencies. |
| `llvmlite` | `>=0.42` | Runtime dependency for `numba`. |
| `imageio` | `>=2.34` | Image/preview support. |
| `imageio-ffmpeg` | `>=0.5` | FFmpeg bridge for preview/video workflows. |
| `Pillow` | `>=10.2` | Image generation and preview assets. |
| `PyYAML` | `>=6.0` | YAML configuration parsing. |
| `requests` | `>=2.34.2` | HTTP utility dependency. |
| `openai-whisper` | `>=20240930` | Optional/advanced audio transcription path used by current runtime requirements. |
| `pyinstaller` | `>=6.10` | Packaging support. |

## Development and Test Dependencies

Development dependencies are declared in `requirements-dev.txt`, which includes `requirements.txt` first.

| Package | Declared minimum | Purpose |
|---|---:|---|
| `pytest` | `>=8.0` | Test runner. |
| `scikit-learn` | `>=1.4` | Test/development support unless later promoted to runtime. |
| `flake8` | `>=7.0` | Linting. |
| `mypy` | `>=1.8` | Type checking. |
| `pytest-cov` | `>=4.1` | Coverage reporting. |
| `bandit` | `>=1.7` | Security linting. |

## Runtime Assets Required for Beta

A real sequencing run needs copied, user-selected inputs:

- audio file, such as WAV or MP3
- xLights template XSQ
- xLights layout XML/XBKP when the selected path requires layout data
- writable output directory that is separate from source inputs

Private layouts, templates, sequences, screenshots, copyrighted songs, and tester-provided material must not be committed to this repository unless explicit written permission is present in repo docs.

## Clean-Room Smoke Fixtures

Repo-safe fixtures live under `tests/fixtures/beta_demo/`. They are intentionally tiny and synthetic. They prove fixture parsing and smoke-run plumbing, not xLights visual quality or production readiness.

## Graphics and Rendering

| Component | Requirement | Notes |
|---|---|---|
| **GPU Support** | Optional | CPU-only smoke checks should remain possible. |
| **Display** | Not required for headless tests | GUI launch and xLights visual import still require separate manual evidence. |
| **FFmpeg** | Via `imageio-ffmpeg` where possible | Native system FFmpeg may still be needed for workflows outside the beta smoke gate. |

## Known Limitations

- **xLights import evidence:** Generated artifacts must be manually imported/opened in xLights before making production-quality claims.
- **Visual quality:** Structural tests do not prove that a sequence looks good.
- **Unicode paths:** Some xLights asset paths with non-ASCII characters may require manual intervention.
- **Network shares:** SMB paths may work but are not a beta guarantee.
- **Large sequences:** Long shows may require more memory and separate performance validation.
- **Concurrent runs:** Multiple simultaneous sequencer instances should use separate output directories.

## Getting Help

- Check the [README](../README.md) for quick start instructions.
- See [BETA_POLICY.md](./BETA_POLICY.md) for data and privacy information.
- Review existing [GitHub Issues](https://github.com/ryankorkowski-boop/helix-sequencer/issues) for known problems.
- For bugs or feature requests, open a new issue with platform details, reproduction steps, and non-private logs/manifests when available.
