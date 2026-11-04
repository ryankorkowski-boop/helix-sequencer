# Layout bench findings

Observed by running `main.py --profile master` on the clean-room fixtures. Sequencing code was not changed. Numbers are from the canonical `*,v27.3.xsq` files, not the sparse `.orchestrated.xsq` sidecars.

Runs: 112. Failures: 0. Logs that record `Snowman band planning skipped`: 112.

## Per layout

### ac16_lor

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (6050), Shimmer (5229), On (1761), Bars (1443), Spirals (647), Lines (590).
No prop was left without an effect on the songs in this report.

### ac32_house

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (6433), Shimmer (5767), On (1980), Bars (1722), Spirals (798), Strobe (632).
No prop was left without an effect on the songs in this report.

### ac64_yard

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (6952), Shimmer (6517), On (2187), Bars (1923), Strobe (720), Spirals (704).
No prop was left without an effect on the songs in this report.

### band_stage

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (9114), On (1641), Bars (1456), Twinkle (957), Shimmer (640), Lines (537).
No prop was left without an effect on the songs in this report.

### pixel_classic

Songs: 7. Mean fraction of props with at least one effect: 99.7%.
Most common effect names: Bars (16948), Wave (7810), On (1254), Twinkle (1248), Tree (1183), Snowflakes (846).
Props dark on one or more songs: Snowflake 5 (1/7 songs).

### pixel_corner

Songs: 7. Mean fraction of props with at least one effect: 99.4%.
Most common effect names: Wave (6787), Bars (2423), Tree (2228), Color Wash (990), On (769), Spirals (687).
Props dark on one or more songs: Star 4 (1/7 songs).

### pixel_driveway

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (7199), Bars (2648), Tree (2399), Color Wash (1262), Spirals (921), On (632).
No prop was left without an effect on the songs in this report.

### pixel_starter

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (5265), Bars (2432), Tree (862), On (727), Twinkle (587), Color Wash (501).
No prop was left without an effect on the songs in this report.

### pixel_windows

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (6390), Twinkle (2044), Snowflakes (1194), On (1157), Bars (1092), Shimmer (516).
No prop was left without an effect on the songs in this report.

### wow_helix

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (7164), On (1009), Bars (901), Twinkle (669), Shimmer (571), Lines (421).
No prop was left without an effect on the songs in this report.

### wow_mirror

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (13450), Bars (1685), On (1674), Shimmer (733), Lines (679), Twinkle (283).
No prop was left without an effect on the songs in this report.

### wow_moire

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (2143), Bars (939), On (520), Lines (327), Ripple (258), Plasma (247).
No prop was left without an effect on the songs in this report.

### wow_showcase

Songs: 7. Mean fraction of props with at least one effect: 99.1%.
Most common effect names: Wave (5486), Bars (1091), Tree (688), On (619), Twinkle (514), Color Wash (486).
Props dark on one or more songs: Ring 1 (1/7 songs).

### wow_spinners

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Twinkle (6236), Spirals (3853), Pinwheel (2148), Color Wash (1695), Strobe (454), Bars (184).
No prop was left without an effect on the songs in this report.

### wow_spirals

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Wave (2264), Tree (1423), Color Wash (1250), Spirals (1048), Butterfly (873), Bars (756).
No prop was left without an effect on the songs in this report.

### wow_tunnel

Songs: 7. Mean fraction of props with at least one effect: 100.0%.
Most common effect names: Spirograph (1847), Plasma (1749), Color Wash (1117), Bars (872), Circles (724), Pinwheel (582).
No prop was left without an effect on the songs in this report.

## Engine notes

- Snowman-band planning raises `KeyError: 'composite_submodels'` inside `core/snowman_band.py` while reading mapped drum events, then the master run continues. Every one of the 112 logs records that skip. Singing-face mouths and eyes, and the nine drum-hit props, still receive the same general effects as the rest of the layout (`Wave`, `On`, `Bars`, `Twinkle`, and sometimes `Pictures`). The template's `Faces` phoneme effect is not what those mouths get.
- The master profile is not AC-only. Single-channel LOR props still receive pixel-family effect names such as Butterfly, Spirals, Plasma, and Lines. That is expected with the default master flags. `--ac-lights-only` was not passed.
- Preview panels light a whole model while any of its effects are active. They do not simulate xLights per-pixel shaders, so matrices, spirals, and the moire stack read as shapes turning on and off together. Overlapping moire matrices can still be told apart when their effect timing differs.
- `Tree 360` virtual pixels in the parser are vertical strands. Spiral layouts also store a spiral `PointData` path, and the preview draws that path, so the panel shows the spiral outline rather than the parser's strand map.
- Poly-line arch sections with a shallow bow are parsed as lines. The `Arch N Sec M` names are still present, and the master run places effects on them.
- Custom RGB snowflakes are also eligible for the matrix family because a custom RGB model with 24 or more pixels is classified as a matrix before the snowflake name is considered. The snowflake name pool still exists.
