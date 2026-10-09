# HELIX MASTER TODO & AGENT HANDOFF LEDGER

> Canonical project roadmap and cross-agent handoff layer.

## 2026-10-09 — Android MP4 previews (generating; layout packaging accepted)

Goal: provide downloadable phone-compatible MP4s from the working portable show files. User says to consider the rest a pass and requests previews while back on Android; layout/package acceptance is recorded as passed, laptop launch is deferred rather than falsely verified, and drummer acceptance remains separate. Branch `feature/android-native-previews` starts from portable delivery `f826cb3`.

Changed files/modules: `tools/render_portable_xlights_previews.py`, `tests/test_portable_xlights_previews.py`, `docs/ANDROID_XLIGHTS_PREVIEWS.md`, verification evidence and this ledger. New behavior: source-hash-checked previews from the exact verified FSEQs, 960×540 at native 20fps with H.264/yuv420p and AAC soundtracks, seven silent original studies, five common-time comparison reels, phone-friendly gallery and movie-only download ZIPs. Preserved: all production show folders, source recordings, cue timing, palettes, geometry, native effects, saved favorites, 22 concept artworks and drummer work. Aurora remains a 24-second study.

Evidence/checklist: [x] read rules/ledger and verify native inputs; [x] record user's acceptance and deferred laptop launch; [x] 11 focused preview/package tests pass; [ ] all 37 previews encoded and completely decoded; [ ] all 30 soundtracks correlated with preserved originals; [ ] decoded frame inspection; [ ] five comparison reels; [ ] ZIP CRC/hash/inventory; [ ] focused validation and feature-branch handoff.

Limitations/risks: geometry previews project actual xLights channel values and are not screen recordings; custom-node coordinates are exact while stock review paths remain illustrative. Lower resolution favors Android viewing. Native full-song timing and original soundtrack are preserved. Laptop audio-device playback and physical installation are not newly verified. No controller output or new concepts; no drummer acceptance claim.

## 2026-10-08 — seven portable xLights shows (verified; laptop launch pending)

Goal: consolidate matching complete sequences and copied original media into independent show folders, then open Fire & Ice / Wire Tree in the user's laptop xLights. Branch `feature/portable-xlights-shows` starts from concept handoff `b56f2cf`. This executor is cloud Linux without laptop desktop access, so laptop GUI launch and audio-device playback remain pending.

Changed modules: portable show preparation, local render-then-open launcher, native verification, focused regressions, reproduction documentation, checked-in verification evidence and this ledger. Preserved: all permanent favorite/model/layout/asset/source-audio bytes, corrected native effect mapping, cue timing and palettes, concept art and drummer logic. Prepared copies contain matching model bindings, portable media references and no configured output networks. Native rendering exits xLights, so the launcher opens the desktop separately after verifying the full FSEQ duration.

Evidence: 30 complete corrected Prime music exports across six flavors, plus seven preserved 24-second studies including Aurora. SHA-pinned xLights 2026.18 rendered all 37 XSQs into native FSEQs: 72,384 full-song frames plus 3,360 study frames. Every RGB model received lighting, controls remained dark and durations matched. All 37 sequences, media, assets and model/submodel references passed validation after extraction of the final ZIP into a different directory with spaces. The archive contains exactly 37 XSQs, 37 FSEQs and 30 copied MP3s, passes CRC validation and matches prepared source bytes. All 57 focused tests pass: eight new packaging/launch/native regressions plus 49 existing layout/export checks. All 85 favorite baseline files and five source recordings remain unchanged.

Cloud GUI evidence: xLights opened the complete Fire & Ice / Wire Tree XSQ with its full soundtrack waveform and matching window title. Cloud virtual-display evidence does not establish laptop launch or audio-device playback. Detailed native proof, screenshots, inventory and handoff live in `outputs/Helix_Portable_Shows/`; archive hash is in `outputs/Helix_Portable_Shows.archive.json`. Checked-in proof is `evidence/portable_xlights/verification.json`; reproduction is `docs/PORTABLE_XLIGHTS_SHOWS.md`.

Validation correction: the first verifier falsely rejected Aurora because xLights omitted unused trailing control channels. The corrected verifier accepts only that omitted control tail as implicit zero, still rejects missing RGB channels and passed the subsequent audit of all 37 native renders without changing show inputs. GUI startup also creates `Backup/OnStart` sequence copies; packaging excludes backup/cache directories while preserving them locally, with a regression checking the exact archive sequence count.

Checklist: [x] corrected complete exports; [x] seven self-contained show copies with media; [x] native rendering, coverage, duration and control audit; [x] final ZIP relocation and source/favorite preservation checks; [x] local render-then-open launcher and cloud GUI proof; [x] focused regressions; [ ] laptop GUI launch and audio-device playback; [ ] user musical/artistic acceptance.

Remaining limitations: Aurora retains its actual short study; no full-song Aurora export is fabricated. Laptop executable discovery, installed-version compatibility, first-run prompts and Python availability require local verification. No complete repository test-suite pass is claimed. Musical/artistic and physical installation acceptance remain open; drummer acceptance is separate. The 22 newer concepts remain artwork awaiting selection. No physical controller output was enabled. Do not mark laptop launch complete from cloud evidence.

## 2026-10-08 — three saved favorites and twenty-two image-only concepts (review ready)

Goal: retain user-selected Fire & Ice, Enchanted Grove and the original first Helix Aurora showcase for the ultimate goal bundle; create additional artwork for selection before building new native layouts. User scope expanded from12 concepts to22: six spatial/true3D, six abstract/layered, and two each extreme traditional, arena stage, 1964 Impala, Gothic church and pontoon designs. Describe actual 3D-to-xLights feasibility using existing native evidence.
Changed files/modules: `showcase/favorites/` selection/hash manifest and notes; `showcase/concepts/2026_10_08/` eleven paired plates, three unchanged favorite reference PNGs,22 briefs, generation prompts, offline gallery, feasibility notes and delivery verification; this ledger. Existing85 favorite-native files, all other layout/XSQ/assets, five-song batch, audio logic and approved drummer are preserved byte-for-byte.
New behavior: durable favorites pinned to baseline15a7e5450d2798eacc57b821267d6a526428884a; an unchanged three-show archive; individually numbered concept views and a browser-local shortlist. No new xLights XML/XSQ/FSEQ/XMODEL/OBJ, actual model coordinates, channel allocations, audio sequences or native renders. Procedural XYZ export is already demonstrated; arbitrary-mesh-to-wired-layout conversion is not claimed.
Checklist: [x] inspect rules/ledger and prior favorites; [x] pin all three existing favorite shows; [x] generate spatial01–06 and abstract07–12 plates; [x] generate themed13–22 plates; [x] document evidence-based 3D feasibility and a future small-module assessment; [x] offline Chromium filters/modal/shortlist/mobile checks; [x] final archives/link/image/favorite-byte checks; [x] save/push feature branch; [ ] user chooses concepts before implementation.
Evidence:85 favorite files hash-pinned;22 concepts on11 unmodified generated plates conserve generation credits; native Aurora108-model/27-family import and480-frame RGB proof referenced rather than rerun. Offline Chromium checks all22 cards, seven category filters6/6/2/2/2/2/2, three favorite references, image decoding, both panel sides, modal Escape, shortlist persistence/copy and390px mobile layout; no JavaScript errors. Local gallery screenshots inspected. ZIP CRC/all packaged bytes and11 original-image copies verified; all85 favorite archived files match originals. Concept ZIP contains no native-layout files. Artwork/notes commit8b5679e pushed to `feature/layout-concept-rounds`; CI intentionally skipped for this art/docs-only request. Packages live in `outputs/layout_concepts/`; source art/gallery permanent in `showcase/concepts/2026_10_08/`.
Limits/deferred/risks: art is not validated geometry or structural engineering. Terrain, source dimensions, supports, spacing, controllers, electrical/marine implementation and practical optical effects remain design work. Novel car/building/boat mesh sampling and native validation are deferred until selection. Existing stock review geometry is illustrative and existing DMX/servo limitations are documented in the feasibility brief. Do not infer user approval from a shortlist or rendered art. Other four flavors and the earlier drummer's outstanding acceptance are retained. MASTER_TODO remains the next-agent handoff authority.

