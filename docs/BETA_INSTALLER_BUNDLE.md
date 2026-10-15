# Verified beta installer review bundle

Issue #143 requires a combined Windows/Android installer ZIP. The workflow
`.github/workflows/beta-installer-bundle.yml` builds a **review delivery** from
successful Windows, Android (both API30/API36), native xLights and complete Python
regression workflows at one exact push SHA. It never merges branches, signs a
production Android release, replaces release assets or closes acceptance gates.

The Windows build now embeds `Helix/BUILD_PROVENANCE.json` with its commit,
Actions run and executable/guide hashes, after its packaged GUI and engine checks.
Older Windows artifacts without that receipt are deliberately ineligible.

On completion, download the `Helix-Beta-v1.0-Installers-Review` Actions artifact.
It contains `Helix_Beta_v1.0_Installers.zip`, its SHA256 checksum and the validation
report. The inner ZIP contains the unchanged Windows portable ZIP, the debug beta
APK tested on API30, welcome/install/license guides, individual file checksums,
source/run/artifact receipts, API30/API36 decode results and a release-status file.
Both independently built APKs are checked; their engine commits must match, while
their binary hashes may differ. The API36 APK is recorded rather than duplicated
in the delivery. No source song, test movie, unsigned release APK or AAB is shipped.

The collector waits up to 35 minutes for the four exact-source push workflows.
A failed/cancelled latest attempt rejects assembly; an older green attempt or PR
merge SHA cannot substitute. GitHub's artifact archive digest and size are checked
before any embedded build checksum. Windows executable/guide hashes and all Android
engine file hashes are independently verified. CRCs, decoded-media proof thresholds
and the final archive checksums must all pass. A failed build leaves no delivery;
an existing output directory is preserved and requires a new destination.

To repeat on a GitHub runner with `gh` and read-only Actions access:

```bash
python -m tools.collect_beta_installers \
  --repository ryankorkowski-boop/helix-sequencer \
  --source-sha FULL_40_CHARACTER_COMMIT \
  --work /tmp/new-installer-inputs --output outputs/new-installer-delivery
```

For previously downloaded artifact ZIPs, use `python -m
tools.package_beta_installers assemble --help` and the collector's
`candidate-inputs.json`. Metadata must come from actual GitHub run/artifact
responses; local fixture tests exercise rejection and integrity, not app behavior.

The report always states `release_ready: false`. Remaining musical review,
missing original audio/rights, physical devices/controllers/vendor LOR,
production signing/upgrade/16KB/store work, licensing authority, reviewed branch
integration and final showcase acceptance remain explicit in `RELEASE_STATUS.md`.
See MASTER_TODO.md for current verified receipts and outstanding work.
