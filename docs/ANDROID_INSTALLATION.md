# Install Helix on Android

Download only from the [official Helix Releases page](https://github.com/ryankorkowski-boop/helix-sequencer/releases).
Choose the APK attached to the current Android release, not a source-code ZIP or an AAB.
When supplied, compare its SHA-256 checksum and signing certificate with the release's
published values. A checksum confirms matching bytes; it does not by itself prove who signed them.

1. Open the official Releases page and download the current Android APK.
2. Open it in **Files** or Samsung **My Files**.
3. If prompted, open Settings and enable **Allow from this source** for that specific
   trusted file app or browser. Return to the APK and retry.
4. On Samsung, if Auto Blocker stops installation, temporarily turn it **off** under
   **Settings → Security and privacy → Auto Blocker**. Menu names vary by One UI version.
5. Retry opening the downloaded APK. If the setting appears ineffective, recheck its
   actual state and retry. One user reported that toggling Auto Blocker off and on,
   then retrying with installation permitted, resolved a stuck block. That is a
   reported workaround, not a universal fix; installation may require it to be off.
6. Complete installation, then **re-enable Auto Blocker**. Remove the file app's
   unknown-app permission if you no longer need it.
7. Launch Helix. Follow the first-run guide: music, lighting layout, xLights/LOR,
   Generate, then Results to preview and save your show.

The offline beta requires Android 8 or later, a supported 64-bit ABI (arm64-v8a or
x86_64), and 4 KB memory pages. Current numerical wheels do not support 16 KB pages.
Keep enough free space for the APK, extracted engine, decoded WAV, sequences, ZIP
and temporary movie files. Large songs need substantially more space than the MP3.
The app uses Android file pickers; it does not request all-files storage access.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Installation blocked | Recheck Samsung Auto Blocker and any device-management restrictions. A managed phone may prohibit sideloading; do not bypass its policy. |
| Unknown-app permission missing | Enable it for the exact app opening the APK, not every app. Browser permission does not grant My Files permission. |
| APK incompatible | Check Android version, 64-bit ABI and the release's supported devices. A 16 KB-page phone cannot run the current offline numerical libraries. |
| Package conflict / signing error | Updates need the same application ID, compatible signing certificate and higher versionCode. Save your shows before uninstalling an older beta; uninstalling removes private jobs. Do not erase the old app merely to troubleshoot without backing up its outputs. |
| Previous version will not update | Older CI debug betas may have a different debug certificate. Compare the published certificates. Use the matching signed update when available; otherwise back up first and perform a clean install. Do not install a lower versionCode over a newer build. |
| Insufficient storage | Free space, then download again. Sequencing expands compressed audio to PCM and temporarily keeps both the show ZIP and preview. |
| Damaged or incomplete APK | Delete only the failed download, download again from the official release, and compare its checksum. Do not rename HTML/error pages to .apk. |
| Preview failed but music sequenced | Open Results and save the sequence or show ZIP. The run report distinguishes sequencing, packaging and preview outcomes. |

See [Android build and distribution](../android/README.md) for beta limitations and
[Play readiness](GOOGLE_PLAY_READINESS.md) for the remaining store work.
