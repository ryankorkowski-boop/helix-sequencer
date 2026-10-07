# Drummer visual polish after the reviewed transcription preview

The user described the 474dec70 / Actions #219 preview as pretty decent, with possibly excessive hi-hat activity. The requested next change is visual: intact strike arms, no persistent raised sticks, alternating snare hands, and the full snare outline visible through the kick.

## Preserved musical performance

The source-hash-bound ADTOF transcription is unchanged. The full event audit and analysis compare exactly against the reviewed preview: 1,022 placements, all timestamps, families, confidence, velocity, tom classes and physical targets preserved. No audio threshold, scheduler gate or onset refinement changed. Hi-hat peaks at seven placements in one second; this statistic cannot establish false hits. Its activity remains unchanged pending timestamp-specific listening evidence.

## Changed visuals

- Remove the original raised arm/shaft artwork from the dim idle layer. Preserve the head, scarf, body, kit and original source image. A deterministic generated `drummer_idle.png` is also the portable native xmodel background.
- Retain complete neutral source arm shading as well as bright edges. Preserve transformed shafts/arms where they cross instrument surfaces in both preview layers and the native node projection. Instrument surface submodels remain disjoint; actuator nodes intentionally may overlap them. The old exclusion contract is superseded because it caused disappearing arm sections.
- Alternate snare LEFT, RIGHT, LEFT across the complete scheduled performance. The eight musical targets and SNARE lane stay unchanged. Native effects select only the appropriate arm's neutral/wood partitions. `sourceHand` metadata drives the same hand in the MP4; clipped review windows do not restart alternation.
- Repose the right source arm around its shoulder toward the snare and use the same source-art shaft, rather than a generic replacement stick.
- Explicitly author the hidden snare shell completion in the normalized pose spec. The magenta top/bottom rims and shell sides illuminate on each snare hit, including the part hidden by the photographed bass drum. Kick extraction contains only its red rim and blue snowflake. Simultaneous snare/kick lighting preserves both components.
- Keep the hi-hat surface primary, its pedal at 32%, no hi-hat/kick stick, exactly three evidence-based toms, and the dim body keepalive.

The shell completion is a visual approximation of occluded artwork, not a new detected musical event. The native uniform arm color uses the source's visible wire pixels, so adding dim arm shading does not darken all physical arm nodes.

## Reproduce

```sh
PYTHONPATH=. python tools/build_drummer_v3_assets.py --overwrite
PYTHONPATH=. python tools/integrate_drummer_v3_into_xsq.py template.xsq 'Helix Audiolights.mp3' --drum-events evidence/drummer/helix_adtof_stem.json --output test_runs/drummer_visual_polish/Helix_Drummer_VISUAL_POLISH.xsq --report test_runs/drummer_visual_polish/report.json
PYTHONPATH=. python tools/export_drummer_only_xsq.py test_runs/drummer_visual_polish/Helix_Drummer_VISUAL_POLISH.xsq --output test_runs/drummer_visual_polish/Helix_Drummer_VISUAL_POLISH_ONLY.xsq --audio 'Helix Audiolights.mp3'
PYTHONPATH=. python tools/render_drummer_v3_preview.py test_runs/drummer_visual_polish/Helix_Drummer_VISUAL_POLISH_ONLY.xsq --audio 'Helix Audiolights.mp3' --output test_runs/drummer_visual_polish/Helix_Drummer_VISUAL_POLISH_FULL.mp4 --fps 60
```

## Validation and limitations

116 relevant tests passed (two preexisting warnings);61 focused checks passed after final visual changes. The source-song audio correlation for the decoded25s video is .9962146413 and full237.44s video .9919693452. The decoded snare/kick overlap at50.1167s shows the entire magenta shell through the lit kick. New regression coverage checks snare alternation without musical changes, removal of idle shafts/arms, preserved face, both snare shell/hand variants, simultaneous kick visibility, every projected native actuator node, matching XSQ/preview hand metadata, and late-start preview hand continuity. Updated previous tests preserve isolated surfaces while allowing full front strikes. Pose review includes both snare hands.

Evidence is in `test_runs/drummer_visual_polish/`: full and 25-second original-song MP4s, isolated XSQ, report, exact musical comparison, decoded-hit frames, soundtrack correlation, pose sheet and test logs. The GitHub workflow regenerates the same assets, runs the relevant suite including the new regressions, and renders the actual song. Native xLights import/playback is still unverified. Human review of the updated MP4 remains the final acceptance gate.
