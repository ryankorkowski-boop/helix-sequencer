# Helix Sequencer — Repository Improvement Roadmap

> **Purpose**: Transform Helix from research-stage to production-grade through disciplined engineering practices, clear boundaries, and automated validation.

---

## Executive Summary

The Helix Sequencer repo has strong conceptual engineering (AGENTS.md, MASTER_TODO.md) but conflates research code with operational code, has manual verification gates, and lacks clear module ownership. This roadmap adds:

1. **Module ownership & clear boundaries** — classify every subsystem
2. **Automated verification gates** — turn manual regression tests into CI
3. **Graduated maturity levels** — each subsystem explicitly versioned
4. **Onboarding & maintenance docs** — reduce developer confusion
5. **Controlled cleanup policy** — safe artifact deletion

Expected outcome: a maintainable, professionally-scoped project that keeps research separate from production and validates everything automatically.

---

## Scope & Non-Goals

### In Scope
- Module ownership matrices
- CI automation for regression checks
- Documentation structure (architecture map, decision log, maturity matrix)
- Cleanup policies and golden artifact baselines
- Developer onboarding guides

### Out of Scope (Explicitly deferred)
- Rewriting `core/effect_engine.py` (use facade pattern instead)
- New AI/learning features (focus on proven paths first)
- Marketplace or model scraping
- Supporting every legacy profile

---

## Current State Assessment

| Aspect | Status | Risk |
|--------|--------|------|
| Documentation discipline | ⭐⭐⭐⭐ (Strong) | Low — AGENTS.md & MASTER_TODO.md are excellent |
| Process hygiene | ⭐⭐⭐⭐ (Strong) | Low — Explicit handoff requirements, change ledger |
| Verification | ⭐⭐⭐ (Partial) | **Medium** — Mix of manual & automated, depends on known-good artifacts |
| Module clarity | ⭐⭐ (Unclear) | **High** — Research/experimental code mixed with operational |
| Onboarding | ⭐⭐ (Minimal) | **High** — New contributors must reverse-engineer scope |
| Cleanup safety | ⭐⭐ (Report only) | **Medium** — CLEANUP_CANDIDATES.md exists but isn't enforced |

---

## Improvement Phases

### Phase 0: Foundation & Ownership (Weeks 1–2)

**Goal**: Make it obvious what each module does, who owns it, and what maturity level it is.

#### 0.1 Create Architecture Map (`docs/ARCHITECTURE.md`)

```markdown
# Helix Architecture Map

## Core Production Subsystems

### core/
- **Owner**: @ryankorkowski-boop
- **Status**: active development
- **Maturity**: Beta (proven on internal tests, pending real-song validation)
- **Key modules**:
  - `sequence_builder.py` — orchestration entry point
  - `effect_engine.py` — main sequencing logic (MONOLITHIC, facade planned)
  - `run_config.py` — structured runtime config
  - `run_manager.py` — execution tracking & artifacts
  - `drum_classification.py` — percussion detection (pending real-song validation)

### xlights/
- **Owner**: @ryankorkowski-boop
- **Status**: stable
- **Maturity**: Production (XSQ structure validated against xLights 2023/2024)
- **Key modules**:
  - `xsq_writer.py` — XSQ XML generation
  - `effect_catalog.py` — xLights effect definitions

### tools/
- **Owner**: @ryankorkowski-boop
- **Status**: stable
- **Maturity**: Production (utility functions, minimal dependencies)
- **Key modules**:
  - shared utilities (file I/O, validation, preview rendering)

### ai/
- **Owner**: @ryankorkowski-boop
- **Status**: experimental stubs
- **Maturity**: Prototype (not active in production path)
- **Note**: Planned for future integration; currently bridge-only

## Legacy & Experimental Subsystems

### legacy_ac/
- **Owner**: @ryankorkowski-boop
- **Status**: isolated research
- **Maturity**: Beta (deterministic, clean-room, not integrated with main)
- **Note**: Clean separation for eventual move to separate repo

### helixville*/
- **Owner**: @ryankorkowski-boop
- **Status**: experimental/inactive
- **Maturity**: Prototype (research/demo only)
- **Note**: Do not integrate into main product without explicit review

### archive/
- **Owner**: @ryankorkowski-boop
- **Status**: inactive
- **Maturity**: Legacy (preserve for history, do not modify)

---

## Clear Dependency Graph

```
gui_launcher.py
  ↓