## 2026-10-08 — five uploaded songs across the new showcase layouts (active)

Goal: run the user's Wire Tree, Tinsel Sawtooth, Frostbitten Fingerboard, Holly Steel Run and Bell Circuit Carol uploads through active Helix Prime on the six new layouts; default scope is all30 combinations, optional pairing preference asked asynchronously. Source uploads verified as readable48kHz stereo MP3s, durations256.56/126.96/48.144/98.76/72.84s. Preserve source media bytes, native layouts/palettes/assets, original Aurora and all drummer work. No invented drum identities, new detector tuning or synthetic music timelines.
Modules/new behavior: `core/audio_run_cache.py`, optional cache integration in `core/effect_engine.py`, focused `tools/run_showcase_audio_batch.py`, native adapter, cached native-value compositor, soundtrack/package/review helpers, tests, source-hash evidence, docs and dedicated native-pilot workflow. One verified song/config cache reuses audio/harmonic/stems/multiband across six layouts (five hits per stage/song); mutable layout profiles copied. No serialized analysis cache. Source recordings preserved byte-for-byte in evidence for reproduction. Do not promote the fixed30-second orchestration seed or reuse the24-second showcase demonstration as musical choreography.
Findings/fixes: Prime placements extended beyond24s but its inherited sequence head remained24s/Animation; native adapter now writes full Media duration and native EffectDB/palette/submodel references. Numeric-name discovery omitted negative-side motifs; explicit routes recover most, while only otherwise unrouted paired candy/snowflake/crown RGB motifs share existing sibling choreography with their own authored palette. No new audio onset, retiming, instrument assignment or overwrite of independently placed motifs. Generated mixed groups exclude controls; native Pictures/Text have actual content sources. Unchanged model/channel/geometry nodes are tested. Exact native pixel dots retained; half-resolution soft halo reduces movie processing cost.
Evidence in progress:30 full-song native XSQs generated with353,944 initial Prime effects before scoped RGB mirroring. All five sources have four cached analysis stages with five reuse hits each. Initial native pilot spans963×50ms rather than480frames; full Wire Tree spans5131frames.107 final focused/native-layout/engine/export compatibility tests pass locally (39.06s), including source/config cache isolation, original-vs-wrong soundtrack, portable ZIPs, late native attacks, paired RGB routes and pixel-identical cached projection outside the footer. Broader compatibility suite:45 passed, one existing legacy vocal-fixture failure (`tests/test_xsq_validation_tool.py::test_valid_fixture_passes`, unchanged validator requires Element rows while fixture has legacy effect rows). Do not describe the full repository as green. Updated focused checks/native30-run proof pending. Active processing/handoff in `outputs/showcase_audio/HANDOFF.md`; documentation `docs/SHOWCASE_AUDIO_BATCH.md`.
Checklist: [x] inspect pipeline/layouts and verify five uploads; [x] clean music templates and pilot native playback; [x] all requested full-song sequences; [x] all native renders and actual-audio previews; [x] native/frame/duration/audio and focused regression checks; [x] review gallery/packages and push; [ ] user musical/artistic review.
Progress follow-up: pushed implementation3b40d6949ceb0703e767fd47c1a264a783100b41. Dedicated native/audio workflow37814126665 SUCCESS, uploaded pilot artifact11566916216 downloaded: everyXSQ/FSEQ/MP4/layout/source hash matches;963native frames, all93RGB models active, controls dark, source-audio correlation.9993269794. GeneralCI37814126649 andBetaCI37814126842 SUCCESS (general regression audit is non-gating; do not imply every legacy test passes). Unrelated inherited demo/birdsong artifact workflows canceled to conserve resources. First four local Wire Tree previews verify full5131frame duration/allRGB coverage; original-vs-AAC correlation.999849. Remaining full previews in progress. Spawned CPU workers replace thread-only composition. Further grid-aligned empty-margin cropping is byte-identical to the prior compositor for all six layouts × both halo modes, with faster frame production; strongest native frame selects common-time comparison excerpts without changing song lighting. Complete review bundle includes all30 movies/native shows plus offline relative-link gallery; source-bound five importZIPs remain separate. All six Wire Tree previews and its six-layout comparison/importZIP now ready. One Frostbitten/Neon CI movie/FSEQ is reused locally only after exactXSQ/layout/source hash equivalence, with provenance recorded, avoiding a repeated render.
Native alias audit supersedes the first20 previews and earlier green native CI: Frostbitten/Masquerade crown5 had12 Ramp cues but zero native frames. Pinned2026.18 EffectManager contains noRamp effect; native six-second same-target probe measured Ramp0/20lit frames vs nativeOn19/20, identical existingOn control and SingleStrand values. Across30 exports,111,433 Ramp cues (30% of367,246 placements after RGB mirroring) were silently unrenderable. Adapter now converts them to nativeOn attack/decay100→0 when an explicit envelope is absent; existing start/end settings preserved. Single Strand canonicalized toSingleStrand (pinned probe confirms its tooltip alias already renders identically). Unknown families now fail closed against the native catalog at export and before render. No audio analysis/event onset/layout-node change. Source cue count unchanged. All30 native renders/videos must be regenerated; old20 movies/FSEQs/proofs preserved under `outputs/showcase_audio/superseded_before_native_alias_fix/`, manifest `native_before_alias_fix_manifest.json`. Probe `test_runs/showcase_audio/native_alias_probe/proof.json`. First Wire comparison shared in chat is superseded, not accepted. Dedicated CI now includes `tools/audit_showcase_audio_native_aliases.py` rather than treating all-model coverage as sufficient.108 relevant tests pass (70.15s); reproducible pinned native alias tool passes. Sorted native RGB indices are cached before per-frame compositing; frame values remain covered by all-six-layout reference tests. Alias implementationa3b39ba1e28cda203e45991f328c8a6b84d5bb25 pushed. Environment reset stopped the active batch after two corrected Wire Tree movies; workspace checkpoints remain intact. Resume uses detached processes and shorter full songs first, preserving source/gallery order and existing verified files. Corrected nativeCI37818565266/generalCI37818565193/BetaCI37818565229 SUCCESS; artifact11569095042 downloaded, allXSQ/FSEQ/MP4/layout/source hashes verified and exact localXSQ/layout match. Native963frames/all93RGB models/controlisolation and source correlation.9993269794 verify, plus the native alias probe. CorrectedFrostbitten/Masquerade crown5 now34lit native frames/peak255 vs0. Before/after JSON proves every one of367,246 cue intervals/targets/palettes unchanged, and allnonRamp settings unchanged. These reports enter the complete review bundle. All correctedFrost/Bell/Holly six-layout runs now ready; remainingTinsel/Wire in progress.
Final technical evidence: all30 corrected full-song1280×72020fps MP4s, nativeXSQs/FSEQs and72,384×50ms native frames verify; everyRGBmodel receives real native lighting, controls remain dark, all native names valid and frames animate. Source originals preserved;30 soundtrack comparisons cover all five originals, minimum correlation.9988084398. Five24s1920×72020fps common-time comparison reels have minimum source correlation.9989922173. Five importZIPs and673MiB fullreviewZIP verify CRC; all100 gallery links resolve inside fullreviewZIP, including30 nativeXSQs/FSEQs and all full movies. Five contact sheets are decoded from actual full MP4s and inspected;15 reviewreel frames decoded for finalinspection. Original Aurora/permanent six layouts/drummer files untouched.108 focused tests pass; corrected native+general+BetaCI success documented above, with all963local/remote corrected pilot frames byte-identical. Checked-in evidence under `evidence/showcase_audio/`; outputs/gallery `outputs/showcase_audio/index.html`, full bundle `Helix_Five_Songs_Six_Layouts_Full_Review.zip`. The early incomplete Wire comparison is overwritten by the corrected final clip; superseded30%missing-cue evidence remains archived. User musical/artistic approval remains open; no musical-correctness or physical-drummers-repaired claim.
Limits/deferred/risks: technical delivery complete; user review pending. Existing general-song inference remains unreviewed; no musical-correctness claim from scores or CI. Native control fixtures stay isolated from RGB sequencing. Each track requires one source-verified analysis reused across layouts; do not perform30 costly independent analyses. Preserve native DNA submodel layer schema, disjoint channel addressing and portable media paths. See earlier layout and drummer acceptance limits below.

