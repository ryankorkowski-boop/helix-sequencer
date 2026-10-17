# HelixHelps first-batch source-audio activity selection — 2026-10-17

Source folder: https://drive.google.com/drive/folders/1W-LJhoClmICX1dCaEAYBO38UTavXycEo

Seven real MP3 files were fetched from the connected HelixHelps Drive and decoded locally. A 35-second rolling window was ranked using normalized STFT RMS energy (35%), positive spectral flux (35%), low-frequency energy below 180 Hz (15%), and high-frequency energy above 2500 Hz (15%). This is **not** instrument classification, lyric transcription, source separation, or proof of native Helix sequencing. Excerpts were exported as separate MP3s without changing the originals.

| Song | Start (s) | Duration (s) | Activity score | Original SHA256 |
|---|---:|---:|---:|---|
| Snowbound Polyrhythm.mp3 | 88.260 | 35 | 0.6786 | 374dda14a7ecc99c411ff53f503edc4a06ac214fe084d7dee489613e4175f148 |
| Holly Steel Run.mp3 | 71.967 | 35 | 0.6063 | 730d7db5128fb81675a61f159dea6fa05a7f677c469536c0f789c03992fdb7af |
| North Pole Overdrive.mp3 | 175.820 | 35 | 0.6052 | d4a22b3b8982ea0e71aebc2ee0c7235cae2e77965b73764274cfbd89f64e54e5 |
| Tinsel Sawtooth.mp3 | 30.886 | 35 | 0.6036 | b23c792a3c42dc27a756d6e302cb4d4b19b9cfe1742a4ec48f813dbbc0604715 |
| Candy Cane Chaos.mp3 | 154.730 | 35 | 0.5943 | ea3d227d5d263483ad71233d70df67951940775da9acd31c8291bfe57e314239 |
| Three Solo Test.mp3 | 58.374 | 35 | 0.5852 | f3db3612e84179684118c8e2ef8e476e1aa87cb7d252e965a8228098d3969933 |
| Wub Wub Wonderland.mp3 | 171.022 | 35 | 0.5170 | 76641340a2a59c5797b333cd36b1e108f503017d190510fbe8da9931ea3f9abc |

## Next required steps

- [x] Read current PR #150 source and physical-output review notes.
- [x] Enumerate HelixHelps Christmas songs and instrumentals; identify alternate mixes by names and sizes, without treating them as duplicates.
- [x] Retrieve seven Drive originals and calculate source SHA256s and activity-ranked excerpt windows.
- [x] Export seven 35-second real-audio review excerpts and machine-readable selection manifest.
- [ ] Expand selection across more recordings and analyze instrumentation and vocals, not only spectral activity.
- [ ] Run **the actual Helix musical analysis pipeline** for each selected original audio file, generating source-bound cue and sequence files.
- [ ] Use actual native Helix renderer and verify complete 30–42-second band, embedded-layout, lyric and six-layout comparison MP4s. **No new Helix MP4 was rendered in this batch.**
- [ ] Preserve review hold: do not merge, rebuild or publish final EXE/APK before owner approval.

The local environment could not clone GitHub directly (DNS resolution failure), so this receipt was committed through the connected GitHub repository interface. This document is a selection checkpoint, not a release or a completed showcase.
