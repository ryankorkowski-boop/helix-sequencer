# Helix Beta Policy

This policy defines how the beta version should handle user/tester inputs, generated outputs, learning behavior, and safety boundaries.

## Plain-English summary

Helix beta is evaluation software for generating xLights-compatible sequencing artifacts from copied test inputs. Testers keep ownership of their files. The beta should not train on private user/tester assets by default. The app should write generated outputs to a Helix-managed output folder and should not overwrite original layouts, templates, songs, or sequences.

## Input ownership

Users and testers keep ownership of:

- Layout files.
- Template XSQ files.
- Sequence files.
- Audio files.
- Screenshots.
- Generated comparison material they choose not to share.

Helix does not gain ownership of these files just because they are used during a beta run.

## Training and learning boundary

The beta path should not persistently learn from arbitrary user/tester assets by default.

Allowed by default:

- One-time audio analysis for the current render.
- One-time layout parsing for the current render.
- Temporary process memory needed to generate the run.
- Run metadata needed for debugging, such as success/failure, selected profile, timestamps, and generated artifact paths.

Not allowed by default:

- Training on user/tester sequences.
- Training on copyrighted songs.
- Training on private layouts or templates.
- Storing copied user/tester files in the repository.
- Uploading user/tester files to external services without explicit permission.

Persistent learning, if added later, must be opt-in and clearly documented.

## Repository safety rules

Do not commit any of the following unless explicit written permission is included in repo documentation or the file is clean-room/generated for testing:

- Private layouts.
- Private templates.
- Private sequences.
- Copyrighted songs.
- Screenshots of private layouts or sequences.
- Tester-provided generated outputs that they did not approve for public use.

Clean-room demo fixtures are allowed when they are generated from scratch or otherwise license-safe.

## Output behavior

The beta should:

- Write to a selected output directory or a Helix-managed `outputs/beta/` folder.
- Create a timestamped run folder for each run.
- Write `run_manifest.json`, `command.txt`, and `helix.log` when possible.
- Clearly identify generated artifacts as Helix-generated or beta-generated when practical.
- Avoid overwriting source layout, template, sequence, or audio files.

## xLights and licensing boundary

Helix beta is an auto-sequencing helper for xLights workflows. It should not be described as a proprietary replacement for xLights. Any xLights-derived compatibility code, legacy helpers, or GPL-relevant boundaries should remain documented and reviewed before public distribution.

## Tester communication

Beta documentation should tell testers:

- Use copies of layouts and templates.
- Do not test against production originals unless they are comfortable with the risk.
- Inspect all generated output manually in xLights before using it in a show.
- Share logs and manifests first; share private layouts/templates/sequences only if they intentionally choose to.
- Expect incomplete quality and rough edges.

## Issue and feedback safety

Issue templates should request:

- xLights version.
- Helix beta version or commit SHA.
- Run manifest.
- Log file.
- Description of the input shape.
- Screenshot only if safe to share.

Issue templates should warn users not to publicly upload private layouts, sequences, templates, or songs unless they intend to share them.