## 2026-10-08 — six additional showcase flavors (built; artistic review pending)

Goal: respond to the user's request for a half dozen different layouts, preserving Aurora as the seventh/original option. Six distinct compositions: Neon Circuit, Enchanted Grove, Celestial Orrery, Fire & Ice, Crystal Lagoon and Midnight Masquerade. Each retains all27 native families, many real spiral trees and volumetric DNA with full addressable rungs.
Modules: new focused flavor composition and collection build/gallery helpers, shared metadata-aware exporter/preview/audit/package, flavor contract tests, native collection artifact workflow and documentation. Existing Aurora behavior and permanent show must remain byte-identical; no user layout, drummer logic/assets or controller configuration changes.
New behavior: independent spatial arrangements, silhouettes, hero shapes, palettes and native-prop placements; six separate import shows, images, interactive viewers, native-lighting videos and ZIPs, plus a comparison gallery/contact sheet. Reuse the verified stock catalog and native serialization rather than cloning the pipeline.
Checklist: [x] six artistic compositions; [x] native/channel/geometry and Aurora preservation tests; [x] comparison images/gallery and six packages; [x] native xLights import/render and RGB audit for every flavor; [x] six decoded lighting videos/browser review; [x] CI/push/delivery; [ ] user artistic review.
Evidence:64 relevant new/existing layout tests pass (two pre-existing deprecation warnings). All six pinned2026.18 native renders contain480×50ms frames and correct palette values for every RGB node:198,395 pixels total. Native totals: Neon104 models/36 spirals/13 DNA; Grove100/36/12; Orrery105/40/13; Fire109/40/16; Lagoon104/40/12; Masquerade106/36/12.228 spirals and78 DNA overall. Aurora export remains byte-identical. Contact sheet inspected; six full native-value videos and the collection tour are generated. Offline compact archive has working links and recomputed checksums, excluding videos/caches/backups; individual ZIPs carry movies. Permanent imports/reviewers/proof in `showcase/flavors/`; reproduction/limits in `docs/SHOWCASE_FLAVORS.md`.
Final evidence: all six1600×90020fps480-frame24s native-value MP4s and1/5/12/20s decoded frames inspected;36s1280×72020fps720-frame tour and3/9/15/21/27/33s frames inspected. All six WebGL viewers have correct selectable model/pixel counts, DNA/spiral filters, selection and camera controls, no JS errors; longest title fits/wraps on390px mobile. Local individual package checksums and210 compact-collection hashes/links verify. Implementation536dcca52e5f686643f396bd9e9758efacfc4cd0 pushed on `feature/showcase-six-flavors`. Native workflow37794173215 SUCCESS:64 tests, six pinned renders/audits/videos, eight artifacts. Downloaded compact artifact11557618824 and review11557958280; all210 remote hashes and gallery links verify, XML/XSQ/manifest/inventory identical, all480 decoded native frames byte-identical for every flavor; uploaded36s tour decoded and inspected. Remote compact ZIP SHA256:f7fed219f594ef86ba80a058a0d1c4d6e1fa4baf964982ca7b5b3a39c1fadd36. Durable collection: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557618824 ; review: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37794173215/artifacts/11557958280 . Final handoff/reports: `outputs/showcase_flavors/HANDOFF.json`, `test_runs/showcase_flavors/ci_final/remote_verification.json`, `docs/SHOWCASE_FLAVORS.md` and checked-in evidence JSON. Artist/user review remains the only open layout gate.
Limits/deferred/risks: source metadata/filenames/palettes propagate to XML/XSQ, preview, package and audit. Affine moves update native screen locations/PointData as well as review geometry. Native headless import/render is checked; no new six-layout native GUI audit or screen recording claimed. Stock paths remain illustrative, custom nodes exact, videos use native values in a geometry compositor without audio. Installation engineering and drummer musical acceptance remain deferred/open as recorded below. Existing layouts, original Aurora and drummer files have no changes.
Image delivery follow-up: user requested one image of each layout. Regenerated six labelled1920×1080 night PNGs with the existing geometry renderer under `outputs/showcase_flavors/images/`, with `image_manifest.json`, and packaged `Helix_Six_Layout_Images.zip`. All six PNGs verify and are byte-identical to the permanent reviewed layout images; ZIP CRC and six-file inventory pass. No renderer, layout, palette, musical logic or visual-contract change; user artistic review remains pending. Native control fixtures and stock-coordinate limits above still apply. Checklist: [x] six full-size images; [x] fidelity/file checks; [x] image-only download package.

## 2026-10-08 — ultimate native-model showcase (built; artistic review pending)

Goal: build the user's artistic ultimate showcase with every creatable native xLights model family, many genuine spiral trees and double-helix sculptures. This new layout task supersedes active drummer work for this session; drummer preview approval and false-hi-hat review remain open above/below, not marked complete.
Modules: focused `models/ultimate_showcase.py`, export/preview helpers, build/native-audit CLIs, eight new layout tests, `docs/ULTIMATE_SHOWCASE.md`, permanent `showcase/Helix_Aurora/` import show and `.github/workflows/helix-ultimate-showcase-preview.yml`. Archive the old builder and workflow: their overlapping channels, invalid singular model names, Z-up spirals and obsolete placeholder drummer are intentionally superseded only for this separate showcase.
Preserved: root/allmodels/Helixia layouts, existing layout builders/contracts, all approved drummer assets and audio logic; no show/controller/hardware configuration overwritten. The new show uses xLights' X-right/Y-up/Z-depth convention, absolute disjoint channel allocations and portable assets. The old append-to-root behavior is archived because it cannot produce a valid independent show.
New behavior: Helix Aurora:108 models,48 groups,27 native families,36 genuine native spiral trees,12 volumetric DNA forms,32,277 RGB pixels and96,929 disjoint channels. Cyan/magenta/gold DNA cathedral and rungs, graduated mint/violet forest, orbital halo, gates, infinity promenade, customized native gallery and original kinetic assets. Includes saved native overview camera, portable relative paths, 12 DNA model exports, offline orbit/filter/selection/pinch viewer and24s XSQ/MP4 lighting study. Native DMX/control types remain separate from RGB effects. Bundle hashes include final proof and exclude xLights backups/caches.
Native findings: actual2026.18 rendering exposed alphabetic channel reallocation from No Controller and silent black DNA from incorrectly nested submodel effect layers; both corrected. Corrected engine-unit radii/heights, reverse cane field, negative icicle direction, a boundary star node and oversized advanced-head mesh. The final480-frame decoded native timeline is identical after the non-RGB camera/fixture changes, so the delivered native-lighting MP4 remains current.
Evidence:43 new/existing layout checks pass (two pre-existing deprecation warnings), xLights GUI recognizes108 models/all27 families and preserves108 start channels; no controllers configured. Native FSEQ480×50ms, all97 RGB models/32,277 pixels have correct palette values at20s. Full1600×90020fps24s MP4 and decoded1/5/12/20s frames inspected; browser32277 points, all108 selectable models,12 DNA/36 spiral filtering, selection and mobile pinch pass without JS errors. Native proof, attributes, screenshot, hashes and ZIP live under `outputs/ultimate_showcase/`. Five stale placeholder-drummer tests reproduce unchanged on baseline3cbd736; do not revive generic sticks/models to pass them.
Checklist: [x] inspect native factory/serialization and legacy layout; [x] geometry/export; [x] images/video and portable bundle; [x] native GUI/headless load/render and decoded frames; [x] focused/existing layout and browser checks; [x] feature-branch commit/push, native artifact CI and downloaded ZIP verification; [ ] user artistic approval.
Remote continuity: build committed/pushed as2c63f73495e0889690520b9e4f76a0865c311361 on `feature/ultimate-helix-showcase`. First native artifact run37731056719 passed43 tests but the minimal Ubuntu runner lacked `libEGL.so.1`; explicitly install EGL/Mesa/OpenGL runtime dependencies before rerunning. No layout/lighting change. Cancelled only the unrelated Flow/Remote/Birdsong artifact runs on this newly created branch to conserve runner work; standard Beta/Helix CI remains active.
Final remote evidence: runtime fixea1692c5bf3fb5ac649e1085f3234ed244f7e984; native showcase run37731290603 SUCCESS (43 tests, pinned2026.18 headless render,24s MP4 and all32,277 RGB pixels). Standard Beta CI37731056603 and Helix CI37731056726 also SUCCESS on the layout implementation. Downloaded artifact11530225902 using the GitHub connector after the CLI redirect returned403;35 file hashes verified, XML/XSQ/manifest/inventory identical to local, all480 decoded native frames byte-identical, uploaded1600×90020fps480-frame MP4 and decoded20s image inspected. CI ZIP SHA256:5837cc843f870390884fdaf5b73fab605d41af1797c3f6b4eae70df1ee88ccf4. Durable download: https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/37731290603/artifacts/11530225902 . Local full bundle additionally contains the108-model GUI attribute/screenshot proof and documentation. Final handoff/proof JSON in `outputs/ultimate_showcase/Helix_Aurora/`; generated CI download in `test_runs/ultimate_showcase/ci_final/`.
Limits/deferred/risks: stock coverage follows pinned xLights factory6ceddc6b; use xLights2026.18+. Custom grid positions are exact, stock review paths illustrative. MP4 uses native channel values in a geometry compositor, not a native screen recording; control/servo/DMX rendering is reviewed in xLights. Snowflakes are actual native Custom props. This large, scalable design is not controller wiring, power/structure design or a surveyed site. Existing user layouts/drummer remain preserved; drummer musical and hi-hat approval remain open. Current work/handoff and reproduction: `docs/ULTIMATE_SHOWCASE.md` and this master entry.

