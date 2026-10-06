# Independent drummer lighting — reconstruction handoff

Base: \`1f66f5dfa09b3173f5cdfd33d28ab1b4421e11ad\` on \`feature/restructure-core\`.
Implementation branch: \`fix/drummer-independent-illumination\`.

Read \`AGENTS.md\` and \`MASTER_TODO.md\` first. The master ledger owns the running checklist and supersedes the historical nine-component instructions for V3.

## Implemented

The existing 593×504 canonical PNG remains the visual source of truth. Source-normalized polygons identify eight instrument surfaces plus the existing left/right arm-stick regions and hi-hat foot/pedal region. The builder exports integrated nodes under the same eight public targets and surface-only \`_SURFACE\` submodels. Other instrument surfaces are subtracted from actuator contributions so a shared arm cannot illuminate a neighbouring drum.

The xmodel now carries an explicit dense 96×72 \`CustomModel\` grid and a portable \`CustomBkgImage="../source/drummerbg.png"\`.

The renderer consumes exported xmodel node ranges. It does not reconstruct circles from the pose spec and does not globally brighten the picture. Idle artwork is fixed at 28% brightness. Active hits restore the existing source pixels only inside the max-union of active node masks, preserving source colors and preventing shared arms from compounding.

Hi-hat includes the existing foot/pedal region and no arms. Kick includes no actuator. The extra lower-right drum is not part of any canonical surface.

PNG review layers are also derived from the same xmodel nodes. The layer manifest selects canonical targets and contains no independently authored geometry commands.

A shared deterministic event oracle drives both WAV and XSQ: eight isolated components in the opening eight seconds followed by combinations and fills. The 20-second fixture contains 68 events. This fixture verifies mapping/rendering; it is not evidence of improved real-song drum detection.

The former expected failure is repaired separately in the same branch: the legacy starter xmodel has real HEAD and DRUMKIT_ALL unions and is retained under \`archived_models\`, while the five active manifest models include V3 and align with the runtime.

## Verification gates

The focused GitHub workflow regenerates the assets, checks the HIGH-right/MID-left/FLOOR-left geometry, validates the exact eight public targets and portable background path, compares the 68-event WAV manifest with the XSQ timing track, runs the focused drummer/manifest tests, and renders a 20-second H.264/AAC preview at 24 fps.

Still open after automated verification:
1. User visual approval of the reconstructed candidate.
2. Native xLights import/playback of the regenerated custom model.
3. Real-song detector evaluation, harmonic rejection, stem provenance, fill context and humanization. Production detection logic is intentionally unchanged.
