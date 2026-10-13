# Helix for Android — offline beta

The launcher embeds the existing Helix master sequencing engine. Audio analysis,
XSQ/LMS generation and simulated MP4 previews run on the phone. No desktop,
account, server or internet connection is required for offline builds.

## Install and use

1. Install the provided APK. Android may ask you to allow installation from the
   app used to open the downloaded APK.
2. Open **Helix**, choose **xLights** or **Light-O-Rama**, then select a song using
   Android's file picker. MP3, WAV, FLAC, OGG and M4A support depends on the phone's
   installed Android codecs; unsupported audio produces a visible error.
3. In xLights mode, choose your own `xlights_rgbeffects.xml` and XSQ template, or
   use the bundled original layout/template. Controller XML and routing JSON are
   optional. In LOR mode, supply an existing legacy `.lms` containing the real
   Unit/Circuit addresses. Native `.loredit` is unsupported.
4. Start with one variant and a short preview. Tap **Build sequence on this
   phone**. The notification keeps the job visible while the app is in the
   background. **Cancel build** stops the isolated engine process.
5. Play the preview or save the show ZIP and MP4 to a folder you choose.

Sources are copied into a fresh private job directory and never overwritten.
The exported ZIP includes the generated sequences, their layout/configuration,
decoded audio, reports and requested preview. xLights layouts and LOR addresses
use the existing desktop packaging/export logic. The complete log remains in
the app's private job directory. Clearing app data removes private jobs; save
the ZIP before doing so. This initial launcher restores the latest job; a
multi-job library is deferred.

## Current limits

- Android 8+ on ARM64 or x86-64. This beta's older SciPy/NumPy Android wheels need
  a 4 KB memory-page device; 16 KB-page phone support requires rebuilt wheels.
- Numba/LLVM is unavailable. An Android-only compatibility adapter executes the
  original librosa kernels without JIT compilation. Desktop code is unchanged.
  Synthetic numerical parity checks cover beats, onsets, HPSS, CQT, pitch,
  extrema, peak picking and zero crossings; long songs can take considerably
  longer than on a desktop. Independent real-song detection accuracy remains
  outside these compatibility checks.
- Neural source separation and Whisper are unavailable. The existing HPSS
  fallback remains active; no gender/voice identity or transcription guarantee.
- Previews use the existing effect-level house renderer and Android H.264/AAC
  codecs, 640×360 at 15 fps, with a 1–120 second preview limit. They are simulated
  geometry, not a native xLights render or a physical-controller validation.
- Android can stop long-running jobs after a platform foreground time limit or
  on memory pressure. Large layouts/songs need practical device benchmarking.
- This is a debug-signed test build, not a Play Store release. A stable release
  signing key and store compliance checks are separate publication work.

## Build

Use JDK 17, Gradle 8.11.1, Android SDK 35 / build-tools 35.0.0 and Python 3.10.
Android Studio can use the same configuration. Install Python build tools first:

```sh
python3.10 -m pip install pip setuptools wheel
cd android
HELIX_BUILD_PYTHON=/path/to/python3.10 gradle :app:assembleDebug
```

`stageHelix` copies only tracked engine code/configuration into a deterministic
asset archive; repository MP3s, movies and history are excluded. The build also
creates a pure-Python msgpack wheel and removes only Numba dependency metadata
from the upstream librosa wheel, verifying all Python/data bytes remain equal.
Native dependency wheels are resolved normally, including libraries used by
SciPy, Pillow and soundfile. Do not add desktop FFmpeg or simplified substitute
analysis code to the APK.

Checks:

```sh
PYTHONPATH=. python -m pytest tests/test_android_offline.py
cd android
gradle :app:connectedDebugAndroidTest
```

The instrumentation check actually decodes synthetic audio, runs the existing
engine in both modes, exports nonempty XSQ/LMS and packages MP4s containing H.264
video plus AAC audio. See `MASTER_TODO.md` for measured validation status; this
document describes intended behavior and does not by itself certify a build.

Reference documentation: [Chaquopy](https://chaquo.com/chaquopy/doc/current/android.html),
[Android document picker](https://developer.android.com/training/data-storage/shared/documents-files),
[Android media codecs](https://developer.android.com/reference/android/media/MediaCodec).