main.py (CLI)
  ↓
core/sequence_builder.py (orchestration facade)
  ├→ core/run_config.py (configuration)
  ├→ core/effect_engine.py (sequencing logic — MONOLITHIC TARGET FOR WRAPPING)
  ├→ core/drum_classification.py (audio analysis)
  └→ xlights/xsq_writer.py (XSQ output)
      ↓
  xlights/effect_catalog.py (effect definitions)

legacy_ac/ (ISOLATED — no cross-imports to core/)
ai/ (EXPERIMENTAL — stubs only, no active integration)
```

---

## Module Ownership Matrix

| Module | Owner | Maturity | Last Validated | Contact |
|--------|-------|----------|-----------------|---------|
| core/sequence_builder.py | @ryankorkowski-boop | Beta | 2026-09-30 | Issue/PR |
| core/effect_engine.py | @ryankorkowski-boop | Beta | 2026-09-30 | Issue/PR |
| core/drum_classification.py | @ryankorkowski-boop | Beta (pending real-song) | 2026-09-30 | MASTER_TODO.md #verify |
| xlights/xsq_writer.py | @ryankorkowski-boop | Production | 2026-09-30 | Issue/PR |
| tools/ | @ryankorkowski-boop | Production | 2026-09-30 | Issue/PR |
| legacy_ac/ | @ryankorkowski-boop | Beta (isolated) | 2026-09-30 | Issue/PR |
| ai/ | @ryankorkowski-boop | Prototype (stubs) | — | Issue/PR |
| helixville*/ | @ryankorkowski-boop | Prototype (experimental) | — | Issue/PR |

---

#### 0.2 Create Maturity Matrix (`docs/MATURITY_MATRIX.md`)

Define the maturity levels for each subsystem:

```markdown
# Subsystem Maturity Levels

## Level Definitions

### Prototype
- **Criteria**:
  - Proof-of-concept implementation
  - Limited test coverage
  - Known limitations documented
  - Not used in production path
- **Example**: `ai/`, `helixville*/`
- **Before Graduation**: Comprehensive tests, real-world validation, decision to integrate or archive

### Beta
- **Criteria**:
  - Feature-complete for stated scope
  - Unit test coverage > 70%
  - Manual validation on representative inputs
  - Known limitations documented
  - May have pending real-world validation
- **Example**: `core/drum_classification.py`, `legacy_ac/`
- **Before Graduation**: Real-song validation, automated regression checks, full integration test suite

### Production
- **Criteria**:
  - Feature-complete & stable
  - Unit test coverage > 85%
  - Automated regression baseline exists
  - No known show-stoppers
  - Actively used in real-world workflows
- **Example**: `xlights/`, `tools/`, `core/run_manager.py`
- **Maintenance**: Automated CI, regression checks, backward compatibility required

---

#### 0.3 Create Decision Log (`docs/DECISIONS.md`)

Template for recording key architectural/process decisions:

```markdown
# Architecture Decision Log

## Format
Each decision includes:
- **Date**: When made
- **Decision**: What was decided
- **Rationale**: Why
- **Alternatives Considered**: What else was possible
- **Status**: Active, Deferred, Superseded
- **Impact**: Modules/teams affected

## Example: ADR-0001 — Facade Pattern for Effect Engine

**Date**: 2026-10-02
**Status**: Active
**Decision**: Wrap `core/effect_engine.py` with a typed facade (`core/engine_runner.py`) instead of immediate refactor.
**Rationale**: 
  - Reduces risk of regression in beta-stage code
  - Allows incremental extraction without behavioral changes
  - Improves testability without touching monolithic internals
**Alternatives**:
  - Full rewrite of effect engine (too risky, high regression potential)
  - No wrapping, continue direct calls (increases coupling, hard to test)
**Affected Modules**: sequence_builder.py, gui_launcher.py, tests/
**Next Steps**: Implement facade in Phase 2.
```

