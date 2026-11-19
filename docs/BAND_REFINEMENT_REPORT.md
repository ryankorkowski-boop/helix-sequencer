# Helix Band refinement review — 2026-10-12

This is an **opt-in review build** for all four requested performers. The primary branch is unmerged. Source implementation commit: `37ffbedde20a9f41f6723223d7fd6a65ceba2fb9` on `feature/band-musical-refinement-20261012`.

**Native export scope:** the delivered XSQs are real xLights **384 × 216 virtual-matrix shows** using Video effects and bundled media. They reproduce the continuous Helix artwork/mesh animation on a matrix. A separate stationary physical-performer prop export remains unfinished. Video D is a screened pitched-percussion diagnostic; confirmed xylophone identity is not claimed.

## Before and after

| Performer | Defect or limitation | Changes | Remaining uncertainty |
| --- | --- | --- | --- |
| Drummer | Moving shoulder anchors alone did not create connected temporal joint motion; held poses could look unnatural. | Connected shoulder–elbow–wrist contours below the scarf; fixed-length original gold shafts; anticipation, contact, rebound, recovery and continuous fast passages. Independent cymbal decay; adjustable idle/strike light. | Three unplayable hand requests remain surface responses. Original body/kit remain planar source artwork. |
| Bass | Source-derived notes existed, but plucks were one-sided and neck positions changed abruptly. | Alternating source-owned pluck envelopes, clearer connected hands, short fretting transitions, stable holds and warm independently visible strings. Kick events do not generate notes. | Pitch/onset estimates remain from retained separate-stem caches. Finger identity and slides are not inferred. |
| Guitar | A supported contact could change unnecessarily during a held chord. | Stable supported dominant contact; strength-based reselection on an attack; restrained metallic strings, smaller picking and broader chord strokes. | Alternating directions are artistic rather than recovered real up/downstrokes; full chord fingering is not implemented. |
| Xylophone | Mallet gates were combined with unrelated broad-bus CQT pitches and piano events. | Dedicated mallet player with literal MIDI 60–84 bars. Use each screened attack's own measured peak; reject weak/vocal-like/out-of-range candidates. Connected mallets contact bars, travel between notes and rest. Piano remains separate. | A spectral peak may be an overtone or another instrument. Exhaustive simultaneous-note transcription is unverified. |

## Source protection and implementation

The most recent band implementation was the October 10 reassessment `4aca41c5ae83a9f4c838e69393380f1dd0817ae6`, incorporating the shoulder/readability work. The default branch was older. The branch inventory and preservation receipt are bundled.

Existing source art, pose specifications, generated layers/XMODEL, audio, layouts, previous compositors, accepted NoteEvents, polyphonic drum predictions and lyric/duet lanes were preserved. No engine replacement or blind branch merge occurred. The new code is a reversible opt-in path.

Drummer links are 39 px upper/lower segments with a 55 px source-art shaft. Hand travel is checked independently of detection: supported snare reassignments can use the other hand; otherwise motion abstains and the detected surface event stays in the audit/lighting. The dry review has 213 deduplicated hand gestures, 18 explicit snare hand reassignments and three motion abstentions. These are animation counts, not detection accuracy. The original 289 accepted source events and 309 cached family predictions remain evidence. Twenty cached unresolved positions plus three independent source-only novelty candidates stay untyped; no tom position is invented.

Idle body gain defaults to 0.72, instrument gain 0.40, idle arm gain 0.58 and strike gain 1.35. Body visibility and local strike light are separate. Cymbal decay never holds a stick aloft. CLI controls: `--idle-brightness` and `--strike-brightness`.

Bass/guitar retain separate-stem note velocities, holds, releases and distinct playable string routes. Source attacks own gestures; held positions stay stable. String vibration is a visible resonance envelope, not acoustic-frequency simulation. Mallet candidates require concentration ≥ 0.20, decay ratio ≥ 1.35 and vocal similarity ≤ 0.65 plus supported source energy. Out-of-range pitches abstain rather than octave-folding.

Output inspection found and corrected weak bars, an occluded mallet grip, abrupt wrist jumps, mixed-frame-rate montage truncation and AAC padding drift at cuts. Superseded pilots are excluded.

## Audio provenance and excerpts

