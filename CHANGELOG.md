# Changelog

## Beta 1.3 (1.3.0-beta)

Shipped from `feature/restructure-core` after merging pull request #218.

- Color fix: master-profile effects no longer point at template palette 0 when that row enables only white. Helix appends a section palette to the sequence `ColorPalettes` table and points the effect at that index. White is used only as an accent on Strobe, Twinkle, Shimmer, Snowflake, and Sparkle.
- Desktop window title and About, `python main.py --version`, the Android `versionName` `1.3.0-beta` (versionCode 9), and the Windows executable version resource all report Beta 1.3.
- Windows and Android packages are built the same way as the November Drive handoff: a one-folder portable zip (`Helix.exe`, `HelixCLI.exe`, and `_internal`) and a debug APK produced by the Chaquopy `assembleDebug` project.

The Drive builds `Helix-Windows-Beta-PR214-64db83d-One-Part.zip` and `Helix-Android-Beta-712b7ba.zip` were produced from later packaging-line commits that already contained this default branch. No other default-branch change since those builds is part of this release. The separate palette-variety work stacked on #218 is not included.
