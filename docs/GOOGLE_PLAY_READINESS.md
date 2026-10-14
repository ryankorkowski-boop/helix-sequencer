# Helix Android — Google Play preparation

Prepared on 2026-10-13. No account registration, payment, submission or publication
is part of this work. GitHub APK distribution remains available.

## Build, signing and updates

- Application ID remains org.helixsequencer.android; versionCode advances from 3
  to 4, versionName to 0.3.0-stability-beta. Increment the code for every subsequent
  shipped update; never reuse a code or change the app identity accidentally.
- compileSdk/targetSdk are 36. Current [Play policy](https://support.google.com/googleplay/android-developer/answer/11926878)
  requires API 36 for new phone apps/updates from August 31, 2026. API 30 and 36
  instrumentation are configured; physical OEM testing remains necessary.
- The workflow builds an installable debug beta APK and an **unsigned** release
  APK/AAB unless the owner supplies all four signing variables:
  HELIX_ANDROID_KEYSTORE, HELIX_ANDROID_STORE_PASSWORD, HELIX_ANDROID_KEY_ALIAS,
  HELIX_ANDROID_KEY_PASSWORD. Partial configuration fails rather than guessing.
  Keep private keys and passwords outside the repository and logs.
- An unsigned AAB is a preparation artifact, **not release-ready** and not
  installable directly. Use the established upload key and Play App Signing when
  publishing is authorized. For APK/Play cross-updates, plan identical app-signing
  certificates; an upload certificate alone does not establish APK compatibility.
- CI-generated debug keys are not a durable update identity. Back up shows before
  switching betas signed with a different certificate.
- **Blocking:** Android numerical/CPython dependencies retain a 4 KB-page
  requirement. Rebuild or upgrade every native dependency, audit ELF LOAD alignment
  and APK ZIP alignment, and test with a 16 KB environment before Play release.
  See [Android page-size guidance](https://developer.android.com/guide/practices/page-sizes).
  Raising targetSdk or running zipalign does not repair incompatible ELF libraries.

## Permission and network audit

| Permission / facility | Reason and limits |
| --- | --- |
| INTERNET | Explicit desktop pairing/upload/download; browser handoff for support links. Local processing uses no server. |
| FOREGROUND_SERVICE | Keeps the private engine process running during a user-started job. |
| DATA_SYNC / MEDIA_PROCESSING service permissions | Version-specific foreground types; long jobs must handle OS time limits. Declare the applicable foreground-service use in Play Console. |
| POST_NOTIFICATIONS | Requested at the first job; denial does not block local sequencing. |
| Storage Access Framework | Only user-selected URIs and export destinations; no MANAGE_EXTERNAL_STORAGE permission. |
| FileProvider | Non-exported provider, temporary read grants for the specific ZIP being shared. |
| Cleartext traffic | Retained for existing explicitly paired desktop HTTP on trusted networks; prefer HTTPS for exposed endpoints. This means not all remote transfers are encrypted. |

No advertising, tracking or automatic crash-reporting SDK is introduced. App backup
is disabled. The private engine service and remote/preview activities remain
non-exported. Existing paired-desktop controls remain opt-in.

## Privacy policy and Data safety draft

The draft policy below must be reviewed by the owner, hosted at a public permanent
URL, linked inside the app and added to Play Console before submission. Confirm
publisher identity and support contact; they are not invented here.

Helix processes selected audio, layouts and templates on the device in local mode.
It stores job outputs, preferences and selected-file access grants in app-private
storage. There is no Helix cloud account or automatic telemetry in this build.
Choosing remote mode sends selected files and settings to the user's paired
desktop endpoint. Choosing Share hands the selected show ZIP to the recipient app.
Donation links open external pages whose providers apply their own privacy policies.
Job logs can contain filenames and local paths. Uninstalling removes app-private
jobs/preferences; exported copies remain wherever the user saved them. Export
important shows before clearing app data.

Data safety assessment is a **draft**, not a submitted declaration:

- Inspect the final bundled SDKs, not just source imports.
- Local-only processing is not developer collection. Review the paired-desktop
  and user-directed sharing exceptions under [Google's definitions](https://support.google.com/googleplay/android-developer/answer/10787469).
- Do not assert universal transit encryption: paired LAN HTTP is permitted.
- Reassess collection/sharing if analytics, cloud relay or crash uploads are added.
- No accounts means no app-account deletion flow in this build. Explain local
  deletion/export behavior in the policy.

## Store listing draft and screenshots

Name: **Helix Light**  
Short description: **Turn your music into xLights and legacy LOR lighting sequences.**

Full description draft:

Create music-responsive lighting sequences with the Helix engine on supported
Android devices. Choose music, select your lighting layout, use xLights XSQ or
legacy Light-O-Rama LMS output, and save a portable show ZIP. Make a synchronized
model-level preview with your soundtrack. Optional desktop pairing lets your
phone start and monitor work on your own Helix desktop.

This beta supports legacy LMS channel addresses, not native loredit. Phone
previews illustrate effects and do not replace testing in xLights/LOR or on
controllers. Local neural stems and Whisper are unavailable. Current offline
native dependencies require 4 KB pages.

Capture real Music, Layout, Generate and Results screens from the verified APK.
Do not use fabricated store screenshots. CI retains a real launcher screenshot;
complete store-resolution/asset requirements after UI review and remove test
filenames or other private data. No screenshot is claimed to be store-approved.

## Release gates and remaining work

1. Owner-approved signing/update identity and publicly hosted privacy policy.
2. Complete native 16 KB rebuild/validation and 64-bit dependency license audit.
3. Verify MP3/WAV, small/full songs, RGB/256 layouts, LMS mappings, preview failure
   recovery, cancellation, scoped exports/share, fresh install and same-key upgrade
   on physical Samsung/Pixel devices and representative RAM/storage limits.
4. Choose crash reporting: local logs and user-approved report sharing are the
   current strategy; Play Android vitals can be used after enrollment. Any new
   uploaded crash reports need privacy/Data safety review and path/token redaction.
5. Content rating, support contact, foreground-service declarations, listing
   assets, policy review and closed-test plan. For personal accounts created after
   November 13, 2023, [Google requires at least 12 testers continuously opted in
   for 14 days](https://support.google.com/googleplay/android-developer/answer/14151465)
   before applying for production access. The owner/account type is not assumed.
6. [Developer registration](https://support.google.com/googleplay/android-developer/answer/6112435)
   currently costs US$25 once. Registration/payment remain explicitly outside scope.

The build can be tested through GitHub without enrolling in Play. A compiled AAB,
target API update, or emulator pass alone does not establish store readiness.