## 2026-10-08 — user-heard high-tom roll lost at the identity gate

Goal: address the user's missed consecutive notes near the end of Dry Drum Test using original-source evidence, preserving the reviewed fill and approved physical drummer. Continuing the existing task; double kick/flailing arms remain deferred questions.
Finding: generic-tom candidates were discarded by the unknown-tom identity gate. The user specifically identifies the missed 32–34 s sound as a high tom/timpani; this supersedes initial diagnostic snare/hat guesses from ADT_STR. Its context-dependent, contradictory predictions are retained as rejected evidence only. The actual source has a roughly500Hz ringing articulation outside the isolated classifier's60–400Hz pitch search, plus brighter and quieter attacks from the same reviewed passage; simply extending pitch range cannot fix the missing class calibration or stem body loss.
Changed modules: optional `audio/drum_source_calibration.py`, transcription import/integration CLI, exact-source exemplar/rejected-probe evidence, independent waveform timing anchors/tests, repeat-tom pose hold mapping, diagnostic audit, dry-audio workflow and documentation. Onset detection, attack timing, HPSS, scheduler and pixel compositor remain untouched.
Preserved: immutable raw model transcript; every original family/timestamp/confidence/velocity; all accepted non-tom decisions; the four reviewed9–11s tom identities; all1,022 Helix musical events; eight targets/three toms, dim body, intact target-specific strikes, alternating snare, transparent kick/snare shell, cymbal shimmer and32%pedal. No synthesized onsets, fabricated bus, tom rotation or new hi-hat hits. The only existing cue-duration change is a brief rest between rapid same-target tom strikes.
New behavior: compare original attack/body log-frequency spectra with user-labelled source exemplars in the audited32.3–34s scope. Distinct matches resolve HIGH; ambiguous high/mid identities still abstain. Preserve original rejection and all class scores/margins in the audit; tom-class confidence is spectral similarity, not a correctness probability. Ten existing attacks at32.36–33.77s now reach TOM_HIGH. Cap rapid same-tom pose holds to leave50ms rest, preventing a roll becoming one continuously lit contact pose; isolated holds and other instruments stay unchanged.
Evidence:140 relevant tests pass locally (87.70s), plus final six calibration/hold regressions. Seven held-out waveform rise anchors cover the user-heard high-tom passage. All275 dry non-tom audit rows, all1,022 Helix musical audit/analysis rows and all16 approved physical asset bytes are identical. Dry sequence now contains289 placements, including10 restored HIGH strikes; counts describe the change rather than an acceptance quota. Full38.32s original-audio MP4 and6s ending clip generated; eight full decoded frames include earlier toms, HIGH strike/rest/restrike and later roll strokes. Soundtrack correlations .9959113596 full/.9922441795 ending. Before/after JSON/CSV/source plots and a side-by-side ending video live in `test_runs/drummer_dry_ending/`; reproduction is in `docs/DRUMMER_ENDING_TOM_RECOVERY.md`.
Checklist: [x] source/activation/rejection audit; [x] investigate and reject second-model family errors using user listening; [x] scoped source calibration and hold/rest fix; [x] source anchor/abstention/preservation tests; [x] before/after report, XSQ/full actual-audio MP4 and decoded strikes/rests; [x]140-test relevant suite; [ ] push/CI and downloaded artifact verification (final remote status in local HANDOFF/FINAL_VERIFICATION); [ ] user preview approval.
Limits/risks: user labels the passage sound and earlier descending order, not every individual event. Lower-pitched change near33.93s and other unreviewed toms remain unresolved rather than inventing destinations. Recording-specific timbre calibration is not a global arbitrary-song solution. Native xLights playback and earlier false-hi-hat behavior remain open. Unseen articulations may require further source-labelled calibration; ambiguous identities abstain. Same-tom gaps below100ms retain old cues because the native50ms frame cadence cannot show full50ms strikes plus50ms rests.

## 2026-10-08 — user-reviewed descending tom fill in Dry Drum Test

Goal: place the audible high → mid → floor tom passage identified by the user at roughly 9–11 s, using the approved mirrored physical targets (viewer right high, viewer left mid, lower viewer left floor). Double kick layout and Steve-style arm motion were explicitly questions; defer implementation of both.
Changed modules: `audio/drum_review.py`, transcription import, integration CLI, source annotations/anchor tests, dry-audio workflow and documentation/checklist. No detector thresholds, fabricated onset grid, or rotating unknown tom destinations.
Preserved: original inferred transcript as audit evidence; all non-tom events, timestamps, confidence and velocity; the complete Helix song performance; eight targets/three toms, cymbal shimmer, dim body, full strike overlays, alternating snare, transparent kick/snare shell and 32% pedal.
Evidence: existing generic tom candidates at 9.69/10.01/10.32/10.47 s were all rejected as unresolved identity. Independent original-waveform attack rises are 9.6995/10.0115/10.3235/10.4815 s. The original/drum-bus body survives while LarsNet removes most high/mid body energy. Source dominant modes are about 181.6/177.2/146.5 Hz; high/mid modes are too close for confident global pitch calibration, so do not weaken classifier separation gates to force coverage. Use the user's reviewed order for the first three; the repeat at 10.47 s has the same measured floor resonance (~148 Hz).
New behavior: explicit source-hash-bound labels resolve only their uniquely matching existing generic tom events, preserve original rejection/evidence in the audit, and leave all other unknown toms unassigned. Primary three timing/family anchors come from user listening plus independent source inspection, not from a detector-generated expected fixture.
Evidence: 134 relevant tests passed, including 12 review/real-audio regressions; all 275 non-tom audit rows identical and the complete 1,022-event Helix audit/analysis unchanged. Updated dry XSQ/38.32 s MP4 contains 279 placements with high 9.69/mid 10.01/floor 10.32/floor 10.47 s; this count describes the reviewed changes, not a numerical acceptance criterion. Eight decoded frames inspected, including all three toms and the floor repeat; source soundtrack correlation .9959113596. All 16 approved physical assets remain byte-identical. Local proof: `test_runs/drummer_dry_toms/`.
Checklist: [x] inspect source/stems and exact missing stage; [x] implement review overlay and fail-closed checks; [x] real-audio anchor/physical target tests; [x] new XSQ/full MP4 and decoded tom frames; [x] c58364b / CI #223 (134 tests), uploaded exact source/report/frame proof verified; [ ] user preview approval.
Limitations/risks: this is a reviewed correction for this exact recording, not automatic high/mid classification for arbitrary songs. Fourth floor label is signal-supported inference rather than a separate user timestamp annotation. Hi-hat false-hit issue remains open; broader reviewed anchors and native xLights playback remain pending.

