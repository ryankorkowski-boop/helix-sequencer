# LOR Compatible mode (xLights XSQ only)

This is the legacy Helix **AC Only** sequencing ability made accessible in the
current root GUI. It does **not** export LMS, LOREDIT, controller-address
mapping, or operate Light-O-Rama hardware. xLights remains the user's conversion
tool.

## For Greg's original 256-model display

1. In `gui_launcher.py`, select the original GP layout and matching XSQ
   template; verify the layout matches the actual controller configuration.
2. Check **LOR Compatible (AC effects; export through xLights)**.
3. Select music and run Helix as normal.
4. Open the output XSQ in xLights, render and inspect it, then use xLights
   to export to the compatible LOR sequence format.
5. Review timing/intensity, physical wiring and channel addressing in the
   LOR application before running the real show.

In the checked mode, Helix passes the established `--ac-lights-only` engine
flag and disables RGB pixel/birdsong/matrix orchestration. It preserves original
musical timing and channel group sequencing, then runs a strict xLights XSQ
compatibility postpass:

- **On**: unchanged, retaining valid dimmer/intensity settings.
- **Ramp** (non-native xLights name): represented as a native **On fade**
  with constant settings from 0 to 100% over the same time interval.
- **Shimmer**, **Twinkle**, **Off**: retained.
- **Strobe**: represented as **Shimmer** for single-channel AC blinking.
- Pixel-only/unknown effects: changed to native **On** intensity on valid
  single-color channels, with each conversion counted in the report.
- RGB-pixel-only model effects: dropped. Mixed group effects expand only to
  their eligible AC members. Unmapped model effects are rejected/omitted.

The layout's physical model type is authoritative. Generic
`Single Color Intensity` models are retained alongside `Single Color Red`,
`Single Color Green` and `Single Color White` models. In the original Greg
layout, this means **255 single-color models** remain eligible, and the one
RGB model is excluded.

A **white effect palette** in this mode expresses white *intensity control*
rather than a white RGB pixel. A red or green physical strand remains red or
green; its hue is determined by the actual bulbs. This is **not** the same as
the erroneous white-only RGB sampler output.

The sanitizer only runs on new/changed XSQs generated in this run, never
on the selected original layout or input template. Each generated XSQ has a
`.lor_compatibility.json` report, including supported effect names,
target model counts, substitutions and final validation. No LMS converter
or duplicate source XSQ is added.

## Important limits

This is an AC-effect compatibility **vocabulary**, not an empirical claim
that every xLights effect converts identically into every version of LOR.
Native xLights and LOR export/import must be checked with a small real
sequence for Greg's controller and software versions.

The current postpass approximates an original `Ramp` using a 0-100%
On fade, and converts unsupported effects to On rather than recreating
their precise RGB patterns. Follow-up precision work should compare
the FSEQ/dimmer output of both approaches on an actual xLights installation.
This feature deliberately does not alter Helix's core audio analysis.

### CLI

Existing flag:

`python main.py --profile master -- --template template.xsq --audio song.wav --layout-file xlights_rgbeffects.xml --output-dir outputs --ac-lights-only --no-prompt`

`--ac-lights-only` now triggers final compatibility validation via the
sequence builder. If nothing can be converted into an AC-valid XSQ,
the run fails rather than claiming success.

## RGB white-only issue remains a separate concern

The unrelated **RGB neon white-only patch**, PR #134, fills missing effect
palettes only when an RGB user explicitly requests `--palette-mode neon`.
The initial 15s preview used hand-chosen saturated cyan/magenta/green
palettes and an approximate renderer, and is not an approved artistic
baseline. The phrase-storyboard experiments in PRs #135 and #136 have
not been confirmed in native xLights or approved via a new RGB preview.

LOR Compatible defaults to off and uses white *intensity* on real
single-color AC circuits. It never triggers RGB neon palette reassignments.

## Protection and verification

- Do not rewrite original `xlights_rgbeffects.xml` or `template.xsq`.
- Do not merge LMS-generation machinery from draft PRs #135/#136.
- `.github/workflows/lor-compatible-strict.yml` runs dedicated
  AC and RGB palette nonregression tests on Python 3.11 and 3.12.
- A successful XML-level validator is not yet native xLights or hardware
  proof; the latter should be tested before any public release.
