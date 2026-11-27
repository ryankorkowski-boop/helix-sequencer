# Handoff: vocal separation for Helix Sequencer

Written 2026-11-27 for Gemini. The owner is Ryan. This is the vocal problem only. Do not reopen the Infinity movie, do not publish a release, and do not treat this note as singer-identity proof.

Repository: https://github.com/ryankorkowski-boop/helix-sequencer
Live code branch: `codex/beta14-live-engine-integration` at `4f7ad6c587b54c1f6f58acdaff38951ffdb5a1df`.
Listening clips, not acceptance: branch `review/harmony-candidate-mp4`.

## The job

Separate, or honestly label, the voices in `Phoneme_Test_Hook.mp3` so three singers can drive three mouth lanes. The current engine has two lanes and a gate that correctly refuses to call them verified. That refusal is right. The missing work is a third lane plus a separation that can survive a mix the owner says was built to fuse the voices.

## Gates you must not move

- Do not lower the 0.65 stage-motion gate or the phoneme median gate. Those are not this bug. Phoneme native verification [45941655656](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655656) already passed on `4f7ad6c`.
- Do not set `independent_backing_verified` or `verification_state=VERIFIED` from a model split of a mix.
- Do not copy the lead mouth shape onto the harmony lane. `tools/stemless_duet.py` forbids that on purpose. A copied syllable looks like a duet and is false.
- Do not fabricate a mouth while that lane is silent.
- Do not put Demucs or RoFormer weights in the offline APK. Desktop RoFormer ONNX export still fails on complex STFT. The phone build is already about 407 MB.
- The phone may only import a desktop ZIP: `vocal_separation_manifest.json` plus the wavs it names. `HELIX_VOCAL_SEPARATION_SOURCE` selects that bundle. Zip-slip must stay rejected. The bundle has to match the selected song. It is not on-device separation.
- `CompositionGovernor` is the conductor. Do not add `CooperativeShowDirector`.
- Infinity is deferred out of Beta 1.4. Leave it alone.

## What the owner says the song is

The file is a pop test track, about 34.88 seconds, mixed stereo. SHA-256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. Fixture path: `fixtures/audio/Phoneme_Test_Hook.mp3`. Constant: `tools/phoneme_source.py` `EXPECTED_SHA256`.

The style prompt asked for a mix that would be easy to separate:

> verse starts dry and close-mic with one male lead, pre-chorus opens into stacked vowels, chorus hits with a female backup singer on harmony and a short background chorus in unison; polished, centered mix with very clear vocal separation.

The owner then listened and said the opposite of the prompt's hope: there are three voices, and this song is hard to pull apart because it was made that way. Trust the ear and the lyric sheet over the prompt's "very clear vocal separation" sentence. The prompt still names the three roles. The recording does not hand them to a splitter.

Three roles:

1. Male lead. Verse, dry, close-mic. Also Bee/dee/gee, Yuh/yah/yow, and the single "ma" the owner marked.
2. Female harmony. Backup on the chorus, plus the passages the owner marked female.
3. Background chorus. Short unison stacks. This is the third voice. The code has nowhere to put it.

## Lyric sheet (owner text, not the detector)

```
[Verse 1]
Pa ta ka, pa ta ka
Ma na la, ma na la
Bee, dee, gee
Fo, vo, so, zho

[Pre-Chorus]
Ah, eh, ee, oh, oo
I, ay, eye
Yuh, yah, yow

[Chorus]
Clear voice, sharp voice
Ba-ba, da-da
Clear voice, sharp voice
Pa, ta, ka

[F] Ooh, ooh, ooh

[Background Chorus]
Ah-ah, eh-eh
Oh-oh, oo-oo
Ma-ma, na-na
La-la, la-la

[Outro]
Pa ta ka
Ah, eh, ee, oh, oo
```

That is 72 syllables if hyphenated notes are split (`Ba-ba` is two, `Ah-ah` is two).

### Owner listening map, in the order he called it

Use this as the role labels. Where it disagrees with a neat section reading of the sheet, do not silently pick one.

- First nine notes: male lead. Best sheet fit: `Pa ta ka, pa ta ka, Ma na la` (6+3).
- Next six notes: female harmony. The sheet's next line is only the second `ma na la` (3 syllables). He counted six. Do not invent the missing three.
- The following "ma": male lead. There is no extra solo "ma" on the sheet between those lines.
- Next six `ma ni la ma ni la`: female. Same words as `Ma na la, ma na la`. He heard `ni`; the sheet says `na`.
- Three notes `b d g`: male. Sheet words are `Bee, dee, gee`.
- Four notes `fo so so sooo`: shared. Sheet words are `Fo, vo, so, zho`.
- `eye ay eye`: female. Sheet words are `I, ay, eye`.
- `Yo yo yo`: male. Sheet words are `Yuh, yah, yow`. Not present as the letters y-o.
- `Clear voice, sharp voice`: shared. It occurs twice on the sheet.
- Then four notes female, four notes female, alternating four notes, then shared again at `Clear voice, sharp voice`.
- `One day`: male. Those words are not on the sheet. Do not add them.

