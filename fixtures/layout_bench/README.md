# Layout test bench

Clean-room xLights layouts for judging what the Helix master profile does with the **same audio** on **different props**. The fixtures are synthetic: common model types and hobbyist names, no copied show, sequence, or song.

Audio and rendered videos stay out of git. `*.mp3` and `test_runs/` are already ignored. Put finished comparison videos in an artifact directory, not the repository.

## Layouts

Sixteen layouts, simple to over the top. Each folder has `xlights_rgbeffects.xml` and a paired `template.xsq`. The template only seeds On/Ramp/Faces settings. `main.py` syncs model rows from the layout and drops the seed row.

| ID | Tier | What it is |
| --- | --- | --- |
| `ac16_lor` | AC | 16-channel LOR-style yard. One dimmable channel per prop. |
| `ac32_house` | AC | 32-channel house. Segmented arches, canes, second window, icicles. |
| `ac64_yard` | AC | 64-channel yard. Color-stacked roof and eaves, more arch sections, path lights. |
| `pixel_starter` | pixel | Arches, canes, mini trees, roofline, window, matrix, star. |
| `pixel_classic` | pixel | Mega tree, matrix, north/south canes, mini trees, windows, stars, snowflakes. |
| `pixel_driveway` | pixel | Four driveway arches, garage matrix, walk-line mini trees, mega tree. |
| `pixel_windows` | pixel | Four window frames, picture-window matrix, outline, stars, snowflakes. |
| `pixel_corner` | pixel | L-shaped roofline, corner mega tree, side matrix. |
| `band_stage` | band | Snowman singer/bass/guitar/drummer, three singing faces with NodeRange phoneme mouths and eyes, backdrop matrix, nine drum-hit props. |
| `wow_spirals` | wow | Spiral trees. |
| `wow_helix` | wow | Three double-helix towers. |
| `wow_tunnel` | wow | Concentric rings, center spinner, far matrix. |
| `wow_spinners` | wow | Radial spinners, pinwheel, star ring. |
| `wow_moire` | wow | Three overlapping matrices with different grid pitches. |
| `wow_mirror` | wow | Mirrored left/right chase arrays. |
| `wow_showcase` | wow | Spiral, helix, rings, spinners, overlapping matrices, arches, mega tree. |

Exact prop, channel, and pixel counts are in `manifest.json`. AC layouts are 16, 32, and 64 channels. Pixel and wow layouts use `RGB Nodes`, so channel count is pixels times 3.

Groups use ordinary names: `Whole House`, `All Arches`, `All Canes`, `All Mini Trees`, `All Stars`, `All Snowflakes`, `Snowman Band`, `Mirror Left`, `Mirror Right`, `Tunnel`.

## Commands

From the repository root:

```bash
python3 tools/layout_bench/generate_layouts.py
python3 tools/layout_bench/run_bench.py --audio-dir /path/to/songs --workers 3
python3 tools/layout_bench/render_comparisons.py --audio-dir /path/to/songs --output-dir /opt/cursor/artifacts/layout_bench_rendered
```

`run_bench.py` calls the main CLI unchanged:

`python main.py --profile master -- --template ... --audio ... --layout-file ... --single --variants 1 --no-prompt --no-save-settings --no-workspace-history --no-learning-memory`

`--variants 1` keeps a single canonical sequence. Workspace history and learning memory stay off so the bench does not write scoring memory. Polish, pixel-reactive placement, and matrix intelligence stay at the master-profile defaults. The canonical sequence is `test_runs/layout_bench/<layout>/<song>,v27.3.xsq`. The `.orchestrated.xsq` sidecar is not the preview source.

`render_comparisons.py` asks xLights (`--headless`, under Xvfb) to render each canonical XSQ to an FSEQ, then draws every node from that channel data at the layout coordinates. The sequence frame time is kept (these fixtures are 50 ms, 20 fps). Set `XLIGHTS_BIN` to the xLights AppImage or extracted `AppRun` if it is not at `/tmp/xlights/squashfs-root/AppRun`. `variants.json` lists ids and descriptions without artifact paths.

Expected song filenames, used only as local test inputs:

- `north_pole_overdrive.mp3`
- `wub_wub_wonderland.mp3`
- `candy_cane_chaos.mp3`
- `clip_b.mp3`, `clip_c.mp3`, `clip_f.mp3`, `clip_g.mp3` (untitled clips from the same test set)

## What the video shows

Panels are xLights FSEQ renders. A pixel node's color is the rendered RGB for that frame. A one-channel AC prop is drawn in its strand color at the rendered level. xLights 2026.19 model types are used (`Candy Canes`, not `Candy Cane`). Default model scale is 1 so poly-line render buffers stay the size of the prop.

## Tests

`python3 -m pytest tests/test_layout_bench.py -q` checks channel counts, singing-face phoneme markup, and that the templates stay clean-room.
