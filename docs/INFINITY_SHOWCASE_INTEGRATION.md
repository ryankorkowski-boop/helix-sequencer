# Infinity Showcase on the integration branch

The layout generator from draft PR #250 is on `integration/unified-beta-completion-20261117`. That draft was not merged. The Infinity workflow fetches the original Bells recording, verifies its SHA-256 and sequences the full song on the 128-model tier. Its artifact contains the layout, sequence and native render evidence available at the end of the run. Check the verification report and job conclusion before using a run as native evidence.

## What landed

- `tools/build_infinity_showcase_layout.py` builds the 128, 512, 2048, and 10240 tiers.
- Singing faces have Mouth and Eyes submodels.
- `HX_INFINITY_DISTRICTS` is a group whose members are the family groups, so nested expansion reaches every model.
- `tools/infinity_showcase_clip.py` orders the faces with the spatial graph and writes `modelGroup` and `submodel` rows with xLights 2026.19 blend keys.

## Native check

xLights 2026.19 rendered a 2 second, 128-prop clip (40 frames, 29952 channels). A mouth-only sequence lit `HX_INFINITY_SINGING_FACE_0001/Mouth` at 255 and left the eyes and the rest of that face at 0. The district group uses `T_CHOICE_LayerMethod=Average`. The mouth uses Canvas and `T_CHOICE_LayerMethod=Layered`. The two faces order by X. This is not owner approval and not the full Bells song.
