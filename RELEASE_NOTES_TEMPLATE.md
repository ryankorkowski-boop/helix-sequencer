# Dream Sequence Weaver Release Notes

## Release Metadata
- Date: {{RELEASE_DATE}}
- Bundle: {{BUNDLE_NAME}}
- EXE: {{EXE_NAME}}
- Version: {{EXE_VERSION}}
- Source commit: {{SOURCE_COMMIT}}

## Highlights
- 

## Changes
- Added:
- Changed:
- Fixed:

## Validation
- [ ] `powershell -ExecutionPolicy Bypass -File .\release_audit.ps1 -RequireSignature`
- [ ] Launch `{{EXE_NAME}}` and verify startup/help
- [ ] Optional: run one end-to-end song generation smoke test

## Artifacts
- `{{EXE_NAME}}`
- `{{CHECKSUM_FILE}}`
- `README.txt`
- `SEQUENCER_INSTRUCTIONS.txt`

## Checksum Verification
Use this from inside the bundle folder:

```powershell
Get-FileHash .\{{EXE_NAME}} -Algorithm SHA256
```

Compare the output with the `{{CHECKSUM_FILE}}` entry.

## Known Limitations / Notes
- 

