# Note-accurate instrument lighting and physical channel acceptance (2026-10-17)

Owner requires illuminated bass/guitar strings, accurate independently lit keyboard and mallet keys, and sufficient **real exported channels** for the keyboard.

## Existing code findings
- `models/native_review_band.py::_role_parts` already declares `STRING_<index>` for live strings and `NOTE_MIDI_<pitch>` for piano keys and xylophone bars.
- `add_band` gives dynamic note/string submodels ownership of pixel nodes ahead of BODY; `allocate` advances the start address by `m.channels` for pixel models.
- `ac_variant` intentionally collapses piano/xylophone keys into 12 pitch-class circuits shared across octaves, plus body and arm circuits, to fit the physical 16-channel limit. **This is not individual key control** and must never be advertised as such.
- Presence of submodels is NOT proof that actual note events drive the correct submodels, or that FSEQ/MP4 outputs show correct lighting.

## Required implementation
1. Pixel output: one independently addressable `NOTE_MIDI_<absolute_pitch>` submodel per available piano key and mallet bar. Assert nonempty, disjoint note-node ownership; distinct pitches must not alias one pixel channel. Verify actual xLights model `channels`, start-channel offsets, channel spans, XSQ effects, rendered FSEQ values and decoded MP4 frames.
2. Bass/guitar: map every confidently transcribed note to its physically playable string and fret; illuminate only the corresponding `STRING_<index>` at onset, with appropriate attack/sustain/release. Chords may illuminate several strings. Do not light strings based solely on broadband loudness or kick-drum transients.
3. Keyboard: illuminate the exact MIDI pitch while the note is held, with attack and release. Black keys remain on the far side from the snowman. When a horn/trumpet/other unrepresented instrument supplies a verified melody, the keyboard lights its correct pitches.
4. Mallet: illuminate the correct pitch bar at each detected strike, synchronized with visible left/right mallet contact; use appropriate brief strike/decay instead of false sustained keyboard behavior.
5. Native rendering: preserve distinct per-note channels throughout XSQ/FSEQ; verify simultaneous notes, repeated notes, chromatic notes, octaves, silence, out-of-range handling and disjoint instrument addressing.
6. AC16: retain existing 12-pitch-class plus body/arms approximation and clearly label it as reduced resolution; never claim independent octave-specific keys on 16 AC circuits. Offer additional controllers or pixel output when per-key hardware independence is required. Do not exceed CTB16PC 16-circuit budget without explicit hardware configuration.
7. Assert actual channel counts from exported models, not assumptions. The desired count is determined by independently lit physical keys/bars and pixel node mapping, not by a fixed arbitrary 16-channel ceiling.
8. All real-audio detector claims must be supported by traced source notes and source-aligned MP4/FSEQ evidence; uncertain instrument identification must be disclosed.

## Release acceptance
Test a bass riff, guitar chord/solo, keyboard melody, mallet run and overlapping ensemble from verified music; produce native closeups with note-by-note timing and channel manifests. Keep EXE/APK integration on hold pending owner review.

Status: acceptance requirement committed. No new lighting pipeline implementation or render verification in this change.
