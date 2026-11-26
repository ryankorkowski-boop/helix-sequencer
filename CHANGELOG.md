# Changelog

## Beta 1.4 (1.4.0-beta)

Shipped from `feature/restructure-core`.

- Depth sweep: prechorus and bridge chases travel front to back on Z. Props in the same depth row share a start, and an even ramp still steps instead of flashing together.
- v24–v27 follow the verse, build, and chorus blueprint. Keyboard routes light one model, not the whole cluster. All-red, all-green, all-white, house, and garage no longer pulse on the same beat.
- With a layout file, spatial awareness defaults to 0.85 and the chase style to wave. Birdsong is on unless `--no-birdsong` is set.
- Desktop title, `python main.py --version`, Android `versionName` `1.4.0-beta` (versionCode 10), and the Windows executable version resource all report Beta 1.4.

## Beta 1.3 (1.3.0-beta)

Shipped from `feature/restructure-core` after merging pull request #218.

- Color fix: master-profile effects no longer point at template palette 0 when that row enables only white. Helix appends a section palette to the sequence `ColorPalettes` table and points the effect at that index. White is used only as an accent on Strobe, Twinkle, Shimmer, Snowflake, and Sparkle.
- Desktop window title and About, `python main.py --version`, the Android `versionName` `1.3.0-beta` (versionCode 9), and the Windows executable version resource all report Beta 1.3.
- Windows and Android packages are built the same way as the November Drive handoff: a one-folder portable zip (`Helix.exe`, `HelixCLI.exe`, and `_internal`) and a debug APK produced by the Chaquopy `assembleDebug` project.

The Drive builds `Helix-Windows-Beta-PR214-64db83d-One-Part.zip` and `Helix-Android-Beta-712b7ba.zip` were produced from later packaging-line commits that already contained this default branch. No other default-branch change since those builds is part of this release. The separate palette-variety work stacked on #218 is not included.