---

### Phase 1: Verification Automation (Weeks 2–4)

**Goal**: Turn the manual regression gate into automated CI checks.

#### 1.1 Add Regression Baseline (`tests/fixtures/regression_baseline/`)

Preserve the known-good drummer render as an executable test:

```python
# tests/test_drummer_regression.py
import pytest
from core.drum_classification import classify_drums
from fixtures.regression_baseline import GOLDEN_EVENTS

def test_drummer_against_oracle():
    """
    Regression check: real-song drum detection must not deviate > 5% 
    from known-good behavior (commit b27e8d7...).
    
    This gates any drummer logic changes.
    """
    audio_path = "fixtures/beta_demo/real_song.wav"
    detected = classify_drums(audio_path)
    
    # Assertions:
    assert len(detected) == pytest.approx(len(GOLDEN_EVENTS), rel=0.05)
    assert event_counts_by_class_match(detected, GOLDEN_EVENTS, threshold=0.05)
    assert timing_deltas_acceptable(detected, GOLDEN_EVENTS, max_drift_ms=50)
```

#### 1.2 Add Artifact Validation (`tests/test_output_contracts.py`)

Check that generated XSQ/MP4 meet structural invariants:

```python
# tests/test_output_contracts.py
def test_generated_xsq_structure():
    """Verify generated XSQ has required sections."""
    xsq = run_sequence_end_to_end(demo_fixture)
    
    assert has_timing_section(xsq)
    assert has_effect_section(xsq)
    assert effect_times_ordered(xsq)
    assert all_model_targets_valid(xsq, demo_layout)
    assert no_nan_values_in_xml(xsq)

def test_xsq_importable_in_xlights():
    """Smoke check: xLights can parse generated XSQ."""
    xsq = run_sequence_end_to_end(demo_fixture)
    # Use xLights command line or library to validate
    result = subprocess.run([xlights_cli, "--check-xsq", xsq.path])
    assert result.returncode == 0
```

#### 1.3 Update CI Workflow (`.github/workflows/helix-ci.yml`)

Add automated gates:

```yaml
name: Helix CI

on:
  pull_request:
    branches:
      - feature/restructure-core
  push:
    branches:
      - feature/restructure-core

jobs:
  test-and-regression:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt
      
      - name: Compile check
        run: python -m py_compile core/**/*.py xlights/**/*.py tools/**/*.py
      
      - name: List profiles
        run: python main.py --list-profiles
      
      - name: Run unit tests
        run: pytest tests/ -v --cov=core --cov=xlights --cov=tools
      
      - name: Regression: drummer oracle
        run: pytest tests/test_drummer_regression.py -v
      
      - name: Output contract checks
        run: pytest tests/test_output_contracts.py -v
      
      - name: Smoke: clean-room demo fixture
        run: python main.py --profile master -- \
          --audio tests/fixtures/beta_demo/demo.wav \
          --template tests/fixtures/beta_demo/template.xsq \
          --output-root tests/outputs/smoke/
      
      - name: Upload smoke artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: smoke-artifacts-py${{ matrix.python-version }}
          path: tests/outputs/smoke/

  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.12
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt flake8 mypy
      
      - name: Flake8
        run: flake8 core xlights tools tests
      
      - name: MyPy
        run: mypy core xlights tools --ignore-missing-imports
```

---

### Phase 2: Documentation & Onboarding (Weeks 4–5)

**Goal**: Make it easy for new developers to understand the project.

#### 2.1 Create Developer Onboarding Guide (`docs/DEVELOPER_GUIDE.md`)

