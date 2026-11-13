# Drastic Measures Brewery — Skeleton Band Night Parade Float

## Owner correction (2026-11-13)
The Polar Prism float is NOT an abstract float. It must clearly advertise **Drastic Measures Brewery, Wadena, Minnesota**, with an independently animated skeleton rock band reacting to the **real instrumental music**. Earlier abstract concept and owner review workflow are superseded as artistic acceptance targets. Never present an earlier Polar Prism render as an approved brewery float.

## Creative / xLights design requirements
- Front and both sides: legible illuminated DR​ASTIC MEASURES BREWERY / WADENA MN signage (no assumed trademark logo); brewery tank, keg silhouettes, hop motifs and Minnesota outline. Brand identity/artwork subject to brewery authorization.
- Center: skeletal drummer on riser with realistic distinct kick/snare/hat/tom/cymbal strikes and decay, no unrelated mallets.
- Stage left: skeletal guitarist with strumming hand, bounded fretting hand and phrase-triggered body/head motion.
- Stage right: skeletal bassist with independently timed plucks and position-constrained fret changes.
- Frontman is the FOURTH performer: independent head, jaw-neutral, arms and body gestures driven by credible melodic phrases and breaks. Do NOT fake sung lyrics or syllables for an instrumental. No keyboardist or second guitarist in the first owner-review version.
- Skeleton bodies must be genuine rigged 3D models, with anatomically constrained shoulders, elbows, wrists, hips and head joints; no 2D face stand-ins or generic idle flailing. Each performer has an independently named xLights model hierarchy and submodel/joint masks.
- Retain the dramatic depth-tunnel, crossed helices, orbital rings, animated wheel halos, matrix equalizers, and side-ribbon architecture, but route them around the band and readable brewery signage. Protect the signs from aggressive overdraw/occlusion.
- Distinct visual groups: BRAND_SIGNAGE, BREWERY_PROPS, SKELETON_DRUMMER, SKELETON_GUITAR, SKELETON_BASS, SKELETON_FRONTMAN, RHYTHM_HALOS, HARMONY_TUNNELS, SPATIAL_HELICES, MATRIX_EQ, DEPTH_RIBBONS, TRANSITION_ACCENTS.
- Avoid a constant white pulse. Use source-separated onset, pitch and timbre confidence, phrase activity, structural builds, rests and spatial propagation. Missing instrument evidence should yield restrained idle, not invented performance.
- Use authentic Drive `Polar Prism Parade.mp3`, SHA-256 `f349d05738ab274a6a37125021a7addae5569f9d074278b351a17c62072a2a0f`, 193.344s. Do not substitute synthetic audio.

## Implementation gates
- [x] Correct owner requirements recorded in the existing isolated showcase branch.
- [x] Owner selects FOUR skeletons for first version: drummer, guitarist, bassist, instrumental frontman.
- [x] Preliminary construction cost allowances added below; NOT a firm quote.
- [x] Prior native render run 43427889199 checked: design tests and real audio succeeded, but native preparation was cancelled; no verified MP4.
- [ ] Refactor `models/parade_float.py` into a brewery-branded float; preserve and reuse existing geometric props where appropriate.
- [ ] Implement actual 3D skeleton meshes, joint hierarchy, and xLights model groups (do not merely rename snowmen).
- [ ] Implement source-evidence-gated instrument-specific skeletal animation and independent joint QA.
- [ ] Add scene visibility tests for signage and skeletons in front, left, right camera views.
- [ ] Run Helix real-source analysis, generate editable XSQ/FSEQ and native xLights preview.
- [ ] Render full-length 1920×1080 H.264/AAC owner-review MP4 and verify original audio, decode, brightness, activity, frame composition and timing.
- [ ] Upload actual MP4 and native model bundle to Drive; wait for explicit owner approval.
- [ ] Keep protected beta PR #188 untouched and do not merge or release.

**IMPORTANT:** The prior Polar Prism workflow was already queued before this correction. Its results, if any, are diagnostic only and MUST NOT be treated as meeting this brewery brief. Do not claim a skeleton-band video exists until genuine assets, timing and native output are verified.

## Build-cost planning estimate (USD; 2026-11-13)
Assume an existing suitable trailer, volunteer labor, 8,000–12,000 12V WS2811 pixels, four custom animated skeletons, weatherproof wiring and substantial layered 3D scenery. No roadworthiness, axle-weight, generator load or venue approval established.

| Item | Low | High |
|---|---:|---:|
| RGB pixels and illuminated props | 2500 | 4500 |
| Controllers, PSUs, cabling | 1000 | 2200 |
| Four articulated skeletons, instruments and motors | 1500 | 3500 |
| Structural frame and sculptural scenery | 2000 | 4000 |
| Branding and brewery props | 800 | 1800 |
| Generator, audio, weatherproofing and safety | 1500 | 3000 |
| Fabrication supplies and contingency | 2700 | 4000 |
| **Total** | **12000** | **23000** |

Reference retail examples (not quotes or stock guarantees): Wally's Lights 100-node 12V strings $37.99 https://wallyslights.com/collections/12v-pixels ; Your Pixel Store 100-node 12V strings $24.99 and 350W supply $27.99 https://yourpixelstore.com/pixel-christmas-lights/ . Actual material counts, power calculations, vehicle dimensions, safe rigging and road-legal height must be measured before purchase. A trailer purchase or paid labor adds substantial cost. Never present the cost as verified BOM.

## Authenticity gate
The final acceptance MP4 MUST be generated by the actual Helix engine and xLights native XSQ/FSEQ with original audio, not an AI video, static concept, simulation or generic audio-reactive mockup. Capture tool versions, audio hash, channel mapping, model inventory, duration, MP4 decode and synchronized evidence. No approval or release until owner accepts.
