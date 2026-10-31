# Readable wire-band revision — October 13, 2026

The previous wire singers' pale mouths disappeared into the face contours.
The stage filter also omitted `electric_guitar_body` entirely and converted
the upright bass body to sparse edges. The revised optional two-stage scene
uses large coral lip rings, dark apertures, pink tongues and ivory teeth.
Both guitar/bass players and their original instrument bodies are solid.

Mouth dimensions follow the existing phoneme lanes and measured vocal energy.
REST and MBP remain closed with hidden tongues and teeth; L raises the tongue.
The wire-face mask contracts with the aperture. Details are appended after
existing rig indices, so hand, fret, string, key and mallet routes stay stable.
Neutral avatar styling is retained. The original RefinedBandScene and previous
movies are preserved.

## Previews

The new output directory is `outputs/Readable_Wire_Band_20261013`.

| Movie | Duration | Content |
| --- | ---: | --- |
| Helix_Readable_Wire_Band_Closeup.mp4 | 32.2 s | Four seconds of dry drums, then Wire Tree's retained final chorus; a closer wire-band camera. |
| Helix_Readable_Two_Stages_1.mp4 | 78.2 s | The original Ember/Glacier soundtrack and stage pair with the revised faces and solid strings. |

Both use 1920×1080, 20 fps, H.264/AAC and the actual source soundtrack. Historical
downloads are not overwritten. Render the other authored pairs with `--version`
2 or 3, and the combined super layout with `--version 4`.

```bash
python -m tools.render_dual_band_showcases --focus-wire
python -m tools.render_dual_band_showcases --version 1
```

## Verification

The 52 focused stage, voice, motion and readable-instrument tests passed.
After the contracting face-mask adjustment, all seven stage tests passed again.
On 96 actual source frames across Wire Tree and 49, all 28,128 sampled guitar,
bass, key and mallet pose matrices match the unchanged-performance scene exactly.
Every source performance curve, voice lane, voice-energy array and mallet
schedule matches. Both closed instrument meshes match the original vertices
and faces exactly and are watertight. See `evidence/readable_wire_band`.

The close-up fully decodes as 644 frames / 32.2 seconds with source soundtrack
correlation 0.998487416; the encoded mouth details and solid instruments were
inspected. The full sampler fully decodes as 1,564 frames / 78.2 seconds with
correlation 0.998725353. Its WAV soundtrack is byte-identical to the original
two-stage sampler. Both movies retain zero measured mallet-contact error.
These checks cover full decode, exact frame counts, duration, audio and decoded frames.
These are rendered video/pixel previews; the new face geometry does not establish
physical discrete-channel wiring or new voice-separation accuracy. No GUI,
sequencing-engine or detector threshold changes are included.
