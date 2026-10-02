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
python main.py --profile master -- \
  --audio song.mp3 \
  --template template.xsq \
  --output-root outputs/
```

Run a specific version:
```bash
python main.py --profile v27.3 -- \
  --audio song.mp3 \
  --template template.xsq
```

## 📖 Documentation

| Document | Purpose |
|---|---|
| [SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md) | Supported OS, Python, xLights versions |
| [BETA_POLICY.md](docs/BETA_POLICY.md) | Data privacy & beta commitments |
| [BETA_TESTER_FEEDBACK.md](docs/BETA_TESTER_FEEDBACK.md) | Copy/paste checklist for beta testers |
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
```

### Run tests

```bash
python -m pytest -q
```

### Smoke checks

```bash
./scripts/run_smoke.sh
# or on Windows
powershell -File .\scripts\run_smoke.ps1
```

## 🔒 Beta safety notes

- The project is beta software and should be treated as a local-only safety gate, not a production automation platform.
- Use copied, permissioned input files only.
- Keep run manifests and generated outputs in a dedicated output folder.
- See [BETA_POLICY.md](docs/BETA_POLICY.md) and [BETA_TESTER_FEEDBACK.md](docs/BETA_TESTER_FEEDBACK.md) for policy and evidence collection.
