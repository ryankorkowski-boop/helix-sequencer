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


## Expanded source-bound native review

The opt-in review now reuses the retained analysis for nine hardKor recordings,
with fresh full-source Drive byte/hash confirmation and lossless excerpt manifests.
`recover_showcase_source_cache.py` verifies the original cached audio hash before
creating a new cache; retained acoustic vocal estimates do not establish singer
identity or verified phonemes. Unsubstantiated harmony lanes remain inactive.
`combine_native_stage.py` combines matching original excerpts, excludes the new
band from unrelated scenery groups, and writes native XSQ/layout inputs for a
fresh xLights render. Full native band spans are compared to standalone output.

Native FSEQ v2 sparse files store the sum of packed sparse ranges in the channel
header, while destinations can occupy higher universe offsets. The quality reader
now validates packed width, nonoverlap and bounded expanded allocation separately,
matching xLights `V2FSEQFile::writeHeader`. Its default allocation guard is unchanged.

The portable review package includes the exact orchestration scripts, edit
manifests, selected source caches, XSQs, layouts, native FSEQs and renderer logs.
MP4 composition uses only verified native footage. Six-view composites retain
40fps band / 20fps scenery sources and are explicitly editorial 40fps outputs.
Advertisement titles and cuts are editorial; no performance movement is added
in postproduction. Original 24-bit PCM excerpts supply exact edit timing before
one final AAC encode. Full decode and source-audio correspondence are mandatory.

These RGB pose-bank review exports do not replace AC16 wiring or release EXE/APK
artifacts. Finite source-pose states, uncertain instrument/vocal separation,
unannotated lyrics and artistic acceptance remain limitations. Section composer
PR171 stays disabled. No release merge or public advertisement publication.