| Recording | Original source window | Use |
| --- | --- | --- |
| Original dry WAV | 0.00–38.32 s, complete | A/B and beginning of E |
| Wire Tree | 164.00–182.00 s | Full stage |
| Candy Cane Chaos | 168.00–186.00 s | Dense full stage |
| Festivus (Remastered) | 26.00–44.00 s | Mallet diagnostic/full stage |
| 49 (Remastered) | 115.00–133.00 s | Bass/C |
| Who Knew (Grinch's Redemption) (Remastered) | 101.00–119.00 s | Guitar/C |

Original dry WAV SHA256: `4cd9ee35b65d359aa44ac4c9e01a256bbcaf3297458340fc512084bae1463913`. Original recordings are unchanged. Retained render inputs come from the SHA-pinned repository ZIP in `evidence/band_instrument_review/remote_render_request.json`.

MP4 audio is AAC. The original 38.32 s is fully retained; frame rounding makes A/B 38.333 s at 30 fps and the dry montage section 38.35 s at 20 fps. Individual excerpts are 18 s.

## Verification

- Local focused checks: **38 passed**. Local full suite: **1,266 passed, 12 failed, 5 skipped**. All 12 failures reproduce on untouched baseline: outdated Helixia prop/band-spec expectations, preview-mux mock/API failures, old snowman/reactive-drummer fallback expectations and an XSQ fixture expectation. Exact test receipts are checked into `evidence/band_refinement/test_results.json`.
- Actual HPSS analysis of the original dry mix produced 216 events (kick 24, snare 4, hat 127, cymbal 58, tom 3). Retained ADTOF separated-input predictions total 309 (kick 67, snare 53, hat 138, cymbal 17, tom 34). **These counts do not rank accuracy:** inputs differ and independent labels are absent. The accepted polyphonic path was retained.
- Local final outputs: 10 MP4s, **7,747 fully decoded frames**, 40 decoded representative frames visually inspected. Fixed dry limb/shaft lengths verify across all rendered joint frames.
- Actual xLights 2026.18 rendered 10 matrix shows, **6,981 native 50 ms frames**, with corresponding pixels compared at matrix resolution. Mean per-show differences are about 2–3 on an 8-bit RGB scale, reflecting scaling/encoding.
- Independent waveform checks verify source excerpts and all montage cut offsets. Minimum corrected local montage correlation: **0.998168**; dry original-to-MP4 correlation: **0.999286**. This measures audio correspondence, not instrument classification.
- The local environment disconnected during final packaging. Delivery was rebuilt independently on GitHub Actions using the same protected branch and pinned inputs. The fresh remote output/native/soundtrack receipts accompany the downloads. The remote workflow repeats focused tests, renders, full decoding, geometry and native/pixel/audio checks.

No listening-based verification, human-labeled precision/recall, verified instrument identity or hardware-controller proof is claimed.

## Deliverables and playback

A: full synchronized drummer comparison (38.333 s). B: complete dry test with family indicators (38.333 s). C: bass/guitar close-ups (36 s). D: Festivus pitched-percussion diagnostic (18 s). E: full-band montage (128.35 s). Five additional individual 18 s source studies are included.

Each `xlights/<video-name>/` folder is a separate show. Keep its XSQ, `xlights_rgbeffects.xml`, `xlights_networks.xml`, `media/performance.mp4` and `media/soundtrack.wav` together. Select that show directory in xLights, open the XSQ, render and preview. No controller output is configured. The bundled MP4s also play directly on a phone. A bare XSQ without its media is insufficient.

The bundle includes screenshots, exact hashes, validation receipts, source commit, checklist, report and reproduction handoff. Published assets are review artifacts, not a primary-branch merge.

## Remaining work

Raw six-stem WAVs and independently reviewed event labels are needed for true drum-family/ghost-note, bass-articulation and mallet-identity evaluation. Do not promote a ringing spectral peak to a confirmed xylophone note or slide.

Detailed fingers/chords, real stroke direction, faster source grids and reliable polyphonic mallet classification remain further work. For separate physical props, build an explicit stationary pose/channel contract from the reviewed geometry and verify fresh native/controller output. The existing generic member runtime states were not fabricated into full production coverage.

User artistic and musical approval remains pending. Continue from `MASTER_TODO.md`, `docs/BAND_REFINEMENT_CHECKLIST.md` and `docs/BAND_REFINEMENT_HANDOFF.md`. Do not merge primary development before review.
