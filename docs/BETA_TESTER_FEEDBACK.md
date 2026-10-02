# Beta Tester Feedback Checklist

This is a repo-safe, copy/paste checklist for beta testers. It is intended to capture the minimum evidence needed to assess whether Helix is safe enough for a real-world smoke test without collecting private assets or screenshots.

## Quick use

- Use this form for a single run only.
- Keep it local to your machine unless you explicitly choose to share it in a GitHub issue.
- Do not paste private layout/audio/template filenames into a public issue unless you have permission to do so.
- Prefer the `run_manifest.json` and output folder as the canonical run evidence. Use the checklist below to add human context.

## Tester run summary

- Tester name or alias: 
- Date/time: 
- OS / version: 
- Python version: 
- xLights version: 
- Helix profile used: 
- GUI or CLI path used: 

## Inputs used

- Audio file used (redacted if private): 
- Layout file used (redacted if private): 
- Template XSQ used (redacted if private): 
- Output directory: 

## Preflight checks

- [ ] I followed the documented bootstrap steps.
- [ ] The GUI launched from the documented command or executable.
- [ ] The input files were copied for testing; source files were not overwritten.
- [ ] The output directory is separate from source directories.
- [ ] The run created a timestamped run folder.
- [ ] A run manifest was written.

## Run outcome

- [ ] The app completed without an unhandled exception.
- [ ] The app produced a generated XSQ or import artifact.
- [ ] The generated output opens in xLights without a crash.
- [ ] The generated output failed in a documented, reproducible way.
- [ ] I did not have to modify source files or input files to make the run work.

## Behavior notes

- What worked well: 
- What was confusing or unstable: 
- Missing or unclear error messages: 
- Any file paths or values that looked wrong: 

## Safety and data-use check

- [ ] I used only copied local inputs for testing.
- [ ] I did not commit or share private layouts, templates, screenshots, songs, or generated user content.
- [ ] I understand this is beta software and not a production automation system.

## Evidence to attach

- [ ] run_manifest.json path: 
- [ ] generated artifact path(s): 
- [ ] screenshot or screen recording path (only if permissioned): 
- [ ] reproduction steps: 

## Suggested improvement

- Highest-priority fix or missing capability: 
- Why it matters: 
- Severity (low / medium / high): 

## Short issue-ready summary

Replace this text with a concise issue summary for GitHub:

"I ran Helix beta using copied local inputs on [OS/version]. The run [succeeded/failed] and [produced/failed to produce] a run folder and manifest. The main issue was [brief summary]. I used a clean-room or permissioned test setup and did not rely on private assets."
