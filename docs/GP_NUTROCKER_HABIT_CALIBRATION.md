# G.P. Nutrocker Habit Calibration

## Purpose

Extract repeatable sequencing habits from the available G.P./Wadena evidence and use them to constrain Helix spatial choreography. This is a behavioral calibration layer, not a claim that the original show was cloned.

## Evidence currently available

- Professional Nutrocker LMS reference: `2024_RGBNutrocker_antiLag_16CCRs_archive_sup.lms`.
- GP/Wadena physical layout: `xlights_rgbeffects_plus_drummer.xml`.
- Multiple archived Wadena XSQ versions are present in the working history (`1Christmas in Wadena,v8.1.xsq`, `1Christmas in Wadena,v9.xsq`, `13,v8.1.xsq`, etc.).
- Public Wadena reporting describes the show as entirely self-made/self-programmed, with 47 computers, approximately three miles of extension cords, and a very large mechanically handled centerpiece wreath. Anderson specifically describes small elements appearing throughout the full show and deliberately catching the viewer's eye.
- Public visual evidence shows strong signature geometry: spiral boulevard/perimeter trees, dense cone/mini-tree fields, arches, snowflakes, candy canes, roof architecture, a large central wreath/hero element, and a sectional mega-tree system.

## Behavioral rules inferred from G.P.'s work

### 1. Build from recognizable physical signatures

A named physical object tends to retain a stable role across the show. Do not replace the layout with abstract audio-reactive particles. Effects should originate from physical landmarks and groups.

### 2. Use repeated vocabulary with variation

The LMS shows long-lived families (candy canes, snowflakes, beat sticks) combined with more sectional hero behavior. Reuse a vocabulary but vary timing, direction, grouping and intensity rather than inventing a new effect grammar every phrase.

### 3. Favor spatial choreography over random simultaneous activity

The physical layout has meaningful left/right/center and foreground/background relationships. A hit should often propagate between physically separated elements, while a phrase can remain localized before expanding to the property.

### 4. Preserve signature motion geometry

Spiral trees should remain spirals: upward trunk motion followed by a large descending/apex motion. Do not reduce these structures to vertical on/off bars when the physical model supports a path-based effect.

### 5. Layer small surprises underneath major phrases

Anderson's public description that viewers notice "cute little elements" appearing during a full show supports a secondary-accent layer. Helix should maintain low-level decorative activity while reserving the largest synchronized events for phrase boundaries and musical peaks.

### 6. Treat the hero element as sectional

The Nutrocker LMS has a concentrated mega-tree/string section around 134.8–181.1 seconds rather than treating the mega tree as the dominant carrier for the entire song. Helix should therefore give the mega tree an explicit sectional state machine.

### 7. Keep global infrastructure coherent

Boulevard/perimeter/architectural groups show closely related timing structures. Model these as coordinated families with small intentional offsets, not independent per-model reactions to every onset.

### 8. Use AC color as a compositional layer

The source Wadena layout preserves separate red/green/white AC models. Helix should retain that electrical truth and derive color choreography at the group/phrase level instead of converting the physical display into generic RGB pixels.

## Coordinate binding

Use the source xLights coordinate frame as the canonical physical frame:

- LEFT_TREE ≈ (122, 302, 0)
- BLVD_LEFT ≈ (120, 62, 0)
- BLVD_CENTER ≈ (644, 11, 0)
- BLVD_RIGHT ≈ (999, -26, 0)
- RIGHT_LINDEN ≈ (1290, 391, 0)
- central wreath ≈ (556, 340, 0)
- garage snowflake ≈ (666, 342, 0)
- roof snowflake ≈ (855, 469, 0)
- central/front beat-stick area ≈ (621, 372, 0)
- right beat-stick area ≈ (1279, 239, 0)

The complete landmark mapping is maintained in `docs/WADENA_NUTROCKER_REAL_WORLD_MAP.md`.

## Video calibration status

The public Wadena pages confirm the show identity and physical/operational behavior, but the retrieval layer has not exposed the supplied YouTube source as a frame-addressable video. Therefore no frame timestamp is being fabricated. When a playable video file is available, calibration should record:

`video_time -> visible landmark(s) -> motion direction -> spatial extent -> LMS time -> channel/group family -> confidence`

The output should be spatial events, not copied effect rows.

## Current Helix rule

`music event -> phrase intent -> physical landmark/group -> neighbor/path traversal -> AC-safe effect`

Never default to:

`music feature -> arbitrary model -> effect`