```markdown
# Developer Guide

## First Time Setup

1. Clone the repo
2. Read `AGENTS.md` (operating rules)
3. Read `MASTER_TODO.md` (current mission & roadmap)
4. Run bootstrap: `scripts/bootstrap_unix.sh` or `scripts/bootstrap_windows.ps1`
5. Run tests: `pytest tests/ -q`

## Repo Structure Quick Map

- `core/` — sequencing engine (Beta, active development)
- `xlights/` — xLights export layer (Production, stable)
- `tools/` — utilities (Production, stable)
- `ai/` — future AI bridge (Prototype, stubs only)
- `legacy_ac/` — isolated legacy sequencer (Beta, not integrated)
- `tests/` — test suite
- `docs/` — documentation
- `archive/` — legacy code (inactive)

See `docs/ARCHITECTURE.md` for full ownership/maturity matrix.

## Making Changes

1. Read the target module's owner in `docs/ARCHITECTURE.md`
2. Check `MASTER_TODO.md` for current phase/priorities
3. If modifying core sequencing, add regression test to `tests/test_drummer_regression.py`
4. If adding new outputs, add validation to `tests/test_output_contracts.py`
5. Update `MASTER_TODO.md` change ledger with your work
6. Ensure CI passes before opening PR

## Running Locally

```bash
# List available profiles
python main.py --list-profiles

# Run demo sequence
python main.py --profile master -- \
  --audio tests/fixtures/beta_demo/demo.wav \
  --template tests/fixtures/beta_demo/template.xsq \
  --output-root outputs/

# Run full test suite
pytest tests/ -v

# Run regression checks only
pytest tests/test_drummer_regression.py tests/test_output_contracts.py -v
```

## Before You Open a PR

- [ ] All tests pass: `pytest tests/ -q`
- [ ] Linting passes: `flake8 core xlights tools`
- [ ] Type check passes: `mypy core xlights tools --ignore-missing-imports`
- [ ] Updated `MASTER_TODO.md` change ledger
- [ ] If you touched core sequencing, regression tests still pass
- [ ] Docstrings added/updated for new functions
```

#### 2.2 Create Architecture Decision Template (`docs/DECISIONS.md` — starter)

(Already outlined in Phase 0.3)

#### 2.3 Add Issue Templates (`.github/ISSUE_TEMPLATE/`)

- `bug.md` — structured bug reports with regression baseline status
- `feature.md` — feature requests with impact assessment
- `regression-alert.md` — regression detection workflow

---

### Phase 3: Cleanup Policy & Golden Baselines (Weeks 5–6)

**Goal**: Make cleanup safe and reproducible.

#### 3.1 Create Cleanup Policy (`docs/CLEANUP_POLICY.md`)

```markdown
# Cleanup & Artifact Management Policy

## Artifact Categories

### Tier 1: Always Safe to Delete (Low Risk)
- `.pytest_cache/` — pytest bytecode, regenerated on test run
- `__pycache__/` and nested `__pycache__` — Python bytecode, regenerated on import
- `.mypy_cache/` — type checker cache, regenerated on run
- Old `test_runs/` subdirectories > 90 days and not referenced in current tests

**Validation**: After deletion, run `pytest tests/ -q` to confirm regeneration.

### Tier 2: Delete Only If Validated (Medium Risk)
- `dist/`, `build/` — build outputs
- `RenderCache/` — preview cache
- Old `outputs/` subdirectories (NOT the latest benchmark runs)
- Temporary demo outputs not referenced in tests

**Validation**: 
- Confirm no active release packaging references old binaries
- Regenerate one preview render and compare output
- Manually audit to retain currently referenced comparison/demo outputs

**Process**:
1. Create PR with list of directories to delete
2. Run CI to confirm no references
3. Require manual approval before merge
4. Tag PR with `cleanup-approved`

### Tier 3: Manual Review Required (High Risk)
- Any folder with active symbolic workflow usage
- `aaatest/` or other experimental output areas
- Anything in `archive/` (preserve for history)

**Process**:
1. Create issue requesting deletion
2. Require explicit sign-off from owner
3. Link to all code that depends on the folder

## Validation Workflow

For any Tier 2 deletion:

```bash
# 1. Confirm deletion target is referenced
grep -r "directory_name" . --include="*.py" --include="*.md"

