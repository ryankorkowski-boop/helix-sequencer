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

## Verified October15 delivery

Source `d3a3d377e64b0d95b54e553e89dce34dc0f93194` passed the full Python3.11/3.12
suites (1,560 passed/5missing-fixture skips each), native xLights, packaged Windows
and both Android emulator gates. The installer workflow38697129438passed and its
[actual download](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38697129438/artifacts/11954249825)
was independently checked after upload, including nested CRCs, all delivery
checksums, Windows provenance and all 968 API30 engine file hashes.

The inner `Helix_Beta_v1.0_Installers.zip` is334173665bytes, SHA256:
`1d93a9cc02d32dcf60f80ba69a279ccb5b8fc10c01a8a4be1991be66578e1eef`.
The outer Actions download is287440630bytes, SHA256:
`77c6256f056e8755a1eea2819b19c9163510be2a2f41be6a3db79f0bdad127d0`.
Both APKs were checked by the CI assembler; the API30APK is included. Local
independent verification downloaded the final bundle, not the separate API36input
archive. Detailed receipts: `evidence/72h_completion/installer_delivery_receipt.json`.
Windows evidence comes from Server2022 and Android evidence from x86_64 emulators;
physical Windows11/Samsung/ARM64 and final release gates remain open.
