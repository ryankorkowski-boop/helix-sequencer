# Native showcase recovery

Development branch based on PR153 f8fafec4. Release integration remains held.

The opt-in body-level adjustment changes static BODY/BASE_DIM illumination only. Instrument and vocal curves, effect times and AC allocations remain unchanged. Default body levels are preserved when the option is absent.

Reproduce from the recovered Helix_3D_Vocal_Review package:

```bash
python -m tools.build_spatial_review --root /path/to/Helix_3D_Vocal_Review --id E14 --variant 4 --body-level .85
```

Render the resulting show/Performance.xsq in official xLights 2026.18. Native House Preview uses the actual pane size. The review uses two rows, 4px square lights and a closer native 3D camera. These preview settings do not fabricate or retime channel activity. The exact portable show and native execution logs accompany the MP4.

Source music: hardKor, Helix Audiolights, seconds 40–76. Current Drive source SHA256 8ced92ba179c931a2c7f29f834df1c8fd6a399d78074de0de030bc952bb5f0ec. The existing multidimensional activity ranker independently selects this interval, score 0.7624476171198415.

Audio trim fix e662469c is recovered and extended through tools.audio_excerpt: configurable 30–42s sample-accurate 24-bit PCM WAV, original sample rate/channels, source/output hashes, finite-range validation, source-end rejection, temporary-file validation and safe replacement. The runner accepts --start, --end and --select-active (existing 36s ranker). Its Python preview remains diagnostic; final media uses native xLights.

Reused unchanged quality/native modules from PR168/169/170. Composer171 stays disabled. Targeted results: 83 passed, one optional environment-dependent native-manifest skip. Native rendering and full MP4 checks are recorded separately; no full-suite claim.

Native light poses are stationary geometric states with source-driven lighting changes, not articulated meshes. Mixed vocals do not identify individual singers; quiet harmony is preserved without independent evidence. Detector accuracy, physical controllers and artistic acceptance remain separate.
