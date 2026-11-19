# Helix Android stability — verified beta handoff

Implementation and tests are in [PR #139](https://github.com/ryankorkowski-boop/helix-sequencer/pull/139), on feature/android-offline-app-stability-20261013. The APK/AAB source commit is **6bdae4e461256df6184200e55dde2675741381ad**, based on the latest offline Android a5e2577. No primary merge or public app release was performed.

## Defects repaired

The old MP4 reader rejected size_field=1 as a size smaller than eight bytes. Real Android MediaMuxer output contains that extended-size mdat. The new reader supports standard 32-bit, extended 64-bit and terminal EOF sizes, validates all boundaries, supports version 0/1 time headers, and makes nested EOF containers finite before adding an audio edit. Measured AAC soundtrack alignment is preserved; atomic metadata replacement keeps media/chunk positions unchanged. Corrupt containers are rejected.

A preview exception formerly prevented the completed sequence from reaching Android packaging/results. XSQ/LMS and show ZIP are now checkpointed before optional rendering. Sequencing, packaging and preview have independent states; failed movies are never advertised as successful. Users can export the completed sequence even if MP4 or ZIP creation fails.

Android joblib is explicitly serial before imports, avoiding unsupported sem_open paths while retaining HPSS. Input hashing is streamed, preview RAM remains bounded, logs/state writes are throttled, stale running-state polling detects interrupted processes, and cancellation stops only the private engine job.

## GUI and preserved capabilities

Music → Layout → Style → Advanced → Generate → Results replaces the old local input arrangement. First-run help, contextual descriptions and saved preferences are included. Birdsong, Matrix Intelligence and Polish are behind expert disclosure in both local and optional desktop-remote Android screens; their algorithms/defaults remain. Neon is an explicit optional RGB palette override. RGB chorus/drop chase is automatic for eligible geometry/timing/free-effect space, with an Advanced override; single-color AC/LOR channels are excluded.

Results provides sequence, MP4, ZIP, share and report actions. xLights XSQ and supported legacy LOR LMS workflows remain. Native loredit/LCC import is not claimed. Both original donation links and remote control remain. Windows GUI, master algorithms, original media/layouts/templates/XSQs and other branches are unchanged.

## Tests and build evidence

**65 host checks pass**, covering MP3/WAV, short/long AAC full decode/alignment, extended/EOF/malformed MP4s, preview/ZIP failure recovery, interruption checkpoints, retained HPSS/librosa numerical parity, LOR mapping, AC/RGB color behavior and donation wiring.

[Final build and full native tests](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38391577471) pass on Android 11/API30 and Android 16/API36 x86_64 emulators:

| Test | Result |
| --- | --- |
| WAV, original 256-channel display, xLights XSQ | Passed, nonempty outputs and portable show ZIP. |
| Legacy LOR LMS fixture | Passed, real Unit/Circuit addresses preserved. |
| Real repo MP3 and current RGB layout | Passed, eight-second Helix Audiolights clip and 120 H.264/AAC frames. |
| Full song | All 237.44 seconds sequenced; soundtrack packaged; three-second preview decoded. |
| Injected MP4 failure after actual sequencing | Sequence and valid ZIP survive; no fake movie. |
| Android VideoView/MediaPlayer | Corrected MP4 actually plays; real screenshot retained. |
| Foreground service interruption | Fresh job reports cancelled; previous shows remain. |
| Installation/reinstall | Fresh install and same-key/same-version reinstall pass with private data preserved. |
| Remote transport and GUI | Auth/upload/start/status/cancel/download and remote activity launch pass. |
| Screenshots | Six actual local screens and playback captured; inspected. |

Independent complete decode covers xLights, LOR, real RGB and full-song previews. Every measured audio offset is 0 ms; minimum correlation 0.9977438; maximum sampled visual mean error 2.2462/255. Previews are **simulated model/effect-level views with the real soundtrack**, not native xLights/controller playback. The delivered RGB movie is 640×360, 15 fps, H.264/AAC, 8.000 seconds.

## Downloads and integrity

The artifact-only handoff workflow copies exact verified outputs; it never rerenders or substitutes a preview. Its separate archives contain:

- APK: debug-signed Helix Android 0.3.0 beta, certificate and checksums.
- AAB: successfully compiled but unsigned release bundle; not release-ready or installable as an APK.
- Media/shows: matching real MP4/XSQ/RGB show ZIP, full-song original256 ZIP and actual screenshots.
- Evidence: outcome/decoded/install/cancellation reports and failed-preview/LOR proof ZIPs.

Both ARM64 and x86_64 are packaged; native tests exercised x86_64. SHA-256 values and debug certificate are included and checked against the source CI outputs. The source API36 artifact digest is ec0d186a0fc25054845977da577a001b0a43199be374708731548aa04943219b.

The local workspace disconnected during standalone download saving. Individual saved files could not be made available from that session; the verified GitHub archives are the handoff route. CI artifacts expire after their retention period (currently January 11, 2027 for the source run). Official release-page publication remains pending through the project's authorized release process.

## Installation

Read [the beginner installation/troubleshooting guide](ANDROID_INSTALLATION.md). Open the downloaded APK in Files/My Files and allow installation from that specific trusted app if prompted. On Samsung, temporarily disable Settings → Security and privacy → Auto Blocker if it blocks installation, retry and re-enable it afterward. Recheck the state if ineffective: toggling off/on resolved one reported stuck install, not a universal fix.

**Retain the old app until important shows are backed up.** Separate CI debug builds can have different certificates and cannot update each other. Seamless updates need the original signing key. If the old preview failure prevents export, preserve its private data; this task has not recovered that phone's old job.

The guide covers blocked installs, unknown-app permissions, ABI/page-size incompatibility, package/signing conflicts, damaged downloads, storage shortages and failed updates. Public APK distribution should use only the official project release and published checksums/certificate.

## Play preparation and remaining limits

[Play readiness](GOOGLE_PLAY_READINESS.md) includes signing configuration, versionCode 4/update strategy, API36 target, permission audit, privacy/Data safety drafts, store description/screenshots, local crash-log strategy and testing plan. [Candidate release notes](ANDROID_STABILITY_RELEASE_NOTES.md) are prepared.

Production signing, a 16 KB-compatible native dependency rebuild, owner-approved public privacy policy/contact, final declarations, physical-device testing and applicable closed testing remain. Current offline wheels need 4 KB pages. For new personal accounts after November 13, 2023, Google currently requires 12 continuously opted-in testers for 14 days. Developer registration currently costs US$25 once. No registration, payment, submission or Play publication occurred.

Physical ARM64/Samsung, Windows-player/controller playback, actual older-beta certificate/version upgrades and native lighting-app imports are not newly verified. Android previews cap at 120 seconds. Fragmented MP4s and EOF boxes above 4 GiB needing relocation are rejected safely.

## Files and commits

Production files: android/app/src/main/python/{helix_mp4.py,helix_mobile.py}; java/org/helixsequencer/android/{MainActivity.java,EngineService.java,RemoteActivity.java}; AndroidManifest.xml; res/xml/show_paths.xml; android/app/build.gradle.

Validation: tests/{test_android_mp4.py,test_android_recovery.py}; OfflineEngineTest.java; tools/{run_android_device_smoke.py,verify_android_device_proof.py}; android-offline.yml. Documentation: MASTER_TODO.md, root/Android README and installation/Play/release-note files. The handoff workflow/report/evidence add no production app logic.

| Commit | Purpose |
| --- | --- |
| 6dfc91a | MP4 repair, recovery, guided GUI and distribution preparation. |
| 024ab99 | Real RGB/full-song native checks and independent decode. |
| f9d86bf | Nested EOF correction and fixture cleanup. |
| a559c31 | Native playback, cancellation and reinstall validation. |
| 1e55e06 | Correct the install marker setup/quoting. |
| 85892f2 | Accurate composited UI screenshots. |
| 6bdae4e | Fold optional remote controls into Advanced; delivered app build. |

Official policy sources are linked in the Play assessment. No master/core/desktop/original-source changes are part of these commits.

## Verified download archives

These contain exact bytes from the successful app build; extract the ZIP first.
GitHub sign-in may be required for Actions artifact downloads.

| Download | Contents |
| --- | --- |
| [APK archive](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38396947536/artifacts/11812187859) | Installable debug beta APK, installation/report text, certificate and SHA256SUMS. |
| [Unsigned AAB archive](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38396947536/artifacts/11812732500) | AAB and Play readiness guidance; not release-ready. |
| [Real preview and show archive](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38396947536/artifacts/11812722486) | MP4, matching XSQ/RGB ZIP, full-song256 ZIP and real screenshots. |
| [Test evidence archive](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38396947536/artifacts/11812487689) | Decode/install/cancel/remote reports, failed-preview and LOR proof ZIPs. |

[Artifact-only handoff run](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38396947536) passed.
APK SHA-256: 7bb6a6e59a365a371e29214c8826244d63e090cfee331881044aa46db201a6a6
AAB SHA-256: f287cf81d667e0b542cfa6333d7718f4dc8ca1f268ae110d60fe0985ef6c5082
Debug certificate SHA-256: 5441a200cd4174070148e76cb03189bbfee81f8cd1fa3b551319dd00d2eb4572

Documentation/handoff commit baba20b3c2618e81e3c0cb59415556ef191a583b adds the report,
verification record and artifact splitting. It does not change the delivered app.
