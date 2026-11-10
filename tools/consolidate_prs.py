#!/usr/bin/env python3
"""
PR Consolidation Script for helix-sequencer

This script safely merges open PRs in a recommended order, with validation checks.
It's designed to work with GitHub CLI (gh) or GitHub API.

Usage:
    python tools/consolidate_prs.py --dry-run
    python tools/consolidate_prs.py --execute
    python tools/consolidate_prs.py --execute --pr 66

Configuration:
    - Set GITHUB_TOKEN environment variable or configure gh CLI
    - Review merge order in MERGE_PLAN before executing
"""

import subprocess
import sys
import json
import argparse
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MergePlan:
    """Defines a PR merge step with validation and context."""
    pr_number: int
    title: str
    target_branch: str
    merge_strategy: str  # 'squash', 'rebase', 'merge'
    phase: int
    risk_level: str  # 'low', 'medium', 'high'
    reason: str
    preconditions: List[str]  # PRs that must be merged first
    validation_tests: Optional[List[str]] = None


# Define the merge plan
MERGE_PLAN: List[MergePlan] = [
    MergePlan(
        pr_number=66,
        title="[codex] Add Phase 4 signature style planner",
        target_branch="feature/restructure-core",
        merge_strategy="squash",
        phase=1,
        risk_level="low",
        reason="All tests passing (70/70), stacked work completion",
        preconditions=[],
        validation_tests=[
            "tests/test_effect_intelligence_system.py",
            "tests/test_musical_intelligence.py",
            "tests/test_effects.py",
            "tests/test_sequence_builder.py",
        ]
    ),
    MergePlan(
        pr_number=59,
        title="Add draft xLights .xmodel assets for accepted band members (v1)",
        target_branch="feature/restructure-core",
        merge_strategy="squash",
        phase=1,
        risk_level="low",
        reason="Isolated assets with explicit draft status, tests confirm boundaries",
        preconditions=[66],
        validation_tests=["tests/test_draft_xmodel_assets.py"]
    ),
    MergePlan(
        pr_number=26,
        title="Stabilize Helixia spatial CI after merge",
        target_branch="feature/restructure-core",
        merge_strategy="rebase",
        phase=2,
        risk_level="medium",
        reason="Fixes known failing tests (motion continuity, motif memory, CI repairs)",
        preconditions=[66, 59],
        validation_tests=[
            "tests/showcase/test_motion_continuity.py",
            "tests/test_motif_memory.py",
            "tests/test_output_quality_report.py",
            "tests/test_working_floor_piano.py",
        ]
    ),
]

DRAFT_PLAN: List[MergePlan] = [
    MergePlan(
        pr_number=27,
        title="fix(helixia): sync local test performance fixes",
        target_branch="feature/restructure-core",
        merge_strategy="rebase",
        phase=3,
        risk_level="high",
        reason="Draft PR with rebased local fixes—requires finalization decision",
        preconditions=[26],
        validation_tests=[
            "tests/test_audio_toolsets.py",
            "tests/test_helixville4_floor_piano.py",
            "tests/test_helixia_smoke_preview.py",
        ]
    ),
    MergePlan(
        pr_number=22,
        title="feat: add Legacy 256 proving ground and calibration tools",
        target_branch="main",
        merge_strategy="squash",
        phase=3,
        risk_level="high",
        reason="Large feature targeting main, legacy-only tooling, keep local assets",
        preconditions=[26],
        validation_tests=[
            "tests/test_legacy_256_manifest.py",
            "tests/test_legacy_256_profiles.py",
            "tests/test_variant_quality_gates.py",
        ]
    ),
]