## 2026-10-07 — uploaded Dry Drum Test requested for false hi-hat audit

User confirms excess/false hi-hat hits and supplies a 38.32 s stereo 48 kHz PCM16 WAV. User is unsure whether/where real hi-hats are present; do not invent negative hat labels or use inferred output as expected truth.
Goal: run the actual current Demucs/LarsNet/ADTOF drummer workflow on the uploaded recording, export source-bound report/XSQ/MP4 and independent signal evidence. Continue requested cymbal shimmer.
Changed modules/data: original uploaded WAV, cached model inference and unlabelled signal measurements in `evidence/drummer/`; `.github/workflows/drummer-ground-truth.yml` uploaded-audio stage; `docs/DRUMMER_DRY_TEST_AND_CYMBALS.md`, recovery checklist and local audit artifacts. Source SHA256: `4cd9ee35b65d359aa44ac4c9e01a256bbcaf3297458340fc512084bae1463913`.
Preserved: no global detector thresholds changed, all 1,022 Helix events identical, existing geometry/lighting/alternating snare hands, unknown tom abstention. The new recording has no measured three-tom kit calibration; its 34 generic tom guesses cannot be assigned to physical toms without evidence.
Evidence: original dry audio 147 hat candidates; separated drum input 138. Stem-backed raw counts kick 67/snare 53/tom 34/hat 138/cymbal 17. Independent isolated-band inspection shows significant body leakage in the nominal hi-hat stem (e.g. strong 2.04 s/3.29 s peaks have 94%/96% power below 1 kHz). These are evidence about separation/native dynamics, not human-approved false-hit labels. Weak high-frequency hits can still be real hats. Complete 275-placement XSQ/MP4 and CSV exported; eight decoded source frames inspected and soundtrack correlation .9959113596 verified. 120 relevant tests passed.
Checklist: [x] verify exact uploaded source; [x] original-mix and separated transcription; [x] isolated attack-energy and source-band plots; [x] source-bound XSQ/MP4; [x] inspect local proof; [x] CI #222 (122 tests) and downloaded exact source/report/decoded proof verified at c0e8bae; [ ] resolve false-hi-hat behavior using additional evidence/human review.
Limitations: model and separator output remain untrusted for class correctness. User's false-hit judgment remains authoritative; this run reproduces it for inspection and must not be declared a musical fix because tests pass. All unknown toms abstain; no previous-song pitch calibration is reused.

## 2026-10-07 — requested cymbal shimmer and decay

Goal: add a bright cymbal attack, subtle metallic shimmer and roughly1.8s visual decay to both MP4 and native XSQ.
Changed modules: `animation/cymbal_lighting.py`, preview compositor/renderer, native cymbal-surface effect export, `tests/test_cymbal_lighting.py`, workflow, documentation/checklist. No detector or mapper changes.
Preserved: all 1,022 detected/scheduled hits, timestamps, families, velocities, physical assignments, short arm/stick strikes, alternating snare hands, clear idle background, full snare shell through kick, eight targets/three toms, independent surfaces and 32% hi-hat pedal.
New behavior: only left/right cymbal surfaces ring out; a new hit restarts its own cymbal. Native On fade and two warm-gold shimmer colours use stock xLights parameters verified against source. Arms retain the existing320ms cue, and hi-hat behavior is unchanged.
Final pixel audit caught the initial shimmer overlay subtracting the cymbal contact part of each stick (232 left/104 right overlapping pixels). Preserve separate full actuator masks and composite complete strikes over the faded surface; add regressions requiring contact pixels to match the approved pose even during soft shimmer. Update workflow review times to include both cymbal strikes as well as hat/snare/idle frames. All 57 affected visual/export tests pass after correction, including six cymbal regressions; all 16 approved generated assets remain byte-identical. The successful initial #221 run is superseded by this correction, not treated as completed proof.
Evidence/checklist: [x] inspect current flash/source effect settings; [x] implement and test (six lighting regressions; final CI 122 tests passed); [x] exact identical event audit/analysis; [x] real-song 25 s MP4/XSQ plus eight decoded attack/decay frames, soundtrack correlation .9962146413; [x] c0e8bae / CI #222 and delivered full-song proof decoded, soundtrack correlation .9919693452; [ ] user approval.
Limitations/risks: decay is an authored lighting effect, not a newly measured audio sustain; native playback remains unverified, though effect fields are source-confirmed. Rapid repeated hits restart the same surface rather than adding musical events. Preview matches sequence-frame shimmer phase; native frame quantization may differ by one frame.

## 2026-10-07 — user finds #219 music pretty decent; requested visual polish

Goal: preserve the reviewed ADTOF performance and fix disappearing strike sections, persistent raised sticks, alternating snare hands, and the complete snare outline visible through the kick.
Preserved: audio transcription, all timing/family/velocity decisions, eight logical targets, three evidence-based toms, independent surfaces, dim body, kick without a stick and hi-hat surface with 32% pedal.
Changed modules: pose spec, source-art compositor, native/layer builders and generated assets including clean idle background, mapper hand metadata, XSQ visual placement, preview/pose review, visual regression tests and CI. Details: `docs/DRUMMER_VISUAL_POLISH.md`.
New behavior: remove raised actuators from idle artwork; full strike overlays in front of instrument surfaces; alternating left/right snare actuation on the same SNARE component; restore hidden magenta snare shell outline (explicit visual geometry, not inferred percussion); kick contains only red rim/blue snowflake.
Evidence/checklist: [x] inspect and implement; [x] exact event audit/analysis comparison; [x] complete native projection and both decoded snare hands; [x] isolated XSQ and original-song 25s MP4 (audio correlation .9962146413); [x]116 relevant tests plus61 final visual checks; [x] full237.44s MP4 and decoded snare/kick overlap (source correlation .9919693452); [x] pushed cd16a03 and CI#220 success (116 tests); uploaded report/native assets identical, decoded uploaded frames inspected; [ ] user preview approval. Evidence: `test_runs/drummer_visual_polish/`.
User's possible excessive hi-hat activity is recorded for inspection, not permission to suppress uncertain notes without evidence. No detector retuning in this visual pass.
Limitations/risks: artwork-derived snare shell completion is an authored visual approximation; shared native grid cells can carry arm overlays; native xLights import remains unverified; human review remains final gate. Prior claims that idle raised sticks are intentionally preserved or native surface clipping is desirable are superseded by this explicit request.

## 2026-10-07 — recovery preview #218 rejected; reassess transcription methods

