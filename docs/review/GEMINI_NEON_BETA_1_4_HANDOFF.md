# Handoff: finish Helix Sequencer Beta 1.4

Written 2026-11-27 for Gemini. Owner: Ryan. Resume from this note and from `BETA_1_4_RELEASE_CHECKLIST.md`. The checklist's older rows still mention a 0.374 phoneme failure and a 600-second Infinity timeout. Those rows are history. This note is the current assignment.

Do not spend the release on `Phoneme_Test_Hook.mp3`. That file is a fixture. The earlier note `docs/review/GEMINI_NEON_VOCAL_SEPARATION_HANDOFF.md` is about that fixture. Ignore it.

## Where the code is

- Repository: https://github.com/ryankorkowski-boop/helix-sequencer
- Live branch: `codex/beta14-live-engine-integration` at `4f7ad6c587b54c1f6f58acdaff38951ffdb5a1df`
- Same work also sits on `integration/beta14-recovered-logic-20261126`
- Draft PR: https://github.com/ryankorkowski-boop/helix-sequencer/pull/264 toward `integration/unified-beta-completion-20261117`. Draft. Do not merge it.
- Default branch `feature/restructure-core` is older. Do not restart from it.
- Latest published release is Helix Beta 1.3, tag `helix-beta-v1.3`, 2026-11-13. There is no Beta 1.4 GitHub Release.
- Unpublished draft that holds binaries, not a release: https://github.com/ryankorkowski-boop/helix-sequencer/releases/tag/untagged-a987b0145879edf508eb tag `baseline/pr264-estimated-16panel-20261126`

`CompositionGovernor` (`core/composition_governor.py`) is the conductor. Do not add `CooperativeShowDirector`. Do not copy a second orchestrator out of PRs #262 or #263.

## What "finished" means

A public Beta 1.4 is allowed only when every line below is true. Do not tag a release that skips one and calls it done.

1. Helix CI is green on the commit you tag.
2. The 0.65 stage-motion gate and the phoneme median gate stay at 0.65. They already pass. Do not lower them.
3. Singer identity is either verified from isolated stems for the recording you ship, or the release notes say `ESTIMATED_REVIEW` in those words and do not claim a verified singer. The owner has not accepted that label in writing.
4. The owner has watched and accepted the 16-panel MP4. The file on the draft is not that acceptance.
5. The Android package is a release APK the owner can install, with checksum. A CI debug APK is not that package.
6. The Windows package is an EXE or the documented portable ZIP, with checksum. Unsigned CI output must be labeled unsigned. A clean-machine install has not been done.
7. `WEBSITE_RELEASE_HANDOFF.md` exists only after the prerelease URL and checksums exist.
8. Infinity is not part of this release. The owner deferred it. Do not block 1.4 on it and do not start another Infinity run to "finish."

## Vocal separation

The product has two vocal lanes, lead and one backing. Real shows need a lead, a harmony singer, and a unison background chorus. The third voice has nowhere to go, so it is folded into the lead or dropped. That is the separation bug.

What the code does today:

- `tools/separate_phoneme_vocals.py` runs a two-stage UVR split (`UVR-MDX-NET-Inst_HQ_3.onnx`, then `UVR_MDXNET_KARA_2.onnx`) and writes `estimated_lead` plus `estimated_backing`. The receipt hardcodes `independent_backing_verified=false`. Weights are not in the repo. `audio-separator` 0.47.1 is the expected package. A hash mismatch on the model file fails closed.
- `tools/stemless_duet.py` `estimate_duet()` is the path used when there are no qualified stems. A second mouth exists only when the lead is already voiced, a second pitch sits 2 to 10 semitones away, that evidence lasts 150 ms, and the backing clock already has its own mouth shape. It must not copy the lead syllable onto the harmony lane. Copying makes a fake duet.
- `tools/phoneme_vocal_export.py` `export()` paints `HX_SNOW_LEAD` and `HX_SNOW_HARMONY`. `verification_state == VERIFIED` is the only switch that sets `independent_backing_verified`. That switch is `tools/vocal_analysis_fixture.py` `verify_fixture()`, and it requires real isolated wavs.
- `core/independent_vocals.py` compares a lead wav and a harmony wav. Sample rates must match. Lengths must agree within about 50 ms.
- `core/vocal_separation_manifest.py` and `android/app/src/main/python/helix_mobile.py` let the phone import a desktop ZIP. The ZIP holds `vocal_separation_manifest.json`, `lead.wav`, and `backing.wav`. `HELIX_VOCAL_SEPARATION_SOURCE` points at it. Reject zip-slip. The bundle must match the selected song. The phone does not run the model. Do not put Demucs or RoFormer in the APK. Desktop RoFormer ONNX export still fails on complex STFT. The phone build is already about 407 MB.
- The E14 archive (`604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10`) is one mixed vocal bus and zero independent tracks. Do not mark that recording verified.

Band and twelve-layout jobs fail closed on this, and they should keep failing until the gate is real:

- Fresh band [45941655624](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655624) and the final band waiter [45941655620](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655620) on `4f7ad6c`. Earlier closed failure with a rendered MP4: [45905840026](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905840026). The exit is "independent lead/harmony identity unverified."
- Twelve-layout [45941655806](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655806) on `4f7ad6c`. Earlier statement of the same gate: [45905839973](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45905839973), "vocal timing and approved-reference identity gates remain open."

A finished vocal solution is one of these:

1. Time-aligned isolated stems for the recording that will ship, one file per singer, passed through `verify_fixture`. Then the release may say the singers are verified. The owner has not provided those files. Do not synthesize them from the mix and then flip the flag.
2. A third review lane that stays off unless the owner labeled it, with `identity_verified=false`, and with tests that a silent lane creates no Faces effects and that lead shapes are not copied. Shipping that lane as "verified harmony" is a fail.
3. Written owner acceptance of `ESTIMATED_REVIEW` on the release notes. Do not write that acceptance yourself.

