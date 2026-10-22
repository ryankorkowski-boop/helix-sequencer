## 2026-10-22 — Rebuild deliverables after visual HUD finding

Actual API36 screenshots show the Layout/Style pages correctly exposing the extravagant default and Quick clip, but the video itself contains the shared renderer's diagnostic panels. Keep source42103ed APK as a held audit file, not the fixed-preview download. Pixel-proven clean preview change is committed9f177427a168b14dd00a358c76c54a9d6d116715 in development PR203, based on Windows persistence41ce64c.67 focused preview/Android/color/provenance/recovery cases pass; new exact-source emulator/Windows screenshots are required.

Update the single-download workflow's pinned runtime to9f177427 in both defaults, retaining checksum/provenance/hash/startup/worker gates. Combine this with the bounded parent-only wait correction so the older interactive wait is superseded. This packaging branch changes no runtime source; receipt must distinguish its own commit from9f177427. No release/default merge or approval claim. Original music, layout, hardware and canonical-band/backing-source gates remain preserved.

---

## 2026-10-22 — Single-file GUI verification wait and Android verification

The first single-download job39865998362 compiled the launcher, then its test used Start-Process -Wait, which waits for descendants including the interactive GUI. Replace that harness wait with a bounded Process.WaitForExit on the unpacking parent, then retain actual visible-GUI/default/worker/hash checks and close only the tracked GUI. NSIS payload/application source is unchanged; this is a validation lifecycle fix, not a weakened check. Official PowerShell and .NET behavior verified against Microsoft Start-Process/Process.WaitForExit documentation. The newer packaging-source run supersedes that test; it must actually finish before EXE delivery.

Android42103ed API36 job120123869594, run39864543319 passed. Artifact12463624002 ZIPSHA256863ac3446842c035a627351d9aecbc352555a794f1ded6c48c2cb8392147aafa independently downloaded/CRC-checked. Actual installable debug APK SHA256e5ccd1ea64fe70f488e5c6d0bb3710cfd28c5f808c4dfca1c423435eb4e0f495,115848588 bytes. All1052 embedded engine file hashes and exact42103ed provenance verified, valid signing receipt, instrumentation success, four decoded modes including full-song audio/image proof; new in-layout video controls pass the actual bounds assertion. android36_verified.json records details. API30, physical Samsung/ARM64, existing-beta certificate upgrade and production signing remain separate; no owner-device success or release approval claimed.

Recovery42103ed full CI39864543252 passes both Python3.11/3.12 (2067 each,6 inherited skips,16 subtests) and both lint jobs. Corrected Windows41ce64c portable39865440149 passes actual frozen GUI/worker/FSEQ/LOR/xLights startup and exports. runtime_check_results.json retains exact identities; don't relabel different source snapshots. All original musical, native, hardware, visual and release gates remain open where not evidenced. MASTER_TODO and handoff are updated with this change.

---

## 2026-10-22 — Single-download Windows packaging candidate

Goal: finish the requested standalone Windows download while retaining the verified Helix GUI/CLI runtime and all dependencies. New isolated branch codex/windows-single-download-20261022 targets the Windows persistence candidate, not the default/release branch. packaging/windows_single_file/launcher.nsi expands the exact portable payload to a persistent per-user, source-versioned cache and launches the real Helix.exe. It preserves outputs after closing and needs neither installed Python nor administrator rights. Runtime functionality is not rewritten.

.github/workflows/windows-single-file.yml waits for a successful exact-source Windows portable build41ce64cad33180e2d9d5ba83a679e9fe7def8e56, refuses older/failed substitutes, verifies portable checksums/provenance and every embedded manifest hash, builds an NSIS single EXE, launches its actual extracted GUI, checks the persisted source-local default layout, runs the original frozen GUI/worker smoke without weakening it, and verifies every extracted runtime hash. Artifact is uploaded only after success. Receipt distinguishes runtime source from packaging source; no publication/default merge. README documents persistent runtime/output placement and source identities.

Current evidence: YAML parses locally; NSIS syntax and real Windows execution require this new workflow. Do not claim a standalone executable until actual build/runtime checks pass. No Python/GUI/engine source changes in this packaging branch. Developer/doc work is preserved in MASTER_TODO and this handoff. The prior engine snapshot42103ed completed2067 tests/6 inherited skips/16 subtests in527.08s;95 current focused cases pass. These results are not native musical/artistic or physical-device acceptance.

Preserved: original audio/layouts/Greg256, native vocal-source negative gate and no-phony-face behavior, APK42103ed and ongoing platform checks, real source-LMS wiring, existing portable distribution and all licensing. Open: source-backed independent harmony, canonical band/mouth acceptance, authentic progressive showcases/native imports, signing/owner devices and final release approval. Risks: first launch expands the runtime, per-version caches use disk, wrappers remain beta review builds, and actual Windows build may reveal compiler/runtime differences. Verify before delivery.

---

## 2026-10-22 — Windows first-run layout persistence correction

Observed actual42103ed Windows run39864543209: frozen GUI initializes and finds the new catalog, but --helix-gui-smoke rejects app.layout_var!=load_layout(). The first-run extravagant sample was applied before the write trace was registered, so the effective selection was not persisted. Fix gui_launcher.py by explicitly saving the effective initial selection after registering the same existing persistence callback. Existing imported layouts retain precedence. windows_portable_entry.py keeps its exact assertion and updates its explanatory comment; no weakened smoke or output checks.

This Windows-only candidate branches from42103ed into codex/windows-default-layout-persistence-20261022 and targets the recovery branch, so ongoing Android42103ed checks are not restarted. Actual packaged Windows startup/build/export validation is required before calling this fixed. Existing tests/layout-preference and frozen-worker checks remain applicable; focused tests and candidate build results will be recorded below.

Also retain evidence from the current recovery snapshot: actual retained E14 source qualification39864543309 fails before compilation because independently resolved lead/backing tracks are absent (native_source_preflight.json); do not turn this into an accepted movie. Repeated owner-audio10s CLI runs have identical lighting trees SHA256729d359fa184173904818c93de2ca5cbc9dec475bbe362471ba3b73711d9392b, full original audio unchanged. docs/SAMPLE_LAYOUT_INDEX.md indexes75 actual saved layouts and distinguishes source inventory from artistic/hardware acceptance. Full_gui_snapshot.log is preserved explicitly despite repository log ignores.

Limitations/deferred/regression risks: save permission errors retain existing guarded startup behavior; physical owner Windows/Android/CTB16PC checks, single-file EXE, actual canonical-band/mouth/backing-source acceptance, progressive native comparisons, signing/upgrade continuity and final approval stay open. No default/release merge or publication. Source identities of separate platform builds must remain explicit; do not relabel42103ed Android as this Windows candidate.

---

## 2026-10-22 — Production singing-face substitution defect repaired

Goal: follow the real owner-audio run into saved XSQ, rather than treating routing metadata as rendered singing. The 9f30fb9 source assigned six backing cues to a dedicated target, but its generic effect picker emitted Strobe effects on that body instead of native phonemes. Source inspection confirms the picker was allowed to replace requested Faces; the sample has no native faceInfo mappings. This is a real unresolved layout/source requirement, not proof of singing.

Changes: core/native_face_instructions.py compiles only actual discovered native mouth mappings and the face's true definition name; unsupported targets/phonemes remain unresolved. core/effect_engine.py bypasses generic effect-family substitution and beat snapping for these validated Faces instructions, preserves exact source cue intervals (including short consonants), and retains existing timing/layer/conflict/output-safety checks. The production path never invents mouth-node geometry. New helpers reuse developed singing_face_discovery/routing and the established xLights Faces settings contract. core/quick_clip.py also isolates concurrent runs by directory while keeping the basename stable, so the engine's name-based RNG seed does not change on repeated quick clips.

Preserved: imported layout/face/controller definitions, actual source audio and source cue clocks; unrelated musician/effect paths; no active-default/native-source visual approval or release claim. AC/LOR modes without native-compatible face mappings remain restricted. Unknown mouth definitions are logged as unresolved rather than replaced with a torso flash.

Evidence: focused compiler/routing/engine failure/provenance/discovery checks pass; source rerun on Phoneme Test Hook, Helixville4/warm produces a valid10s XSQ and logs six unresolved face cues with no substitute body effects. This intentionally does not claim new native singing on that incomplete sample. tests/test_native_face_instructions.py checks actual serialized native settings and exact113–137ms timestamps. Stable repeated clips preserve exact audio bytes and deterministic basenames. Broader/remote candidate validation remains required.

Limitations/risk: strict missing-mapping behavior can reduce previously decorative body flashes; it does not repair an incomplete face layout or isolate backing from mixed audio. Native frame-level import/artistic verification of this production route remains open. New runtime modules must be included in the rebuilt APK/Windows package. Follow current job status in evidence/jobs_recovery_20261022; do not distribute a prior build as containing this fix. MASTER_TODO and the current handoff retain all other release blockers.

---

## 2026-10-22 — Current-job recovery, GUI samples and source qualification

Goal: finish the actionable launcher and regression work and stop repeating the known empty-harmony native render. Baseline ab15f09ffa01813c665c9af92cf06dce7bb73c15; development branch codex/eight-hour-recovery-20261019; PR188 remains draft. Release remains INCOMPLETE; no default/release merge or publication.

