# Third-Party License Checklist

This file is a practical distribution checklist for `Helix Sequence Helper`.
It is not legal advice.

## Required Notices You Should Ship

1. **xLights**
   - Project: https://github.com/xLightsSequencer/xLights
   - License: GPL-3.0
   - File: https://github.com/xLightsSequencer/xLights/blob/master/License.txt
   - Action: keep clear attribution and provide GPL-3.0 notice where applicable.

2. **Lua (for xLights Lua scripting context)**
   - Project: https://www.lua.org/
   - License: MIT-style Lua license
   - File: https://www.lua.org/license.html
   - Action: include Lua license notice when distributing Lua-related functionality/docs.

3. **PyInstaller**
   - Project: https://pyinstaller.org/
   - License: GPLv2+ with bootloader exception
   - Action: include PyInstaller notice and exception reference.

4. **openai-whisper**
   - Project: https://github.com/openai/whisper
   - License: MIT

5. **requests**
   - Project: https://github.com/psf/requests
   - License: Apache-2.0

6. **imageio / imageio-ffmpeg**
   - Projects: https://github.com/imageio/imageio and https://github.com/imageio/imageio-ffmpeg
   - Licenses: BSD-family
   - Action: include notices and verify any FFmpeg binary license terms used in your build.

7. **numpy / scipy / librosa / soundfile / numba / llvmlite / Pillow**
   - Licenses: BSD / ISC / similar permissive licenses (package-specific)
   - Action: include package notices for distributed binaries.

## Practical Distribution Tip

When shipping the customer bundle, include:

- `LICENSES/` folder with license texts
- this checklist
- your own product EULA/terms (if any)
- attribution section in the GUI License window

## Helix Learning Boundary

The self-improving scoring system must only persist learning from Helix-generated outputs that include the project watermark metadata. Do not use copyrighted songs, licensed vendor sequences, third-party templates, marketplace XSQs, or other externally licensed material as training or reinforcement memory. Third-party materials may be used only according to their licenses for normal sequencing/rendering workflows, not as persistent learning sources.