If the phone bundle grows a third stem, change `vocal_separation_manifest.py`, `helix_mobile.py`, and `tests/test_android_vocal_bundle.py` together. Do not hide two singers inside `backing.wav`.

## What already passed on `4f7ad6c`

- Helix CI [45941655857](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655857)
- Helix Unified Beta Integration [45941655777](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655777)
- Helix Beta CI [45941655695](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655695)
- Compliance [45941655728](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655728)
- Phoneme native MP4 verification [45941655656](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655656). This is the motion gate, not a singer-identity pass. An earlier pass on `009af23` measured median_motion 1.174, median_luma 12.85, against an unchanged 0.65 threshold.
- Windows portable [45941655673](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655673). Preserved on the draft as `Helix-CI-Portable-UNSIGNED-4f7ad6c-Windows.zip`, 386,621,374 bytes, SHA-256 `44cd5979cd2a97b9b57f8f007c292a78231816dc5af25de3352d09c9e1da1320`. CI smoke returned 0. Unsigned. Not a clean Windows install.
- Android offline beta [45941655649](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655649). API 36 artifact 407,770,980 bytes. API 30 artifact 407,453,256 bytes. Debug/stability builds, not a signed Play APK.

Older unsigned Windows zips are also on that draft (`009af23`, `abe557e`, `7ddf34aa`). Keep them. Do not delete the 16-panel baseline MP4 on the same draft:

- `Helix-Baseline-16-Panel-ESTIMATED-REVIEW-f068aecb.mp4`, 8,336,391 bytes, SHA-256 `b50f315ce2e4f981db92cdb38eccec5b3c1fb525b2b46e645960bb73d29bc831`
- That movie is `ESTIMATED_REVIEW`. It is not owner acceptance.

## What is still open

| Gate | State |
|---|---|
| Singer identity | BLOCKED. No isolated stems. Do not claim them. |
| Nine-panel and twelve-layout | BLOCKED on the same vocal-timing and reference-identity gates. |
| 16-panel visual acceptance | OWNER REVIEW REQUIRED. |
| Signed APK and signed EXE | NOT DONE. No signing credentials in the session. |
| Clean-device install | NOT DONE. |
| Public GitHub Release and checksums as the release | NOT DONE. The draft is a drawer, not the release. |
| `WEBSITE_RELEASE_HANDOFF.md` | NOT DONE. Write it after the prerelease URL exists. |
| One conductor, production-path features | PARTIAL. Role and shared-row admission is in the live placer. Nine-pass orchestration runs from sequence build. A real `audio_analysis.json` may replace the synthetic section seed only at confidence ≥ 0.7 with a matching hash. |
| Infinity movie | DEFERRED by the owner. Last attempt [45941655671](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/45941655671) reached about 84% during `openSequence`, then the post-dialog health check timed out. No MP4. Leave it. |
| CooperativeShowDirector extract | NOT DONE and not required for the tag. |

## Architecture you must not break

- Canonical AC layout is 252 circuits. Four deleted arch apex models stay deleted: channels 133, 142, 151, and 160. Do not renumber the map. RGB still starts at 257. Arch 1 Sec 1 stays 129. Arch 1 Sec 6 stays 134.
- Empty `base`, `motion`, and `accent` weaver layers are reserved on demand (`reserve_effect_layer` in `xlights/xml_io.py`). Do not go back to creating those lanes before an effect exists. That change was about load time, not about vocals.
- `openSequence` on a huge show may wait up to 1200 seconds, and only when a longer render budget was already requested. Ordinary previews stay shorter. Do not raise that cap to force Infinity through. Infinity is out of 1.4.
- The phoneme body pulse (material stepping between 86 and 96) is what moved the stage-motion median over 0.65. Leave it. It is not a vocal change.

## Order of work

1. Decide the vocal release claim with the owner: isolated stems, or the words `ESTIMATED_REVIEW`. Do not pick the second one for him.
2. If he supplies stems, wire them through `verify_fixture` and the existing two-file manifest. Add a third file only with the schema and tests named above.
3. If he accepts estimated review, update the release notes and the band/twelve-layout jobs so they fail closed on a false "verified" flag and pass only when the notes carry that label. Do not weaken the check into a silent pass.
4. Ask him to watch the 16-panel baseline, or render a new one from `4f7ad6c` and wait for his yes. No yes, no tag.
5. Build the release APK and the Windows package you can actually sign. If you still cannot sign, the release notes say unsigned and point at the draft checksums above. Do not rename a debug APK into `Helix-Sequencer-v1.4-beta-Android.apk` without the version fields matching.
6. Tag, upload checksums, then write `WEBSITE_RELEASE_HANDOFF.md`.
7. Leave Infinity, the phoneme fixture song, and CooperativeShowDirector out of the tag.

## Files

- `BETA_1_4_RELEASE_CHECKLIST.md` — session log. Trust this handoff where they disagree.
- `tools/stemless_duet.py`, `tools/phoneme_vocal_export.py`, `tools/separate_phoneme_vocals.py`, `tools/vocal_analysis_fixture.py`
- `core/vocal_separation_manifest.py`, `core/independent_vocals.py`, `android/app/src/main/python/helix_mobile.py`
- `core/composition_governor.py`, `core/effect_engine.py`, `xlights/xml_io.py`
- `tests/test_android_vocal_bundle.py`, `tests/test_phoneme_vocal_export.py`, `tests/test_vocal_separation_manifest.py`
