# Beta Policy

The Helix Sequencer is under active development and available as a beta release. This document outlines our approach to data, privacy, and stability.

## Data Collection and Privacy

### What We Do NOT Collect

✅ **Private data is never collected.** The Helix Sequencer:

- **Does not phone home.** No telemetry, usage stats, or error reports are sent to external servers without explicit user action.
- **Does not analyze your content.** Your audio files, xLights project files, templates, layouts, and sequencing decisions remain local to your system.
- **Does not scan your network.** The tool operates only on directories and files you explicitly specify.
- **Does not require account creation.** No login, registration, or authentication is required for any core functionality.
- **Does not embed tracking.** No analytics, cookies, or tracking pixels are used.

### Local-Only Operation

All processing happens locally on your machine:

- Audio analysis and processing
- Sequencing calculations and effect generation
- Artifact writing and manifest tracking
- Report generation

### Optional Cloud Integration

If you choose to use cloud features in the future (not currently available):

- Explicit user consent will be required before any data leaves your system
- You will have full visibility into what data is being transmitted
- Data will be transmitted over encrypted channels
- You can disable cloud features at any time

## Run Tracking and Logs

The Helix Sequencer creates local run manifests and logs to help you track execution:

- `run_manifest.json` - Status, artifacts, and timing for each run (local only)
- `command.txt` - The exact command used to invoke the sequencer (local only)
- `outputs/` directory - All artifacts and generated files (local only)

These files are stored in your configured `output_root` directory and are never transmitted anywhere without your explicit action.

## Beta Stability and Support

### Known Limitations

As a beta product:

- **Backwards compatibility:** Output format, configuration structure, and CLI arguments may change between versions
- **Performance:** Some operations may be slower than the final release
- **Edge cases:** Unusual project configurations may not be fully supported
- **Windows-first:** Development focuses on Windows; macOS and Linux support is community-driven

### Version Tracking

Each run generates a unique timestamped directory (`YYYYMMDD_HHMMSS_mmm`). The manifest includes:

- When the run started and finished
- Which profile was used
- Success or failure status
- Any errors encountered
- List of generated artifacts

This helps you track results across multiple runs and diagnose issues.

### Crash Recovery

If the sequencer crashes:

- Run directory and partial manifests are preserved for forensics
- Error summaries in `run_manifest.json` help identify the issue
- Subsequent runs do not interfere with previous ones

## Bug Reports and Feature Requests

We encourage feedback during beta:

1. **Enable local logging.** The manifest and command.txt files help diagnose issues.
2. **Include reproduction steps.** Describe exactly what you tried and what happened.
3. **Attach your manifest.** The `run_manifest.json` from a failed run is helpful (no content is exposed).
4. **Open a GitHub Issue.** See [GitHub Issues](https://github.com/ryankorkowski-boop/helix-sequencer/issues).

## Third-Party Dependencies

The Helix Sequencer uses open-source libraries. For a full list of dependencies and their licenses, see [THIRD_PARTY_LICENSES.md](../THIRD_PARTY_LICENSES.md).

## Support and Community

- **GitHub Discussions:** Ask questions and share ideas in [Discussions](https://github.com/ryankorkowski-boop/helix-sequencer/discussions)
- **Issue Tracker:** Report bugs at [Issues](https://github.com/ryankorkowski-boop/helix-sequencer/issues)
- **Supported Platforms:** See [SUPPORT_MATRIX.md](./SUPPORT_MATRIX.md)

## Policy Changes

This Beta Policy may be updated as the project evolves. Changes will be announced in release notes. Your continued use of the tool after a policy update indicates acceptance of the new terms.

---

**Last Updated:** 2026-06-03

For questions about this policy, please open an issue on GitHub.