User says the 73bb80b / #218 preview is still far from passable. Historical agreement is insufficient and the recovery candidate is rejected musically. Approved physical artwork remains authoritative.
Goal: assess other automatic sequencers and drum transcription systems; test independent methods on the identical song and deliver a more convincing actual-audio performance.
Current work: new source-hash-verified polyphonic transcription import and external-model exporter; comparing pretrained ADTOF and ADT_STR on the identical original mix and Demucs drums. LarsNet instrument stems provide independent signal and dynamics evidence. Original ADT_STR mix probe hallucinated weak auxiliary/tom events; stem input improved the probe, but the first51.2s still had unreliable identities and long decoding stalls, so that full run was stopped. Existing heuristic remains a rejected comparator, not an accepted default.
Preserved: all eight targets, three evidence-based tom identities, body keepalive, independent lighting, complete strike poses, 32% pedal and no kick/hat sticks.
Changed: `audio/drum_transcription.py`; external stem-preparation/ADTOF exporters; source-verified XSQ input and truthful detector metadata; comparison/audit/click tools; cached model evidence; import/physical contract tests and CI candidate selection; reassessment docs/checklist. Original heuristic is retained only as rejected comparator for this pass.
New behavior: independent 100fps family activations from separated drums, simultaneous typed placements, measured isolated per-family dynamics, source-calibrated stable tom resonance with abstention; no fake groove/grid notes.
Evidence: ADTOF on complete mix and drum stem, individual-stem ablation, ADT_STR mix/stem probes and first51.2s (not adopted); waveform/activation/family-stem views. Candidate1022 hits (kick349/snare227/hat416/cymbal18/tom12); 35 unresolved toms abstain. All9 earlier provisional anchors match;110 tests passed plus21 focused checks; original song soundtrack correlation .99621464; 25s and full237.44s video and isolated XSQ generated. Counts/model agreement are not musical acceptance.
Limitations: external evaluation model licenses and dependencies are recorded, not bundled. CI renders a source-bound inferred performance rather than independently rerunning ML. Legacy callers without `--drum-events` retain the rejected heuristic; general backend promotion awaits acceptance. Human listening/labels, native xLights import and tom calibration remain pending. Risks: separator-induced loss of quiet hats/cymbals, false low-velocity notes, heuristic calibrated tom resonance, estimated dynamics.
Detailed reproduction and tradeoffs: `docs/DRUMMER_TRANSCRIPTION_REASSESSMENT.md`; artifacts: `test_runs/drummer_transcription/`.
Evidence and limitations: #218 passed 100 tests but user rejected its musical performance. No auditory perception tool is available; model agreement and signal inspection will not be called human listening or acceptance.
Deferred/final gate: explicit user approval of the next real-audio preview. Running checklist: `docs/DRUMMER_RECOVERY_CHECKLIST.md`.

## 2026-10-07 — recover accepted drummer behavior; musical acceptance remains open

The user rejected #217. This supersedes all prior #216/#217 musical-acceptance claims. Approved physical artwork remains authoritative.

Goal: reconstruct historical/current timelines from the identical song, diagnose stages, port useful b27 behavior into the modern drummer, and provide human-reviewable artifacts.
Changed: active audio detector and compatibility config entry; archived rejected #217; integration audit; isolated XSQ export; historical replay/ablation/comparison/plot/click/frame inspection tools; sparse provisional and archived-timeline fixtures/tests; drummer CI workflow; audio docs/checklist/handoff and this ledger.
Preserved: original source artwork and generated asset bytes, exact eight targets, body keepalive, strike overlap, three toms, no kick/hat sticks, 32% pedal, non-emitting bus, no tom cycling, scheduler merge/clutter/attenuation, simultaneous typed-input mapping, and unrelated integration effects.
New: historical native-rate HPSS/transient grid/features/principal-family behavior, traceable rejection and target decisions, measured tom resonance above background, literal cutoff rejection, supported entrance, full-song/media-correct drummer-only XSQ, archival behavior protection, independent provisional anchors, and full-song real-audio MP4/diagnostic evidence.
Evidence: true historical run 35485877322 found; all 1335 raw events reproduced, 1315 scheduled, all 400 archived timeline rows verified. Rejected #217 reproduced at 405 events with 825 rejected candidates. Recovered candidate: 1182 physical hits (kick188/snare36/hat202/cymbal749/tom7), 1182 one-to-one historical family/time matches versus185 for rejected logic. 100 relevant local tests passed; deterministic 68-event eight-target fixture, byte-identical assets, signal plots, full/25s MP4s, exact decoded-hit frames and soundtrack correlation .99621464 are recorded in `test_runs/drummer_recovery/`.
Limitations: signal-inspected sparse labels await human listening; native xLights playback unverified; mono cymbal side and relative tom pitch remain conventions/heuristics. Original archived 48MB video located but not decoded here due transfer limit. Risks: historical mixed-family classification and sustained-metal/hat distinction remain uncertain. Counts, source agreement and CI are not musical acceptance. No unrelated beta roadmap work performed.
Deferred/final gate: user must approve real-song MP4 and sparse auditory labels. If rejected, continue from timestamp-specific audit evidence. Remote CI status and commit are discoverable on `fix/drummer-target-strikes`; the final handoff names the actual outcome.
Running checklist: `docs/DRUMMER_RECOVERY_CHECKLIST.md`; detailed evidence/reproduction: `docs/DRUMMER_FINAL_FIX_HANDOFF.md`.

## 2026-10-06 run #216 musical-acceptance claim — superseded by 2026-10-07 rejection

- [~] Earlier #216 acceptance report is superseded by the newest explicit user rejection of #217 musical logic.
- [~] The earlier detector freeze is superseded; historical musical behavior is being recovered. Approved visuals remain preserved.
- [x] Identify the arm/stick glitch: preview strike art was clipped against foreign instrument surface masks.
- [x] Allow full-resolution preview strike poses to pass in front of neighboring kit artwork while leaving native xLights node isolation unchanged.
- [x] Add a preview-only 42% body keepalive so the central snowman remains dimly readable at idle and during hits.
- [x] Add regressions for body persistence and unclipped preview strike pixels.
- [ ] Regenerate the real-audio proof, inspect CI/artifacts, and obtain user visual approval.

## 2026-10-06 music sync / drummer logic corrective pass — implementation

- [x] Preserve the user-approved independent target-lighting artwork and strike geometry.
- [x] Normalize drummer analysis to 44.1 kHz / 441-sample hop / 2048-sample FFT so 48 kHz input cannot silently expand the spectral window to 4096 samples.
- [x] Refine accepted HPSS onset frames to the waveform attack and record the correction in every event audit row.
- [x] Reject decay/cutoff release edges with a local attack-contrast gate instead of manufacturing extra hits.
- [x] Tighten cymbal-vs-hi-hat decay evidence and restore three tom body classes without weakening the exact eight-target contract.
- [x] Render musical proof at 60 fps using nearest-frame interval sampling (maximum placement quantization ~8.3 ms).
- [x] Add deterministic 44.1/48 kHz identity, cutoff, attack-timing, and preview-frame regression coverage.
- [ ] GitHub CI + regenerated real-song artifact inspection pending this commit.

## 2026-10-06 corrective pass — completed engineering pass, acceptance open

Baseline/rollback: `87c4b51bab45fb80b630288ef82f29c3da5e0014`; branch `fix/drummer-target-strikes`.
The attached corrective handoff supersedes historical claims that cycling toms or green CI imply musical/visual acceptance.

- [x] Verify remote baseline, preserve it, and inspect source artwork/tests (38 selected baseline tests passed).
- [x] Six target-specific source-art shaft poses with explicit distal-tip/contact coordinates.
- [x] Repose floor-tom arm to reach the visible upper edge rather than crossing the mid tom.
- [x] Tighten instrument search windows to remove neighboring green artwork; restore complete red kick rim.
- [x] Keep idle artwork at 30%; use 32% supplemental hi-hat pedal intensity, no hat arm/stick.
- [x] Split native neutral-arm/gold-stick nodes using source colors; keep eight musical components.
- [x] Extract production HPSS classifier to `audio/drummer_v3.py`; detection/export consume it.
- [x] Archive older classifiers; unknown tom classes and drum_bus do not emit, including animation callers.
- [x] Log every accepted event with spectral evidence and physical assignment; provide 10–30s timeline/CSV.
- [x] Inspect nine isolated states and one decoded MP4 frame per state (18s slow video, 2s/state).
- [x] Full focused drummer/geometry/audio/legacy-analysis suite: 76 passed, no xfails, 2 preexisting warnings.
- [x] Regenerate 14 xmodel/layer/sheet files and verify byte-identical hashes.
- [x] Render and inspect 25s proof (source 9.5–34.5s), 24 fps, 600 frames, aligned AAC audio.
- [x] Update workflow with pose artifacts, event audit, broader regressions, and strict generated-asset checks.
- [ ] Auditory annotation and musical approval: detector thresholds intentionally unchanged pending evidence.
- [ ] Native xLights import/playback validation and user visual approval.