# 2. Run full test suite
pytest tests/ -v

# 3. Run smoke test
python main.py --profile master -- \
  --audio tests/fixtures/beta_demo/demo.wav \
  --template tests/fixtures/beta_demo/template.xsq

# 4. Verify no errors in generated outputs
# (manual inspection of run_manifest.json and XSQ structure)
```

## Golden Baseline Preservation

Never delete:
- `fixtures/regression_baseline/` — known-good drummer render
- `tests/snapshots/` — golden output snapshots
- `fixtures/beta_demo/` — clean-room demo fixtures

These are source of truth and cannot be regenerated from code.
```

#### 3.2 Lock Golden Baseline (`tests/fixtures/regression_baseline/golden_drummer_oracle.json`)

Store the known-good drummer events from commit `b27e8d77...`:

```json
{
  "oracle_commit": "b27e8d77a63027ed32bcf6851dcff3925472c155",
  "oracle_date": "2026-09-30",
  "oracle_description": "Ground-truth drummer behavior: 8 V3 submodels, correct timing",
  "audio_file": "real_song.wav",
  "detected_events": [
    {
      "timestamp_ms": 123.45,
      "class": "kick",
      "confidence": 0.98,
      "features": { "onset_strength": 0.75, "spectral_centroid": 150 }
    },
    ...
  ],
  "summary": {
    "total_events": 412,
    "by_class": {
      "kick": 98,
      "snare": 104,
      "hihat": 156,
      "tom": 28,
      "cymbal": 26
    }
  }
}
```

#### 3.3 Add Artifact Lineage Doc (`docs/ARTIFACT_LINEAGE.md`)

Track which outputs are safe to delete and which must be preserved:

```markdown
# Artifact Lineage & Preservation Map

## Critical (Never Delete)
- `tests/fixtures/regression_baseline/` — oracle reference
- `tests/snapshots/` — golden outputs
- `tests/fixtures/beta_demo/` — demo fixtures

## Transient (Safe to Clean)
- `tests/outputs/smoke/` — CI smoke test artifacts (>7 days old)
- `.pytest_cache/`, `__pycache__/` — build caches
- Old `test_runs/` (> 90 days, not in recent PRs)

## Requires Review
- `outputs/` — may contain demo/benchmark comparisons
- Anything in `archive/` — preserve for history
```

---

### Phase 4: Subsystem Facade & Extracted Modules (Weeks 6–8)

**Goal**: Reduce coupling and improve testability without rewriting internals.

#### 4.1 Create Effect Engine Facade (`core/engine_runner.py`)

Wrap the monolithic engine with a typed interface:

