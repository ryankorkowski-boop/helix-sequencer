# Snowman band physical channel audit (2026-10-14)

## Source contracts and limitations

- `core/ac_band_channel_map.py` creates one AC circuit for each `submodel_order` item in `models/helixville4_band_assets.py`. This is a **background outline asset** map, not the complete performing band's independently animated hardware map.
- `models/helixville4_vocal_phonemes.py` defines REST, AH, EE, OH, MBP, FV, L (seven exclusive vocal states) for both lead and female singer.
- `models/working_band_member.py` uses mouth_A/E/I/O/U/MBP in a separate singer pipeline. Do not silently equate the two vocabularies.
- `assets/drummers/snowman_locked/drummer_layers.yaml` defines 12 active visual overlays plus a dim stationary base; its snare-left and snare-right are separate, as are open/closed hi-hat, left/right crashes, ride and dual crash. These are **overlay events**, not automatically 12 independently wired outputs.
- Existing PR #146 reports twelve physical drummer circuits in its release snapshot. Inspect that implementation before changing or duplicating wiring.
- The xylophonist/mallet player's finalized physical channel allocation remains unverified.

## Physical-kit requirements (not yet verified implemented)

- Independently illuminate left cymbal, floor tom, mid-left tom, left-hand snare, right-hand snare, kick, high-right tom, hi-hat and right cymbal.
- Each strike channel should illuminate its relevant instrument plus the arm/stick contact pose; left and right snare hits share the same physical snare face but require distinct arm/stick circuits. Avoid connecting the same AC string to two switched circuits without isolation.
- Maintain a separate always-dim decorative base channel for drummer body and stationary kit outlines; it must never duplicate moving arms/sticks.
- For AC builds, each independently animated pose generally requires a separately controllable string or circuit. For pixels, distinct logical submodels can share physical pixels and the RGB channel count is typically three per RGB pixel, not one per submodel.
- Preserve distinct seven-shape singer mouth support in Helixville4. Determine actual node topology before assigning pixel counts, strings, controller outputs or price.
- Do not price one 100-count light string as if it necessarily fits a short arm or mouth: account for excess length, circuit minimums, and approved manufacturer cut restrictions.

## Acceptance tests before manufacturing

1. Export the *current PR #146* drummer AC and xLights mappings and enumerate physical circuits and channel addresses.
2. Trigger each of the nine requested percussion targets in isolation; verify arms/sticks make contact with the correct target, both snare hands separately, and dim base unchanged.
3. Test overlapping dual hits, fast rolls and both hi-hat states without channel collisions.
4. Export lead/female singer faces and test all seven phoneme states against xLights face definitions and real physical string/pixel geometry.
5. Export bass/guitar/mallet targets, inventory independently animated poses and map each to actual AC circuit or pixel submodel.
6. Produce BOM from verified circuit/node counts, with separate 2D/3D framing, fence area, post spacing, shipping weight and retailer SKU quotations.
7. Test generated XSQ/FSEQ import and hardware channel addresses; do not call a diagram or SVG a verified physical output.

## Commercial quoting cautions

Menards, Lowe's, Home Depot and Amazon pricing varies by location, pack size, availability and date. Treat prior kit dollar totals as estimates until SKU, quantity, freight, taxes and delivery zone are checked. Standard 120V light strings require listed outdoor-rated products, GFCI protection and safe loading; never splice mains light strings to improvise channels. 12V pixel power injection must be fused and weatherproofed.