A review video colored a guess on top of this and said so. `Pa, ta, ka` after the second "clear voice" was marked alternating only because it was the leftover short line. That guess is not owner-confirmed. `Ooh, ooh, ooh` was marked female because of the `[F]` tag. The background-chorus block was marked as the third voice because the sheet says so.

## What the detector actually wrote

Schema `helix.vocal-review-timeline.v1` and the chronoflow lyric hits. Lexical phonemes are not verified. The report's own fallback is `rule_based_lexicon_and_energy_heuristics`.

The 59 guessed syllables, in order, with the first hit time:

`Ba da da da da da Ba da ka` (0.00–2.68), `ba da ka` (2.98–3.66), `Ma na la ma na la` (4.00–5.70), `Pee tee jee` (5.90–6.84), `Fo fo so zo` (7.56–9.02), `Ah eee Ai ai ai` (9.82–12.90), `Clear one sharp voice` (13.82–15.00), `Clear one sharp voice` (15.42–18.98), then `Ba da ka Shoo Ai ai ai Fo fo fo Ma ma na na la la la Ba ai ai Oh`.

Useful correspondences, and they are only correspondences:

| Owner / sheet | Detector | Note |
|---|---|---|
| Pa ta ka… | Ba da ka… | consonant errors |
| Bee, dee, gee | Pee tee jee | place-of-articulation errors, around 5.90 s |
| Fo, vo, so, zho | Fo fo so zo | held last note became `zo`, around 7.56 s |
| I, ay, eye | Ai ai ai | split badly, around 11.72 s |
| Yuh, yah, yow | not found | |
| Clear voice, sharp voice | Clear one sharp voice | `voice` once became `one` |
| One day | not found | |

`HX_SNOW_LEAD` got 257 Faces effects (206 not rests) on timing track `Helix_Lead_Phonemes`. `HX_SNOW_HARMONY` got 7 (5 not rests) on `Helix_Harmony_Phonemes`. Both effects carry the mix SHA, not a stem SHA, when the stemless path is used. Harmony mouths borrow lead syllables. Do not describe those 7 effects as a second singer.

## Why the current separator fails on this file

There are two different estimators, and both are two-lane.

1. Optional MDX split in `tools/separate_phoneme_vocals.py`. It needs `audio-separator` 0.47.1. Weights are not in the repo. Models and the hashes the tool demands:

   - `UVR-MDX-NET-Inst_HQ_3.onnx` `317554b07fe1ea5279a77f2b1520a41ea4b93432560c4ffd08792c30fddf9adc`
   - `UVR_MDXNET_KARA_2.onnx` `bf32e15105a09c0f7dddd2b67346146334d6f3ecb399ed7638eba2ab07cbf5f4`

   First model pulls vocals out of the mix. Second model splits those vocals into `estimated_lead` (KARA vocals) and `estimated_backing` (KARA instrumental of the vocal stem). The receipt hardcodes `independent_backing_verified=false`. A CI diagnostic reported:

   - `estimated_lead.wav` SHA `d3496a3040dcbfbb629f5a8c27acfd50d9f60697a0fd7f35ef66a28424155ec5`, 16.09 voiced seconds
   - `estimated_backing.wav` SHA `57e7f258273b22e035db191c4afa65f06a6ea99c2ea91e8e12edb7e7573a423a`, 3.87 voiced seconds
   - `gain_or_short_delay_duplicate=false`
   - Silero VAD screening, threshold 0.15
   - Those wavs were not kept in the phoneme artifact. Do not invent replacements. Re-run separation if you need the audio.

2. Stemless gate in `tools/stemless_duet.py` `estimate_duet()`. This is what actually drives the Phoneme Test Hook mouths when no qualified stems exist. It looks for a second pitch 2 to 10 semitones from the strongest, persisting 150 ms, and only where the lead lane is already voiced and the backing clock already has its own mouth shape. On this file that gate fired for 10 frames: 0.62–0.72 s. Lead held `OH`. The candidate flipped `AH`/`OH`. Instruments can fake that. `independent_voice_identity_proven=false`. `second_lane_active_frames=10`.

A two-pitch gate cannot represent three fused singers. Collapsing them into "lead plus one harmony" is the bug, not a reason to drop the gate.

Screening of MDX lanes lives in `music/vocal_qualification.py` `screen_candidate_lanes()`, called from `tools/phoneme_vocal_export.py`. Export onto the snowmen is `export()` in that same file. A lane becomes "qualified" only when `verification_state == VERIFIED` and `tools/vocal_analysis_fixture.py` `verify_fixture()` accepts real isolated wavs. This test hook is not in that state.

