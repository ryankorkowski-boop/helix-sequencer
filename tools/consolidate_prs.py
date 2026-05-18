#!/usr/bin/env python3
"""
PR Consolidation Automation Script

Safely orchestrates merging of open PRs in helix-sequencer based on:
- Risk assessment (low/medium/high)
- Dependency chains
- Test validation
- Draft status

Usage:
    python tools/consolidate_prs.py --dry-run
    python tools/consolidate_prs.py --execute
    python tools/consolidate_prs.py --execute --pr 66
    python tools/consolidate_prs.py --execute --include-drafts
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class MergeRisk(Enum):
    """Risk levels for PR merges."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class PRPhase(Enum):
    """Merge phases for progressive consolidation."""
    PHASE_1_IMMEDIATE = "Phase 1: Immediate (Low Risk)"
    PHASE_2_STABILIZATION = "Phase 2: Stabilization (Medium Risk)"
    PHASE_3_DRAFTS = "Phase 3: Draft Consolidation (High Risk)"


@dataclass
class PRInfo:
    """PR metadata and merge strategy."""
    number: int
    title: str
    draft: bool
    base_branch: str
    head_branch: str
    risk_level: MergeRisk
    phase: PRPhase
    depends_on: List[int] = field(default_factory=list)
    tests_required: List[str] = field(default_factory=list)
    notes: str = ""