Goal: physical contact and traceable musical evidence, not arbitrary hit coverage.
Changed modules: pose spec; shared source-art mask/pose compositor; xmodel/layer builders;
preview and pose-review tools; audio detector/archives; XSQ integration and audit tool;
mapper/animation; regression tests; generated geometry/layers; ground-truth workflow; this ledger.
Preserved: exact eight public targets, original background, source instrument colors, intro quality
gate, simultaneous body+metal hits, non-emitting drum_bus, untouched rollback baseline.
New: target-specific transformed source shafts and floor arm; narrower correct instrument windows;
neutral/wood native submodels (median source palettes); obsolete generated generic-arm layers removed on re-injection;
one active production classifier; unclassified toms no longer cycle.

Evidence: 455 scheduled song events: kick 54, snare 142, hat 154, tom 23, cymbal 82.
Zero events before 10s; first 10.990s. In 10–71s: 122 events, 46 with confidence <0.45,
18 simultaneous onsets. Full-song maximum rolling 1s counts: snare 5, cymbal 3, kick 3,
hat 4, tom 2. Confidence measures percussive support, NOT calibrated instrument-class probability.
Encoded proof audio correlation to decoded source at 9.5s: 0.9967868; selected decoded frames
at 9.75, 11.00, 18.82, 20.82, 21.82, 27.84, 28.63, 29.79, 29.96s inspected.

Limitations: no auditory hit-by-hit labels; sparse 11–18s region and 142 snares still require listening.
Source-derived static strike poses are not articulated motion; simultaneous poses sharing a hand can
show more than one stick. Native 96x72 nodes/median palettes approximate the full-resolution preview;
xLights playback, continuous native idle lighting, and exact native palette appearance are unverified.
The source screenshot contains numbers and resting sticks, which remain dimly visible by design.
Regression risks: callers of `audio.drum_detection` now use conservative V3 detection; older config
fields other than onset_delta are compatibility-only. Unknown toms now drop rather than cycling.
Deferred: beta roadmap, unrelated engine work, stem separation, and classifier retuning remain open.
See `docs/DRUMMER_TARGET_STRIKES_HANDOFF.md` for reproduction and next steps; this ledger is authoritative.

## Current mission
Build Helix into a reliable AI-assisted xLights auto-sequencer while preserving deterministic sequencing, verified artifacts, and cumulative behavior.

## Beta roadmap baseline status

This repo is currently in the beta-safety phase described by `ROADMAP_BETA_TODO.md`.

- [x] Phase 0 guidance is in place: beta roadmap, safety baseline, and support/data-use policy are documented.
- [x] Core beta docs are linked from the README and are available under `docs/`.
- [x] Agent task index is aligned with the roadmap and points to the current next tasks.
- [x] Sample beta tester feedback checklist exists and is documented for testers.
- [ ] Continue with Phase 0/1 execution in the exact order called out by the roadmap before moving into engine-facing refactors.
- [ ] Keep this ledger updated as each beta phase completes.

## Current priority
The current repo priority is the beta-readiness sequence defined in `ROADMAP_BETA_TODO.md`:

1. Add/maintain `TASKS.md` pointing to the beta roadmap.
2. Maintain `docs/SUPPORT_MATRIX.md` and `docs/BETA_POLICY.md`.
3. Normalize dependencies and CI with `requirements-dev.txt`.
4. Add repo-safe smoke fixtures and structural validation.
5. Add run manifest/output safety behavior.
6. Add GUI beta mode + dry-check behavior.
7. Add beta tester docs and issue templates.
8. Add Windows packaging smoke coverage.
9. Only then begin engine facade/extraction work.

## Current V3 drummer contract — independent component lighting

This supersedes the nine-component/four-tom V3 claims retained below as history.

- Eight hit targets: KICK, SNARE, HI_HAT, TOM_HIGH, TOM_MID, TOM_FLOOR, CYMBAL_LEFT, CYMBAL_RIGHT.
- HIGH is image-right, MID image-left, FLOOR lower-left. The extra lower-right drum is unused.
- Snare/toms/cymbals use target-specific transformed source-art strike poses; kick has no arm/stick; hi-hat includes a secondary foot/pedal and no arm/stick. This supersedes the generic raised-arm behavior retained in historical entries.
- Review rendering uses a 30% dim baseline and 1.45 active gain on full-resolution source artwork. Native effects use 68–100% brightness, with pedal effects scaled to 32% of that. Simultaneous poses/bloom take a pixelwise maximum; shared arms do not compound brightness.
- Source remains \`fixtures/band_geometry/source/drummerbg.png\`; no substitute drummer.

### Running implementation checklist
- [x] Replace misregistered primitive lighting with source-normalized physical surfaces/actuators.
- [x] Export integrated eight public hit targets plus \`_SURFACE\` geometry submodels.
- [x] Render the shared full-resolution source-art spec and reject missing/empty/out-of-range xmodel targets. This supersedes enlarging native 96x72 masks, which produced blocky artwork.
- [x] Remove global brightness changes and painted yellow blobs.
- [x] Use max-union simultaneous hits and exclude other instrument surfaces from actuator contributions.
- [x] Derive PNG review layers from the same exported nodes.
- [x] Share one deterministic event oracle between WAV and XSQ; 68 events over 20 seconds.
- [x] Fix the former starter-model/manifest expected failure and archive that legacy contract.
- [x] GitHub Actions verification of the reconstructed branch.
- [x] Replace spotty 96×72-upscaled preview masks with full-resolution masks from the same authored geometry.
- [x] Restore the approved `b27e8d77...` detector decision order and thresholds; real-song raw counts now match the oracle exactly.
- [x] Fix production mapping to the actual `HX_SNOWMAN_DRUMMER_V3_*` target names and xLights brightness to 60–100%.
- [~] Historical HIGH→MID→FLOOR fallback is superseded: the current contract rejects unknown tom identities; no cycling is permitted.
- [x] Render a 160-second proof using `Helix Audiolights.mp3`; all eight V3 targets occur inside the rendered window.
- [ ] User visual approval of the corrected real-song candidate.
- [ ] Native xLights import/playback confirmation.

See \`docs/DRUMMER_INDEPENDENT_LIGHTING_HANDOFF.md\` for reproduction and limitations.

## Historical drummer / band state — superseded for V3

- [x] Canonical nine-component drummer contract documented.
- [x] Runtime drummer state model changed to nine integrated hit components.
- [x] Structure catalog changed to nine drummer sequencing components.
- [x] XML exporter no longer emits the legacy `line0="1-4"` placeholder for drummer components.
- [x] Pose geometry spec now defines nine component composites with embedded contacting-stick geometry.
- [~] xLights model exporter still needs to emit the new component composites as the nine canonical sequencing submodels.
- [~] Drum detector uses HPSS/percussive onset analysis plus spectral features.
- [x] Classification now rejects high harmonic-contamination candidates when unsupported and suppresses ambiguous low-margin classifications into `drum_bus`.
- [ ] Add per-event source/stem provenance to rendered XSQ debug metadata.
- [ ] Validate detector against real-song audio and quantify false positives.
- [ ] Generate real-song XSQ.
- [ ] Render full-song MP4 with audio.
- [ ] Human visual review of rendered drummer timing.

## Historical nine-component contract — superseded for V3
1. `HX_SNOWMAN_DRUMMER_KICK` = KICK + KICK_RIM
2. `HX_SNOWMAN_DRUMMER_SNARE` = SNARE + SNARE_RIM + SNARE_CONTACT_STICK
3. `HX_SNOWMAN_DRUMMER_TOM_1` = TOM_1 + TOM_1_CONTACT_STICK
4. `HX_SNOWMAN_DRUMMER_TOM_2` = TOM_2 + TOM_2_CONTACT_STICK
5. `HX_SNOWMAN_DRUMMER_TOM_3` = TOM_3 + TOM_3_CONTACT_STICK
6. `HX_SNOWMAN_DRUMMER_TOM_4` = TOM_4 + TOM_4_CONTACT_STICK
7. `HX_SNOWMAN_DRUMMER_HI_HAT` = HI_HAT + HIHAT_CONTACT_STICK
8. `HX_SNOWMAN_DRUMMER_CYMBAL_LEFT` = CYMBAL_LEFT + CYMBAL_LEFT_CONTACT_STICK
9. `HX_SNOWMAN_DRUMMER_CYMBAL_RIGHT` = CYMBAL_RIGHT + CYMBAL_RIGHT_CONTACT_STICK

**Physical rule:** the contacting stick is part of the corresponding hit component. There are no independent stick sequencing channels. Kick has no stick.

## Detection architecture
**audio → HPSS/percussive isolation → onset candidates → spectral/transient features → confidence-gated drum classification → nine-component mapper → XSQ**

## Ground-truth regression oracle
A prior drummer render was explicitly identified by the user as having the **correct drummer logic** and must be preserved as the behavioral reference while the implementation is upgraded.

- Known-good commit: `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- Prior successful artifact lineage: **Helix Full Current 256 + Drummer**; published workflow run `35486153096` was previously identified as the MP4-producing run.
- The repository's dedicated ground-truth workflow at that point exercised the real V3 drummer submodels and generated deterministic audio/XSQ/preview artifacts.
- Current nine-component geometry remains authoritative for the new implementation: four tom zones and contacting-stick geometry integrated into the hit component.