Implemented in this change set:
- core/snowman_band.py: give the dedicated harmony performer an explicit catalog entry and stable, separate target. Recognize native lead/harmony names; never rotate its phonemes onto the lead, instrumentalists or a matrix. Restore chorus intensity scaling for this dedicated performer. Tests now assert actual second-singer ownership, not obsolete guitarist/bassist singing; classifier fixture supplies a real second model. These are routing tests, not proof of independent vocals in a mixed recording.
- core/quick_clip.py and sequence_builder.py: optional --helix-quick-clip creates a separate first-ten-second lossless input before analysis. Original song is untouched; full-song processing remains default. Desktop, on-device and paired remote launchers pass the option. Both source-LMS and RGB entrypoints retain their existing gates. Equals-form --audio arguments are replaced correctly.
- config/gui_options.json and core/gui_options.py: one seven-palette/nine-layout catalog. Six existing display XMLs (original Greg256 preserved) plus three separate stage-scenery layouts, first-run Helixville4 default, imported/persisted user layouts take priority. Stage scenery does not claim an approved canonical performer ensemble or an automatically merged band. New 16-channel starter geometry and fresh progressive comparison videos remain open.
- Android MainActivity/RemoteActivity/UiOptions: expose quick clip, catalog samples and actual existing engine palette modes; save local choices. PreviewActivity replaces the floating MediaController window with controls below the movie. Instrumentation requires visible playback and controls below actual video bounds; actual emulator result remains pending.
- Packaging: Android staging includes all catalog files and catalog asset; sparse checkout includes their directories. Windows spec includes all sample XMLs. Existing AC/LOR restrictions, real hardware mappings, audio, approved art, exports and release hold are intentionally preserved.
- tools/verify_native_vocal_source.py and fresh-real-band-mp4.yml: check source hash, independent lane ownership/fingerprints, frame validity and actual non-rest lead/backing before compiling/rendering. Consumer-triggered PR source paths now schedule their matching producer. Recovery uses its open PR event to avoid duplicate push/PR render jobs; standalone native development branch retains push support. Preserve the final native/audio/readability gates unchanged. Retained E14 is expected to fail source qualification; do not invent harmony or repeatedly render it.

Verified local evidence:
- 62 initial routing/quick-clip/desktop/remote cases passed; later source/ownership/native-preflight group 95 passed. Platform/packaging/Android/GUI subset 73 passed. Stage/catalog/quick-clip subset 17 passed; these groups overlap and must not be summed as a total.
- Actual production CLI run on owner Phoneme Test Hook.mp3 (SHA256 19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938), Helixville4/warm: exactly 10.000s, 778 lighting effects, every effect interval bounded to the clip; original input hash unchanged. evidence/jobs_recovery_20261022/quick_clip_runtime.json. No native MP4 or artist-approved output inferred.
- Full local regression is running at this checkpoint; fresh exact-source Windows/Android CI builds are required after commit. Prior ab15f09 Windows39739132595, Android39739132570 and native39739132690 passed; full CI39739132783 and final-band39739132812 failed, the latter for no non-rest HX_SNOW_HARMONY. Those previous builds do not include these GUI changes.

Limitations/deferred work: authentic canonical 3D band identity/10-phoneme and whole-band musical/visual approval; independently defensible source-backed harmony (the recovered 34.88s Phoneme Test Hook is mixed stereo and is not automatically labeled two isolated voices); newly rendered synchronized distinct native comparison shows; universal compatible exports/native vendor imports; standalone single-file Windows EXE; physical Windows/Samsung ARM64/CTB16PC tests, signing/upgrade acceptance and final owner release approval. Stage choice currently selects scenery as a layout, without inserting performers. Wider style/effect intelligence and issue176 remain open. Earlier roadmap tasks are retained, not silently closed.

Regression risks: new catalog resources must ship in frozen/APK builds; stricter vocal qualification intentionally turns an unqualified full-band source into an early actionable failure instead of spending another long render; a quick-clip run intentionally exports only its first ten seconds; workspace-matching palettes need workspace history to differ from fallbacks. New playback layout requires actual API30/36 verification and owner-phone confirmation.

Next: finish full regression, commit all source and this ledger together, track exact-source CI/builds, inspect actual Android playback screenshots, provide only a verified installable APK. Retain explicit native-source blocker; finish missing source separation/qualified analysis before a new full-band acceptance render. Do not present prior rejected footage or an approximate mobile preview as a newly approved native band.

---

## Final verified checkpoint — 2026-10-21, Android/build review files delivered

Latest verified runtime source remains `546fcd454c4dd37ba357d05c9928f3e45e696d26`; subsequent recovery commits only update evidence/documentation. PR197 is integrated into recovery and closed as merged there. PR188 stays open against the default branch. **No default/release merge or release publication. Release is INCOMPLETE.**

- AND-SOURCE01 [x] for build/emulator/artifact scope: run39608785388 SUCCESS, API30 artifact12350661773 (ZIPSHA6139b23e3a6f1261134a44fe9fe8bf87a551a7d584a8383faa32e63f48d86f54), API36 artifact12350666406 (ZIPSHA5affc942e991f69ea9c946dbef3c356966bdf21769a0c324d49678b73771fdf7). Both embedded source546fcd4,1043 file hashes, signing receipt and4 decoded preview modes independently verified. Full-song preview237.47s, decoded audio correlation~.9957; tested real-RGB and legacy LOR/xLights modes. Actual installable API36 debug APK SHA7913cd4af74cd40cd1bd19fbfefff60b8de92fa2d5143d869d563b687b77e7b6. Physical Samsung/ARM64, upgrades from an earlier beta certificate and production signing remain open.
- WIN-SOURCE01 remains verified at546fcd4: run39608785241 / artifact12349097869. Actual Windows package source/EXE/guide hashes and FSEQ/LOR/xLights smoke passed. It is a complete portable folder, not a single standalone file.
- CI-FINAL01:2034 tests pass/6 skip/16 subtests on each Python3.11/3.12 at546fcd4 (39608785140), both lint jobs pass; local same counts. Full260.2s sampler production output at546fcd4 has72539 bounded lighting/timing intervals and preserves original audio. Native full-sampler render remains open.
- Native36s band review remains sourcecc736b1, run39605876463/artifact12347664834; do not relabel it as546fcd4. Actual source-keyed cache hit/restoration is confirmed in native job119243150656 (13:15:52 cache hit,13:16:02 restored), followed by wxWidgets runtime/dependency and native render success. Artistic/musical approval and keyboard-top camera readability remain open. Silent E14 harmony is still an honest negative gate.
- New proof files: android_api30_verified.json, android_api36_verified.json, windows_verified.json, final_runtime_validation.json, full_sampler_duration.json, native_media_audit.json and local_full_tests.log in evidence/release_recovery_20261021/.
- Review downloads prepared: actual native MP4; actual signed debug APK; verified Windows portable ZIP; editable sources ZIP (native36s XSQ/FSEQ/layout/audio; full-sampler XSQ/layout/audio; standalone pixel/AC16 xModels and position/inventory audits); standalone full-sampler XSQ; manifest and SHA256 list. This is not an accepted final release-candidate bundle.

### Resume without repeating prior failures
1. Fetch recovery HEAD, read this checkpoint and MASTER_TODO. No critical current-source build job remains pending. Code is committed; no implementation is left only in a scratch checkout.
2. Resolve defensible independent vocal sources and core-source ownership. Current sampler's59 harmony/group-classifier windows are inferred, not independently resolved backing evidence; do not use them to bypass the strict full-band negative case.
3. Verify keyboard/drummer/guitar/bass musical contacts and owner visual/artistic approval on genuine new native media. Do not fake harmony, add placeholder actors or reuse cc footage as a new source.
4. Complete universal compatible dual export/native LOR import and owner controller mappings without guessed Unit IDs. Physical Windows, Samsung/ARM64 and CTB16PC plus single-file Windows packaging remain separate gates.
5. Build/render six-to-nine distinct authentic native layouts using the recovered high-energy sampler. The older FSEQ illustrative compositor is not a genuine native House Preview pipeline. Preserve Greg256 and separate experimental RGB. Then assemble synchronized panels and any ads only from verified native sources.
6. Finish final packaging/legal surfaces and request owner release approval only after those required gates have concrete review evidence. No release is authorized now.

## Current integration checkpoint — 2026-10-21 13:42 UTC

**Release INCOMPLETE.** Latest verified runtime source: `546fcd454c4dd37ba357d05c9928f3e45e696d26` (PR197 candidate, now integrated into recovery by this documentation/evidence-only fast-forward). This checkpoint deliberately skips duplicate CI; it does not relabel any earlier build/media SHA. No default/release branch merge or publication.

| ID | Status | Requirement/evidence | Remaining blocker / exact next action |
|---|---|---|---|
| NAT-MAT01 | [x] scoped implementation/render | Sourcecc736b1, producer39605876463, artifact12347664834; actual36s1080p MP4/audio, full decode, five audio windows, frames1/10/21/34 inspected. Keyboard case/stands and per-material colors restored;1320 original musical/pose arrays unchanged. | Whole-band musical/artistic acceptance remains separate; top of keyboard is foreshortened. |
| DUR01 | [x] production duration/bounds | Source546fcd4 actual high-energy sampler CLI run:260.200s header,72539 lighting/timing intervals all within0..260200ms. AudioSHAf76e41469c5e844442da18d1716de8fbec8c4ab2bfee84128a0a6f9515924c9f unchanged. | Fresh native FSEQ/MP4 for this full sampler is NOT produced. Open accompanying show directory in native xLights; render and inspect full duration. |
| EXP03 | [x] strict source-wired converter | Malformed timing, invalid/nonfinite/duplicate/unsupported intensity refused before writing; valid wiring/fades/shimmer/twinkle preserved. Existing-output preservation regressions retained. | Universal default dual output, native legacy LOR import and physical CTB16PC remain unaccepted. No owner Unit IDs inferred. |
| GUI-BOTH01 | [x] implementation/regression | Recovered PR194 GUI Both selection and frozen-worker converter; source mapping required; explicit1–8 candidates retained; normal default1/Vendor Bar opt-in.90 focused cases pass. | Actual owner desktop usage and broad export/hardware acceptance open. |
| CI-FINAL01 | [x] source546fcd4 | Full CI39608785140:2034 pass,6 skip,16 subtests on BOTH Python3.11/3.12; both lint jobs pass. Local2034/6/16 also passes. | Skips: absent2.wav sandbox fixtures and optional external native-manifest integration. They do not establish native approval. |
| WIN-SOURCE01 | [x] exact source/package checks | Run39608785241, artifact12349097869, outer ZIPSHA8456e9d8d2b90c471b395361e25b5496690e0a3a19286e992efbd34e13445ef8. Embedded source546fcd4 and EXE/guide hashes verified; packaged native-FSEQ/LOR/xLights smoke passes. | Portable folder needs HelixCLI.exe/_internal. Single-file EXE, physical Windows/audio acceptance and final signing remain open. |
| AND-SOURCE01 | [~] exact-source build/emulators | Run39608785388 at546fcd4, API30 job119252428167 and API36 job119252428767 both running emulator smoke at this checkpoint. | Preserve healthy jobs. Fetch both artifacts only after success; run verify_android on each and verify embedded546fcd4, certificate, complete full-song/image/audio proof before offering direct APK. Physical Samsung/ARM64 remains open. |
| MODEL-GEO01 | [x] geometry/inventory audit only | Source546fcd4:14 independent pixel/AC catalog models audited. AC circuits drummer10,bass9,guitar11,piano15,optional legacy xylo15,lead14,harmony14. Actual standalone xModels/layouts and position/inventory CSV generated. | Native import and physical dimensions/controller wiring unverified; catalog legacy option does not change six-member default. |
| VOC01 | [!] retained negative source | cc736b1 consumer39605876881 fails missing non-rest harmony. Independent backing is absent in retained E14 data; do not add activity. | Recover independently identified source/stems or a different owner-authorized qualified recording; preserve E14 negative regression. |
| EXACT-NATIVE01 | [!] source546fcd4 | Candidate consumer39608785433 failed waiting for an absent exact-source producer. Runtime export/GUI PR does not trigger the path-filtered native producer. | Nativecc footage stays explicitlycc. Schedule a genuine current-source producer only through a supported execution workflow; do not promote older media as new. |
| SHOW02/03 | [ ] source recovered | Exact high-energy sampler and prior Greg256 show recovered. Earlier render_prior_sampler_comparison.py draws illustrative geometry from FSEQ; it is not a genuine native House Preview movie. | Build six-to-nine genuinely different layouts and source-bound musical analyses; render every panel through actual xLights before timestamp-aligned composite. No generic renderer substitute. |
| LICENSE-DOC01 | [x] scoped corrections | Recovered PR195 current-license paragraphs; historical MIT/third-party notices retained. Compliance39608785223 passes. | Final distribution/legal surface audit and owner commercial/release policy acceptance remain distinct. |