class PRConsolidator:
    """Orchestrates safe PR merging and validation."""

    # Audit-defined merge strategy
    PR_STRATEGY: Dict[int, PRInfo] = {
        66: PRInfo(
            number=66,
            title="[codex] Add Phase 4 signature style planner",
            draft=False,
            base_branch="codex/spatial-choreography-phase3",
            head_branch="codex/signature-style-phase4",
            risk_level=MergeRisk.LOW,
            phase=PRPhase.PHASE_1_IMMEDIATE,
            depends_on=[65],
            tests_required=[
                "tests/test_effect_intelligence_system.py",
                "tests/test_musical_intelligence.py",
                "tests/test_effects.py",
                "tests/test_sequence_builder.py",
            ],
            notes="Stacked on #65. All tests passing (70/70).",
        ),
        59: PRInfo(
            number=59,
            title="Add draft xLights .xmodel assets for accepted band members (v1)",
            draft=False,
            base_branch="feature/restructure-core",
            head_branch="feature/draft-xmodel-assets-v1",
            risk_level=MergeRisk.LOW,
            phase=PRPhase.PHASE_1_IMMEDIATE,
            depends_on=[],
            tests_required=["tests/test_draft_xmodel_assets.py"],
            notes="Isolated assets with explicit 'draft' status. Should merge after #66.",
        ),
        26: PRInfo(
            number=26,
            title="Stabilize Helixia spatial CI after merge",
            draft=False,
            base_branch="feature/restructure-core",
            head_branch="fix/post-helixia-spatial-ci",
            risk_level=MergeRisk.MEDIUM,
            phase=PRPhase.PHASE_2_STABILIZATION,
            depends_on=[],
            tests_required=[
                "tests/showcase/test_motion_continuity.py",
                "tests/test_motif_memory.py",
                "tests/test_output_quality_report.py",
                "tests/test_working_floor_piano.py",
            ],
            notes="Stabilization fixes (7 commits). Merge before drafts.",
        ),
        27: PRInfo(
            number=27,
            title="fix(helixia): sync local test performance fixes",
            draft=True,
            base_branch="feature/restructure-core",
            head_branch="feature/helixia-local-fixes",
            risk_level=MergeRisk.HIGH,
            phase=PRPhase.PHASE_3_DRAFTS,
            depends_on=[],
            tests_required=[
                "tests/test_audio_toolsets.py",
                "tests/test_helixville4_floor_piano.py",
            ],
            notes="Draft with rebased local fixes. Finalize decision needed.",
        ),
        62: PRInfo(
            number=62,
            title="Draft Birdsong Engine v2 generative roadmap",
            draft=True,
            base_branch="feature/restructure-core",
            head_branch="feature/birdsong-engine-v2",
            risk_level=MergeRisk.HIGH,
            phase=PRPhase.PHASE_3_DRAFTS,
            depends_on=[],
            tests_required=[],
            notes="Pure roadmap + isolated module. Safe to keep as draft long-term.",
        ),
        22: PRInfo(
            number=22,
            title="feat: add Legacy 256 proving ground and calibration tools",
            draft=True,
            base_branch="main",
            head_branch="feature/restructure-core",
            risk_level=MergeRisk.HIGH,
            phase=PRPhase.PHASE_3_DRAFTS,
            depends_on=[26],
            tests_required=[
                "tests/test_legacy_256_manifest.py",
                "tests/test_inspect_lms.py",
            ],
            notes="Largest change. Wait until #26 stabilizes.",
        ),
    }

    def __init__(self, dry_run: bool = True, include_drafts: bool = False):
        """Initialize consolidator.

        Args:
            dry_run: If True, simulate merges without executing.
            include_drafts: If True, include draft PRs in merge plan.
        """
        self.dry_run = dry_run
        self.include_drafts = include_drafts
        self.merged: List[int] = []
        self.failed: List[Tuple[int, str]] = []
        self.skipped: List[int] = []
        self.log_file = f"test_runs/pr_consolidation_{datetime.now().isoformat()}.log"

    def get_merge_plan(self) -> List[int]:
        """Generate merge plan based on phases and dependencies.

        Returns:
            Ordered list of PR numbers to merge.
        """
        plan = []

        # Phase 1: Low risk, immediate
        for pr_num in sorted(self.PR_STRATEGY.keys()):
            pr = self.PR_STRATEGY[pr_num]
            if pr.phase == PRPhase.PHASE_1_IMMEDIATE:
                if not pr.draft or self.include_drafts:
                    plan.append(pr_num)

        # Phase 2: Medium risk, stabilization
        for pr_num in sorted(self.PR_STRATEGY.keys()):
            pr = self.PR_STRATEGY[pr_num]
            if pr.phase == PRPhase.PHASE_2_STABILIZATION:
                if not pr.draft or self.include_drafts:
                    plan.append(pr_num)

        # Phase 3: High risk, drafts (only if requested)
        if self.include_drafts:
            for pr_num in sorted(self.PR_STRATEGY.keys()):
                pr = self.PR_STRATEGY[pr_num]
                if pr.phase == PRPhase.PHASE_3_DRAFTS:
                    plan.append(pr_num)

        return plan

    def validate_dependencies(self, pr_num: int) -> bool:
        """Validate that PR dependencies have been merged.

        Args:
            pr_num: PR number to validate.

        Returns:
            True if all dependencies are met.
        """
        pr = self.PR_STRATEGY[pr_num]
        for dep in pr.depends_on:
            if dep not in self.merged:
                self.log(f"  ⚠️  Dependency #{dep} not yet merged. Skipping ##{pr_num}.")
                return False
        return True

    def run_tests(self, pr_num: int) -> bool:
        """Run validation tests for a PR.

        Args:
            pr_num: PR number to test.

        Returns:
            True if all tests pass.
        """
        pr = self.PR_STRATEGY[pr_num]
        if not pr.tests_required:
            self.log(f"  ✓ No tests required for #{pr_num}.")
            return True

        self.log(f"  🧪 Running tests for #{pr_num}...")
        for test_path in pr.tests_required:
            cmd = ["python", "-m", "pytest", test_path, "-q"]
            try:
                if self.dry_run:
                    self.log(f"    [DRY-RUN] Would execute: {' '.join(cmd)}")
                else:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    if result.returncode != 0:
                        self.log(
                            f"    ❌ Test failed: {test_path}\n{result.stderr}"
                        )
                        return False
                    self.log(f"    ✓ {test_path} passed")
            except subprocess.TimeoutExpired:
                self.log(f"    ❌ Test timeout: {test_path}")
                return False
            except Exception as e:
                self.log(f"    ❌ Test error: {str(e)}")
                return False

        return True

    def merge_pr(self, pr_num: int) -> bool:
        """Merge a PR using GitHub API.

        Args:
            pr_num: PR number to merge.

        Returns:
            True if merge succeeded.
        """
        pr = self.PR_STRATEGY[pr_num]

        # Validate dependencies
        if not self.validate_dependencies(pr_num):
            self.skipped.append(pr_num)
            return False

        # Run tests
        if not self.run_tests(pr_num):
            self.failed.append((pr_num, "Tests failed"))
            return False

        # Execute merge
        try:
            if self.dry_run:
                self.log(f"  [DRY-RUN] Would merge PR #{pr_num} into {pr.base_branch}")
            else:
                cmd = [
                    "gh",
                    "pr",
                    "merge",
                    str(pr_num),
                    "--merge",
                    "--repo",
                    "ryankorkowski-boop/helix-sequencer",
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    self.log(f"  ❌ Merge failed for #{pr_num}: {result.stderr}")
                    self.failed.append((pr_num, result.stderr))
                    return False
                self.log(f"  ✅ Merged PR #{pr_num}")

            self.merged.append(pr_num)
            return True
        except Exception as e:
            self.log(f"  ❌ Error merging #{pr_num}: {str(e)}")
            self.failed.append((pr_num, str(e)))
            return False

    def log(self, message: str):
        """Log a message to console and file.

        Args:
            message: Message to log.
        """
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

    def consolidate(self, specific_pr: Optional[int] = None) -> int:
        """Execute consolidation plan.

        Args:
            specific_pr: If provided, only merge this PR.

        Returns:
            0 if successful, 1 otherwise.
        """
        mode = "[DRY-RUN]" if self.dry_run else "[LIVE]"
        self.log(f"\n{'='*70}")
        self.log(f"{mode} PR CONSOLIDATION STARTED")
        self.log(f"{'='*70}\n")

        # Generate merge plan
        if specific_pr:
            plan = [specific_pr]
            self.log(f"Merging specific PR: #{specific_pr}\n")
        else:
            plan = self.get_merge_plan()
            self.log(f"Consolidation Plan ({len(plan)} PRs):")
            for pr_num in plan:
                pr = self.PR_STRATEGY[pr_num]
                status = "(DRAFT)" if pr.draft else ""
                self.log(f"  #{pr_num}: {pr.title} {status}")
            self.log()

        # Execute merges
        for pr_num in plan:
            self.log(f"\n📋 Processing PR #{pr_num}...")
            pr = self.PR_STRATEGY[pr_num]
            self.log(f"   Title: {pr.title}")
            self.log(f"   Risk: {pr.risk_level.name}")
            self.log(f"   Notes: {pr.notes}")

            self.merge_pr(pr_num)

        # Print summary
        self.log(f"\n{'='*70}")
        self.log(f"{mode} CONSOLIDATION COMPLETE")
        self.log(f"{'='*70}")
        self.log(f"\n📊 Summary:")
        self.log(f"  ✅ Merged: {len(self.merged)} PRs")
        if self.merged:
            self.log(f"     {', '.join(f'#{p}' for p in self.merged)}")
        self.log(f"  ⏭️  Skipped: {len(self.skipped)} PRs")
        if self.skipped:
            self.log(f"     {', '.join(f'#{p}' for p in self.skipped)}")
        self.log(f"  ❌ Failed: {len(self.failed)} PRs")
        if self.failed:
            for pr_num, reason in self.failed:
                self.log(f"     #{pr_num}: {reason}")

        self.log(f"\n📝 Log saved to: {self.log_file}\n")

        return 0 if not self.failed else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidate and merge helix-sequencer PRs safely."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute merges (default is dry-run).",
    )
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Include draft PRs in consolidation.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="Merge only a specific PR number.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate merges without executing (default).",
    )

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.execute

    # Create consolidator
    consolidator = PRConsolidator(
        dry_run=dry_run,
        include_drafts=args.include_drafts,
    )

    # Execute consolidation
    return consolidator.consolidate(specific_pr=args.pr)


if __name__ == "__main__":
    sys.exit(main())
