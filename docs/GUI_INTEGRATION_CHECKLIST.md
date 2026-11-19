# Integrated GUI execution checklist — 2026-10-12

Working branch: `codex/gui-complete-integration-20261012`, based on band delivery `5c78ffa1`. Primary is unmerged.

- [x] Inspect recent portable, dual-mode, native-FSEQ and musical-color source branches; selectively integrate modules without reverting current band architecture.
- [x] Distinct xLights XSQ and legacy LOR LMS modes, real Unit/Circuit source mapping, portable-worker dispatch.
- [x] GUI RGB options, native xLights render, real FSEQ preview, mapped AC XSQ export; mode guards disable incompatible choices.
- [x] Fix duplicate palette-table index bug; retain explicit palettes; guard missing neon assignments against AC, mixed and unknown targets; PRECHORUS build palettes precede CHORUS matching.
- [x] Fix exact imported LOR swatch priority and actual video ndarray encoding.
- [x] Optimize worker logging with main-thread queue and 100-event batches; asynchronous layout building; numeric input validation; concurrent job guard; isolated LOR run workspaces.
- [x] 59 backend/render/export tests and 9 worker/command tests pass. Initial failures retained in evidence; corrected and rerun.
- [x] Actual Tk GUI initializes, switches both modes and AC compatibility, with all visible controls/log fitting 1140x850; screenshot decoded and inspected.
- [x] Fix independently reproduced direct-script `core` import failure in FlowQuality exporter.
- [x] Fresh Windows EXEs, both GUI modes, native FSEQ and real eight-second XSQ/LMS/MP4 workers pass at323b6cde.
- [x] Native duplicate-palette probe confirms RGB255/46/209 and neutral AC255.
- [x] Retrieve exact previous six-song sampler WAV and its six-layout native reference package.
- [x] Locally rendered/decoded two3603frame movies on the exact WAV; native six layouts and band matrix verified. Workspace then went offline before saving.
- [x] Issue132 local experiment completes after external template/CLI fixes; original checkout is clean. Three real-audio movies generated.
- [ ] Independent Actions rebuild38312641499 restores exact encrypted inputs, passes regressions and is rendering. Publish/inspect/hash-verify new durable downloads before final handoff.

Sampler provenance: previous Library package `Helix_Six_Song_Sampler_Package.zip`. WAV SHA256 `0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb`; 7,944,585 stereo PCM16 frames at44100Hz =180.14931972789117s. Prior six30s cuts retained, including recovered AAC tail padding; no guessed reconstruction.

Limits: legacy LMS, not S5/S6 loredit; vendor-app/hardware playback unverified. Default sequence MP4 simulates XSQ effects; FSEQ button reads genuine rendered bytes with approximate stock-model geometry. Windows bundle excludes optional Whisper/PyTorch/3D-band runtime. Musical detections remain estimates pending independent listening/labels. Physical native band parity is not claimed.
