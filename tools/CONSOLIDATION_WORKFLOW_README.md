# PR Consolidation Runner README

This workflow runs the consolidation script located at `tools/consolidate_prs.py`.

Usage:
- Go to the Actions tab in GitHub, select "PR Consolidation Runner" and "Run workflow".
- Set "execute" to true to perform live merges (workflow will authenticate using GITHUB_TOKEN).
- Set "include_drafts" to true to include draft PRs.

Notes:
- The workflow runs on the `feature/consolidate-prs-script` branch where the script lives. Open a PR to merge this workflow into your default branch to enable it more broadly.
