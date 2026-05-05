# AAA Pipeline

## AAA Pack Generation Flow

- Entry point: `tools/generate_aaatest_pack.py`
- Inputs:
  - audio file
  - template XSQ
  - layout XML
  - deterministic variant plan
- Flow:
  - create a clean `_work` directory under the output folder
  - run `main.py` once per variant plan
  - copy the selected XSQ into the output folder
  - render an MP4 preview for each XSQ
  - optionally clean non-XSQ/MP4 work products

## Scoring Flow

- Core scorer: `core/youtube_show_scorer.py`
- Report tool: `tools/youtube_show_report.py`
- Reports are scored from existing report JSON payloads.
- Older reports can derive section-aware scoring from XSQ with `--xsq`.
- Scoring is report-only and does not modify generated sequences.

## Current Implemented Tooling

- `tools/generate_aaatest_pack.py`
- `core/youtube_show_scorer.py`
- `tools/youtube_show_report.py`
- `tools.preview_renderer`
- quality and audit payloads produced by existing generation systems

## Expected Outputs

- XSQ sequence files.
- MP4 previews.
- Per-sequence report JSON files when produced by generation.
- YouTube show grading summaries.
- Pass/fail indicators from configured quality gates.

## Grading And Report Flow

- Load a report JSON.
- Build or derive a show-direction summary.
- Score with generalized show-direction principles.
- Print text or JSON summaries.
- Surface score, grade, problem count, and recommendations.

## Pass/Fail Philosophy

- Generation success alone is not a pass.
- Parser-valid output is required before grading matters.
- Grading should flag risks without rewriting the sequence.
- Pass/fail thresholds should be deterministic and explicit.
- Existing scoring heuristics should remain stable during production validation.
