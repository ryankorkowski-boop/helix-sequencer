# Third-Party License Checklist

This file is a practical distribution checklist for Helix Sequence Helper.
It is operational guidance only and not legal advice.

## Required Notices

### xLights
- Project: https://github.com/xLightsSequencer/xLights
- License: GPL-3.0
- Action: preserve attribution and review GPL interoperability boundaries.

### Lua
- Project: https://www.lua.org/
- License: MIT-style Lua license
- Action: include Lua attribution when distributing Lua-related functionality.

### PyInstaller
- License: GPLv2+ with bootloader exception
- Action: include PyInstaller attribution and bootloader exception notice.

### openai-whisper
- License: MIT

### requests
- License: Apache-2.0

### imageio / imageio-ffmpeg
- Licenses: BSD-family
- Action: independently validate FFmpeg redistribution obligations.

### Scientific/Audio Ecosystem
- numpy
- scipy
- librosa
- soundfile
- numba
- llvmlite
- Pillow

Action: include package notices for distributed binaries.

## Required Distribution Contents

Ship:
- LICENSES/
- NOTICE
- docs/TRAINING_POLICY.md
- docs/GPL_BOUNDARY.md
- docs/WATERMARK_POLICY.md

## AI Learning Boundary

Persistent learning systems must only learn from authenticated Helix-generated outputs containing valid Helix watermark metadata.

Externally licensed material, marketplace sequences, copyrighted music, vendor assets, and third-party choreography must not be persisted into reinforcement memory or long-term training datasets without explicit licensing rights.
