# Helix Knowledge Collector

`helix_knowledge` is a lawful ingestion and task-extraction subsystem for Helix Sequencer.
It collects **public instructional guidance** about xLights workflows and converts it into structured task cards with source citations.

## Allowed Sources

- Official xLights manual pages.
- Official xLights public site pages/blog/tips.
- Public forum pages when allowed by `robots.txt`.
- GitHub docs content when the repository license is compatible.
- YouTube transcripts only when:
  - transcript is user-provided, or
  - transcript is obtained through an official API flow.
- Local user-provided files (`.txt`, `.md`, `.json`, `.pdf`).

## Forbidden Sources

- Paid vendor sequence downloads.
- Proprietary `.xsq` / `.fseq` sequence files.
- Pirated packs or bypassed content.
- Login-only/private forum pages.
- Sources that forbid automated access or AI training.
- Unofficial transcript scraping/bypass tools.

## Compliance Controls

- Source policy allow/deny decisions are logged.
- `robots.txt` checks are enforced for web crawling.
- Per-domain rate limiting is applied.
- Crawl outcomes are tracked in `crawl_log`.
- Every extracted task card stores `source_ids` for citation traceability.

## CLI Usage

Collect official xLights manual pages:

```powershell
python -m helix_knowledge.cli collect --source xlights_manual
```

Collect a specific URL with automatic source-type inference:

```powershell
python -m helix_knowledge.cli collect --url "https://manual.xlights.org/xlights/"
```

Import a user-provided YouTube transcript:

```powershell
python -m helix_knowledge.cli import-transcript path/to/transcript.txt --title "xLights Timing Tips" --video-url "https://www.youtube.com/watch?v=..." --channel "Example Channel"
```

Import local files:

```powershell
python -m helix_knowledge.cli import-local path/to/file.pdf
```

Extract structured task cards:

```powershell
python -m helix_knowledge.cli extract-tasks
```

Search generated task cards:

```powershell
python -m helix_knowledge.cli search "how do I make arches go both directions"
```

Export task cards:

```powershell
python -m helix_knowledge.cli export-taskcards data/taskcards.jsonl
```

Review cards flagged for human verification:

```powershell
python -m helix_knowledge.cli review-needed
```

## Data Model

The SQLite store includes:

- `sources`
- `chunks`
- `task_cards`
- `crawl_log`
- `source_policy_decisions`

Task cards are categorized into xLights-relevant areas (layout, model groups, timing, effects, controllers, WLED, troubleshooting, and more) and include Helix-specific relevance guidance.

## How Helix Uses Task Cards

The collector turns raw instructional text into structured, searchable steps with:

- problem statement,
- step-by-step guidance,
- mistakes/troubleshooting hints,
- xLights area classification,
- Helix relevance impact notes,
- citation linkage to source records.

This enables Helix to provide actionable xLights task assistance without training on restricted sequence assets.
