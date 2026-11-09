# Friendly guide: Helix Sequencer and the Snowman Band

**Audio in. Lights out. Let the snowman band play!**

Helix helps you turn a song into a lighting sequence you can inspect and refine in xLights or, for supported legacy setups, Light-O-Rama. This guide is for first-time hobbyists. **Snowman Band native exports and physical wiring have not completed final verification.**

## Start with Helix on Windows

1. Download a **verified** portable release from the official GitHub repository. Extract the **whole** ZIP to a writable folder. Do not run Helix.exe from inside the ZIP.
2. Keep `Helix.exe`, `HelixCLI.exe`, and `_internal` together. Double-click `Helix.exe`.
3. Select a song (MP3 or WAV is a safe starting choice).
4. Choose **xLights** or **Light-O-Rama** and provide your matching layout/template or correctly addressed legacy LMS file. Do not assume an example layout matches your hardware.
5. Choose an output folder and run the sequence build. Helix processes the song; the preview duration is a separate setting.
6. Inspect the run log, exported files, model assignments, and musical timing before trying real lights.

**Source-code alternative:** With Python 3.11+ and the documented dependencies installed, run `python gui_launcher.py`. See the root README and INSTALL_AND_TROUBLESHOOT.md.

**Android:** Use only a verified APK, keep a backup of previous shows, and follow INSTALL_AND_TROUBLESHOOT.md for your device. App installation and physical-device behavior depend on the actual build.

## Meet the seven Snowman Band members

- **Drummer:** Separate percussion targets and left/right stick-contact poses, including snare and cymbal components.
- **Bassist:** String-oriented lighting and instrument/arm submodels.
- **Guitarist:** String-oriented lighting and strumming/fingering pose submodels.
- **Pianist:** Keyboard note submodels, with an AC variant that groups notes by pitch class.
- **Xylophone player:** Mallet/instrument note submodels, with a similar AC pitch-class option.
- **Lead singer:** Independently addressable mouth-shape (viseme) submodels.
- **Harmony singer:** Separate singer and mouth-shape submodels.

The aim is to illustrate what musicians are playing or singing. Actual timing, detection quality, model appearance, and xLights playback must be checked against a rendered native sequence; an animation or simulated MP4 alone is not proof.

## Pixels versus traditional AC strands

**Pixel mode:** Independently addressable model nodes permit more detailed poses and musical responses. Match the exported model and channel layout to your real pixel controller and wiring.

**AC16 mode:** Each Snowman Band AC model is designed to have **at most 16 logical circuits**. This is **per model**, not a promise that all seven musicians can fit on one 16-channel controller. Several physical bulb positions may share one circuit. Never interpret exported geometry positions as the number of bulbs you must buy.

For a **Light-O-Rama CTB16PC**, assign actual Unit IDs and circuit numbers from your own controller configuration. Verify compatible lamp types, loads, electrical ratings, and dimming behavior using the manufacturer's instructions. Do not connect an unverified mapping to live power. Legacy LMS support is not the same as direct support for modern `.loredit` files.

## Generate a planning inventory (source checkout)

For developers and builders using the source repository, a standalone command generates JSON and CSV planning inventories without requiring a music file:

```bash
python -m tools.export_snowman_band_inventory --output-dir build/snowman_wiring
```

Look in `build/snowman_wiring/pixel/` and `build/snowman_wiring/ac16/` for `snowman_submodel_inventory.json` and `snowman_submodel_inventory.csv`. The generator refuses to overwrite existing inventories; use a fresh output directory for a new run. It is a **planning** report, not a physical wiring diagram: bulb counts, controller Unit IDs, and actual circuit wiring remain unverified until you enter and test them.

## A friendly first test

1. Try a short song you know well and start with a simple xLights layout.
2. Check each musician's submodels and whether the performance matches the music.
3. Check singer mouths, drummer strikes, and instrument-note effects independently.
4. Verify model positions in xLights 2D/3D preview where supported by your installed version.
5. Test real hardware only after confirming channel assignments and electrical safety.
6. Save your logs, xLights version, model mapping, and a short screen recording if something looks wrong.

## Troubleshooting

**Helix will not launch:** Re-extract the entire portable package and keep `_internal` beside the executables.

**No XSQ or LMS:** Check the run log, selected output directory, chosen format, and template.

**Wrong props respond:** Compare your real layout model names and channels against the selected template and role mapping.

**Band looks different in xLights:** Confirm you are looking at the native imported models and rendered playback, not just a Helix simulation.

**No snowman inventory files:** The generator is a source-checkout developer tool and is not guaranteed to be included in a portable beta package. Check its error output; the native inventory workflow may still be awaiting CI.

## More help

- [Helix repository](https://github.com/ryankorkowski-boop/helix-sequencer)
- [Helix community](https://Facebook.com/helixsequencer)
- See `README.md`, `INSTALL_AND_TROUBLESHOOT.md`, and `docs/SUPPORT_MATRIX.md` for version-specific details.

**Beta reminder:** Always preview and validate exported sequences, controller mappings, and electrical loads before operating a show. Do not treat the Snowman Band as a verified turnkey hardware kit.
