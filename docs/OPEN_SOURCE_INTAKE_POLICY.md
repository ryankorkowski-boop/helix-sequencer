# Open-Source Intake Policy

This project includes a metadata-only intake utility:

```powershell
python tools/open_source_intake.py --min-stars 20 --limit 30
```

## Purpose

- Discover high-star open-source XSQ/shader repositories.
- Record only repository metadata and licensing status.
- Avoid source copying or training contamination.

## Legal Guardrails

- Allowlist licenses only (MIT, Apache-2.0, BSD-2/3, ISC, MPL-2.0, CC0-1.0, Unlicense).
- Repositories with missing or non-allowlisted SPDX IDs are marked blocked.
- Utility stores links/metadata only; no code download path is implemented.
- Vendor/proprietary sequence files are out of scope.

## Output

Default output:

- `outputs/open_source/open_source_manifest.json`

Manifest includes:

- repository URL and stars
- license SPDX ID
- `legal_ok` boolean
- reason for allow/block decision

## Optional Backend Licensing

- `Essentia` remains optional and is not required for core Birdsong flow.
- Core Birdsong pipeline works with `librosa`, `numpy`, and `scikit-learn`.
