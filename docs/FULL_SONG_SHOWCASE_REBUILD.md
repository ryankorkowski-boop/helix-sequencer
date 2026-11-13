# Helix Motion showcase rebuild

Issue #216 and draft PR #217 track the one-song pilot. Both previous Helix Motion videos, including run 43274451494 at b84f7c1, remain owner-rejected. A separate Phoneme Test Hook render exercises vocal models. The other 82 songs require explicit pilot approval. PR #188 and public release have separate approval gates.

## Residential layout references

- Light-O-Rama's [sequence layouts](https://store.lightorama.com/pages/sequence-layouts) and [48-channel layout drawing](https://www1.lightorama.com/wp-content/uploads/TypicalLayout48Channels.pdf) show how house circuits, mini trees and arches can share a residential installation. The 16- and 64-channel builds here use independently addressed circuits, with editable custom prop geometry.
- [Haus of Holiday Lights](https://www.hausofholidaylights.com/layout) and [Spectacle of Light](https://www.solsequencing.com/Display-Layout-c129728748) show grouped wreaths, arches, outline elements, mega trees and display ornaments. [RGB Sequences](https://rgb-sequences.com/products/for-king-country-joy-to-the-world) and the [xLights community Jingle Bells sequence](https://xlightsseq.com/sequences/andrea-bocelli-muppets-jingle-bells.1426/) provide examples of mapping shared sequences across different display inventories.
- The [xLights model-group manual](https://manual.xlights.org/xlights/chapters/chapter-four-tabs/model-groups) and [singing-face manual](https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/singing-faces) describe native groups and face node ranges. Helix writes the group membership and exact ranges into the show XML.
- Setbacks, elevations, dimensions, camera positions and the large helix installations are original showcase design choices. They are preview geometry. Site measurements, mounting engineering and electrical plans require separate work.

## Editable layout inventory

| Panel | Layout | Main prop groups |
|---:|---|---|
| 1 | Classic LOR 16 AC | Roof, windows and door, arches, mini trees, candy canes |
| 2 | 64-channel AC | Four independently addressed circuits per authored fixture |
| 3 | Original 256-channel AC | Source-address AC fixtures, including legacy trees, note props and canes |
| 4 | Basic RGB house | Rooflines, windows, door and candy canes |
| 5 | RGB arches and mini-tree forest | Ground arches and staggered mini-tree rows |
| 6 | Single mega-tree residence | Side mega tree, topper, house and ground arches |
| 7 | Dual mega-tree residence | Two independently addressed mega trees, toppers and residential props |
| 8 | Singing-face house | Bulb face, snowman face and house outline |
| 9 | Singing Christmas trees | Two separately routed tree faces and candy canes |
| 10 | Matrix-centered residence | Porch matrix, outline, trees and arches |
| 11 | Canonical snowman band | Drummer, bass, guitar, keyboard, lead and purple harmony |
| 12 | Advanced RGB residence | Garage matrix, wreath, spinners, snowflakes, spiral trees and mega trees |
| 13 | Massive Spiral Forest Estate | Three spiral groves, mega trees, estate rooflines, matrices, spinners and arches |
| 14 | Double-Helix Wonderland | Four intertwined helix models, counter-directed groves, layered arches and snowflakes |
| 15 | 3D Helix Megastructure | Nested towers, depth matrices, tunnel rings, overhead rings and depth columns |
| 16 | Ultimate Helix Universe | Twin and overhead helices, three spiral groves, mega trees, matrices, depth grids, tunnel rings, snowflakes, spinners, two face pairs and the full band |

Each panel is a portable xLights show folder with its own `xlights_rgbeffects.xml`, networks file, custom model exports and editable XSQ. The primary renderer shares one Helix analysis across the sixteen layouts. Panel 3 retains all source names, channel addresses and fixed color families. Its preview continues to use the existing legacy virtual-geometry adapter.

## Band, voices and sequencing

The rejected video rendered the original artwork as a planar grid and lit major kit components in a neutral color. The rebuild uses the repository's closed-depth `SourceDrummer3D` implementation, bound to the canonical `drummerbg.png` hash. It keeps source front projection, samples the front and rear surfaces, retains static source colors and uses source-timed shoulder, stick, hi-hat and beater poses. The body and eight instrument surfaces have measured depth. Native xLights displays addressable sampled surfaces and a finite pose bank. Check the captured front frame against the original artwork for visual approval. Hi-hat, tom and cymbal claims remain limited to the retained detector evidence, and cymbal side is a staging assignment.

A keyboard performance requires the production confidence gate for source ownership. The pilot's mixed-bus keyboard events lack ownership and are suppressed for the performer. Lighting props can still use their harmonic pitches as measured musical evidence. Compare those decisions with the band instrument receipt. No mallet or xylophone performer is included.

Helix Motion has no vocal performance. Phoneme Test Hook uses its own exact recording hash and separately screened lead and residual-backing acoustic clocks. Separate timing and moving mouths establish independent exported animation. Singer identity and lexical alignment remain unverified. The export maps the native xLights phoneme vocabulary to seven existing physical shape profiles.

Measured production notes and percussion drive the native prop scheduler. Coordinate slices allow travel along arches and through height on the cones, towers and helices. Section strategy changes spatial spread and direction. The native route clips delayed effects to source note endings where coordinate routing is enabled. Matrix effects use supported note windows. The on-screen facade is a zero-channel native view object. Transparent unlit nodes allow independent foreground and background props to remain visible.

## Application paths

Windows starts the shared production CLI via `gui_launcher.py`. Android stages the shared Python engine via `tools/stage_android_engine.py` and runs it through `helix_mobile.py`. The showcase layout and native preview adapters in this branch are still a separate entry point. Same-source GUI layout selection, xLights and FSEQ behavior, preview visibility, offline resource limits and physical device parity require implementation and testing before packaging. The historical Windows and Android builds do not establish parity for this change.

## Finale render recovery

The initial 427 MiB panel 16 XSQ exceeded the native process budget and ended with signal 9. The revised panel retains 180 models and the same source kit and layout, distributes measured pitches across physical prop banks, and uses a lower native surface sampling density for the overview. The regenerated XSQ is 110 MiB and contains 334,437 native channel slots. The full-resolution vocal band view and panel 11 retain the original sampling.

## 13 November — rebuilt Helix Motion and vocal review delivered

- Native Helix Motion pilot: 264.800 s, 1920×1080 H.264/AAC, 30 fps, 7,944 frames, all 16 distinct and active. Source correlation 0.9991234, max lag 0.125 ms. SHA-256 `68ba662f92004deaeb61c1d190bda34e2c2999438486f0751ef1b2d8ca5398e0`. [MP4](https://chatgpt.com/library?file_id=libfile_b16cb208a6688191864cc1772c066dcf&account_id=personal).
- The finale's second monolithic native attempt also exited with signal 9. Six bounded xLights 2026.18 renders supplied the exact 5,296-frame channel timeline. The archive preserves the full editable XSQ, chunk XSQs and original native FSEQ blocks. Intersecting On fades were interpolated; native effect phase can restart at a join. [Native XSQ/FSEQ and layout inventory](https://chatgpt.com/library?file_id=libfile_0ad590fdca4c8191a3d176bf3ba97f9e&account_id=personal).
- The 16/64/256 AC panels each have zero all-on frames. All three checked instrumental face panels have zero open-mouth frames. The source-front V3 kit uses the same `drummerbg.png` SHA as `54ded375`. [Drummer frame comparison](https://chatgpt.com/library?file_id=libfile_2d519f0d83548191a3d4db5d613b5e96&account_id=personal).
- Native vocal review: [Phoneme Test Hook MP4](https://drive.google.com/file/d/1fYm8KxIG5v3dWxb4Wx5Ufw_mPLygS9dA/view), SHA `cc56007189571ddaa59870f590ee5104167c0e3c9f055fbead5d234ab8503990`. 265 lead-only and 47 backing-only native open-mouth frames in each view. Seven physical mouth profiles and acoustic estimates remain; lexical alignment and independent singer identity are unverified.
- Exact-source Windows candidate `3872c7f` passed packaged smoke and archive/EXE integrity checks. [Unreleased candidate](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/43374313005/artifacts/14013538889). Android API 30 and 36 compiled at that commit. [Android emulator and export run](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/43374312938). Showcase selection/native adapter integration, device behavior and parity require separate completion.
- Exact-source Python 3.12 passed 2,396 tests with six skips and 24 subtests. Python 3.11 passed 2,392 and failed four inherited bounded-audio numerical assertions at their existing tolerance. Strict independent vocal qualification still fails. [Regression runs](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/43374313207).
- Status: awaiting owner review. Other 82 songs held. PR #188 open and unmerged. Beta publication and public installer replacement remain unauthorized.