```python
# core/engine_runner.py
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import json

@dataclass
class SequenceJobConfig:
    """Structured input for a sequencing job."""
    audio_file: Path
    template_xsq: Path
    layout_xml: Path
    output_root: Path
    profile: str = "master"
    enable_learning_memory: bool = False
    dry_run: bool = False
    extra_engine_args: Optional[dict] = None

@dataclass
class SequenceJobResult:
    """Structured result from a sequencing job."""
    success: bool
    run_id: str
    output_manifest_path: Path
    generated_xsq_path: Optional[Path] = None
    generated_mp4_path: Optional[Path] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'success': self.success,
            'run_id': self.run_id,
            'manifest_path': str(self.output_manifest_path),
            'xsq_path': str(self.generated_xsq_path) if self.generated_xsq_path else None,
            'mp4_path': str(self.generated_mp4_path) if self.generated_mp4_path else None,
            'error': self.error_message,
            'warnings': self.warnings or []
        }

def run_sequence_job(config: SequenceJobConfig) -> SequenceJobResult:
    """
    Execute a sequencing job with structured input/output.
    
    This is the canonical entry point for GUI, CLI, and testing.
    It wraps core/effect_engine.main_for() and provides typed contracts.
    """
    try:
        # Validate inputs
        if not config.audio_file.exists():
            return SequenceJobResult(
                success=False,
                run_id="",
                output_manifest_path=config.output_root,
                error_message=f"Audio file not found: {config.audio_file}"
            )
        
        # Call wrapped engine
        result = _run_effect_engine(config)
        
        return result
    
    except Exception as e:
        return SequenceJobResult(
            success=False,
            run_id="",
            output_manifest_path=config.output_root,
            error_message=str(e)
        )

def _run_effect_engine(config: SequenceJobConfig) -> SequenceJobResult:
    """Wrap the current effect_engine.main_for() call."""
    from core import effect_engine
    from core import run_manager
    
    run_mgr = run_manager.RunManager(config.output_root)
    
    # Delegate to existing engine
    run_info = effect_engine.main_for(
        audio_path=str(config.audio_file),
        template_path=str(config.template_xsq),
        layout_path=str(config.layout_xml),
        output_root=str(config.output_root),
        profile=config.profile,
        dry_run=config.dry_run,
        extra_args=config.extra_engine_args or {}
    )
    
    return SequenceJobResult(
        success=run_info.get('success', False),
        run_id=run_info.get('run_id', ''),
        output_manifest_path=run_mgr.manifest_path,
        generated_xsq_path=Path(run_info.get('xsq_path')) if run_info.get('xsq_path') else None,
        generated_mp4_path=Path(run_info.get('mp4_path')) if run_info.get('mp4_path') else None,
        error_message=run_info.get('error'),
        warnings=run_info.get('warnings', [])
    )
```

Update GUI and CLI to use the facade:

```python
# gui_launcher.py (excerpt)
from core.engine_runner import run_sequence_job, SequenceJobConfig

def on_run_clicked():
    config = SequenceJobConfig(
        audio_file=Path(self.audio_var.get()),
        template_xsq=Path(self.template_var.get()),
        layout_xml=Path(self.layout_var.get()),
        output_root=Path(self.output_var.get()),
        profile=self.profile_var.get(),
        dry_run=False
    )
    
    result = run_sequence_job(config)
    
    if result.success:
        self.status_label.config(text=f"✓ Completed: {result.run_id}")
    else:
        self.status_label.config(text=f"✗ Error: {result.error_message}")
```

#### 4.2 Add Extraction Plan (`docs/EFFECT_ENGINE_EXTRACTION_PLAN.md`)

Document the seams where the engine can be safely extracted:

```markdown
# Effect Engine Extraction Plan

## Current State
`core/effect_engine.py` is monolithic (~1000+ lines) and couples many concerns:
- input validation
- profile dispatch
- audio analysis
- effect placement
- xLights export
- manifest writing
- quality scoring
- learning memory

## Extraction Sequence (Do Not Execute Yet)

### Phase A: Input Handling
**Target**: Extract input validation and discovery into `core/input_resolver.py`
**Seam**: Currently `effect_engine.main_for()` lines X-Y
**Risk**: Low — input validation is stateless
**Tests Required**: 
  - Missing file detection
  - Path resolution
  - Format validation (audio, XSQ, XML)

### Phase B: Profile Dispatch
**Target**: Extract profile resolution into `core/profile_dispatcher.py`
**Seam**: Currently handled inline
**Risk**: Low — profile lookup is simple registry access
**Tests Required**:
  - Known profiles load
  - Unknown profiles error gracefully

### Phase C: Output Artifact Naming
**Target**: Extract manifest/output naming into `core/run_naming.py`
**Seam**: Currently scattered
**Risk**: Low — stateless, no side effects
**Tests Required**:
  - Unique run IDs generated
  - No output overwrites
  - Manifest paths correct

### Phase D: Quality Scoring
**Target**: Extract quality logic into `core/quality_scorer.py`
**Seam**: Currently embedded in effect placement
**Risk**: Medium — scoring affects effect selection
**Tests Required**:
  - Scorer produces consistent results
  - Scorer doesn't change effect placement (initially)
  - Regression tests still pass

### Phase E: Learning Memory
**Target**: Extract learning logic into `learning/memory_manager.py` (isolated)
**Seam**: Currently optional hooks
**Risk**: Medium — learning data persistence
**Tests Required**:
  - Memory reads/writes work
  - Invalid memory is skipped gracefully

### Phase F: Effect Placement Core
**Target**: Last (do not extract until A-E are stable)
**Seam**: Audio analysis → effect generation
**Risk**: High — core sequencing logic
**Tests Required**:
  - All regression tests pass
  - Real-song comparison unchanged
  - Visual quality unaffected

## Validation Gate

Do not extract Phase X until:
1. Facade (core/engine_runner.py) is in production
2. Tests for seam pass at 100%
3. Regression tests still pass
4. Extraction does not change behavior in any test
```

