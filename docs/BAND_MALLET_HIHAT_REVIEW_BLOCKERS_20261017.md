# Band performance defects — review blockers (2026-10-17)

## Mallet/xylophone performer repeatedly missing

**Observed by owner:** the xylophone/mallet performer is missing from review movies.

**Verified code facts:** `models/native_review_band.py` declares seven separate roles, including `piano` and `xylophone`; `add_band` creates the native snowman cast. `tools/native_source_pose_band.py` exports exactly seven models and supplies the xylophone's stage position. Thus the xylophone is not universally absent from the source layout definition.

**Why it appears omitted is NOT yet conclusively determined.** The recovery checklist documents that unsupported musical roles can remain quiet, and that finite source-pose lighting states do not guarantee an observable mallet performance. Likely failure gates to investigate separately are: source note/transient classification, xylophone role assignment, nonzero `NOTE_MIDI_*` curves, active mallet rig geometry, native XSQ effects, rendered FSEQ channels, camera occlusion/brightness, and final video crop. Do not assume an instrument was detected because its model exists.

**Required acceptance test:** select a verified mallet/pitched passage from a real Drive recording; trace time-aligned detected events through each layer, require visible independently timed left/right mallet motion and contact with the correct bars, verify decoded native FSEQ activity and MP4 frames, and include a focused mallet close-up plus full-stage shot. If evidence does not support mallet notes, report silence instead of inventing notes. Owner previously requested one unified keyboard/mallet performer per band; reconcile that requirement with the present seven-role piano + xylophone cast **before changing cast counts or releasing**.

## Hi-hat is a FOOT/PEDAL action, not a drumstick hit

**Owner's explicit requirement:** drummer's hi-hat must show foot/pedal movement, NOT a stick striking the hi-hat.

**Verified defect:** `models/review_3d_scene.py` includes `HI_HAT` among stick-target `TARGETS`; `update_drummer` assigns every non-`KICK` event to an arm/hand/stick contact. `models/native_review_band.py` likewise builds a stick-contact pose for `HI_HAT`. This violates the requested visual semantics.

**Implementation specification:**
- Introduce a separately animated hi-hat pedal, foot and linkage with stable idle, depress, release and cymbal-close poses.
- Route `HI_HAT` events to pedal/foot articulation; exclude them from arm-stick contact candidates in the owner's requested display mode. Keep left/right arm motion for snare, toms and crash/ride cymbals.
- Preserve the event timestamp, velocity, channel mapping and audio timing. For real acoustic performances, open/closed/foot-splash classification requires evidence; if unknown, animate a simple foot closure and avoid falsely labeling splash.
- Keep existing CTB16PC and <=16-circuit exports backward compatible. Additional RGB geometry may have independent pixel nodes, but do not silently add AC circuits.
- Extend native source-pose capture to include the new pedal/foot rig; otherwise native MP4s will continue showing old stick-hit semantics even if the 3D scene is corrected.
- Add regressions asserting a hi-hat-only event changes foot/pedal pose, leaves both sticks idle, and produces no stick-contact proof; verify repeat hits, releases, no spurious kick-beater activation, FSEQ channel parity and decoded native MP4.
- Ensure both snowman and rock-band variants implement the same semantics.

**Release gate:** no band showcase acceptance, final EXE/APK merge or release until the owner reviews a visible foot-operated hi-hat and a clearly active mallet/keyboard performer. Keep all existing release holds.
