# Cleanup Candidates (Report Only)

No deletions were performed.

## Candidate List

- path: `.pytest_cache/`
- why it appears safe to delete: pytest cache is regenerable and not source of truth.
- equivalent/current content exists inside 414: yes (tests and source remain).
- risk level: low
- validation needed before deletion: rerun `python -m pytest` after deletion.

- path: `__pycache__/` and nested `__pycache__` folders
- why it appears safe to delete: bytecode cache only; recreated automatically.
- equivalent/current content exists inside 414: yes.
- risk level: low
- validation needed before deletion: run one command from README to regenerate if needed.

- path: `test_runs/styler_mixup_sweep/_speed_test/`
- why it appears safe to delete: temporary speed benchmark run, superseded by full sweep outputs.
- equivalent/current content exists inside 414: yes, in `test_runs/styler_mixup_sweep/` named runs.
- risk level: low
- validation needed before deletion: confirm desired comparison artifact is not uniquely in this folder.

- path: `test_runs/styler_mixup_sweep/_speed_test2/`
- why it appears safe to delete: temporary benchmark variant run used during tuning.
- equivalent/current content exists inside 414: yes, in full sweep set and e2e proof run.
- risk level: low
- validation needed before deletion: verify no one depends on this folder name in scripts.

- path: `outputs/core_sandbox_audio_only/`
- why it appears safe to delete: intermediate sandbox output; canonical baseline is in `tests/snapshots/`.
- equivalent/current content exists inside 414: yes (`tests/snapshots/core_audio_intelligence_snapshot.json`).
- risk level: low
- validation needed before deletion: rerun `python -m pytest tests/test_core_sandbox.py -q`.

- path: `outputs/core_sandbox_after_merge/`
- why it appears safe to delete: post-merge validation artifact can be regenerated.
- equivalent/current content exists inside 414: yes, snapshot tests and guardrail scripts.
- risk level: low
- validation needed before deletion: rerun the Part 1 sandbox command from README_CURRENT.md.

- path: `outputs/core_sandbox/`
- why it appears safe to delete: full sandbox report cache; test snapshots already pinned.
- equivalent/current content exists inside 414: yes.
- risk level: low
- validation needed before deletion: rerun sandbox + snapshot test.

- path: `dist/`
- why it appears safe to delete: likely build artifact directory.
- equivalent/current content exists inside 414: yes, source and build scripts.
- risk level: medium
- validation needed before deletion: verify no active release packaging currently consuming old binaries.

- path: `build/`
- why it appears safe to delete: build working directory, usually reproducible.
- equivalent/current content exists inside 414: yes.
- risk level: medium
- validation needed before deletion: run intended build command after cleanup.

- path: `RenderCache/`
- why it appears safe to delete: cache/intermediate render state.
- equivalent/current content exists inside 414: yes.
- risk level: medium
- validation needed before deletion: regenerate one preview render and compare output.

- path: `outputs/` (older subfolders only, selective)
- why it appears safe to delete: generated outputs can be regenerated.
- equivalent/current content exists inside 414: partially; keep latest useful benchmark/demo outputs.
- risk level: high
- validation needed before deletion: manually audit and retain currently referenced comparison/demo outputs.

- path: `aaatest/` (present)
- why it appears safe to delete: appears generated/experimental output area.
- equivalent/current content exists inside 414: likely yes, but depends on operator workflow.
- risk level: high
- validation needed before deletion: confirm no active manual workflow depends on files in this folder.

## Specifically Requested Names

- `aaa`: not found in current 414 root.
- `qqq`: not found in current 414 root.
- `q`: not found in current 414 root.

If these exist outside 414, they were not modified or deleted.
