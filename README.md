<!-- CI trigger: repaired drummer preview -->
<!-- PR preview trigger enabled -->
# Helix Sequencer

> **Sequencing, simplified.** Audio in. Lights out. Helix.

A Python-based automated sequencing engine for [xLights](https://xlights.org/), transforming audio into synchronized light show sequences.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** or **3.12** (see [SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md))
- **xLights 2023.x** or **2024.x** (see [SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md))
- Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+)
- ~500MB disk space for dependencies

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ryankorkowski-boop/helix-sequencer.git
   cd helix-sequencer
   ```

2. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python main.py --list-profiles
   ```

### Running the Sequencer

#### GUI (Recommended)

Launch the interactive control center:

```bash
python gui_launcher.py
```

Or on Windows:
```bash
launch_sequencer_app.cmd
```

#### Command Line

List available profiles:
```bash
python main.py --list-profiles
```

Run the active master profile:
```bash
python main.py --profile master -- \\
  --audio song.mp3 \\
  --template template.xsq \\
  --output-root outputs/
```

Run a specific version:
```bash
python main.py --profile v27.3 -- \\
  --audio song.mp3 \\
  --template template.xsq
```

## 📖 Documentation

| Document | Purpose |
|---|---|
| [SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md) | Supported OS, Python, xLights versions |
| [BETA_POLICY.md](docs/BETA_POLICY.md) | Data privacy & beta commitments |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute & development setup |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community guidelines |
| [ROADMAP_BETA_TODO.md](ROADMAP_BETA_TODO.md) | Feature roadmap & priorities |

## 🏗️ Project Structure

```
core/              # Sequencing engine, audio analysis, orchestration
xlights/           # xLights file format (XSQ) writer and effect catalog
tools/             # Shared utilities and preview rendering
ai/                # Optional AI bridge stubs for future integrations
tests/             # Comprehensive test suite
docs/              # Documentation
main.py            # CLI entrypoint
gui_launcher.py    # GUI entrypoint
```

## 🧪 Development

### Setup

```bash
# Install dev dependencies (includes pytest, flake8, mypy)
python -m pip install -r requirements-dev.txt

# Run tests
python -m pytest -q

# Run linting
flake8 core ai xlights tools tests
mypy core ai xlights tools --ignore-missing-imports

# Run security checks
bandit -r core ai xlights tools
```

### Testing

Run the full test suite:
```bash
python -m pytest -q --cov=core --cov=ai --cov=xlights --cov=tools
```

Run specific test:
```bash
python -m pytest tests/test_sequence_builder.py -v
```

Run the beta smoke wrapper:
```bash
scripts/run_smoke.sh
```

On Windows PowerShell:
```powershell
./scripts/run_smoke.ps1
```

The smoke wrapper covers compile/profile-list checks, selected contract tests, and the clean-room beta demo fixture. It does not prove xLights import success, visual quality, controller/channel safety, or production readiness.

## 🔧 Configuration

### Engine Arguments

Passed after `--` when using CLI:

```bash
python main.py -- --audio file.mp3 --template template.xsq
```

Common arguments:
- `--audio FILE` — Audio file to sequence
- `--template FILE` — xLights template XSQ
- `--layout FILE` — xLights layout XML
- `--output-root DIR` — Output directory (default: `outputs/`)
- `--variants N` — Generate N variant outputs (default: 1)
- `--enable-learning-memory` — Enable learning from prior runs
- `--controller-padding N` — Padding around controllers (default: 50)

### Run Tracking

Each execution creates a timestamped directory with:
- `command.txt` — Full invocation command
- `run_manifest.json` — Status, artifacts, timing, errors
- Generated `.xsq` files and logs

Example manifest:
```json
{
  "schema": "helix.run_manifest.v1",
  "status": "completed",
  "run_id": "20260603_100130_123",
  "profile": "master",
  "started_at": "2026-06-03T10:01:30Z",
  "finished_at": "2026-06-03T10:05:45Z",
  "success": true,
  "artifacts": [
    {
      "kind": "effect_placement",
      "path": "outputs/20260603_100130_123/sequence.xsq",
      "recorded_at": "2026-06-03T10:05:45Z"
    }
  ],
  "errors": []
}
```

## 📊 Architecture

### Core Components

**RunConfig** — Structured configuration from CLI arguments
- Defines output location, audio/template paths, enable/disable flags
- Bidirectional conversion to/from CLI arguments

**RunManager** — Lifecycle tracking for each execution
- Creates timestamped run directory
- Records artifacts and manifest
- Captures success/failure with error summaries

**SequenceBuilder** — Main orchestration
- Parses arguments and creates RunConfig
- Wraps engine execution in try/except
- Manages effects orchestration and template promotion

**EffectEngine** — Audio → effects transformation
- Analyzes audio features (tempo, energy, pitch)
- Places effects on xLights models
- Generates XSQ output

## 🐛 Troubleshooting

### Installation Issues

**Problem:** pip install fails on librosa or numpy
```bash
# Solution: Ensure Python 3.11+ and upgrade pip setuptools wheel
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

**Problem:** xLights file not found
```bash
# Solution: Use absolute paths or verify file exists
python main.py -- --template /full/path/to/template.xsq --audio /full/path/to/audio.mp3
```

### Runtime Issues

**Problem:** Run fails with error in manifest
```bash
# Solution: Check run_manifest.json in the timestamped output directory
cat outputs/20260603_100130_123/run_manifest.json
```

**Problem:** Type checking warnings from mypy
```bash
# Solution: These are usually safe to ignore; use --ignore-missing-imports
mypy core --ignore-missing-imports
```

## 📝 License

This project is licensed under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

### Code Quality

All contributions must:
- ✅ Pass `pytest`
- ✅ Pass `flake8` linting
- ✅ Pass `mypy` type checking
- ✅ Include docstrings and tests
- ✅ Follow [CONTRIBUTING.md](CONTRIBUTING.md)

## 💬 Support

- **Questions?** → [GitHub Discussions](https://github.com/ryankorkowski-boop/helix-sequencer/discussions)
- **Found a bug?** → [GitHub Issues](https://github.com/ryankorkowski-boop/helix-sequencer/issues)
- **Security concern?** → See [BETA_POLICY.md](BETA_POLICY.md#bug-reports-and-feature-requests)

## 📚 Additional Resources

- [xLights Documentation](https://xlights.org/)
- [xLights GitHub](https://github.com/xLights/xLights)
- [Python 3.12 Docs](https://docs.python.org/3.12/)

---

**Status:** Beta 🧪

For the latest roadmap and known limitations, see [ROADMAP_BETA_TODO.md](ROADMAP_BETA_TODO.md) and [SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md).
