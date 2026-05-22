from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]
    required_paths: tuple[Path, ...] = ()


STEPS = (
    Step(
        "compile focused recovery modules",
        (
            sys.executable,
            "-m",
            "py_compile",
            "core/birdsong_issue2_runtime.py",
            "core/feature_state.py",
            "core/sequence_builder.py",
            "tools/preview_hq.py",
            "tools/validate_xsq_structure.py",
        ),
    ),
    Step(
        "birdsong runtime adapter tests",
        (sys.executable, "-m", "pytest", "-q", "tests/test_birdsong_issue2_runtime.py"),
        (ROOT / "tests/test_birdsong_issue2_runtime.py",),
    ),
    Step(
        "feature state tests",
        (sys.executable, "-m", "pytest", "-q", "tests/test_feature_state.py"),
        (ROOT / "tests/test_feature_state.py",),
    ),
    Step(
        "preview HQ preset tests",
        (sys.executable, "-m", "pytest", "-q", "tests/test_preview_hq.py"),
        (ROOT / "tests/test_preview_hq.py",),
    ),
    Step(
        "preview HQ preset validation command",
        (sys.executable, "tools/preview_hq.py", "--validate-quality-presets"),
        (ROOT / "tools/preview_hq.py",),
    ),
    Step(
        "xLights contract validator tests",
        (sys.executable, "-m", "pytest", "-q", "tests/test_xlights_contract_validator.py"),
        (ROOT / "tests/test_xlights_contract_validator.py",),
    ),
    Step(
        "sequence builder smoke tests",
        (sys.executable, "-m", "pytest", "-q", "tests/test_sequence_builder.py"),
        (ROOT / "tests/test_sequence_builder.py",),
    ),
)


def _run(step: Step) -> tuple[str, bool]:
    if any(not path.exists() for path in step.required_paths):
        print(f"SKIP {step.name}: required path is unavailable.")
        return ("SKIP", True)

    print(f"\n== {step.name} ==")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) if not env.get("PYTHONPATH") else f"{ROOT}{os.pathsep}{env['PYTHONPATH']}"
    result = subprocess.run(step.command, cwd=ROOT, env=env, check=False)
    if result.returncode:
        print(f"FAIL {step.name}: exit {result.returncode}")
        return ("FAIL", False)
    print(f"PASS {step.name}")
    return ("PASS", True)


def main() -> int:
    print("Helix recovery gate")
    print(f"Repository root: {ROOT}")
    print("This targeted gate does not replace full CI, xLights import proof, or controller validation.")

    results = [(step.name, *_run(step)) for step in STEPS]
    failures = [name for name, status, ok in results if not ok and status == "FAIL"]

    print("\nRecovery gate summary")
    for name, status, _ok in results:
        print(f"{status:4} {name}")

    if failures:
        print(f"FAIL recovery gate: {len(failures)} step(s) failed.")
        return 1
    print("PASS recovery gate: targeted checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
