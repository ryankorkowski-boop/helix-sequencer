# Seven self-contained xLights shows

The portable delivery groups songs by layout rather than making a separate show
directory for every song. It preserves the original Aurora, all six flavors,
source audio, saved favorites and drummer work. The 22 concept images remain
outside this implementation.

Each of the six flavor folders contains five complete Media XSQs, copied
soundtracks under `media/`, the original 24-second lighting study, portable
assets/models and one matching layout/network pair. Aurora contains its actual
24-second lighting study; it has no fabricated or transplanted full-song XSQ.

The six music layouts retain unchanged physical model nodes and the existing
exporter's RGB-only group restrictions. Permanent originals remain unchanged.
The packaging tool changes only each music sequence's `head/mediaFile`, to a
show-relative `media/<song>.mp3`. Native settings, palettes, cue intervals,
targets and submodel layers must remain identical to the corrected export.

## Prepare and verify

Generate the thirty corrected exports with the existing batch `generate()`
function, or use an available complete corrected batch. Then run:

```sh
python -m tools.prepare_portable_xlights_shows \
  --batch outputs/portable_music_generation --output outputs/Helix_Portable_Shows

DISPLAY=:99 XL_NO_GPU_COMPUTE=1 python -m tools.verify_portable_xlights_native \
  --root outputs/Helix_Portable_Shows \
  --xlights /absolute/path/to/xLights/AppRun --workers 2
```

The native verifier renders every included XSQ, checks full duration, native
animation, RGB model coverage and dark control channels, and records results
in `SHOWS.json` and per-show `native_verification_portable.json`. Repackage after
native verification to include the FSEQs and final reports. Baseline native
proofs are retained under `baseline_native_verification.json` to distinguish
them from current portable verification.

`--audit-existing` checks a just-rendered batch again without rerendering. It
refuses native files older than their XSQ/layout inputs; it does not replace
source-bound native rendering. xLights can omit unused trailing control
channels from FSEQ; those channels are implicit zero. Missing RGB channels
still fail verification.

The archive is `outputs/Helix_Portable_Shows.zip`. Each `Helix_*` directory is a
show folder. Selecting another layout changes show folders; opening another
song in the same layout does not. Extract the whole archive and keep assets,
models and media together. Neither a neighboring repository checkout nor the
original audio upload location is required for playback.

## Open on the laptop

Install/use xLights 2026.18 or newer. The included launcher requires Python 3.
Run `Open_Fire_and_Ice.cmd` on Windows or `Open_Fire_and_Ice.command` on
macOS/Linux. It finds common installed xLights paths, renders the complete
`Wire_Tree__Helix_Fire_and_Ice.xsq`, then opens that sequence in the GUI with
Fire & Ice as the active show folder. Rendering is separate from opening:
`--headless` and `-r` exit after rendering, so neither belongs in the final
desktop invocation. No output-enable or settings-wipe flags are used.

If executable discovery needs an explicit path:

```sh
python launch_xlights.py --xlights /absolute/path/to/installed/xLights
```

On macOS, pass the executable inside `xLights.app/Contents/MacOS/`. Native
rendering uses `-s <show> -m <show>`, so `media/` references resolve from the show
root. Native logs are written to `laptop_render.log` in the selected show.
`--open-only` uses an already rendered sequence; `--render-only` omits the GUI.

This task's executor is cloud Linux, not the user's laptop. Native cloud
rendering and a launcher do not establish laptop GUI launch, audio-device
playback or local installed-version compatibility. The laptop launch remains
an explicit handoff item. Artistic/musical/drummer approval is also separate.
Read `MASTER_TODO.md` for authoritative status and acceptance limits.