### Running/remaining execution
- Keep Android39608785388 healthy; no duplicate/restart. Windows and both-Python CI are already verified at runtime546fcd4.
- PR193 native renderer-bundle recovery remains separate until actual bundle publication/restoration evidence is reviewed. Do not blindly replace the now successful native cache path.
- Recovered PR194/195 work is integrated with stricter validation; no task silently retired. PR197 documents candidate source/evidence; PR188 is the long-lived integration review.
- Next commands: `gh run view 39608785388 --repo ryankorkowski-boop/helix-sequencer`; `python -m tools.package_beta_installers --help`; `python -m pytest -q` (2034 cases at546fcd4). Native next producer uses current runtime code and authentic source; keep original quality gates and absent-harmony failure.
- Primary remaining production areas: defensible independent backing and source ownership, keyboard/drummer whole-band musical/visual acceptance, broader intelligence/effects integration, universal dual export/native imports, six-to-nine full-song native comparisons, single-file Windows packaging, physical Windows/Android/CTB16PC and final owner approval. No final release-candidate package is claimed.

## 2026-10-21 recovered GUI dual-export and license documentation

- Recovered verified existing PR194 (`a3ce1b2`) rather than leaving its developed GUI work disconnected: desktop Both now selects the source-LMS backend, keeps editable XSQ+LMS, requires real source mapping, and portable workers dispatch the existing strict AC/CSV converter. Normal desktop defaults now match the measured CLI single-candidate default; explicit1–8 choices remain and Vendor Bar is opt-in with its3+ requirement visible. Candidate source/export tests preserve these behavior changes.
- Unified duration ownership with PR194's existing `xlights.xml_io.set_sequence_duration` interface across production engine plus three retained writer paths. Preserve its nearest-millisecond rounding; retain namespace support, Media sequence identity and the new final audio-bound cue-tail fence. No second active duration helper remains.
- Recovered PR194 duration/GUI/worker and preserved-output tests unchanged; extended source-wired LMS validator still rejects malformed/nonfinite/unsupported fields.90 combined focused cases pass. Recovered PR194's real38.32s dual-export evidence under evidence/desktop_dual_export_20261020/ remains source-specific historical evidence, not owner hardware validation.
- Recovered both current-license documentation corrections from PR195 (`da4cf8c`) while retaining historical MIT/third-party notices. No new licensing policy, prices or donation URLs introduced.
- Fresh real260.2s sampler run now has72539 total lighting/timing effects, every interval bounded to0..260200ms, original audio hash unchanged. New native FSEQ/MP4 for this full sampler is still open; it is not the36s native band movie. Final source musical ownership/backup evidence remains unverified.
- Candidate runtime parent `a127102`, PR197 targets recovery only. Full3.11/3.12 CI and exact-head Windows/Android packaging remain required at this combined source. Prior nativecc736b1 stays a separately identified genuine review artifact; no recycled footage is relabeled.
- Keep PR193 renderer-bundle recovery separate pending live bundle publication/restore evidence; current cc736b1 cache restoration/render succeeded, so no cold-build fix is blindly merged. Remaining source intelligence, backing separation, six-to-nine native layout comparisons, hardware/owner and final release gates stay open.

## 2026-10-21 runtime/export/build source correction candidate

- Scope: `core/effect_engine.py`, `xlights/xml_io.py`, source-wired LMS exporter, focused regressions, Windows/Android workflow source pins; no default/release merge or music publication.
- DUR01 [~]: recovered exact high-energy sampler SHA256f76e41469c5e844442da18d1716de8fbec8c4ab2bfee84128a0a6f9515924c9f from Library; previous show had260.2s audio but inherited132.039s template head. Actual production run now writes260.200s and72539 editable effects. Follow-up audit found final cue tails90ms beyond audio; production finalizer now bounds generated intervals to the decoded audio end. Fresh rerun with that finalizer is active; do not claim its native FSEQ/MP4 yet. Focused duration/contract cases pass.
- EXP03 [~]: direct source-wired LMS path (separate from EXP02) silently clipped malformed/out-of-bounds timestamps and defaulted invalid intensity to100. It now refuses malformed/duplicate/unsupported intensity settings, invalid ranges/timestamps and nonfinite durations before writing, while retaining real source wiring, fades, Shimmer/Twinkle, overlap policy and centisecond quantization.79 export tests pass; legacy vendor import/CTB16PC physical validation remains open.
- BUILD02 [~]: Windows run39605876807 artifact12347924541 declares headcc736b1 but its actual BUILD_PROVENANCE reports PR merge63612a840b8c7f4c58ee15ff419cd953508b8596. Do not relabel it as exact branch source. Windows/Android checkout now explicitly uses PR head (push SHA otherwise) and asserts HEAD before building.86 app/export focused cases pass; fresh exact-source builds required.
- Native cc736b1 evidence: producer39605876463 and artifact12347664834 passed; ZIP8e2c9c8a4b3c8fe0c1a98b3c7dad6d1e72677a758a7ee23f0b8c1abf041338d6; MP4154f045f3e8ba7bb9a1475dcfb7982a5cb68b59e1a3fb5ac10f3d9296e5048bb. Full local decode, five soundtrack windows >.99 correlation/<=.125ms offset, four actual frames reviewed; colors and authored keyboard structure restored. Keyboard top is foreshortened; owner review remains.1320 source musical/pose arrays unchanged. Strict same-source full-band consumer39605876881 remains FAILED for absent non-rest harmony; no second voice fabricated.
- Full CI39605864195 atcc736b1 passed both Python3.11/3.12 and lint. Local intermediate runtime suite2001 passed/6 skipped/16 subtests; later duration/source-pin changes require final revalidation. Source-specific media reports in evidence/release_recovery_20261021/.
- Intentionally preserved: source audio bytes; Greg256 original layout; interior cue clock and independent musician lanes; physical source LMS unit/circuit identities; AC16 ownership; mandatory quality thresholds; previous performance defaults. New native geometry adds432 pixel channels in this regenerated pose-bank show and requires its accompanying layout.
- Regression risks: stricter LMS settings may reject formerly ignored external modifiers; interval bounding drops effects wholly beyond actual audio. New installs must be rebuilt from exact candidate SHA. No generic RGB-to-LMS claim, standalone single-file EXE, physical device/controller success, nine-layout native comparison or full-band approval is inferred.
- Next: finish live sampler rerun/final tests and source-matched builds; integrate verified candidate into recovery only, update PR188/checklist with exact SHAs/run/artifact hashes. Keep independently resolved backing, broader source intelligence, six-to-nine distinct layouts, Windows/Android/CTB16PC physical tests and final release acceptance open.

## 2026-10-21 native instrument/material recovery (implementation candidate)

- Goal: correct the current-source native review rejected during actual frame inspection; no final visual acceptance inferred.
- Source baseline: recovery `ef8a345677bb29461f8c4fbeb5a16093cc12a9f0`, PR188. Current producer39548845276 succeeded and artifact12321993842 (ZIP SHA256493dccbf5882c7d9f242d6893661c9f5a8223a49829589c65bd17f0d3693a21f) contains authentic36s1920x1080 native MP4/audio. Frame at10s inspected: physical keyboard case/stands absent and BODY color flattened. Do not promote this as visually approved.
- Root causes: `models/native_review_band.py::_role_parts` excluded `keyboard_*` structure; `tools/native_source_pose_band.py` assigned the first BODY node's color to its entire submodel. The latter removed purple accents and instrument material distinction.
- Changed: include authored keyboard case/stands; split static BODY/BASE_DIM RGB lanes by authored per-node colors; add explicitly nonmusical dim key/kit idle lanes which are zero during genuine source cues. Original musical arrays, node addresses, timestamps, source audio, short-arm constraints, legacy opt-in and AC16 circuit allocation are preserved. Native preflight now runs material/structure regressions before render.
- Tests:49 native source-pose/staging/artifact cases pass locally on Python3.12;35 existing LMS/layout-preference cases plus6 subtests pass. Broader test execution and fresh native job pending. Full decode, source music matching, physical devices and owner approval remain separate.
- Regression risks: more static submodels/effects; changed native color/detail readability requires fresh renderer/frame review. No harmony source invented; current strict consumer must retain its silent-harmony rejection. No merge/publication.
- Next: commit source/tests/workflow and both ledgers, record exact fresh native run, inspect exported material lanes/FSEQ and full decoded frames; retain independent backing/source and six-layout/full-song gates as open.