**Rule:** do not discard or rewrite the behavior that made the prior render correct. New detection/mapping logic must be compared against the prior oracle before being accepted.

## Verification gate
**audio → detected events → mapped components → XSQ → full-song MP4 with real audio → compare against prior correct drummer render → human visual review**

Do not mark complete from unit tests alone.

## Change Ledger

### 2026-10-06 — Correct rejected drummer proof: full-component lighting + oracle logic restoration
**Trigger:** user rejected the prior candidate because components were spottily lit and the musical logic appeared regressed.
**Visual fix:** review rendering now rasterizes the same authored component geometry at full source-image resolution instead of enlarging the 96×72 xmodel grid. Idle is dimmed to 15%; active artwork receives a strong source-preserving emissive lift. xLights effect brightness is emitted on the correct 60–100 percent scale.
**Logic fix:** restored the exact approved `b27e8d77a63027ed32bcf6851dcff3925472c155` classifier decision order and thresholds. On `Helix Audiolights.mp3`, the raw detector counts now exactly match the historical oracle: kick 194, snare 37, tom 9, hi-hat 208, cymbal 840, drum_bus 47.
**Mapping fix:** production events now target the actual `HX_SNOWMAN_DRUMMER_V3_*` submodels. When a multi-hit tom passage's spectral subclasses collapse to fewer than HIGH/MID/FLOOR, the mapper preserves the historical distribution behavior by cycling real detected tom hits HIGH→MID→FLOOR; the final real-song mapping yields 3 hits on each tom.
**Proof:** GitHub Actions run `37432351105` passed focused tests, the deterministic 68-event geometry regression, exact real-song oracle-count gating, all-eight-target-in-window gating, and a 160-second real-song H.264/AAC preview.
**Still open:** user visual approval and native xLights import/playback.

### 2026-10-06 — Reconstruct independent V3 component lighting
**Goal:** restore the tested independent-lighting design from the saved candidate artifacts and handoff after the original local patch could not be recovered.
**Changed:** V3 pose geometry, xmodel exporter/static asset, node-driven PNG layer builder, canonical preview renderer, shared fixture oracle/WAV/XSQ exporters, focused tests, ground-truth workflow, runtime hi-hat description, geometry manifest, and this ledger.
**Preserved:** canonical source image, eight public XSQ target names, HIGH-right/MID-left/FLOOR-left orientation, deterministic sequencing contract, extra-drum exclusion, and production drum detector.
**New:** source-aligned surfaces/actuators, integrated hit nodes, dense xmodel grid, portable background path, fixed 28% idle brightness, xmodel-node-driven max-union rendering, hi-hat foot/no-arm behavior, and exact WAV/XSQ oracle agreement.
**Evidence:** GitHub Actions run `37416429803` passed canonical regeneration, exact 68-event WAV/XSQ agreement, 37 focused tests with 3 existing deprecation warnings, and a 20-second H.264/AAC render at 24 fps. All eight isolated decoded states were inspected after encoding; the kick/snare shared-cell regression was corrected by exclusive instrument-surface ownership. User approval and native xLights import remain open.
**Limitations/deferred:** static reference arms illuminate but are not re-posed; xLights native import and real-song detector quality remain separate gates.
**Regression risks:** public hit targets now include actuator nodes; geometry-only checks must use \`_SURFACE\` submodels.

### 2026-10-06 — Resolve legacy starter expected failure
**Goal:** make the archived starter xmodel/manifest contract internally valid without confusing it with the active V3 runtime.
**Changed:** starter HEAD and DRUMKIT_ALL unions, geometry manifest active/archived split, strict xmodel and manifest tests.
**Preserved:** all existing starter node ranges and all five active performer identities other than replacing the obsolete starter drummer identity with V3.
**New:** starter contract is archived and fully testable; active manifest resolves the V3 runtime.
**Evidence pending:** focused CI on the publication branch.


### 2026-10-02 — Beta tester feedback checklist documented
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Added a repo-safe beta tester feedback checklist document for single-run evidence collection.
- Linked the checklist from the root README so testers can find it from the main entrypoint.
- Kept the checklist focused on privacy-safe, local-only evidence collection without requiring private asset disclosure.

**Limitations:**
- This is a documentation gate only; it does not claim xLights import success or visual quality.
- The beta roadmap still requires run manifest, GUI, and packaging safety work before broader beta claims.

### 2026-10-02 — Beta roadmap baseline alignment
**Agent:** GitHub Copilot
**Branch:** `feature/restructure-core`

**Recorded:**
- Restored the task index to the beta-roadmap-first workflow required by `ROADMAP_BETA_TODO.md`.
- Added a repo-level beta baseline status note to this ledger so the project continues in the intended order.
- Preserved the active drummer work while making the higher-priority beta safety work explicit.

**Limitations:**
- This does not replace the deeper engineering work required for drum detection or xLights import validation.
- Beta-safety milestones must still be executed in order before engine refactor work begins.

### 2026-09-30 — Ground-truth regression oracle locked
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Recorded:**
- Prior known-good drummer behavior is anchored to commit `b27e8d77a63027ed32bcf6851dcff3925472c155`.
- The historical 8-submodel V3 workflow is retained as a behavioral regression reference while the physical model evolves to nine components.

### 2026-09-30 — Confidence-gated drum classification
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`
**Commit:** `b8e7f8fa5ab5044c774b3ca482711b47b89fb61c`

**Changed:** `audio/drum_classification.py`
- Added harmonic-contamination gating using the existing percussive/harmonic ratio.
- Added a minimum score-margin requirement between the best and runner-up drum classes.
- Ambiguous or weak events now become `drum_bus` instead of being confidently misclassified.

**Preserved:** existing kick/snare/tom/hat/cymbal feature scoring and six-stream event schema.

**Not yet verified:** real-song false-positive rate, XSQ output, and MP4 behavior.

### 2026-09-30 — Nine-component drummer geometry spec
**Agent:** ChatGPT/GitHub
**Branch:** `feature/restructure-core`

**Changed:** `fixtures/band_geometry/drummer_v3_pose_spec.json`
- Four distinct tom zones and nine canonical hit composites.
- Contacting sticks are embedded in snare/tom/hi-hat/cymbal components.

**Known limitation:** xmodel exporter still needs to make the nine composites the canonical sequencing submodels.

## Next actions
1. Preserve the prior known-good drummer behavior as the regression baseline.
2. Reconcile xLights drummer geometry with the nine canonical composites.
3. Add event provenance/debug output.
4. Run detector on the repository's real song and inspect event counts by class/confidence.
5. Generate full-song XSQ.
6. Render full-song MP4 with real audio.
7. Compare rendered component flashes to actual audible drum events and the prior known-good render.
8. Iterate only on measured false positives/false negatives.


## Publication status
- [x] User explicitly authorized publication.
- [x] GitHub write access restored.
- [x] Publish and validate \`fix/drummer-independent-illumination\`; implementation run `37432351105` passed all automated gates.
- [ ] User visual approval and native xLights import/playback remain final acceptance gates.
