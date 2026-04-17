# Snowman Band Concepts

Three larger-than-life 2D snowman band concepts sized for roughly 8-9 foot performer builds.

Files in this folder:

- `snowcap_swing.svg`
- `aurora_echo.svg`
- `candy_cabaret.svg`
- `gallery.html`

## Shared Performance Logic

### Standup Bass

- Height target: 9 ft performer with a 10-11 ft total silhouette including bass scroll.
- Four strings are audio-reactive.
- Right hand uses a short slap motion across the strings.
- Left hand travels up and down the neck to follow pitch zone changes.
- String logic: map low-to-high notes across the four strings in order so string 1 reads as the lowest lane and string 4 reads as the highest lane.

### Guitar

- Height target: 8.5-9 ft performer.
- Six strings are audio-reactive.
- Right hand uses fast strum strokes instead of bass-style slaps.
- Left hand shifts between three or four neck positions to imply chord and lead movement.
- Background vocals trigger a subtle singing-face layer.

### Lead Singer

- Height target: 8-8.5 ft plus top hat or scarf plume.
- Face should be exaggerated: wide mouth open shapes, eyebrow pops, cheek accents, and oversized mic pose.
- Main vocal stem drives mouth shapes and expression intensity.

### Background Vocal Faces

- Bass player and guitarist each get a low-intensity face layer.
- Only trigger when backing vocals are present.
- Keep it softer than the lead singer: smaller mouth shapes, fewer eyebrow hits, shorter hold times.

### Drummer

- Crash cymbal:
  - Primary string is a 2D arc above the kit.
  - Secondary offset arc sits slightly higher.
  - Hit logic: fire primary on impact and trigger the secondary with a 200 ms sparkle or shimmer decay.
- Kick drum:
  - Use three concentric circles.
  - Pulse center to medium to large in about 100 ms.
- Hi-hat:
  - Use upper and lower plates at rest.
  - On hit, briefly switch to a combined horizontal flash.
- Snare:
  - Use a dense flat disc or horizontal oval.
  - Hit logic: full intensity flash for the duration of the snare stem.
- Arm logic:
  - Use six arm-position frames as the skeleton.
  - Cymbal hits should drive the biggest arm flail.
- Layering:
  - Body stays on a background layer.
  - Drum hits, arms, and cymbal overlays ride on stem-reactive overlay layers.

## Concept 1: Snowcap Swing

- Visual direction: vintage jazz quartet with warm brass, cranberry scarf accents, upright posture, and a crooner singer front and center.
- Best for: classy Christmas jazz, big band, crooner vocals, sleigh-style swing.
- Footprint:
  - Bassist: 5 ft wide x 9 ft tall.
  - Singer: 4 ft wide x 8.5 ft tall.
  - Guitarist: 5 ft wide x 8.5 ft tall.
  - Drummer and kit: 7.5 ft wide x 8.5 ft tall.
- Sequencing feel:
  - Bass strings read clearly with big isolated slap hits.
  - Guitar favors quick offbeat strums.
  - Singer face is the star.
  - Drummer feels like a jazz showman with big cymbal swells.

## Concept 2: Aurora Echo

- Visual direction: icy blue and teal snowmen with aurora gradients, crystalline instruments, and a cooler, more modern stage picture.
- Best for: cinematic instrumentals, synth-heavy Christmas music, dramatic intros, and moody builds.
- Footprint:
  - Bassist: 5.5 ft wide x 9 ft tall.
  - Singer: 4.5 ft wide x 8.5 ft tall.
  - Guitarist: 5 ft wide x 8.75 ft tall.
  - Drummer and kit: 8 ft wide x 8.75 ft tall.
- Sequencing feel:
  - Bass strings can glow with cleaner pitch buckets.
  - Guitar hand motion reads as sleek rapid tremolo.
  - Singer face has sharper mouth geometry and stronger eye accents.
  - Drummer kit feels icy and high-contrast.

## Concept 3: Candy Cabaret

- Visual direction: extra theatrical and festive with candy-striped instruments, peppermint drum shells, bold scarf tails, and playful stage energy.
- Best for: hyper-festive tracks, novelty Christmas songs, audience-favorite singalongs, and high-energy medleys.
- Footprint:
  - Bassist: 5.5 ft wide x 9 ft tall.
  - Singer: 4.5 ft wide x 8.25 ft tall.
  - Guitarist: 5.25 ft wide x 8.5 ft tall.
  - Drummer and kit: 8.5 ft wide x 9 ft tall.
- Sequencing feel:
  - Bass slaps can be exaggerated and comedic.
  - Guitar strums feel snappy and flashy.
  - Singer face can push the biggest expression changes.
  - Drummer is the most animated of the three concepts.

## Build Notes

- Use the SVG posters as look-development references, not final fabrication drawings.
- Keep each performer on separate controller groups so face, hands, body, and instrument strings can layer independently.
- Treat strings as ordered lanes. The sequencing logic you just asked for can use the number of strings or grouped string segments directly.
- If you build only one full band first, start with the bassist and singer. Those two props will prove out the face and string-mapping logic fastest.
