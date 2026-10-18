# Keyboard orientation acceptance blocker — 2026-10-17

Owner reports that the keyboard is upside down in many native showcase videos.

**Required physical orientation:** the snowman stands at the near/player side of the keyboard. White-key fronts are closest to the performer; the raised black keys are farther away, toward the audience-facing/back edge of the instrument. Black keys must NEVER be nearest the snowman's body in the normal performance pose.

Investigate local instrument coordinate axes and transforms in `models/review_snowman_scene.py`, `models/review_3d_scene.py`, `models/native_review_band.py`, the layout placement/camera and xLights native export. Do not fix a model-space inversion by flipping only the editorial video; this would make the actual xLights 3D layout wrong.

Acceptance tests:
- Define a performer-to-keyboard near/far axis in world coordinates and assert every black-key center is farther from the performer than the corresponding white-key front.
- Assert left-to-right pitch order from the performer's viewpoint and that finger/key contacts align with the mapped MIDI notes.
- Test both front-facing 2D and xLights 3D views, both snowman and rock band, standalone and embedded stages, and all six native layouts.
- Confirm the unified keyboard/mallet performer and universal melody fallback use this same orientation, including brass/horn notes mapped to keys.
- Produce native-rendered stills and MP4 frames from player-side and audience-side cameras before artistic approval.

Status: defect reported by owner; exact transform/root cause not yet proven. Keep EXE/APK merge and release on hold until fixed and visually approved.