---

## Remaining Phases (Outline)

### Phase 5: Release & Packaging (Weeks 8–10)
- Windows executable build via PyInstaller
- Release checklist
- Beta feedback collection

### Phase 6: Long-Term Maintenance (Ongoing)
- Quarterly architecture reviews
- Deprecation policy for old profiles
- Community contribution guidelines

---

## Execution Timeline

| Phase | Duration | Owner | Key Deliverables |
|-------|----------|-------|------------------|
| 0: Foundation | Weeks 1–2 | @ryankorkowski-boop | ARCHITECTURE.md, DECISIONS.md, ownership matrix |
| 1: Verification | Weeks 2–4 | @ryankorkowski-boop | CI regression checks, golden baseline, test suite updates |
| 2: Onboarding | Weeks 4–5 | @ryankorkowski-boop | DEVELOPER_GUIDE.md, issue templates |
| 3: Cleanup Policy | Weeks 5–6 | @ryankorkowski-boop | CLEANUP_POLICY.md, artifact lineage |
| 4: Facade & Extraction | Weeks 6–8 | @ryankorkowski-boop | engine_runner.py, extraction plan |
| 5: Release | Weeks 8–10 | @ryankorkowski-boop | Packaging, beta checklist |
| 6: Maintenance | Ongoing | @ryankorkowski-boop | Quarterly reviews, community guidelines |

---

## Success Criteria

By end of Phase 3:
- [ ] Every subsystem has clear owner and maturity level
- [ ] Architecture map is complete and linked from README
- [ ] CI includes automated regression gates
- [ ] New developer can start contributing in < 30 min
- [ ] Cleanup policy prevents accidental deletion of golden baselines

By end of Phase 4:
- [ ] Effect engine facade is in production
- [ ] Extraction plan is documented and ready
- [ ] All changes are non-behavioral (regression tests unchanged)

By end of Phase 6:
- [ ] Project is maintainable at scale
- [ ] Community contributions follow clear process
- [ ] Quarterly reviews feed back into roadmap

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Facade layer adds complexity | Keep facade minimal; wrap, don't rewrite |
| Extraction plan never executes | Use CI gates; do not mark complete without tests |
| Documentation becomes stale | Link from README; update in every PR |
| Cleanup accidentally deletes golden baseline | Explicit Tier 3 preservation in policy |
| New contributors still confused | Short onboarding checklist in README |

---

## Next Steps

1. **This week**: Implement Phase 0 (ARCHITECTURE.md, DECISIONS.md, ownership matrix)
2. **Next week**: Implement Phase 1 (CI regression gates, golden baseline)
3. **Week 3**: Implement Phase 2 (DEVELOPER_GUIDE.md, issue templates)
4. **Week 4**: Implement Phase 3 (CLEANUP_POLICY.md, artifact lineage)
5. **Weeks 5+**: Begin Phase 4 (facade, extraction plan)

Open PRs in order; do not merge Phase N until Phase N-1 is complete.

---

**Last Updated**: 2026-10-02  
**Status**: Ready for implementation  
**Next Review**: After Phase 0 completion