# Final roadmap and release handoff

Updated 2026-10-20 (startup recovery milestone). Status is evidence-based.
Statuses: [ ] not started; [~] in progress; [x] completed and verified; [!] blocked; [-] intentionally retired.









## Current checkpoint — native MP4 recovered, profiling measured, 2026-10-20
- **Fresh native producer SUCCESS:** [39473385296](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39473385296), source `b9f1ca0237c1819c4d99d69fb8bba3c4f333554f`. Actual compile/cache-save, dependency checks, private startup profile, sequence regeneration,1920x1080 native36s MP4/audio, full decode and luma/motion gates passed. Source startup/media recovery is evidenced; appearance is not yet owner-approved.
- [Video + editable XSQ/FSEQ/source package12290387567](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39473385296/artifacts/12290387567): ZIP SHA256415dc3f153b82f0b84b63454c7f5bd35146909c5a55b3df8d9d60462b259c114. Do not call this a full-song/six-layout deliverable or a later integration source render.
- **Strict complete-band consumer FAILED:**39473385254/job118804387655: no non-rest musical effects for HX_SNOW_HARMONY. Preserve this exact source-backed vocal blocker. Drive stem searches found no candidates, not proof of universal absence. Do not restart unchanged E14 input or fake second vocals.
- **OPT01 representative-excerpt profiling passed:** [39478636237](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39478636237), source d8709f5. Four actual CLI runs, former/current/current/former. Former72.1475s mean vs current29.0256s; peak RSS859048 vs621592KiB. All four selected XSQs byte-identical with8038 model effects. Same current code/DSP cache; former options reconstructed, history/learning disabled, one36s excerpt and cProfile/cold-cache limitations. No historical executable/catalog-wide claim.
- Raw summary: evidence/real_cli_profile_20261020/log_summary.json. Full JSON/pstats/XSQs/logs:artifact12291227053, ZIP SHA2562253b6a751f79ccba3c5bae958aac5fb0d8d996e604e93f68956e029a32d9b7d.
- **CI02 missing-producer wait fix tested:** PR191/source831e37a; Node39479496217 passed10 behavioral cases. Absent source fails after5 polls(two minutes), queued/running source retains110-poll allowance. Source/repository/named-live-artifact checks and all downstream media gates remain. No native jobs cancelled.
- Earlier EXP02 remains complete: canonical LMS conversion exact-settings fix. Profiling CI39478636195 and polling CI39479496015 each passed1966 tests+16 subtests/6 skipped on BOTH Python3.11/3.12, with both lint jobs passing. Actual CLI3.12 profiling and all10 Node polling tests also passed.
- Live CI02 workflow39479496095/job118825815030 loaded the new helper and correctly FAILED an absent producer after~122 seconds(19:03:16–19:05:18). This demonstrates missing-source diagnostics, not native acceptance. Producer/event coverage is still separate future work.
- Native build cache was an actual miss and compiled18:20–18:58; successful cache save now observed. Restored-cache runtime still needs an actual hit before marking that separate path verified.
- **Release INCOMPLETE.** Next: owner visual review of this native package; recover/derive independently evidenced backing analysis, then rerender a changed input. Continue remaining real production/export/layout checks, full-song/synchronized six-layout assets, packaging and physical Windows/Android/CTB16PC validation. Preserve source hashes and release/publication hold.
- Local execution remains unavailable; no local tests, artifact extraction, image/video visual review or device checks claimed.

