# Wadena / Nutrocker Real-World Geometry Map

This document records the first hard mapping between the professional Nutrocker LMS reference, the GP/Wadena physical display evidence, and the Helix layout coordinates. It is deliberately a **truth/calibration document**, not a claim that the source show was cloned.

## Evidence basis

- Professional reference: `2024_RGBNutrocker_antiLag_16CCRs_archive_sup.lms`.
- The LMS declares a 246.93 s sequence and the audio filename `24 - Nutrocker.mp3`.
- The LMS uses a 0.05 s fixed timing grid.
- The LMS contains 176 named LOR channels in its primary channel list and 27,183 effects total.
- 26,878 effects are `intensity`; 305 are `shimmer`.
- The companion GP/Wadena xLights layout `xlights_rgbeffects_plus_drummer.xml` supplies the physical layout coordinates used below.
- Public Wadena reporting and photographs/video stills establish the real-world landmark vocabulary: house/roof, garage, large wreath, conical/spiral tree forms, boulevard/perimeter trees, candy-cane elements, line trees, snowflakes and beat-stick/impact structures. Public reporting also describes thousands of synchronized lights and an LED tree/wreath centerpiece.

## Important limitation

The supplied YouTube URL could not be fetched as a playable video by the web retrieval layer during this pass. Therefore, this document does **not** pretend to contain frame-by-frame video timing claims. The geometry mapping below is based on the available public visual evidence plus the actual LMS/layout truth. The next video-analysis pass should replace visual-event hypotheses with timestamped frame observations wherever the video is accessible.

## Coordinate convention

Coordinates below are the coordinates already present in the GP/Wadena xLights layout. They are not invented Helix coordinates. Keep them as the source coordinate frame and transform them only at the renderer boundary.

| Real-world landmark | xLights model/group | World X | World Y | Z | Nutrocker LMS channel(s) |
|---|---|---:|---:|---:|---|
| Left/front tree | LEFT_TREE | ~122 | ~302 | 0 | Left Tree Grn / White / Red |
| Left boulevard tree | BLVD_LEFT | ~120 | ~62 | 0 | Left Blvd Grn / White / Red |
| Center boulevard tree | BLVD_CENTER | ~644 | ~11 | 0 | Center Blvd Grn / White / Red |
| Right boulevard tree | BLVD_RIGHT | ~999 | ~-26 | 0 | Right Blvd Grn / White / Red |
| Right Linden/perimeter tree | RIGHT_LINDEN | ~1290 | ~391 | 0 | Linden Grn / White / Red |
| Paired central wreath | wreath 1 2 | ~556 | ~340 | 0 | N Wreath Grn / White / Red; S Wreath Grn / White / Red |
| Garage snowflake | big snowflake garage | ~666 | ~342 | 0 | Garage Snowflake |
| Roof snowflake | big snowflake roof | ~855 | ~469 | 0 | Roof Snowflake |
| Lower roof/C9 field | Roof Lower | ~550 | ~434 | 0 | Lower C9 Grn / White / Red |
| Upper roof/C9 field | Roof Top | ~810–1039 | ~372–517 | 0 | Top C9 Grn / White / Red |
| Front/garage impact stick | Beat Stick B 4 | ~621 | ~372 | 0 | Beat Stick 1/2 and 1A/2A family |
| Right impact stick | Beat Stick A 4 | ~1279 | ~239 | 0 | Beat Stick 3/4 and 3A/4A family |
| Front line-tree field | Line Tree 1–4 | ~820–956 | ~220–240 | 0 | GRN TREE 1–9 / RED TREE 1–9 families |
| Candy-cane field | North/South Candy Cane banks | see source layout | see source layout | 0 | Candy Canes 10.1–10.16 / 11.1–11.16 |
| Mega-tree field | Mega Tree strings | source coordinates include negative X/Y | 0 | Mega Tree 1–8 red/green/white families |

## What the Nutrocker LMS says about choreography

### 1. GP-style infrastructure is not treated as independent pixels

The major boulevard/perimeter/roof/wreath families repeatedly reuse nearly identical intensity timing blocks. For example, the three boulevard green channels all begin at the same early timing pattern and remain closely synchronized for most of the show. Differences later in the block are only a few centiseconds, consistent with hand-tuned or copied-and-adjusted intensity events rather than an autonomous per-prop algorithm.