## What "solved" means

A solution is one of these, in order of honesty:

1. Best: three time-aligned wavs for this exact SHA, one per role, long enough to match the 34.88 s mix within the existing 50 ms tolerance in `core/independent_vocals.py`. Then a manifest that names three stems, not two. Mouths come from each stem's own clock. `independent_backing_verified` may become true only after `verify_fixture` passes on those files. The owner has not provided these files.
2. Acceptable engineering step: an owner-labeled lyric map, stored as data, marked `owner_listening_map` and `identity_verified=false`. It may drive a review preview. It must not flip the verification flags. The sheet and the listening notes above are that map. Several lines are still ambiguous; ask before filling them.
3. Not a solution: another UVR pass that still emits two files, a lower hysteresis, copying lead shapes, or labeling the 0.10 s flicker as the female singer.

If you add a third stem to the phone bundle, change the manifest schema on purpose and update `core/vocal_separation_manifest.py`, `android/app/src/main/python/helix_mobile.py`, and `tests/test_android_vocal_bundle.py` together. Do not quietly overload `backing.wav` with "female plus chorus."

## Files to read first

- `tools/separate_phoneme_vocals.py` — MDX entry, refuses a hash mismatch on the mp3 or the onnx files.
- `tools/stemless_duet.py` — the 150 ms dual-pitch gate and the no-copy rule.
- `tools/phoneme_vocal_export.py` — Faces effects, timing tracks, static body pulse (86/96 every 400 ms, unrelated to vocals).
- `tools/vocal_diagnostic.py` — `Vocal_Timeline.csv` columns: `lead_active`, `lead_phoneme_estimate`, `backing_active`, `backing_phoneme_estimate`.
- `tools/offline_vocal_candidates.py` — presence screening. VAD values are not estimate confidence.
- `core/vocal_separation_manifest.py` — desktop ZIP the phone can import.
- `core/independent_vocals.py` — how real lead and harmony wavs are compared.
- `tools/vocal_analysis_fixture.py` — the only path that sets `verification_state=VERIFIED`.
- `tests/test_phoneme_vocal_export.py`, `tests/test_vocal_diagnostic.py`, `tests/test_android_vocal_bundle.py`.

## Evidence already on GitHub

- Latest phoneme diagnostic, motion gate passed, identity not claimed: run [45941655656](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655656), artifact `phoneme-test-hook-native-review-7ed4b04882fb6571e85ab663e396492a32bc8e54`. Contains `vocal_lane_diagnostic.json`, `Vocal_Timeline.csv`, the native MP4, and the mp3. Does not contain `estimated_lead.wav` or `estimated_backing.wav`.
- Older failed band job, correctly closed: [45905840026](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840026). Native MP4 existed. Exit was "independent lead/harmony identity unverified."
- Twelve-layout failure to leave closed: [45905839973](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839973). "vocal timing and approved-reference identity gates remain open."
- E14 is a different recording. One mixed bus, zero independent tracks, archive SHA `604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10`. Do not use it as stems for this test hook.

Review clips the owner has, all on `review/harmony-candidate-mp4`:

- `docs/review/harmony-candidate-assessment.mp4` — the 0.10 s flicker only. Superseded.
- `docs/review/harmony-lyric-voicemap.mp4` — detector words, not the sheet.
- `docs/review/lyric-sheet-voicemap.mp4` and `docs/review/lyric-sheet-syllables.mp4` — sheet words. Phrase starts are pinned to the detector hits above. Syllables inside a phrase are evenly spaced, not transcribed. A peak-picked clock was tried and rejected because it moved `Bee, dee, gee` and `Clear voice` about two seconds early.

## Out of scope

- Infinity layout. Last run [45941655671](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655671) died in `openSequence` / the post-dialog health check. Owner removed it from Beta 1.4.
- Signing the APK or the Windows EXE. Unsigned CI packages already exist on the draft release. They are not a release.
- The 252-circuit arch map. Do not renumber it.
- Any claim that this handoff verifies a singer.

## Suggested first experiments

1. Re-run `tools/separate_phoneme_vocals.py` on the pinned mp3 and keep the wavs. Listen to `estimated_backing.wav` against the sheet. If the female and the chorus are still in the lead file, say so and stop treating KARA as a three-voice splitter.
2. Measure how many simultaneous pitched vocal partials the mix actually holds in the chorus. The owner says three. Report the count. Do not promote the count to identity.
3. Add a third clock only as an owner-labeled review lane, default off, flagged unverified, with tests that a silent third lane creates no Faces effects and that lead shapes are not copied.
4. Ask the owner for the three bounced stems if the model split still fuses them. That is the unblock, not a threshold change.