## EXP02 completed — audited legacy LMS conversion, 2026-10-20
- Tested source `90b15d09d05072a5b954489bd6eb779ba0201538`, [PR189](https://github.com/ryankorkowski-boop/helix-sequencer/pull/189), now incorporated into development.
- Fixed substring acceptance of Start=1000/End=100.5, disabled or modified palettes and hidden brightness modifiers. Only the canonical flat-On/white-palette fields are converted to intensity100. Reordering/whitespace are accepted; duplicates and malformed/unsupported settings fail before output.
- [Full CI39476903541](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39476903541): **1966 passed,6 skipped,16 subtests** on each Python3.11/3.12; both lint jobs passed. All ten new export cases ran in these full suites.
- Beta39476903476, Birdsong39476903636, Windows packaging39476903483 and license39476903374 passed. Dedicated new focused workflow has no separate run; do not claim one.
- Source files: tools/legacy_lms_export.py; tests/test_legacy_lms_export.py. Canonical master ledger records limitations and compatibility risk for externally modified XSQs.
- Integration intentionally skips CI to preserve original native producer39473385296 at b9f1ca0. Its install/build remains active at18:49UTC. Exact consumer39473385254 remains pending. Do not queue a duplicate or relabel that footage as this later source SHA.
- EXP01 dual-default/native import/physical CTB16PC validation remains open. Native acceptance, keyboard visual review, independent backing, real-audio profiling, full-song/six-layout assets and physical Windows/Android checks remain open. **Release INCOMPLETE.**

## Live run checkpoint — 2026-10-20 18:25 UTC
- Runtime source revision: `b9f1ca0237c1819c4d99d69fb8bba3c4f333554f`. The documentation-only commit containing this update does not alter runtime code; it intentionally skips CI to preserve this source run.
- Effective native producer: [39473385296](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39473385296). Preflight118803027735 passed; render118804074546 started18:19UTC and remains in Install checksum pinned native xLights after source retrieval/cache lookup. Actual cache-hit/miss for this run is not yet available from completed logs; do not infer success from the step name. No accepted MP4 yet.
- Superseded duplicate push39473336387 cancelled during preflight; no healthy native render was cancelled. One effective producer remains.
- Exact-source consumer: [39473385254](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39473385254). Diagnostic native-proof118802997831 passed. accepted-native-band118804387655 waits for successful exact-b9f1ca0 producer; fixture success is not musical acceptance.
- Prior genuine compile39467730818 saved698,927,819-byte source/build cache at18:10UTC; current upstream patch file is identical (Git blob d6e0739c3d31e7e44bcdff25c9bd223bbad3bef8). Current restoration behavior is still under observation. Do not launch duplicate full builds or cancel the healthy run speculatively.
- Source/vocal candidate tests39473005943 passed27 unittest+51 pytest; real-source proof and declared-vocal-slot tests are preserved below.
- Release decision: **INCOMPLETE — CONTINUE IMPLEMENTATION**. Missing independent E14 backing evidence remains a separate actual blocker even if native recovery succeeds.

| ID | Status | Requirement / files | Branch / relevant source | Tests / Actions | Artifacts | Blocker | Next action |
|---|---|---|---|---|---|---|---|
| NAT03 | [~] | Private owned Linux profile disables optional tip; tools/native_preview.py, tests/test_native_preview_resolution.py, fresh-real-band-mp4.yml | recovery branch, b9f1ca0 (tested83fc26b) | 27 startup tests pass; fresh native39473385296 active | No accepted new MP4 | Live installation/render pending | Inspect runtime ldd, profile/window/health JSON, native dimensions/audio/luma/motion |
| KEY02 | [x] | Bounded rest anticipation in actual universal keyboard motion; keyboard_motion_plan.py, musical_band_performance.py | recovery, integrated1be1e0/tested8420ec0 | Real source39471482781:190->260 contacts,76 cue arrays unchanged; 44 keyboard/artifact tests +24 startup pass |12286444058 and committed source_contact_audit.json | None for source implementation; native appearance separate KEY01 | Review fresh source-b9 native pose-bank footage |
| VOC03 | [x] | Fixed lead0/backing1 slots, collision refusal; prepare_vocal_roles.py, test_prepare_vocal_roles.py | recovery, b9f1ca0/tested95b7f5 |51 focused pytest pass including7 public-preparation cases | Tested NPZ/JSON fixtures; source audio preserved | None for slot implementation; no E14 backing created | Apply only to actual declared source parts |
| VOC01 | [!] | Independent E14 backing activity; retained voice_roles.json/npz | Original archive bound to audio8905fcaf... |39472148043: mixed-only input,0 independent tracks, energy/shapes[630,0] |12288276045; committed source_contact_and_voice_audit.json | Retained source contains no independent backing lane | Recover/generate evidenced independent vocal analysis; never fake a second mouth |
| BAND02 / PROV01 | [~] | Actual musical XSQ lanes and same-SHA artifact provenance; verify_native_band_artifact.py, beta-completion-native.yml | recovery, b9f1ca0 |32 original acceptance tests plus later focused suites pass; consumer39473385254 awaits producer | Acceptance report pending | Native success first; harmony expected to fail truthfully | Inspect exact consumer error and report, not merely producer start |

### Next agent's immediate commands
- Inspect current branch HEAD and both ledgers. Current runtime evidence is tied explicitly to b9f1ca0; do not claim a later documentation SHA was natively rendered.
- `gh run view 39473385296 --repo ryankorkowski-boop/helix-sequencer`; when finished, `gh run view 39473385296 --repo ryankorkowski-boop/helix-sequencer --log-failed` if needed.
- `gh run view 39473385254 --repo ryankorkowski-boop/helix-sequencer`.
- If producer succeeds, fetch only its actual named artifact, check native_startup_profile.json, native_startup_health.json, original audio, media hashes and strict quality report. Preserve the genuine MP4 and editable files. If consumer rejects silent harmony, retain source blocker rather than rerunning unchanged input.
- If producer fails, use its actual completed diagnostics and error before changing code. The private setting is source-confirmed; its live execution remains unverified until this run completes.

## Previous implementation checkpoint — source-verified keyboard, vocal slots, private native profile
- Recovery parent inspected: `1be1e0654085f6389a39d0f315063f0f57a85a10`. This integration contains tested candidate `83fc26b03feb89ba5be8c0b88e4286dc179bd108` plus source-evidence/audit metadata and ledger updates.
- [Focused run39473005943](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39473005943), job118801660716: **27 unittest passed in0.051s;51 pytest passed in2.02s; compilation and workflow YAML parsing passed**.
- NAT03 [~]: pinned Linux2026.18 renderer now gets a unique private XDG config/state profile with `main.MinTipLevel="Off"`, output disabled, migration complete. Source code proves non-forced startup tips obey this setting. User profiles/environment and existing xLights processes are untouched; owned-process/REST/window diagnostics remain mandatory.
- NAT01/NAT02 [~]: genuine native recovery still requires fresh run acceptance. Prior [39467730818](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818) at0a2fceb **failed** after successful full compile, ldd, cached-build preservation and active FSEQ: `xLights startup dialog remains viewable after dismissal`. It was a real cache miss, not a frozen queue; compile completed17:40–18:10UTC. Diagnostics [12286908211](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818/artifacts/12286908211). No MP4 from that run.
- Fresh integration commit will start one producer/consumer at its exact source SHA. Cache patch hash remains unchanged. Inspect actual cache hit and restored wxWidgets installation; do not assume successful restoration from an executable's presence.
- KEY02 [x] source-motion implementation verified:190->260 contacts,76 cue lanes byte-identical,367 notes retained, audio SHA unchanged. KEY01 native appearance/pose-bank review remains [~].
- VOC03 [x] fixed declared-role placement and verified public prepare()/NPZ/JSON: lead0, backing/second1, explicit model_lane, collision refusal, instrumental silence and source preservation. Existing retained analysis is not silently regenerated.
- VOC01 [!] independent E14 backing source missing: [source evidence run39472148043](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39472148043) at4845afa confirms exactly one `demucs_mixed_vocals` input, `mixed_bus_only=true`, `voice_identity_resolved=false`, `independent_tracks=0`,630 lead-active frames and0 backing-active frames in both energy and shapes. Source SHA matches original. [Artifact12288276045](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39472148043/artifacts/12288276045), ZIP SHA2560a5490a1bb1f8a5e997b27e5685fa42f538ef52d72d7d912c234e622b28c3925.
- Exact measured combined report: `evidence/keyboard_contact_recovery_20261020/source_contact_and_voice_audit.json`. This explains E14 silence upstream; it is not a dropped nonzero backing lane. The generic slot fix does not create independent E14 vocals.
- Final-band verifier must reject E14's absent non-rest harmony rather than falsely passing body/rest illumination. A successful producer MP4 can establish native recovery while overall band/release acceptance remains incomplete.

### Immediate next steps
1. Inspect the new recovery source SHA and its fresh-real-band-mp4.yml run (push/PR may initially create two entries; shared concurrency must leave one effective producer).
2. Require native startup_profile showing private settings, startup_windows not blocked, startup_health with alive process/responding REST, actual FSEQ, native1920x1080 MP4 and original-audio/brightness/motion checks.
3. Inspect beta-completion-native.yml matched exact-SHA producer. If it rejects HX_SNOW_HARMONY for no non-rest effects, retain that precise source-evidence blocker; do not repeatedly restart unchanged jobs.
4. Record actual run IDs/artifacts in this file and MASTER_TODO.md. Continue source-backed vocal extraction, real native review, production intelligence/profile/export/layout/packaging and showcases from the remaining roadmap below.
5. Keep all source hashes/strict quality gates and no default merge/release/publication hold.

**Decision: INCOMPLETE — CONTINUE IMPLEMENTATION.** No fresh MP4 or independent backing/source accuracy has yet been accepted.

## Earlier checkpoint — native startup-profile recovery
- Native run39467730818 completed with failure at0a2fceb. Compile and ldd passed; genuine FSEQ rendered. The tip remained IsViewable across5 attempts; error: `xLights startup dialog remains viewable after dismissal`. [Diagnostics12286908211](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818/artifacts/12286908211). No accepted MP4.
- Logs confirm cache miss, then completed pinned native build and successful cache save. No speculative cancellation or duplicate compile occurred.
- Pinned upstream839c0f inspected: XLightsConfigAdapter.cpp reads Linux XDG_CONFIG_HOME/xLights/settings.json. TipOfTheDayDialog::DoTipOfDay(false) returns without showing when main.MinTipLevel="Off"; sequencer/tabSequencer.cpp startup event uses false. --quiet only suppresses command-line notices.
- NAT03 [~]: fresh Linux renderer gets a unique private XDG config/state profile seeded with MinTipLevel=Off, OutputActive=false and migration marker. User config and existing xLights processes are untouched. Existing PID/window diagnostics + post-dismissal process/REST gate remain enabled.
- New tests check private JSON schema, no user/environment mutation, distinct profiles and non-Linux preservation; candidate focused tests pending. Native workflow uploads native_startup_profile.json.
- Vocal slot correction at95b7f508 passed focused run39472449599. E14 source evidence in39472148043 confirms one demucs_mixed_vocals input, mixed_bus_only=true, independent_tracks=0, measured energy/shapes active frames[630,0], and original source SHA match. Slot fix cannot create independent E14 backing.
- Next: pass profile tests, integrate tested source/vocal changes and source evidence, then trigger exactly one fresh native producer on recovery SHA. Cache patch hash is unchanged; inspect runtime restore and real MP4 output before completion.

## Vocal preparation slot correction candidate (earlier checkpoint)
- Branch work/vocal-lane-placement-20261020; base1be1e0654085f6389a39d0f315063f0f57a85a10. Native run39467730818 remains active.
- VOC03 [~]: tools/prepare_vocal_roles.py previously packed ordered voices from column0, promoting background-only/second-only input into the lead slot. Consumers assume fixed lead=0/backing=1.
- Candidate assigns each declared role to its fixed slot, records model_lane explicitly, and rejects independent tracks colliding in the one backing slot instead of silently merging or relabeling them.
- Tests exercise public prepare() and exported actual NPZ/JSON with supplied acoustic-clock fixtures, source hash preservation, independent shapes, collisions and instrumental silence. They do not claim real-source separation accuracy.
- E14 source evidence inspection is running separately in39472148043; no assertion that this generic bug explains that source's silence yet.

## Verified source-contact milestone — 2026-10-20
- Tested candidate source commit: `8420ec04696b14efdd4d89d645c8f18cecf9c295`. [Run39471482781](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39471482781) passed focused tests and the actual real-source comparison. [Report artifact12286444058](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39471482781/artifacts/12286444058); ZIP SHA25637b5bddf8397ae0a98fcbd17e46bc6e012735c2f351bca8774e9dedb24030b71.
- KEY02 [x] implementation + source-kinematic validation: source-contact frames **190 ->260** (+70,36.84%). Left168->207, right22->53. Source-active frames remain474/144; all367 accepted events retained. Remaining source-active frames without contact: left267, right91. This is improvement, not perfect physical coverage.
- Musical clock parity: all76 non-pose musical cue lanes are byte-identical before/after; digest `6c94a6a186ea3aca78719a0ec7ba11eb4ea220a4a90911f239a3cc2fe557c8e2` matches both. Original WAV SHA remains8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171.
- Preparation wall times baseline24.174s/candidate24.266s. This is a contact audit timing observation, not a complete audio-to-sequence performance profile or speedup claim.
- Initial focused run39471158993:24 unittest +44 pytest cases passed. Candidate rerun39471482781 focused job passed as well; Python/workflow validation passed. Isolated production installation method is executed with its actual event compiler and planner, not a replacement algorithm.
- Committed raw measured report: `evidence/keyboard_contact_recovery_20261020/source_contact_audit.json`.
- Tested keyboard source implementation is integrated on recovery with [skip ci] to preserve healthy native run39467730818. The actual xLights movie from this newer source commit is still pending; source contacts do not prove medoid native playback or artistic acceptance.
- KEY01 native visibility/appearance/contact acceptance remains [~]. VOC01 backing-source evidence remains unresolved. Original native run still installing/building; after it completes, follow exact-source dispatch instructions below for the newer recovery HEAD.

## Real-source keyboard audit (earlier checkpoint)
- Candidate source-motion tests passed in [39471158993](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39471158993) at55f9fb1. Confirm exact counts from job logs.
- Added tools/audit_keyboard_anticipation.py and a dependent real-source-contact job in the focused workflow. It recovers the exact SHA-verified original archive/audio, runs actual native source-pose preparation twice, disables only anticipation for baseline, compares non-pose musical cue arrays and source activity, and requires increased contacts without regression in either hand.
- This is source preparation/kinematic evidence only. Native video, medoid playback, musical ground truth and hardware acceptance remain explicitly false.
- Original native run39467730818 is still healthy/in progress; do not cancel it for this independent audit.

## Keyboard contact recovery candidate — 2026-10-20 continuation
- Recovery HEAD inspected: 769d6d17db034de83ebf3799518449b2cc12cea5. Native run39467730818 remains in renderer install/build as of17:58UTC; it is not cancelled.
- Candidate branch: work/keyboard-contact-recovery-20261020. KEY02 [~]: add opt-in, 12-frame (600ms) motion lookahead during rests for the short-arm universal keyboardist. Hand speed .030 and acceleration .010 limits, own-half/reach filters and source note-light timing stay unchanged. Only source-active notes can claim contacts.
- Default legacy planner remains reactive (anticipation_frames=0). Guitar/bass/drum/vocal routes and arm lengths are untouched. Future reachable frames are indexed once per hand.
- Files: models/keyboard_motion_plan.py, tools/musical_band_performance.py, tests/test_keyboard_anticipation.py, focused test workflow, both ledgers.
- Tests pending candidate CI: compare single-frame short-note contact with and without anticipation for both hands; verify speed/acceleration/link reach/no early or invented contacts; reject invalid windows/unreachable notes; execute the isolated actual production installation method with the real event compiler/planner and verify unchanged note arrays.
- This is a source-motion improvement candidate, not evidence of improved E14 footage. Actual source contact audit and native video review remain required. Do not integrate until focused tests pass; do not restart the healthy native build to test this.

## Current execution checkpoint — tested acceptance integrated without interrupting native build
- Recovery branch now contains the startup/process/REST fix, cached wxWidgets runtime restoration, headless loader diagnostics, and stricter musical-activity/exact-source acceptance. This commit intentionally uses `[skip ci]` to leave the healthy renderer installation/build in run39467730818 intact.
- Tested acceptance source: `1c471c41564fef5df047387513ace640b289dfa4` on `work/native-acceptance-evidence-20261020`; [focused run 39468604731](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39468604731), job118786433373: **24 unittest cases passed (0.039s), 32 pytest cases passed (1.63s), Python compile and workflow YAML parsing passed**.
- Current integration changes the candidate checkpoint documentation only; the runtime/verification code is the tested candidate code. Full current-HEAD native output and release acceptance remain **unverified**.
- Active native run: [39467730818](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818), source branch head `0a2fcebd63314db906c3f112560c24bcc42f307f`, actual PR checkout `0c6f89a`; preflight24+7 passed. Render job118783981953 was still in “Install checksum pinned native xLights” at 17:44 UTC. Do not cancel healthy compilation. No new accepted MP4 exists yet.
- The run above uses the older permissive artifact verifier. Even if its consumer turns green, that is **not** proof of the stricter current verifier, independent backing vocals, or current integration SHA.
- BAND02 implementation is tested: transported XSQ must contain actual timed musical effects for each of six performers; BODY, idle pose banks and MOUTH_rest cannot substitute. The source visibility audit also excludes rest from active mouth counts.
- PROV01 implementation is tested: checkout exact source head, assert actual git HEAD, write source_commit in manifest + PROVENANCE, require consumer --expected-commit. Missing/earlier/mismatched identity fails.
- VOC01 remains unresolved: retained E14 harmony lane is entirely at rest. A current final-band check is expected to refuse acceptance until actual source-backed activity is present. Do not fabricate second vocals or claim inferred identity as verified separation.
- KEY01 remains unresolved: source contact counts show gaps; no untested choreography alteration was introduced.
- Source audit findings and hardware/device limits are retained below. New native media, six-layout/full-song assets, measured real-audio profiling and physical runtime validation are unfinished.

### Exact continuation after the healthy native run completes
1. Fetch the recovery branch and record actual `git rev-parse HEAD`; read AGENTS.md and MASTER_TODO.md. The commit containing this checkpoint is the integrated acceptance milestone; its parent is `0a2fcebd63314db906c3f112560c24bcc42f307f`.
2. Inspect run39467730818, native-runtime-libraries.log, native_headless.log and native_startup_health.json. First establish loaded binary, then genuine active FSEQ, then live GUI/REST after dismissal, then genuine HD MP4. Record exact failure if any.
3. Do not silently use that earlier-source run as current proof. After it finishes, dispatch a fresh producer at the current recovery branch; with authenticated gh:
   `gh workflow run fresh-real-band-mp4.yml --repo ryankorkowski-boop/helix-sequencer --ref codex/eight-hour-recovery-20261019 -f archive_file_id=1XZTghW96Adc27iL4b_7Vi8kBJQzLCM1j -f archive_sha256=604107acea8e57e8e5436b6bcbcb6f584806a4bed3a85679f72295d340c37b10 -f audio_sha256=8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171`
4. Run its matching consumer:
   `gh workflow run beta-completion-native.yml --repo ryankorkowski-boop/helix-sequencer --ref codex/eight-hour-recovery-20261019`.
   The consumer selects only the exact same SHA and independently checks bytes/audio/video/model activity. Missing harmony must produce an explicit failure, not rest-mouth acceptance.
5. Original audio/source hashes, native size/luma/motion thresholds and default-branch/release hold stay unchanged. For backing activity, inspect voice_roles.json/npz with the original source; independently isolated tracks or evidenced source analysis is required before claiming independent voices.
6. Continue the remaining roadmap below. Update both ledgers with actual run IDs, source SHAs, artifacts and limitations at each milestone.

**Decision remains INCOMPLETE — CONTINUE IMPLEMENTATION.** No fresh native MP4, final-band completion or physical-device approval is claimed.

## Earlier implementation checkpoints (historical; current checkpoint above takes precedence)
## Recovery result at 7f2f568 and cached-runtime follow-up
- Commit: `7f2f5686df0a888b6433e1a30c89f109d1b1c78b`; [native run 39466709677](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39466709677), PR checkout `90b4333`.
- Preflight job 118779879306 **passed**: 23 native-preview tests in 0.026s, 7 source-selection tests, compileall. Includes seven new safe-dismissal/process/REST regression cases. This verifies tests, not real GUI survival.
- Native render job 118780967104 **failed before GUI startup**: `Native headless render exited 127`. [Diagnostic artifact 12285522374](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39466709677/artifacts/12285522374); no accepted MP4.
- New finding from pinned upstream Makefile and reference build logs: wxWidgets shared libraries are built inside cached `wxWidgets-xlights_2026.17c/lib` but installed into `/usr/lib` during a fresh build. Restoring only xlights-src skips that installation on a new runner. The exact failed loader message was hidden inside native_headless.log.
- Follow-up change restores the cached wxWidgets installation (`sudo make -C wxWidgets-xlights_2026.17c install`, then ldconfig) before cache-hit early return; runs ldd and rejects unresolved libraries before sequence/render; uploads native-runtime-libraries.log. It preserves the cached compiled renderer and does not trigger a speculative full recompile.
- Headless failures now include the actual last 4000 log characters in the run manifest/Actions output; one added regression tests exit127 with the missing-library diagnostic. Follow-up preflight execution pending.
- Next: inspect follow-up native preflight (24 expected tests), runtime ldd report, actual headless FSEQ, then post-dismissal health and native MP4. Do not rerun 7f2f568 as proof of follow-up changes.

### Additional source audit (not full implementation acceptance)
- Production `core/effect_engine.py` defaults CLI variants to 1 (line 12789) and uses internal `_SongAnalysisCache` near line 13102. `core/audio_run_cache.py::AudioRunCache` is a separate hash-verified implementation not used by that entrypoint; evaluate consolidation only with real-audio baseline/parity evidence.
- `core/sequence_builder.py` already makes orchestration opt-in; `core/effects_orchestration_bridge.py` is a compatibility re-export, not a second engine. `effects_orchestrator_bridge.build_seed_graph` still seeds five fixed sections and defaults to 30s rather than deriving structure from audio. Do not silently enable this demo-like schedule as musical ground truth.
- Matrix intelligence CLI describes shader planning in reports. A report recommendation is not proof a native Shader effect with packaged resources was exported. Trace actual exported effects/resources before completion claims.
- Desktop license GUI, root LICENSE/NOTICE/README/COMMERCIAL_LICENSING.md and Android InfoActivity Legal content are PolyForm/separate commercial terms; existing MIT mentions describe third-party or earlier grants and must remain. Android InfoActivity exposes Instructions + Legal; full license asset also exists. Full distribution surface audit remains open.
- Desktop layout_preferences saves to user config and reloads only an existing file; Android MainActivity restores URI selections from SharedPreferences and persists granted URI access. Source presence does not establish device behavior.
- Actual native artifact verifier currently accepts any effects per model, so body/rest-only harmony could pass transport. Next acceptance fix must require non-rest mouth and actual NOTE_MIDI/STRING/drum effect lanes, while preserving the distinction from independently proven vocal sources.


## Acceptance candidate checkpoint (subsequently tested and integrated)
- Candidate branch: `work/native-acceptance-evidence-20261020`, based on `0a2fcebd63314db906c3f112560c24bcc42f307f`. Recovery branch's active [native run 39467730818](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39467730818) remains intact.
- Recovery preflight at 0a2fceb: job118783515172 passed **24 native-preview tests in 0.031s plus 7 source-selection tests**. Native job118783981953 still installing renderer; do not cancel healthy work.
- BAND02 [~]: verifier now checks actual transported XSQ lanes for non-rest mouth, NOTE_MIDI, STRING and physical drum-hit effects with positive bounded intervals; BODY/rest-only models cannot establish playing. Reports per-model musical counts and leaves independent-vocal-source verification explicitly false.
- PROV01 [~]: producer/consumer checkout the exact requested PR head SHA; producer asserts git HEAD, writes source_commit to run_manifest.json and PROVENANCE.json; consumer CLI requires --expected-commit and rejects missing/mismatched provenance.
- VOC02 [~]: source visibility audit excludes MOUTH_REST from active_mouth_parts, so 720 resting frames no longer suppress the absent-harmony warning. No vocal events or source audio are fabricated or changed.
- Candidate files: tools/verify_native_band_artifact.py; tests/test_native_band_artifact.py; tools/native_source_pose_band.py; fresh-real-band-mp4.yml; beta-completion-native.yml; native-acceptance-regressions.yml; both ledgers.
- Tests: focused candidate workflow passed at 1c471c4 (24 unittest +32 pytest); integrated at current checkpoint. Cases cover silent performer per role, rest-only harmony, zero/reversed/out-of-range intervals, missing/mismatched/invalid commit provenance, and existing source hashes/media transport.
- Integration updated: tested code is now on recovery with [skip ci] to preserve its healthy active build. After that run completes, dispatch fresh exact-SHA producer and consumer using the current checkpoint instructions above. Do not mark final-band complete if it correctly rejects silent harmony.
- Existing native producer may be compiling on cache miss; completed cache-restore step was near-instant. Do not assert cache hit without logs.
- Source-policy audit: read the current supplied model_effect_policy.py (Library version2) and helix_effect_adapter.py (version1). Both explicitly say standalone integration candidates, with native catalog validation required; direct Shader insertion lacks a packaged shader-resource guarantee. Keep their candidate status and avoid creating a duplicate production selector.



## A. Current repository state
- Branch: `codex/eight-hour-recovery-20261019`; inspected parent HEAD: `746b63f110f9dbbd5a8f2c68826317944a388e27`. The commit containing this checkpoint is the startup-recovery child of that SHA; use `git rev-parse HEAD` after fetching.
- Integration [PR #188](https://github.com/ryankorkowski-boop/helix-sequencer/pull/188): open, draft, base `feature/restructure-core`. No merge/publication authorized.
- Working tree: changes are committed atomically through GitHub Git Data API; no local checkout/runtime available in this session. Do not interpret this as a checked local clean tree.
- At inspected HEAD, core CI 39449667720, beta CI 39449667902, Windows 39449667881, Android 39449667728, license bundle 39449667741 passed.
- Last successful native producer: [39414958884](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884), head lineage `ff019a902d721504e599701b7433f6a3091b8f92`; PR checkout was synthetic merge `175a50b`. Preserve both provenance values.
- Regression: `746b63f` adds unconditional `xdotool windowclose` after cooperative dismissal. Failed run's X11 tree contains only Openbox afterward; export receives connection refusal. Correlation strongly implicates destructive closure; no direct exit trace yet.

## B. Completed and verified
- [x] REC01: fetched actual HEAD, PR metadata, root AGENTS.md (only AGENTS.md found in recursive tree), canonical MASTER_TODO.md, failed job 118721373351 and successful reference job 118602350198.
- [x] REF01: successful native reference confirmed from Actions logs: median luma 24.072 (>=12), bright fraction 0.13098 (>=0.012), motion 0.921 (>=0.65), original-audio verification and native decode steps passed.
- Reference artifact: [12264050159](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884/artifacts/12264050159). Historical evidence only; not acceptance of current changes.
- No new native movie or new test pass is claimed at this checkpoint.

## C. In progress
All rows use branch `codex/eight-hour-recovery-20261019`. Commit/evidence identifies inspected parent or this recovery change, not a presumed passing build.

| Task ID | Status | Description | Files | Commit | Tests | Actions | Artifacts | Blocker | Next action |
|---|---|---|---|---|---|---|---|---|---|
| NAT01 | [~] | Restore safe startup dismissal and process/REST survival | tools/native_preview.py; tests/test_native_preview_resolution.py | Recovery child of 746b63f | 7 added cases plus exact 2-command assertion; execution pending CI | Native push workflow preflight gates render | native_startup_health.json uploaded even on failure | No local runtime | Inspect preflight then native producer on recovery SHA |
| NAT02 | [~] | Genuine 1920x1080 original-audio native movie and strict visual gates | .github/workflows/fresh-real-band-mp4.yml | Recovery child | Existing HD/audio/luma/motion gates unchanged | Last failure 39449667724 | Failed diagnostics 12281386545; no MP4 in failed run | Fresh render required | Inspect successful producer logs and decoded frames |
| BAND01 | [~] | Exact-head artifact verification | tools/verify_native_band_artifact.py; beta-completion-native.yml | Present at 746b63f | Existing verifier tests; fresh consumer required | Last failure 39449667840 | None accepted for recovery SHA | Producer dependency | Check accepted-native-band at same source SHA |
| KEY01 | [ ] | Visible complete keyboard, pitched key activity, natural contact | tools/native_source_pose_band.py; source choreography | 746b63f baseline | CI 39449667850 passed; visual acceptance absent | Native producer pending | Retained source data, not approval | Failed-run audit: left contact 168/474 active frames, right 22/144 | Inspect source contact mapping and fresh decoded native frames |
| VOC01 | [ ] | Independently active backing singer with restrained lyric mouth | vocal/role analysis and native_source_pose_band.py | 746b63f baseline | No vocal ground truth claimed | Failed producer source audit available | Harmony mouth_rest=720/720, active non-rest parts=0 | Actual backing role inactive in retained analysis | Inspect role extraction before changing activity; never fabricate harmony |
| PERF01 | [ ] | Drummer/guitar/bass synchronization and independent snowman performance | source band geometry/choreography | 746b63f baseline | Drum CI 39449667963 passes; musical review still open | Fresh native pending | Historical reference only | Needs actual media review | Review instrument passages including fast kick and solos |
| AUD01 | [ ] | Recover/integrate developed unused intelligence and effects | audio/; core/; music/; effect policies | Prior ledger retained | Prior 79-test subset historical | Core CI passes at parent | None new | Current entrypoint coverage audit incomplete | Trace real sequencing entrypoint to existing analysis, styles, Meteors/Shader assets |
| OPT01 | [ ] | Representative real-audio time and memory profile | core/sequence_builder.py; audio caches | Parent already defaults 1 variant; unused sidecar opt-in implemented earlier | No new baseline/after measurements | None new | None | Local runtime absent | Profile same real source, record wall/RSS and musical output parity |
| EXP01 | [ ] | Independently editable XSQ/FSEQ plus supported dual LMS and AC safety | xlights/; lor exports; model mapping | Parent baseline | File-level checks pending fresh exports | Parent CI historical | Reference XSQ/FSEQ retained | Native import/CTB16PC hardware not established | Validate generated files/timing; document physical limits |
| LAY01 | [ ] | Layout selection persists across desktop/Android runs | layout_preferences.py; GUI/config | Prior settings recovery tested historically | Fresh persistence/runtime evidence needed | Desktop capture 39449667991 passed at parent | No new runtime package | Real-device checks absent | Inspect saved selection and missing-layout behavior |
| WIN01 | [~] | Portable EXE runtime and licensing | packaging/Windows GUI | 746b63f | CI build passed; physical Windows untested | 39449667881 success | Query current run artifacts before use | No Windows device | Review package/startup/export/offline evidence |
| AND01 | [~] | APK runtime, storage, playback, persistence | Android GUI/package | 746b63f | CI build passed; physical Android untested | 39449667728 success | Query current run artifacts before use | No Android device/emulator this session | Collect available CI checks and owner-device feedback |
| LIC01 | [~] | PolyForm Noncommercial and separate paid commercial licensing consistency | LICENSE; NOTICE; GUIs; package metadata | 746b63f | License bundle passed; surface audit incomplete | 39449667741 success | Query artifact before use | Full current distribution audit pending | Audit first-party MIT mentions; retain required third-party notices |
| SHOW01 | [ ] | Six-performer native preview | native workflow | Recovery SHA pending | Strict native checks required | NAT02 dependency | No new MP4 | Native render pending | Complete NAT02 then inspect six performers |
| SHOW02 | [ ] | Six synchronized distinct layouts | showcase pipeline | None newly verified | No acceptance | None new | None | Native core first | Generate same-passage native panels after band acceptance |
| SHOW03 | [ ] | Full-song native demonstration | source/showcase pipeline | None newly verified | 36s reference is not full-song | None new | None | Source analysis/native runtime | Use authorized original full-length source and preserve duration |
| SHOW04 | [ ] | Advertisement, teasers, highlights | promotional pipeline | Historical assets preserved | No fresh approval | None new | None | Core band acceptance first | Produce only after SHOW01; no publication |
| HAND01 | [~] | Continuous handoff and canonical ledger | docs/FINAL_ROADMAP_HANDOFF.md; MASTER_TODO.md | This recovery change | Evidence updated with every milestone | Runs to be recorded after push | GitHub tracked files | None | Append actual SHA, tests, runs and artifacts |

## D. Blocked
- Local execution: exec_command returned exactly `No usable execution environment is available. Wait for an environment to become available before using this tool.` No local tests, rendering, profiling, install or physical checks claimed. GitHub source edits and Actions remain available.
- Native failed job 118721373351 at 746b63f: `Native audio preview unavailable; retain XSQ for xLights: <urlopen error [Errno 111] Connection refused>`. FSEQ was active (720/720 frames, 33,617,814 nonzero samples); the failure occurred after GUI startup handling, before video export.
- Backing voice audit in the same job: harmony had only rest frames (720), all 9 non-rest phoneme tracks zero. Do not mark two-vocal acceptance from performer presence alone.
- Keyboard contact audit: 306/474 left-active and 122/144 right-active frames lacked source-key contact. Source estimators explicitly do not establish musical ground truth.

## E. Remaining roadmap (priority order)
1. Require passing focused preflight, live owned process + REST health, accepted native MP4 on recovery commit.
2. Require exact-SHA consumer acceptance, source hashes/audio synchronization/independent editable rows and genuine FSEQ.
3. Fix and visually verify keyboard presence/contact and independently evidenced backing vocals; preserve six performers and snowman art.
4. Audit real production musical/effect entrypoints, profile actual audio, validate exports and layout persistence.
5. Review Windows/Android/license runtime evidence and identify remaining physical validation.
6. Produce synchronized distinct six-layout and full-song native assets; then advertisement cuts.
7. Owner visual/hardware review and explicit release approval.

## F. GitHub Actions status
| Run | Source SHA | Outcome | Evidence |
|---|---|---|---|
| [39414958884](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958884) | ff019a9 (PR checkout 175a50b) | success | Native reference artifact 12264050159 and strict readability pass |
| [39414958924](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39414958924) | Historical ff019a9 lineage; inspect checkout before reuse | Reported successful reference; consumer details not independently re-read yet | Historical only |
| [39449667724](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667724) | 746b63f | failure | [12281386545](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667724/artifacts/12281386545), diagnostic/source archive, not a successful MP4 |
| [39449667840](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39449667840) | 746b63f | failure | Producer unavailable |
| 39449667720 / 39449667902 | 746b63f | success | Core / beta CI; runtime acceptance separate |
| 39449667881 / 39449667728 | 746b63f | success | Windows / Android builds; physical checks separate |
| Recovery child | Inspect branch HEAD | Pending push and focused preflight | Never rerun failed old SHA as proof of the fix |

## G. Validation evidence and limits
- Exact source diff: 746b63f adds only two windowclose lines to tools/native_preview.py. Recovery removes those lines and adds post-dismissal process/REST checks with persisted JSON.
- Regression suite adds: safe Escape-only fallback, healthy process+endpoint, dead process before request, connection refusal, rejected REST, death during request, production export refuses to proceed after process death. Existing dismissal test now asserts exactly two cooperative commands.
- Required preflight command: `python -m unittest discover -s tests -p test_native_preview_resolution.py -v`. Not executed locally; CI must pass before render.
- Historical metrics above are verified from logs, not a fresh quality claim. Frame review, backing-source accuracy, physical controller/device performance and full-song assets remain open.
- Source audio identity remains SHA256 `8905fcaf105faf5016608517cf2d8a798d1809d8e615f1d4f5bca58e0c0b1171`; archive identity and renderer pin remain unchanged.

## H. Next Agent Starts Here
1. `git fetch origin codex/eight-hour-recovery-20261019 && git switch codex/eight-hour-recovery-20261019 && git pull --ff-only`; inspect `git rev-parse HEAD` and `git status --short`.
2. Read root AGENTS.md, MASTER_TODO.md, then this current checkpoint; older text below is retained history.
3. Run `python -m unittest discover -s tests -p test_native_preview_resolution.py -v`; broader installed-runtime suite: `python -m pytest tests/test_native_preview.py tests/test_native_preview_resolution.py tests/test_native_band_artifact.py -q`.
4. Inspect latest branch fresh-real-band-mp4.yml run. Do not queue duplicates or cancel healthy work. Preflight is a dependency of render.
5. Inspect native_startup_windows.json + native_startup_health.json + native_gui.log, ffprobe, readability and native artifact provenance. Require alive process and responding REST after dialog handling.
6. Inspect beta-completion-native.yml accepted-native-band consumer for exact producer SHA. Record run URLs/artifact IDs and results in this file and MASTER_TODO.md.
7. Continue KEY01/VOC01 while rendering; start with source audit counts above. Preserve estimator uncertainty and never invent backing-vocal events.
8. Keep release hold until all actual acceptance requirements are evidenced.

## I. Last Known Good
| Subsystem | Last evidence | Limits |
|---|---|---|
| Native startup / native MP4 / visibility | ff019a9 producer 39414958884 | PR checkout 175a50b; earlier footage only |
| Core and beta CI | 746b63f runs 39449667720 / 39449667902 | CI cannot establish artistic quality |
| Windows and Android packaging | 746b63f runs 39449667881 / 39449667728 | No physical-device validation claimed |
| License bundle | 746b63f run 39449667741 | All GUI/distribution surfaces still require audit |
| Keyboard focused regression / drum benchmark | 746b63f runs 39449667850 / 39449667963 | Contact/real-song ground truth remains open |
| Backing vocal acceptance / six-panel full-song showcase | No completed current evidence | Must continue implementation |

## J. Final release decision
**INCOMPLETE — CONTINUE IMPLEMENTATION**

No release/default merge, publication, public music distribution, physical-device success or fresh MP4 acceptance is implied by this milestone.

---

# Retained earlier handoff (historical; current checkpoint above takes precedence)

# Final roadmap and release handoff

Updated 2026-10-20. Branch: `codex/eight-hour-recovery-20261019`; inspected HEAD: `3077fb3fffbc9b0a16b22ad1850b1d1abc30eb63`; integration PR: #188.
Read `MASTER_TODO.md` and `docs/HELIX_LIVE_IMPLEMENTATION_CHECKLIST.md` for preserved history. This file records the current release gates. No default/release merge or publication authorized.

Status: [ ] not started; [~] in progress; [x] completed and verified; [!] blocked; [-] superseded with explanation. Code presence is not acceptance.

| ID / status | Task and files/subsystems | Commit / evidence | Remaining work and exact next action |
|---|---|---|---|
| REC01 [x] | Reconcile branch and latest Actions | HEAD 3077fb3; latest 20 branch runs queried; no newer HEAD | Continue checking after implementation commits |
| NAT01 [~] | Native startup dialog: tools/native_preview.py, focused tests | Run [39400549536](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549536), render job 118554038926: `xLights startup modal persists in X11 tree` | Implemented actual Map State/PID checks and persistent diagnostics; 16 focused tests pass. Commit and track fresh native Actions; real mapped state/MP4 still pending |
| NAT02 [ ] | Native camera/model/playback/export visibility | Same run: 720/720 FSEQ frames active; 128691 channels; 33617814 nonzero samples; mean lit 0.362818; no MP4 exported | After NAT01, run actual native export and inspect images/luminance/motion; keep thresholds |
| BAND01 [ ] | Final-band same-artifact dependency / XSQ editability / audio provenance | [39400549581](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549581) failed | Inspect exact job log and consumer workflow; bind to accepted native artifact |
| DRM01 [x] | Original V3 drummer source review / workflow download | Historical run 39400549476 failed gdown public-link retrieval; fresh [39413537064](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537064) success at f8a7b68; source authentication, 36s render and decode/sync checks passed | Artifact [12261025120](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537064/artifacts/12261025120); owner visual review remains; separate 3D source-art review, not native xLights |
| AUD01 [ ] | Production analysis/effects integration and performance | Prior recovery ledger retained | Inspect current tests, entrypoints, redundant variants/decodes, Shader/Meteors assets; implement measured fixes |
| PERF01 [ ] | Six-snowman musical and visual performance | Native review absent; separate 3D workflow success does not establish native acceptance | Review fresh genuine native footage incl. drummer, guitar, bass, universal keys, two singers |
| EXP01 [ ] | Native editable XSQ, layout persistence, AC/RGB, dual XSQ/LMS | Prior focused CI passed; native imports/hardware not established | Run focused integration tests and inspect generated native files; document LOR import limits |
| WIN01 [~] | Windows portable build and end-user validation | [39400549704](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549704) success at 3077fb3 | Inspect package/runtime evidence; no physical Windows validation claimed |
| AND01 [~] | Android offline build and end-user validation | [39400549441](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549441) success at 3077fb3 | Inspect runtime/storage evidence; physical Android testing remains unperformed |
| LIC01 [~] | Licensing/docs/package consistency | [39400549473](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549473) success | Audit remaining terms/documentation; preserve third-party notices |
| SHOW01 [ ] | Fresh native preview and synchronized six-panel comparison | No accepted new native MP4 | Complete NAT02 first; generate distinct layouts using authorized real audio; ads follow owner approval |
| CI01 [x] | Historical current-HEAD core and beta CI | [39400549607](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549607) and [39400549680](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39400549680) success at 3077fb3 | Revalidate relevant changed code; do not rerun unchanged successful builds |
| HAND01 [~] | Permanent checklist and master ledger | This change set | Update after every milestone; commit with implementation |

## Last Known Good
3077fb3: core CI, beta CI, Windows/Android packaging, keyboard regression, drum benchmark, license bundle and separate animated 3D band workflows pass. Native MP4 and final-band verification fail. No fully accepted release candidate.

## Failed approaches and pending runs
9eb8012: wmctrl dismissal alone did not establish dialog state. 3077fb3: string presence in X11 tree incorrectly used as visibility proof. Preserve actual window-state evidence next. No active runs found in latest 20 results at start.

## Next Agent Starts Here
1. Fetch current branch; `git status --short`; read this file and MASTER_TODO.md.
2. Finish NAT01 and run `python -m unittest discover -s tests -p 'test_native_preview_resolution.py' -v` plus dialog tests.
3. Commit tested changes and this checklist to development branch; inspect the resulting native workflow run, exact job logs, state diagnostics and frames.
4. Keep native 1920x1080, original-audio identity, luminance and motion gates. Do not promote diagnostic media or claim device/hardware testing.

Decision: **INCOMPLETE — CONTINUE IMPLEMENTATION**.

## Native startup milestone validation
`python -m pytest tests/test_native_preview.py tests/test_native_preview_resolution.py -q`: **25 passed, 1 skipped, 8 subtests passed** (0.94s). Skip requires a real native manifest; this is not native-render evidence. Compileall and diff-check pass.

## Continuation at f8a7b68
- Native startup fix committed: `f8a7b68c43ddbd50061de275a0c7b8188c49dc2c`. Native run [39413537205](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39413537205), render job 118597682419, compiling pinned xLights. Preflight and authentic source acquisition pass. Do not restart for speculative changes.
- Local production-focused suite: 69 passed + 6 subtests (layout/preferences, dual export, styles, native source pose, ownership, orchestration). Additional style/geometry/inventory suite: 37 passed. No native import or hardware validation implied.
- BAND01 consumer implementation prepared in `tools/verify_native_band_artifact.py`, `tests/test_native_band_artifact.py`, `.github/workflows/beta-completion-native.yml`: only successful exact-SHA native producer, exact named unexpired artifact, independent file hashes/6 editable XSQ rows/FSEQ activity/native dimensions/decoded audio correlation and unchanged luma-motion gates. Keeps diagnostic inventory separately; does not label a 36s clip as full-song completion. Pending commit and real producer acceptance.
- AUD01 performance: default already 1 variant and per-run analysis cache exists. `core/sequence_builder.py` still ran unused orchestration sidecar unconditionally; prepared opt-in `--effects-orchestrator`, with promotion flag still enabling orchestration and disable flag taking precedence. Engine argument/output path is unchanged by default. 16 builder/bridge tests passed. Pending milestone commit and CI.
- Combined changed-code/nearby suite: 79 passed, 1 native-manifest-dependent skip, 14 subtests (3.04s). Full collection found 1874 tests plus 3 missing-torch collection errors in this local environment; full local suite not claimed.
- Local native fallback investigation: checksum release AppImage downloaded and isolated Xvfb provisioned. GTK socket creation fails `socket(): Operation not permitted`; local interactive xLights unavailable. Actions remains native execution environment.

## Confirmed native camera startup defect / next native milestone
Pinned xLights 2026.18 source (839c0f590dc454bb7adb8a16c4dd92a70b46156e) inspected: `ModelPreview` constructors start in 2D and camera3d distance -2000. `src-ui-wx/app-shell/TabSequence.cpp::LoadEffectsFile` restores default cameras near line 550, then selects saved XML 3D mode near line 700. A fresh profile therefore restores 2D, leaves 3D camera at -2000, and ignores this show's authored distance -65. `LayoutPanel::Set3d` does not restore the camera. This is a confirmed ordering defect; its quantitative contribution to prior black video still requires native output evidence.
Prepared `tools/patch_xlights_native_export.py`: restore saved default cameras after mode selection and retain genuine native dimension fix. Validated both exact patch sites against actual upstream 2026.18 checkout; 4 transformation regression tests pass. Native workflow now caches a completed build before video acceptance, pins exact upstream SHA, and uses shared push/PR branch concurrency to prevent two simultaneous 30-minute compiles. Previous source had been compiling twice (push 39413528055 and PR 39413537205); the new preflight cancels only older native runs on this same branch. Confirmed camera defect justifies superseding those builds.
V3 download hardened with three bounded attempts and unchanged archive/audio identity; gdown pinned 6.4.2. Current source-access blocker is resolved by successful fresh run 39413537064.
Latest changed-code suite: 55 passed, 1 real-native-manifest skip, 8 subtests in 2.60s. Native/consumer acceptance still pending.

Validation update: the full initial GUI/routing worktree snapshot completed 2,055 passed, 6 inherited skips and 16 subtests in574.98s. It began before the later-added native-source/face-export cases; do not label it a full final-source run. The later51-case focused group and actual second production run cover those changed paths; fresh full/current-source CI remains required. full_gui_snapshot.log and face_export_runtime.json retain the evidence.
