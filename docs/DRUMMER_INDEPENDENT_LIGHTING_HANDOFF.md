# Independent drummer lighting — reconstruction handoff

Base: \`1f66f5dfa09b3173f5cdfd33d28ab1b4421e11ad\` on \`feature/restructure-core\`.
Implementation branch: \`fix/drummer-independent-illumination\`.

Read \`AGENTS.md\` and \`MASTER_TODO.md\` first. The master ledger owns the running checklist and supersedes the historical nine-component instructions for V3.

## Implemented

The existing 593×504 canonical PNG remains the visual source of truth. Source-normalized polygons identify eight instrument surfaces plus the existing left/right arm-stick regions and hi-hat foot/pedal region. The builder exports integrated nodes under the same eight public targets and surface-only \`_SURFACE\` submodels. Other instrument surfaces are subtracted from actuator contributions so a shared arm cannot illuminate a neighbouring drum.

The xmodel now carries an explicit dense 96×72 \`CustomModel\` grid and a portable \`CustomBkgImage="../source/drummerbg.png"\`.

The xmodel remains the xLights/export geometry contract and is validated for eight non-empty public targets. For review video, the renderer rasterizes the same authored source-normalized geometry directly at the 593×504 source resolution instead of enlarging the coarse 96×72 node grid. Idle artwork is held at a 15% dim baseline; active masks receive a strong source-preserving emissive lift. This removes the spotty/blocky review lighting while keeping component ownership identical. Simultaneous hits use a max-union so shared arms never compound.

Hi-hat includes the existing foot/pedal region and no arms. Kick includes no actuator. The extra lower-right drum is not part of any canonical surface.

PNG review layers are also derived from the same xmodel nodes. The layer manifest selects canonical targets and contains no independently authored geometry commands.

A shared deterministic event oracle drives both WAV and XSQ: eight isolated components in the opening eight seconds followed by combinations and fills. The 20-second fixture contains 68 events. This fixture verifies mapping/rendering; it is not evidence of improved real-song drum detection.

The former expected failure is repaired separately in the same branch: the legacy starter xmodel has real HEAD and DRUMKIT_ALL unions and is retained under \`archived_models\`, while the five active manifest models include V3 and align with the runtime.

## Verification gates

The focused GitHub workflow regenerates the assets, checks the HIGH-right/MID-left/FLOOR-left geometry, validates the exact eight public targets and portable background path, compares the 68-event WAV manifest with the XSQ timing track, runs the focused drummer/manifest tests, and renders a 20-second H.264/AAC preview at 24 fps.

Current automated verification now includes both the deterministic geometry fixture and a production-path real-song proof. The approved `b27e8d77a63027ed32bcf6851dcff3925472c155` classifier behavior was restored exactly: `Helix Audiolights.mp3` produces the historical raw counts kick=194, snare=37, tom=9, hi-hat=208, cymbal=840, drum_bus=47. Production mapping targets the real `HX_SNOWMAN_DRUMMER_V3_*` names, and ambiguous/collapsed multi-hit tom subclassing falls back to HIGH→MID→FLOOR distribution so no physical tom is starved.

Still open after automated verification:
1. User visual approval of the corrected 160-second real-song candidate.
2. Native xLights import/playback of the regenerated custom model.


## Reconstruction evidence

Remote GitHub Actions run `37416429803` succeeded on the implementation branch after the independent-surface fix. The workflow regenerated canonical assets, proved the exact 68-event WAV/XSQ oracle and eight public targets, ran **37 focused tests with 3 existing deprecation warnings**, rendered a 20-second 960×540 H.264/AAC preview at 24 fps, and uploaded both XSQ/audio and MP4 artifacts.

The eight isolated decoded frames at 0.333, 1.333, …, 7.333 seconds were inspected after encoding. An intermediate reconstruction exposed a kick/snare shared-grid-cell bleed; the builder now gives adjacent instrument surfaces mutually exclusive node ownership, and the corrected kick state leaves the snare at idle brightness. The renderer still uses a max-union for simultaneous hits and subtracts all raw instrument surfaces from actuator contributions.

The generated xmodel, PNG review layers and pose sheet are checked into the branch. The workflow now verifies regeneration is byte-for-byte clean with `git diff --exit-code`; it does not mutate the branch during ordinary validation.

User visual approval, native xLights import/playback, and real-song detector quality remain open. This reconstruction does not claim the unavailable original local commit SHAs or byte identity with the lost source patch.


## Corrected real-song proof

After the first reconstructed preview was rejected for spotty component lighting and regressed rhythm behavior, the branch was re-audited against the historical oracle instead of treating the synthetic fixture as sufficient evidence.

GitHub Actions run `37432351105` is the current implementation proof. It passed the focused test suite, regenerated/validated the V3 model, passed the 68-event deterministic geometry fixture, matched the historical real-song detector counts exactly, proved that all eight V3 targets occur within the first 160 seconds, and rendered/uploaded a 160-second preview using the repository's real `Helix Audiolights.mp3` audio.

Real-song mapped component counts are: KICK 193, SNARE 37, HI_HAT 205, TOM_HIGH 3, TOM_MID 3, TOM_FLOOR 3, CYMBAL_LEFT 412, CYMBAL_RIGHT 412. Raw detection remains exactly equal to the historical oracle; the small difference between raw and mapped totals comes from the existing scheduling/de-clutter stage and bus suppression.

The synthetic fixture remains only a geometry/isolation regression test. It is no longer presented as proof of musical detection quality.
