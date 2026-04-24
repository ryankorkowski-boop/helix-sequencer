## hardKor Rulebook (AC-First)

Date: 2026-04-23

Goal:
- Build a deterministic placement machine for AC-heavy shows (GP 256-channel style).
- Keep effect family AC-safe: primarily `On` and `Ramp` usage patterns, with timing-driven pulses/chases to emulate shimmer/twinkle behavior.

### Source Notes Used

Official xLights manual and project sources:
- AC Lights Toolbar + Show AC Ramps behavior:
  - https://manual.xlights.org/xlights/chapters/chapter-five-menus/view
  - https://github.com/xLightsSequencer/xLights/blob/48d5e205b14a35e4fb00bfde1135cdfa4aff1b50/src-ui-wx/wxsmith/xLightsframe.wxs
- Layer capacity and blending guidance (up to 200 layers/model, blend/morph/transition controls):
  - https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/layers
  - https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/layers/layer-blending
- Timing-track workflow and practical editing behavior:
  - https://manual.xlights.org/xlights/chapters/chapter-four-sequencer/timing-tracks
- Timing-event VU behavior and sweep/bar styles:
  - https://manual.xlights.org/xlights/effects/off/vu-meter
  - https://github.com/xLightsSequencer/xLights/blob/48d5e205b14a35e4fb00bfde1135cdfa4aff1b50/resources/effectmetadata/VUMeter.json
- Tip-of-the-day references:
  - Color-order dependency in effects: https://xlights.org/tip-of-the-day-059/
  - Folder/show organization for resilient sequencing workflow: https://xlights.org/tip-of-the-day-060/
  - Stable start-channel strategy in evolving layouts: https://xlights.org/tip-of-the-day-061/

Public community guidance (legal/public forum references):
- Layering order and "allow blending between models" guidance:
  - https://auschristmaslighting.com/threads/layering-effects.14957/
- Arch chase timing approaches (one-arch-per-beat patterns):
  - https://auschristmaslighting.com/threads/timing-leaping-arches-to-a-timing-track.15409/

Visualizer mapping references used for routing inspiration:
- LedFx virtual segment mapping (`span` vs `copy`, segment directionality):
  - https://docs.ledfx.app/en/latest/howto/virtuals.html
  - https://docs.ledfx.app/en/v2.1.2/developer/architecture.html
- projectM beat-synced preset architecture context:
  - https://projectm-visualizer.org/docs

### hardKor Placement Rules (Current)

1. AC-safe effect family:
- hardKor only schedules `On` and `Ramp`.
- Shimmer/twinkle character is approximated with dense short `On` pulses on white props.

2. Color-role backbone:
- Red tree channels track bass/kick backbone.
- Green tree channels route mids/vocals in spatial jumps.
- White channels react to highs/hat-style activity.

3. Sequential group behavior:
- Arches run beat chases and flip direction each bar.
- Line trees and candy canes run timing-event style "VU count" expansions.

4. Phrase/mood behavior:
- Build sections (`PRECHORUS`/`BRIDGE`) trigger whirl build-up patterns.
- Pre-drop windows get compressed twinkle pulses.
- Chorus starts trigger full-yard burst emphasis.

5. Layering policy:
- hardKor enables deeper layer budgets than baseline to exploit xLights layering headroom.
- Routing is deterministic and grouped by channel role to avoid flat "same effect everywhere" behavior.