class ConsolidationScript:
    """Manages PR consolidation with validation and reporting."""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.merged_prs: List[int] = []
        self.failed_prs: Dict[int, str] = {}
        self.skipped_prs: Dict[int, str] = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")

    def run_command(self, cmd: List[str], description: str = "") -> Tuple[bool, str]:
        """Execute shell command and return (success, output)."""
        try:
            if self.verbose:
                self.log(f"Running: {' '.join(cmd)}", "DEBUG")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, f"Command timeout: {description}"
        except Exception as e:
            return False, f"Command error: {str(e)}"

    def get_pr_status(self, pr_number: int) -> Dict:
        """Fetch PR status from GitHub CLI."""
        success, output = self.run_command(
            ["gh", "pr", "view", str(pr_number), "--json", "state,isDraft,title,baseRefName"],
            f"Fetch PR #{pr_number} status"
        )
        
        if not success:
            return {"error": output}
        
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse PR #{pr_number} status"}

    def validate_pr(self, plan: MergePlan) -> Tuple[bool, str]:
        """Validate PR is ready to merge."""
        status = self.get_pr_status(plan.pr_number)
        
        if "error" in status:
            return False, f"Could not fetch PR status: {status['error']}"
        
        # Check if PR is open
        if status.get("state") != "OPEN":
            return False, f"PR is not open: state={status.get('state')}"
        
        # Warn if PR is still a draft (but allow override)
        if status.get("isDraft"):
            self.log(f"⚠️  PR #{plan.pr_number} is still marked as draft", "WARN")
        
        # Check preconditions
        for precondition_pr in plan.preconditions:
            if precondition_pr not in self.merged_prs:
                return False, f"Precondition not met: PR #{precondition_pr} not merged"
        
        return True, "Validation passed"

    def run_tests(self, tests: List[str]) -> Tuple[bool, str]:
        """Run validation tests."""
        if not tests:
            return True, "No tests configured"
        
        self.log(f"Running {len(tests)} validation tests...", "INFO")
        
        for test_file in tests:
            success, output = self.run_command(
                ["python", "-m", "pytest", test_file, "-q"],
                f"Test: {test_file}"
            )
            
            if not success:
                return False, f"Test failed: {test_file}\n{output}"
        
        return True, f"All {len(tests)} tests passed"

    def merge_pr(self, plan: MergePlan) -> bool:
        """Merge a single PR."""
        self.log(f"Merging PR #{plan.pr_number}: {plan.title}", "INFO")
        
        # Validate
        valid, msg = self.validate_pr(plan)
        if not valid:
            self.log(f"❌ Validation failed: {msg}", "ERROR")
            self.failed_prs[plan.pr_number] = msg
            return False
        
        self.log(f"✓ Validation passed", "INFO")
        
        # Run tests if configured
        if plan.validation_tests:
            success, msg = self.run_tests(plan.validation_tests)
            if not success:
                self.log(f"❌ Test failed: {msg}", "ERROR")
                self.failed_prs[plan.pr_number] = msg
                return False
            self.log(f"✓ {msg}", "INFO")
        
        # Merge
        if self.dry_run:
            self.log(f"[DRY RUN] Would merge with strategy: {plan.merge_strategy}", "INFO")
        else:
            merge_cmd = [
                "gh", "pr", "merge", str(plan.pr_number),
                f"--{plan.merge_strategy}",
                "--auto",
            ]
            success, output = self.run_command(merge_cmd, f"Merge PR #{plan.pr_number}")
            
            if not success:
                self.log(f"❌ Merge failed: {output}", "ERROR")
                self.failed_prs[plan.pr_number] = output
                return False
            
            self.log(f"✓ Merged successfully", "INFO")
        
        self.merged_prs.append(plan.pr_number)
        return True

    def consolidate(self, plan_list: List[MergePlan], specific_pr: Optional[int] = None) -> Dict:
        """Execute consolidation plan."""
        self.log(f"Starting PR consolidation ({'DRY RUN' if self.dry_run else 'LIVE'})", "INFO")
        self.log(f"Plan: {len(plan_list)} PRs to process", "INFO")
        
        for plan in plan_list:
            if specific_pr and plan.pr_number != specific_pr:
                self.log(f"Skipping PR #{plan.pr_number} (not requested)", "INFO")
                continue
            
            self.log(f"\n--- Phase {plan.phase}: PR #{plan.pr_number} (Risk: {plan.risk_level}) ---", "INFO")
            self.merge_pr(plan)
        
        return self.report()

    def report(self) -> Dict:
        """Generate consolidation report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "merged_count": len(self.merged_prs),
            "merged_prs": self.merged_prs,
            "failed_count": len(self.failed_prs),
            "failed_prs": self.failed_prs,
            "skipped_prs": self.skipped_prs,
        }
        
        self.log("\n" + "=" * 60, "INFO")
        self.log("CONSOLIDATION REPORT", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"✓ Merged: {report['merged_count']} PRs → {self.merged_prs}", "INFO")
        
        if self.failed_prs:
            self.log(f"❌ Failed: {report['failed_count']} PRs", "ERROR")
            for pr, reason in self.failed_prs.items():
                self.log(f"   PR #{pr}: {reason}", "ERROR")
        
        if self.skipped_prs:
            self.log(f"⊘ Skipped: {len(self.skipped_prs)} PRs", "WARN")
        
        self.log("=" * 60, "INFO")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate open PRs safely with validation"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute merges (default is dry-run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry-run (default)"
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="Merge only a specific PR number"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Merge only a specific phase"
    )
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Include draft PRs in consolidation (Phase 3)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default)"
    )
    
    args = parser.parse_args()
    
    # Determine plan
    plan = list(MERGE_PLAN)
    if args.include_drafts:
        plan.extend(DRAFT_PLAN)
    
    if args.phase:
        plan = [p for p in plan if p.phase == args.phase]
    
    # Create and run
    script = ConsolidationScript(
        dry_run=not args.execute,
        verbose=args.verbose
    )
    
    report = script.consolidate(plan, specific_pr=args.pr)
    
    # Return exit code
    sys.exit(0 if not report['failed_prs'] else 1)


if __name__ == "__main__":
    main()
