from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

COMPILE_TARGETS = [
    "core",
    "ai",
    "xlights",
    "tools",
    "tests",
    "main.py",
    "gui_launcher.py",
]

SMOKE_TESTS = [
    "tests/test_sequence_builder.py",
    "tests/test_effects_orchestrator_bridge.py",
    "tests/test_xlights_contract_validator.py",
]


def existing(paths: list[str]) -> list[str]:
    return [path for path in paths if (REPO_ROOT / path).exists()]


def run(command: list[str]) -> None:
    print("\n$ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    compile_targets = existing(COMPILE_TARGETS)
    smoke_tests = existing(SMOKE_TESTS)
    if not compile_targets or not smoke_tests:
        print("Required check targets are missing.", file=sys.stderr)
        return 1
    run([sys.executable, "-m", "compileall", *compile_targets])
    run([sys.executable, "main.py", "--list-profiles"])
    run([sys.executable, "-m", "pytest", "-q", *smoke_tests])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
