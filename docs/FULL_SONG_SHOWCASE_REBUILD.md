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
