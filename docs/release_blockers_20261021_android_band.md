# Release blockers reported 2026-10-21 — Android install and band regression

Status: OPEN — owner acceptance failed. Do not label a build release-ready.

## Android installer
- [ ] Reproduce Android 16 Samsung installer message: "Install this app" then "App not installed".
- [ ] Preserve any existing installation/data; do not advise uninstalling without backup.
- [ ] Check APK artifact is standalone, nonzero, ZIP integrity and v2/v3 signing with apksigner verify; inspect package name/versionCode, minSdk, targetSdk, ABI and split configuration.
- [ ] Compare signing certificate with previous installed/released Helix APK; avoid signature-conflicting upgrade. Produce documented clean-install and upgrade-install tests.
- [ ] Install using adb install -r and capture exact INSTALL_FAILED_* reason; test API 30 and API 36 emulator, and physical Android 16 device before approval.
- [ ] Publish direct verified APK artifact with SHA256, commit SHA, size and install evidence; do not link a ZIP as an APK.

## Approved band regression
- [ ] Restore asset-first HX_SNOWMAN_DRUMMER_V3 (see docs/drummer_v3_audio_analysis.md); reject generic/legacy drummer and placeholders.
- [ ] Current approved band includes lead singer, independently reactive backup singer, guitarist, bassist, drummer V3, keyboardist; exclude xylophone performer from this showcase.
- [ ] Verify correct visual roster by inspecting actual rendered frames, not only manifests or model names.
- [ ] Verify backup singer responds independently to true backing/harmony vocals with nonzero timed mouth cues; no fabricated cues or cloned lead performance. Reject preview if backing vocals cannot be established from audio.
- [ ] Use owner-provided phoneme test audio where available; native xLights MP4 with original audio, verified duration, decode, and frame inspection.
- [ ] Add automated roster and singer-activity regressions and preserve a durable evidence log.
- [ ] Keep release blocked until owner approves APK installation and fresh native band MP4.

Owner report: latest APK does not install; latest band used wrong drummer and unwanted xylophone; second singer inactive.
