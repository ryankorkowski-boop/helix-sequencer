# Beta 1.4 recovery handoff

The recovered foundation is the packaged 1.3 master engine at `1b1ff83c9c1b992a3ad5e202fc29ee0b292919bf`. Release artifacts and the owner's Drive checksums agree on the package names. PR 218 reports native results from xLights 2026.19 for 22 paired layouts/songs. The exact revision of the owner's favorite video remains uncertain. Its V01 and V06 source paths were local to that historical runner. The separate drummer reference is commit `b27e8d77a63027ed32bcf6851dcff3925472c155`, successful run 35486153096. That run verifies an older drummer lineage only.

[Packaged baseline](https://github.com/ryankorkowski-boop/helix-sequencer/releases/tag/helix-beta-v1.3) · [Native color measurements](https://github.com/ryankorkowski-boop/helix-sequencer/pull/218) · [Package checksums](https://drive.google.com/file/d/1Cy0CkahlOzdCj60i-2-EIFlqI8iCmHaq/view) · [Drummer reference run](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/35486153096).

## Reproduce the controlled comparison

Use fresh settings for each checkout. Extract eight seconds from the repository copy of Helix Audiolights.mp3 with FFmpeg. Use each checkout's template.xsq and original xlights_rgbeffects.xml. The filename clip.wav matters because it contributes to the deterministic seed.

```sh
ffmpeg -v error -i 'Helix Audiolights.mp3' -t 8 -ac 1 -ar 22050 clip.wav
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python main.py --profile master -- --template template.xsq --audio clip.wav --layout-file xlights_rgbeffects.xml --output-dir recovered --settings fresh.settings.json --variants 1 --no-prompt --no-workspace-history --no-learning-memory
```

Both runs placed the same 1,050 effects on 181 target rows across 12 effect types. Comparing the full multiset of target, effect, start and end found zero differences. The 1.3 orchestrator wrote 21 inline palette values. Recovery wrote zero. The master header changed from 132.039 seconds to the decoded 8.000, and inherited timing marks past the audio end were bounded. Unit coverage includes native palette and setting tables, actual table indexes with duplicates, pitch normalization, and source duration. Historical 91.1% → 0.040% bright near-white RGB results are prior evidence, separate from this run.

## Selective integration

Keep the 1.3 master profile, model routing, section palettes, and approved drummer reference. Bring forward source-duration handling, editable native effect references, bounded per-frame pitch peaks and checks from integration `feaa06b467adcee18d1de1b3bf250ca09309411b`. Repair the default orchestrator palette writer and the birdsong writer. Save unscaled profile inputs to prevent repeated sequencing from multiplying the bass, speed and darkness settings. Previously saved settings are accepted as the user's starting inputs. Previously accumulated scaling cannot be inferred from those files.

Isolate the 1.4 vivid-style and musical-bed postprocessing. Source inspection shows they change the final sequence after the master runs. Their contribution to rejected videos has not been established by a paired render. The rejected bundle contains a 36-second band diagnostic and a 34.9-second single pilot. Both sampled frames show a band stage. The archived reports flag independent vocals and pilot reference timing.

## Outstanding verification

Use the native regression on the recovery branch to verify lit RGB, deliberate white, rests, and AC intensity from real FSEQ bytes. Local xLights 2026.19 GTK initialization could not obtain a display. The local X server could not open a listener. Verify branch protection in GitHub. Continue with the first owner-reference-matched native band excerpt, using documented drum and independent vocal sources before composing the comparisons. The historical 12-layout gate, 9-panel production path, and 16-panel full-song output are open. Android and Windows runtime parity and the release bundle are open.

## Native color and drum recovery

Run 44974483062 passed all three native color cases on commit 675b1996. Its archive contains three matched XSQ/FSEQ pairs and show folders. Next verify the real 36-second Helix Audiolights excerpt on the original layout. The private Helix Motion file requires separate download approval.

The recovery now includes the nine-component V3 mapper and source-art masks, detector, XSQ injector and preview support. The original drummer source image matches both branches. The injector had discarded detected ride events when reconstructing streams, and the 1.3 band plan looked up a nonexistent composite key. Both paths are repaired. The hash-bound Dry Drum Test transcription produced 289 events, 585 visual placements, 53 snares and 17 crashes. All three toms fired. This particular transcription contains no ride. Thirty-six targeted drum tests passed. A six-performer native visual pass is outstanding.
