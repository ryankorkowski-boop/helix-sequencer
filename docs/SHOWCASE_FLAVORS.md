# Six additional Helix showcase layouts

The collection adds six independent shows alongside the preserved original Helix Aurora. Each has a different arrangement, skyline and native-prop placement. All retain the 27 creatable xLights model families verified against the pinned 2026.18 factory.

| Show | Composition | Models | Spirals | Double helices | RGB pixels |
| --- | --- | ---: | ---: | ---: | ---: |
| Neon Circuit | Asymmetric DNA skyscrapers, circuit avenues, antenna farms | 104 | 36 | 13 | 32,834 |
| Enchanted Grove | Woodland crescents, ancient trunks, lantern trail, root bridge | 100 | 36 | 12 | 30,227 |
| Celestial Orrery | Concentric tree orbits, three suspended DNA halos, observatories | 105 | 40 | 13 | 34,408 |
| Fire & Ice | Warm and cool kingdoms, opposing groves, elemental bridge | 109 | 40 | 16 | 36,350 |
| Crystal Lagoon | Five terraced islands, reef bridges, tidal halo, lighthouse | 104 | 40 | 12 | 31,848 |
| Midnight Masquerade | Graduated theatrical fan, DNA balcony, gold crowns, royal throne | 106 | 36 | 12 | 32,728 |

The trees use native Tree 360 spiral wiring. DNA forms have two addressable strands and complete illuminated rungs, including horizontal bridges and circular halos. Family, zone, strand and spiral groups are available for sequencing. Native control/DMX/servo fixtures are preserved separately from the RGB demonstration.

## Review and import

Generated deliverables live in `outputs/showcase_flavors/`:

- `index.html`: full comparison gallery linking six offline 3D viewers, videos and individual ZIPs.
- `Helix_Six_Flavors_Comparison.png`: six-layout contact sheet.
- `Helix_Six_Flavors_Tour.mp4`: 36-second tour, six seconds from each native-lighting study.
- `Helix_Six_Flavors_Layouts.zip`: compact collection with its own offline gallery, import shows, assets, viewers, images, XSQs, native FSEQs and verification. Videos stay in the individual packages.
- `Helix_<Flavor>_Ultimate_Showcase.zip`: each complete show, including its 24-second lighting MP4 and checksums.

Extract the compact collection and open its `index.html`. Choose one layout folder as a **new xLights 2026.18+ show directory**, retaining `assets/` and `models/` alongside the XML. Restore Default ViewPoint or load its named overview. Open that show's XSQ for the lighting study. Permanent import layouts, portable assets and review images/viewers are checked in under `showcase/flavors/`.

## Reproduce

Static design export:

```sh
python -m tools.build_showcase_flavors --no-video
```

Native channel rendering and full collection:

```sh
xvfb-run -a python -m tools.build_showcase_flavors \
  --xlights /absolute/path/to/xlights/squashfs-root/AppRun
```

Use the pinned official xLights 2026.18 AppImage, SHA256 `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`. `--flavor neon_circuit` (or another key from `models/showcase_flavors.py`) builds one show. `--gallery-only` refreshes the comparison and collection package from completed builds.

CI uses the existing **Helix Ultimate Showcase Preview** workflow with dispatch input `collection=true`. It runs the layout suite, renders all six with the pinned engine, audits every RGB node, produces the videos and extracts 1/5/12/20-second review frames. Eight separate artifacts provide the compact collection, tour/comparison and six full individual packages. Default dispatch still builds Aurora.

## Evidence and limits

Local native rendering verifies 480 frames at 50 ms for each show and the intended palette on all 198,395 RGB pixels across the collection at 20 seconds. The layout suite covers all native families, disjoint absolute channels, sparse custom-grid reconstruction, transformed native vertices/endpoints, native DNA submodel palettes, control isolation, genuinely different geometry and compact-package links/hashes/cache exclusion. The original Aurora native export remains byte-identical to its delivered show.

These MP4s use actual native channel values in the design geometry compositor. Custom node coordinates exactly match exported grids; stock model review paths are illustrative. Native headless import/render is checked for every flavor. No new six-layout GUI attribute audit or native screen recording is claimed. The studies have no song audio. Physical engineering, site surveying, controllers, wiring and power are separate work. Existing layouts and the drummer are preserved; drummer musical approval remains open in `MASTER_TODO.md`.

Final validation: 64 layout checks pass locally and in native CI. Six 1600×90020fps480-frame24s videos, their 1/5/12/20-second decoded frames, the 36-second tour and all six browser viewers were checked. Downloaded compact-package 210 hashes and gallery links verify; all six complete 480-frame native channel arrays and XML/XSQ/manifest/inventory match local builds exactly.

Implementation commit: `536dcca52e5f686643f396bd9e9758efacfc4cd0`, branch `feature/showcase-six-flavors`. [Native CI run 37794173215](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215) succeeded.

- [All six native layouts and offline comparison gallery](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557618824)
- [Collection video tour and comparison image](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557958280)
- [Neon Circuit full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557953390)
- [Enchanted Grove full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557673718)
- [Celestial Orrery full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557499059)
- [Fire & Ice full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557998029)
- [Crystal Lagoon full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557803680)
- [Midnight Masquerade full show and MP4](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557593938)

The remote compact ZIP SHA256 is `f7fed219f594ef86ba80a058a0d1c4d6e1fa4baf964982ca7b5b3a39c1fadd36`. Artifacts have 30-day retention; permanent import shows and generated builders remain checked in. `docs/evidence/showcase_flavors_verification.json` records the downloaded checks. Artistic acceptance belongs to the user and remains pending. The collection's `HANDOFF.json` and master ledger preserve continuity.