**Helix implication:** model choreography as **physical group phrases with controlled offsets**, not as every prop independently responding to audio features.

### 2. There is a strong global pulse vocabulary

Snowflakes, beat sticks and candy-cane channels have activity beginning around 0.34 s and continuing through roughly 242.2 s. These are long-lived show vocabulary layers rather than one-off effects.

**Helix implication:** maintain persistent layers:

- pulse/impact layer
- perimeter/roof architecture layer
- decorative sparkle layer
- phrase/hero layer

### 3. The mega tree is a sectional hero event

The named Mega Tree string channels are concentrated in a distinct block from approximately **134.8 s to 181.1 s** (~2:15–3:01). That is materially different from the long-lived snowflake/candy-cane/beat-stick vocabulary.

**Helix implication:** the mega tree should be treated as a **sectional hero geometry**, activated as a coherent spatial system when the musical section warrants it, rather than being forced to carry the entire song.

### 4. Beat sticks are a persistent spatial impact vocabulary

Beat Stick 1–4 contain roughly 275–283 effects each and run across almost the entire reference duration. Their physical coordinates are separated: one near the central/front field and another toward the right/perimeter side.

**Helix implication:** impact events should be capable of **cross-stage propagation** between physically separated impact props, not merely global flashes.

### 5. Snowflakes are persistent punctuation, not the main melody carrier

Roof Snowflake has 351 effects and Garage Snowflake 331. Both begin around 3.4 s and continue to approximately 242.4 s.

**Helix implication:** snowflakes are a high-frequency decorative punctuation layer that can reinforce phrase boundaries without becoming the dominant spatial trajectory.

### 6. Candy canes are a long-lived banked system

The 32-channel North/South candy-cane banks are active across essentially the full reference duration. This makes them useful as a **spatial note/rhythm field**. The existing Helix note mapping should preserve their physical ordering instead of treating them as arbitrary numbered channels.

## GP/Wadena visual geometry vocabulary

The available public visual evidence shows a display whose geometry is strongly organized around a few large anchors:

1. **House/roof mass** — the architectural background plane.
2. **Large circular wreath** — a dominant central hero shape.
3. **Tall conical/spiral tree forms** — strong vertical motion anchors.
4. **Front/perimeter trees** — left-to-right spatial framing.
5. **Candy-cane vertical marker** — a high-contrast vertical landmark.
6. **Garage/roof snowflakes** — localized high-visibility punctuation.
7. **Line trees and beat structures** — repeated foreground rhythm/impact elements.
8. **Mega-tree/string field** — a separate large-scale sectional surface.

This is the geometry vocabulary Helix should learn. The exact object shape can change, but the **relative topology and spatial roles should remain stable**.

## Mapping rule for Helix

Use this chain:

`real-world landmark -> source layout coordinate -> physical path -> neighbor graph -> acoustic spatial intent -> AC-safe renderer`

Do **not** use:

`audio feature -> arbitrary prop name -> effect`

The latter loses the physical meaning that the Wadena reference is valuable for.

## Required next calibration pass

1. Acquire/playable copies of the supplied GP/Wadena videos.
2. Extract frames at fixed intervals and at visible lighting transitions.
3. Label each frame with the source coordinate landmarks above.
4. Detect real spatial transitions: left->center, center->right, ground->roof, perimeter->hero, inward/outward, vertical rise/fall, and simultaneous global hits.
5. Align those observations to the Nutrocker LMS time axis when the same musical/reference section can be identified.
6. Store observations as timestamped **spatial events**, not as copied effect rows.
7. Use those events to calibrate the Helix neighbor graph and physical-path renderer.

## Status

- [x] LMS duration/channel/effect structure inspected.
- [x] Major physical channel families identified.
- [x] Major GP/Wadena layout landmarks mapped to source coordinates.
- [x] Persistent-vs-sectional choreography layers identified.
- [ ] Frame-by-frame supplied-video timing extraction.
- [ ] Timestamped video-to-LMS event alignment.
- [ ] Final calibrated Wadena neighbor graph.
