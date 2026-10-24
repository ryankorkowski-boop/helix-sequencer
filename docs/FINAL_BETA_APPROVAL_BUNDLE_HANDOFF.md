## Recovery verification commands and workflow results — 2026-10-24

Documentation-only follow-up: exact commands for the already recorded checks.
Files changed: this ledger and final handoff. No implementation, test threshold,
musical clock, artifact byte or acceptance status changed. No extra tests run
for this documentation update; post-save byte comparison remains unconfirmed
because the execution environment is unavailable.

Run from repository root. Separate suites overlap; do not add counts as unique tests.

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m pytest tests/test_review_archive_staging_guard.py tests/test_recovery_string_geometry.py tests/test_canonical_native_band.py tests/test_sampler_comparison_duration.py tests/test_approval_collection.py tests/test_source_spatial_direction.py -q
# 18 passed

OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m pytest tests/test_approved_concepts.py tests/test_android_recovery.py tests/test_recovery_pilot_gate.py tests/test_vocal_clock_conflict_audit.py tests/test_sampler_recovery_provenance.py tests/test_review_musical_recovery.py -q
# 147 passed

python -m pytest tests/test_recovery_tail_audio_alignment.py tests/test_sampler_recovery_provenance.py tests/test_recovery_pilot_gate.py -q
# 4 passed; the ending-only test fails the old verifier

OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m pytest tests/test_approval_collection.py tests/test_sampler_comparison_duration.py tests/test_sampler_recovery_provenance.py -q
# 7 passed

python -m tools.native_preview /absolute/matching-show --xsq /absolute/matching-show/SEQUENCE.xsq --audio /absolute/matching-show/media/AUDIO.mp3 --xlights /absolute/pinned2026.18/usr/bin/xLights
python -m tools.verify_recovery_media VIDEO.mp4 AUDIO.mp3 --expected-sha256 AUTHENTIC_AUDIO_SHA256 --output media-verification.json
ffmpeg -v error -xerror -i VIDEO.mp4 -map 0:v:0 -map 0:a:0 -f null -
ffprobe -v error -select_streams v:0 -show_frames -show_entries frame=best_effort_timestamp_time -of json VIDEO.mp4
```

Native calls run inside one owned Xvfb/openbox namespace;1280x720 target and
50ms source frames. Use the pinned executable SHA256
ea7cde8ae6ea4385dec1e835fa270c48a3c289769323891f1fb2e072db674930
beside the matching AppImage resources (archiveSHA256
62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b).
The complete native receipts and media/provenance reports are inside r2.
The full prior suite used bounded OMP/OPENBLAS/MKL/NUMBA threads and
`python -m pytest -q`:2126 passed,6 skips,24 subtests; it is a historical
checkpoint, not a claim that the whole suite was rerun after every later change.

| Workflow | Result and scope |
|---|---|
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40051497233 | FAIL: original full-band source lacks resolved independent singer evidence. |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40051497268 | Native render succeeded; raw-native readability/finalization FAIL. |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40051497274 | FAIL: unresolved timing/reference pilot receipt correctly prevents full12 scale-up; raw finalization also failed. |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/40051497239 | API30/API36 fresh-only Android smoke PASS; historical baseline update NOT TESTED. |
| https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/39511779105 | Retained pinned native build source; stripped-runtime hash/provenance verified before local renders. |

These workflow results are from their recorded source revisions, not an
all-current-workflows-green assertion. Latest implementation sourceb519d226;
delivery status commit55b6a5d8. Technical failures, unavailable signing key,
unconfirmed final byte readback and the separate owner-approval gate remain open.

## 2026-10-24 — Diagnostic delivery saved; technical acceptance still FAIL/BLOCKED

COMPLETE — Eight selected owner files saved successfully with durable identities
and local metadata: r2 bundle, native band pilot, native face closeup, authenticated
sampler technical comparison, four-camera verification, separate solid diagnostic,
status report and archive report. Save results explicitly succeeded for every item.
Published file existence/metadata was subsequently read/materialized successfully.

Bundle: Helix_Recovery_Diagnostics_20261024_r2.zip
Bytes: 401660108
SHA256: 8d56230c288a83a030e17650d4755c42cf36885cb6c525a4f2c66889e0d36ace

COMPLETE — Before saving, all13 r2 H264/AAC movies fully decoded; codec, dimensions,
frame counts and increasing20fps timestamps checked. All interior and actual
ending audio windows measured zero source lag; minimum whole-track decoded
correlation0.9968248041636503. All ZIP entries match SHA256SUMS; ZIP CRC passed.
Individual movies1280x720; technical comparison3840x720; four-camera
faces/guitar/bass/drum-key verification2560x1440. No30fps claim.
The Forced Perspective corridor is depth-framed; original decoded channel frames
are unchanged. The drummer gray reference rectangle is removed without changing
decoded channel bytes. Native body/kit remain coarse pixels and pose banks.

BLOCKED / UNCONFIRMED — The execution environment became unavailable during the
post-save download-byte comparison. All8 materialization requests returned files,
but the comparison process result could not be retrieved. DO NOT assert that
published bytes were independently hash-compared with tested files. Save success,
pre-upload hashes and server existence are established; final post-save comparison
is not. The earlier smaller recovery checkpoint readback had succeeded; it does
not prove the final r2 readback. Resume that exact gate when execution is available.
The expensive r2 media are saved; do not unnecessarily rerender them to recover
an unavailable scratch workspace. Some raw sampler-analysis intermediates were
not saved independently; retain the delivered XSQ/event-provenance timing rather
than silently replacing it with a different analysis or montage.

Latest CODE checkpoint:b519d2265071251210543fb3c17b135f542f20e7.
Other recovery code:58532473d40da91ff086826cd2d46747436ea409,
9d821b1162215a5abb21d29bd3fb561b245d1b0d,
ac713e5d453ac8ba480e8d9a6943756c8d76f6f5,
138f28b2b8899ef996d6f31ecdcf51d0ded91c98.
Full prior local checkpoint2126 passed,6 skips,24 subtests. Later separate
focused suites:18 passed;147 passed;4 passed;7 passed. Ending-only100ms drift
regression fails the old verifier and passes the repaired EOF-aware check.
Current CI is NOT all green. Singer-source qualification, final pilot gate and
raw-native readability failures remain in runs40051497233,40051497274 and
40051497268. Android fresh-only API30/API36 run40051497239 passed; those receipts
are not a historical baseline-update result.

FAIL — Vocal timing. Both retained acoustic-estimate lanes admit unsupported
episodes32.82–33.03s and33.10–34.41s. Cached source activity precedes Faces/native
rendering; zero measured soundtrack lag does not fix it. Periodic residual energy
is not verified singing. No blanket final mute, copied vocal lane or arbitrary
delay was applied. Independent second-singer activation stays preserved.
FAIL — Advanced-layout acceptance: geometry/targeted native pilots improved;
final twelve-layout collection and Ultimate visual acceptance remain unpassed.
FAIL — Musical direction: semantic source roles/pitch/depth gestures implemented;
isolated source truth, excess overlap and full-layout behavior remain unresolved.
BLOCKED — Android update. Historical recovered code6/1.0-beta signer:
b814ef47f37a86461008bdfbfbd812127b870d92586807078422c657cd09760b.
Actual downloaded/tested CI code7 signer:
ef0f9e93e18fc365f0a31fc251e0c44d8db3c999d5fab5b4e7b31e3cbbf1f05f.
Code7 APK SHA25615c3be0cfa04fb59576720a2ef19ff8744faa1247754fb5f7a32a0fcb2a0dd6d.
Monotonic code now passes; signer preflight fails. Original private key/authorized
lineage is unavailable. Owner-phone baseline matching, PM failure logs, genuine
update/data preservation and post-update smoke are NOT TESTED. Expected
INSTALL_FAILED_UPDATE_INCOMPATIBLE is conditional analysis, not an observed PM
log. No incompatible debug/unsigned APK was published as a working update.
FAIL — Canonical band: original V3 reference family recovered; exact approved
six-member composition/native fidelity unverified. Solid companion is OpenGL
with planar drummer artwork; native sampled pixels/discrete poses are not exact
continuous solid geometry or approved source-art motion.
FAIL — Lights-band acceptance: strings/contrast/reference overlay repaired and
detail cameras provided; mouth timing and drummer fidelity remain open.

Audio identity is explicit for every file in Soundtrack_Provenance_Report.json:
9 movies use complete34.88s Phoneme_Test_Hook.mp3,
SHA25619e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938.
4 use authentic prior256s Helix_Starred_All_Songs.mp3,
SHA256ffeaba9b9f8fc253a0356505c2b4147b7576b772db42a1c8ea63094b42545acf.
It is4:16, despite the colloquial3-minute description; not the distinct260.2s
or180s montages. Retained16 source-clip IDs/ranges/hashes are included. Prior
Oct21 compact8-way comparison matches at zero lag/correlation0.9727751881223241.

NOT STARTED — Final12 repaired native layout movies, six/twelve/band-integration
approval comparisons and compatible signed Android update. They remain gated by
a passing full-song pilot; no failed diagnostic is relabeled as repaired.
PR188 is confirmed open/draft/unmerged. No public beta or release tag created.
Its stale prior vocal-approval description was rewritten to reflect owner rejection.

Exact next actions:
1. Recover the saved r2 bundle/featured files when execution is available; verify
   the ZIP SHA above, CRC and every SHA256SUMS entry. Compare standalone featured
   downloads with the identical inside-ZIP bytes; record actual results.
2. Use safe authenticated offline vocal stems/presence evidence, or obtain
   explicit authorization for the previously blocked analysis. Optional stem
   reconstruction was rejected by automatic approval review for Microsoft
   telemetry with an unestablished/unauthorized payload; it was not retried.
3. Fix full-recording vocal presence and verify rests/transitions/independent
   singers; inspect ending and instrument/face crops with the original soundtrack.
   Do not stretch sampler clocks, invent lexical phones or mute the final passage.
4. Restore/verify native V3 fidelity and exact six-member approved composition,
   rerender/pass the full-song pilot, then produce the actual twelve-layout
   collection using the authenticated soundtrack appropriate to each output.
5. Recover the legitimate historical signing key through private CI secrets,
   confirm actual installed baseline identity, then test a real seeded baseline
   update/data preservation, cold launch, offline processing, quick clip, layout
   selection and export. Never uninstall/clear owner data or substitute a new key.
6. Keep public beta unpublished and PR188 unmerged until technical gates pass
   and the owner explicitly approves the repaired visuals/musical behavior.

## 2026-10-24 — Forced Perspective near-plane/framing repair

Goal: fit the depth corridor entrance in actual native frames. Changed
 tools/build_approval_collection.py and tools/build_sampler_technical_pilot.py,
this ledger and final handoff. Prior width/height-only camera distance120 with
18/12-degree orbit cropped near structures. Layout11 camera now adds half the
119-unit depth span to the XY fit margin, distance170.5, with centered frontal
view. No source event, cue, node, geometry, grouping or other layout camera changed.
Evidence:7 focused collection/sampler checks passed in14.38s. Fresh full original
and256s sampler native exports succeeded;8s/24s original and sampler frames are
inspected. Original decoded FSEQ frames remain exactly identical before/after
camera repair. This is camera-aware perspective, not geometric rotation.
Vocal/instrument verification now includes four synchronized native cameras:
faces, guitar, bass and drums/keyboard;2560x1440,20fps, full34.88s original,
zero measured source lag including final2s. All six performers have a detail view.
Limitations:660 of698 decoded forced-original frames differ; that is file motion
evidence, NOT musical-intelligence acceptance. Original source estimates and
phantom mouths remain FAIL. Final12 approval collection remains gated. Final
forced comparison re-encode/verification and durable bundle saving IN PROGRESS.
No approval or controller/device equivalence is inferred. No merge/public beta.

## 2026-10-24 — Ending-only soundtrack drift regression

Goal: detect a late audio offset even when a256s comparison's global correlation
still exceeds.97. Changed tools/verify_recovery_media.py and
 tests/test_recovery_tail_audio_alignment.py; this ledger and final handoff.
Preserved: source hashes, codec/resolution/full-decode requirements, interior
alignment windows and50ms tolerance; no movie/audio/cue retiming occurs.
New behavior: actual last2s window; EOF search buffer is zero-extended so valid
correlation does not hide positive lags near the file boundary. This is search
math, not source padding. New deterministic100ms ending-delay case fails the
old verifier and passes after repair.4 tail/sampler/pilot checks pass.
Evidence: all13 r2 H264/AAC diagnostic files pass full decode, monotonic20fps
frame timestamps and zero measured lag in interior and ending windows.
Limitation: matched soundtrack/PTS does not verify whether a mouth should open.
Original clock false positives remain32.82–33.03/33.10–34.41s. No masking applied.
Source uncertainty and native/reference fidelity stay FAIL. The current actual
code7 CI debug APK15c3be0cfa04fb59576720a2ef19ff8744faa1247754fb5f7a32a0fcb2a0dd6d
was downloaded and independently inspected: signer ef0f9e93e18fc365f0a31fc251e0c44d8db3c999d5fab5b4e7b31e3cbbf1f05f,
not historicalb814ef47f37a86461008bdfbfbd812127b870d92586807078422c657cd09760b.
Monotonicity is now correct; only established signer preflight fails. Owner-phone
baseline match/update/data preservation remain untested. CI fresh reinstall
receipts are kept as fresh-only evidence, never upgrade proof.
Deferred: full12 repaired approval collection is gated by failed full-song pilot;
private signing-key recovery and safe vocal-presence evidence remain necessary.
Risk: silent windows cannot establish an offset; all delivered source windows
contain usable audio. No threshold reduced; no merge/public beta performed.

# 2026-10-24 authoritative recovery checkpoint

## 2026-10-24 — Native reference overlay and staging-copy repair; workspace recovery

Goal: remove the source editor rectangle from native performer renders without
changing source pixels, musical clocks, asset bytes or the six-member cast.
Changed: models/canonical_native_band.py, tools/build_helpers/ultimate_showcase.py,
tools/render_approval_collection.py, tests/test_recovery_string_geometry.py,
tests/test_review_archive_staging_guard.py, this ledger and final handoff.
Native cause: pinned xLights CustomModel::DisplayModelOnWindow draws
CustomBkgImage in House Preview. Retaining the reference path exposed its gray
source rectangle in real MP4 frames. Canonical export moves that path to Helix
reference metadata; writer still copies exact reference PNGs. Historical source
xModel/standalone approved-concept behavior is preserved. Node coordinates,
submodel membership, colors, voices, timing, export/synchronization stay unchanged.
Archive guard excludes interrupted staging paths; legitimate files stay identical.
Evidence:18 focused geometry/canonical/collection/archive/spatial checks passed
in52.38s;147 additional affected legacy/Android/pilot/vocal/sampler checks passed
in33.26s. Regenerated band-v2 native export success and15s frames inspected show
rectangle removed. Original Phoneme34.88s hash remains19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938.
Authenticated prior256s sampler hash remainsffeaba9b9f8fc253a0356505c2b4147b7576b772db42a1c8ea63094b42545acf.
Workspace maintenance removed the previous13 local movies before durable saving.
They are NOT delivered. Source58532473/9d821b11 survives remotely. Recovered
current native artifact12543339014/run40051497268; restored both exact audios,
source clip manifest and cached original plan. New sampler production analysis
completed once; comparison/frame and matching-show regeneration IN PROGRESS.
Durable recovery checkpoint6590955 bytes,SHA256
c35800963d10a4c9aa756525e9e47977159f7ece3d7f8ad08c6f302bbc90febe
was saved and byte-readback verified. It is diagnostic, not approval evidence.
Native renderer initially crashed without adjacent resources; patched executable
now runs beside checksum-verified2026.18 AppImage resources, binary unchanged.
Limitations: phantom mouths32.82–33.03/33.10–34.41s remain FAIL, independent
voice presence/source truth unresolved; no blanket ending mute or copied lane.
Original V3 reference family was recovered; its source-art motion is planar and
native pose banks are not a continuous solid3D recreation. Exact approved
six-member composition/fidelity still not verified. Android historical baseline
and rejected APK differ in signer and share code6; source code7 alone is not an
update. Original private key/actual phone PM logs/update/data preservation absent.
Deferred: final12 repaired approval movies/comparisons remain gated by the failed
pilot. No beta release or PR188 merge. Risks: reducing the image overlay reveals
coarse native body/kit pixels; this is disclosed, not declared approved. Follow
this ledger for exact later save hashes, tests and next actions.


Historical records below are superseded for delivery availability and acceptance.

# Owner-rejected recovery — current authoritative status, 2026-10-23

The owner rejected the delivered bundle. Historical COMPLETE entries below
describe file production, not acceptance. Prior vocal approval is superseded by
reported bad timing. PR188 is draft/open; no merge or public beta is authorized.

## Latest executable checkpoint

- COMPLETE — original audio verified; new native full-song band/string pilot,
  separate native face/guitar/drum-key camera views and original-recording
  technical9/10/11 pilots rendered at1280×720/20fps. Actual frames inspected.
  New face composition is readable in native camera closeup, but timing still
  fails and drummer/reference identity remains unapproved. New solid OpenGL
  diagnostic is separately labeled; it still uses planar original drummer art.
- COMPLETE — all12 editable layouts rebuilt with exact AC16/64/256 budgets,
  semantic source roles, source-pitch spatial propagation, native matrix Bars,
  layered optical lattices, cathedral side helices/ribs and nested depth boxes.
  Final Ultimate source has131 models/205194 channels; its visual gate is NOT passed.
- COMPLETE — actual prior sampler recovered, superseding the initial unresolved
  sampler search below: `Helix_Starred_All_Songs.mp3`,256.000s,SHA256
  `ffeaba9b9f8fc253a0356505c2b4147b7576b772db42a1c8ea63094b42545acf`.
  Retained PCM WAV SHA256`c69e0a4632a6c67f7ae59d2e1c630ce6de5969ca954d403f094176a1376c6524`.
  Prior retained native source package supplies16 source clips with Drive IDs,
  source hashes and exact sample ranges. All16 IDs were found in the authenticated
  Starred folder. Prior compact8-way source audio aligns at zero lag, correlation
  .972775188 to MP3 (.972882605 to retained WAV); compact lossy encoding is
  disclosed. The256s source is distinct from the260.2s and180s montages.
- COMPLETE — three native technical sampler pilots using ONE
  fresh256s analysis, not the Phoneme cache. Missing isolated sampler vocal roles
  abstain. Native sampler9/10/11 exports succeeded;11 startup returned transient
  malformed HTTP and succeeded after bounded valid-JSON retry. First256s export
  hit fixed60s RPC timeout; exporter now derives a bounded timeout from duration.
  Final sampler presentation/comparison verification COMPLETE: all13 final movies decode, original-recording correlation>=.996824804; sampler individual correlation.997331227. Saving and final archive verification remain IN PROGRESS.
- COMPLETE — full local suite checkpoint2126 passed,6 existing/receipt skips,
 24 subtests,248.78s. Final narrow regression suites additionally cover streaming
  FSEQ, native long-export transport, report changes and full sampler duration.
  Earlier full test failure was the stale `passed_in_prior_video` assertion,
  superseded by latest owner rejection. No quality threshold was lowered.
  Final focused verification43 passed; broader affected native/media suite55
  passed,1 receipt skip,10 subtests. New malformed-startup/long-export tests2
  passed. Additional source report changes enumerate exact unmapped pitches.
- BLOCKED/FAIL — the retained cache still admits phantom source activity around
 32.82–33.03s and33.10–34.41s. Positive periodic energy is not proof of singing.
  Full-song source-separation leakage classification remains unresolved. No
  blanket final mute, copied lane or arbitrary delay was applied. Cache/source
  hashes and all active intervals are retained in audit evidence.
- BLOCKED — optional stem reconstruction was rejected by automatic approval
  review for contact with an external Microsoft telemetry endpoint whose payload
  was not established/authorized. No retry or indirect bypass was attempted.
  Continue only with authenticated offline stems/evidence or separately
  established safe authorization; do not silently rerun that path.
- BLOCKED — approved canonical6-member/drummer reference is not established by
  repository class names, historical README claims or recent rejected renders.
  Need an actual approved frame/movie/asset revision before restoring identity.
- BLOCKED — recovered historical Android baseline code6 signer
  `b814ef47f37a86461008bdfbfbd812127b870d92586807078422c657cd09760b`
  differs from rejected code6 signer
  `7b1a77af3d5c23cdb2b32fcdccd52d77fec3804f4862ce434a4d80d642c1aa73`.
  Candidate source code is7, but original private key/signing lineage and actual
  installed-phone PM logs are unavailable. No compatible APK or real update/data
  preservation is claimed. Certificate alone cannot recover the private key.
- NOT STARTED — final12 individual repaired movies and6/12/band integration
  approval comparisons, because the full-song canonical/timing pilot gate fails.
  Diagnostic pilots are not relabeled as an approved/repaired collection.
  final-approval-collection CI now checks hash-bound pilot timing/reference
  evidence before scale-up. A successful download or native file alone cannot
  unlock it; no acceptance receipt was invented for this recovery.

Current local roots: `final-band-pilot`, `detail-pilots`, `recovery-layouts`,
`sampler-technical-pilots`, `solid-diagnostic` and
`Helix_Recovery_Diagnostics_20261023_r1`. Exact native receipts bind XSQ/layout/
audio/FSEQ/MP4 hashes; final media verification, artifact hashes and saving
results must be appended after successful packaging. Keep release held.

Final portability check found the planar drummer editor/reference image paths absent from generated shows. The writer now includes exact retained drummer_idle/drummerbg PNGs when referenced; generated assets were repaired without changing XSQ/layout/video bytes. Focused portability/source geometry tests passed. This does not establish approved drummer identity or create solid geometry.

Reproduce source-only sampler pilots after authenticated recovery:
```
python -m tools.build_sampler_technical_pilot AUDIO_MP3 ANALYSIS_DIR SAMPLER_MANIFEST OUTPUT
```
`AUDIO_MP3` must have the exact256s MP3 hash above. `ANALYSIS_DIR` must retain
that MP3 and one production snowman-band plan. Never reuse the Phoneme clocks
for a different soundtrack. Use native_preview inside one Xvfb/openbox process
namespace, then verify_recovery_media with explicit original source hash.

Baseline HEAD: `d3749d365431fa852cb8793205c20b71de55fa7b`. Clone completed;
tracked worktree initially clean (one interrupted checkout PNG temporary file
was untracked and is left untouched). AGENTS/master ledger/release handoffs,
open issues199/196/192 and actual rejected bundle/frame were inspected.

| Status | Owner defect | Current evidence / next action |
|---|---|---|
| IN PROGRESS | Phantom singer openings | Retained10ms cache admits every positive periodic-energy estimate; source leakage is not excluded. Preserve independent lanes; classify nonvocal evidence over full original before changing clocks. |
| IN PROGRESS | Advanced geometry | Inspect native spatial layouts and actual effects; distinct geometry alone did not pass owner review. |
| IN PROGRESS | Beat-only choreography | Builder assigns guitar/bass/keys by model index modulo3 and repeats On envelopes. Replace with semantic zones and source-derived spatial direction. |
| BLOCKED | Android baseline update | Recovered Oct21 Helix-Android-Beta.apk has signer b814ef47f37a86461008bdfbfbd812127b870d92586807078422c657cd09760b; rejected7c1a248 APK has signer7b1a77af3d5c23cdb2b32fcdccd52d77fec3804f4862ce434a4d80d642c1aa73. Different keys cannot update without legitimate lineage/original private key. No actual phone package-manager log available. |
| BLOCKED | Approved canonical band | FinalBandScene naming and source README do not prove owner approval. Retained footage/screenshots/history examined; exact approved six-cast reference still unidentified. |
| IN PROGRESS | Lights-band readability | Rejected frame inspected. The guitar string spacing was widened, duplicate originals remained visible and native strings were exported as cylinder samples. Inherited transforms require explicit clearance in front of the widened neck. New implementation restores guitar endpoint XY, raises the bridge/pickup to the string plane, preserves bass bridge spacing, emits thin native paths and removes duplicate rods; native mouth background contrast repaired without enlarging proportions. Rerender/inspect required. |

Exact original fixture SHA256 verified:
`19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`,34.88s.
Recovered prior rejected bundle SHA256 matches documented8a224575c41c426170fb984bc68119c7c784135cbd3f3dc450aabcc58edcbb95.
Google Drive authenticated profile is helixhelps@gmail.com. Root/music/starred
and compact comparison folder were enumerated after indexed search returned no
results. Starred sampler was recovered from retained files; filename
Helix_Music_Mix_Starred_High_Energy_Sampler.mp3,260.2s,SHA256
f76e41469c5e844442da18d1716de8fbec8c4ab2bfee84128a0a6f9515924c9f.
Tracklist retains15 nominal18s source clips with Drive source provenance.
Drive Oct21 compact8-way comparison is256s and initial decoded-audio correlation
does NOT establish a match to that sampler. Earlier Oct12 sampler is a separate
180.14931972789117s recovered WAV (historical hash0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb).
Do not mix these identities or silently substitute one for another.

Native runtime artifact12491875007 restored; binary SHA256ea7cde8ae6ea4385dec1e835fa270c48a3c289769323891f1fb2e072db674930.
Actual baseline show prepared from current engine; native2026.18 export succeeded
at1280x720. Xvfb/openbox/render must run in the SAME execution network namespace.
No repaired movie has passed acceptance yet. Full collection must wait for pilot.

Reproduce in this workspace: baseline-show contains production plan/XSQ;
native-run.py starts local Xvfb/openbox and executes the supplied Python command.
No source/generic substitutes for inaccessible canonical references are approved.

# Historical final beta approval bundle — execution checkpoint

Branch: `codex/eight-hour-recovery-20261019`; starting HEAD
`29f0fcae19cff99b555692d817d9662d9e9504e5`; draft PR #188.
Read MASTER_TODO.md for the full preserved ledger. No merge/public beta authorized.

| Status | Task | Evidence / next action |
|---|---|---|
| COMPLETE | Current source recovered | Cloned exact branch/HEAD, read AGENTS.md, master ledger and release handoff. |
| COMPLETE | Original recording recovered | Retained fixture matches SHA256 `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`. |
| IN PROGRESS | Solid-scene native integration | New canonical_native_band exports FinalBandScene surface geometry; six stable identities, purple harmony, restrained native mouth proportions, exact source drummer node ranges and semantic aliases. |
| COMPLETE | Vocal algorithm preserved | tools/phoneme_vocal_export.py and retained source-separated clocks unchanged. Model source revision 5f60522 is retained. Owner observed vocal-animation approval remains separate from source-separation identity uncertainty. |
| IN PROGRESS | Full-song canonical show | prepare_phoneme_show now uses canonical_native_band, not Review3DScene. First run correctly rejected duplicate REST aliases; adapter now emits only native viseme names. Fresh run canonical-show-v2. |
| IN PROGRESS | Native runtime recovered | GitHub compact artifact12491875007, stripped runtime SHA256 ea7cde8ae6ea4385dec1e835fa270c48a3c289769323891f1fb2e072db674930; pinned2026.18 AppImage for resources/compatibility only. |
| NOT STARTED | Verified canonical MP4 | Generate using actual xLights and inspect rendered frames before promotion. |
| NOT STARTED | Twelve layouts/comparisons/bundle | No missing file may be represented as generated. |
| NOT STARTED | Current Windows/Android validation | Prior evidence in FINAL_RELEASE_EXECUTION_HANDOFF.md is historical, not this candidate. |
| BLOCKED | Exact continuous solid geometry in native pixel preview | Native exports surface samples and stationary light poses; FinalBandScene uses original planar drummer art via compositor. Do not describe native pixels as continuously animated solid meshes. |
| BLOCKED | Owner visual approval/public beta | Owner must approve new band visuals; no public beta/merge. |

Reproduction:

```
python -m tools.prepare_phoneme_show --audio fixtures/audio/Phoneme_Test_Hook.mp3 --output /absolute/fresh-show
HELIX_NATIVE_PREVIEW_WIDTH=1280 HELIX_NATIVE_PREVIEW_HEIGHT=720 python -m tools.native_preview /absolute/fresh-show --xsq /absolute/fresh-show/Phoneme_Test_Hook_Helix.xsq --audio /absolute/fresh-show/media/Phoneme_Test_Hook.mp3 --xlights /absolute/patched/xLights
python -m tools.finalize_phoneme_review /absolute/fresh-show
```

Xvfb and the export command must share the same execution network namespace.
Use private extracted GUI dependencies when package installation is unavailable;
system GTK/GLib plus retained wx libraries, not the full mixed AppImage library path.

## Native collection follow-up

- COMPLETE — twelve distinct native layouts generated from one retained production band plan; AC budgets16/64/256, six-member native bands in7/8/12,88 literal helix rungs. No geometric rotation claimed.
- COMPLETE —36 focused tests passed, one environment-dependent native integration skip. New tests cover literal event clocks/omissions, unique model identities, channel allocation and source vocal counts.
- COMPLETE — actual native xLights exports produced at1280x720/20fps, source34.88s. Earlier diagnostic band frames failed luma/motion acceptance; not promoted.
- IN PROGRESS — all12 native movies, source soundtrack/decode checks, comparisons and packaging via tools/render_approval_collection.py. Render root: /workspace/scratch/b503538b9f0a/approval-layouts-final; delivery root: /workspace/scratch/b503538b9f0a/delivery. Log: render-all.log.
- IN PROGRESS — full unweakened local pytest suite.
- Exact source control/render changes additionally include models/approval_layouts.py, tools/canonical_band_cues.py, tools/build_approval_collection.py, tools/render_approval_collection.py and tests/test_approval_collection.py.
- Repairs: native parent DisplayElements retained after replacing musician rows; active/idle arm nodes separated; literal strings and keys receive retained source events; out-of-range keyboard pitches reported rather than transposed; idle key/string visibility only in event complements.
- First collection native attempt revealed missing parent musician rows, fixed before final collection. Earlier source preparation duplicate REST aliases and duplicate display rows were rejected, then repaired. Missing native GUI effectmetadata caused ColorPanel crash; resource share restored beside retained binary, preserving system GTK.
- Native image/audio results alone never imply owner artistic approval, independent vocal identity, instrument ground truth, hardware/controller tests or platform release acceptance. Post-beta work remains deferred.

Reproduce collection from a completed clean prepared Phoneme show:
```
python -m tools.build_approval_collection /absolute/prepared-show /absolute/fresh-layouts
python -m tools.render_approval_collection /absolute/fresh-layouts /absolute/output --xlights /absolute/patched/xLights
```
Run Xvfb/openbox and renderer in the same execution namespace.

## Verified band checkpoint

- COMPLETE — pushed implementation2ba32e83872819a528dc830fa0e8cb1a0c56ba05.
- COMPLETE — full local Python3.12:2106 passed,6 skips,24 subtests in259.47s. Initial missing-torch collection error repaired by installing CPU dependency, no test exclusions.
- COMPLETE — canonical native band movie7 passed unchanged readability/motion gate: luma14.648, motion1.014, extent.812×.811. Soundtrack correlation.996824804, complete34.88s H264/AAC720p20fps decode. Actual frame inspected; six members and purple harmony visible. Native samples/two-pose limits remain.
- IN PROGRESS — bright native collection under approval-layouts-bright/, output delivery-bright/, log render-bright.log. Earlier obsolete collection was interrupted and must not be delivered as current.
- BLOCKED — simpler layouts still fail unchanged global luma gate. Do not call bundle complete.
- IN PROGRESS — source-specific Windows40007465634 and Android40007465179 queued; compliance40007465091 and GUI evidence40007465082 success at2ba32e8.
- New workflow final-approval-collection.yml saves complete zipped candidate plus explicit technical/owner gates without publishing beta.

## Full movie inventory and solid companion

- COMPLETE —12 native individual movies,6-panel3840x1440,12-panel3840x2160,3-panel band integration3840x720, native close-up and verification feature:17 native-derived MP4s. Original full soundtrack correlation and complete decode measured.
- COMPLETE — separate1280x72020fps FinalBandScene solid OpenGL visualization, clearly captioned non-native. Same retained vocal clocks/production plan; original planar drummer, unresolved toms omitted and cymbal/hand staging unverified.
- IN PROGRESS — explicit gamma2.2 presentation curve and final-file revalidation; prior failures retained. Source AC preview bulbs12px, actual channel budgets unchanged.
- BLOCKED —AC256 lacks dedicated spinner/singing-face circuit props; native drum localization/contact, exact solid native equivalence, geometric helix rotation, current platform/hardware validation and owner visual approval remain.
- Do not label the bundle release-complete even if final file acceptance passes. It contains a real full inventory plus an explicit incompleteness report.

## Final source repair checkpoint

- COMPLETE —37 focused checks pass,1 receipt-dependent native skip. Full suite rerunning.
- IN PROGRESS — native rerenders03/07/08/12 with explicit drum component clocks and completedAC256 spinner/two singing faces. Earlier missing-face/spinner item is superseded by this implementation; final rendered evidence pending.
- Corrected source body idle ownership so kit events can flash independently. Unresolved toms, source cymbal side and snare hands remain honest uncertainty.
- COMPLETE —Windows40009240809 at4cdd069 passed packaged engine/GUI/native-FSEQ checks; current final code still requires source-specific CI. Android pending.
- Final delivery after rendering: run finish_approval_presentation, inspect18 final MP4s, verify ZIP checksums, save ZIP + featured videos persistently, then append download identifiers/results here.

## Final media validation COMPLETE

- COMPLETE —18 MP4s all fully decoded; every final readability/motion/foreground gate passes. All videos34.900s/20fps with the complete original34.88s soundtrack, minimum correlation0.996824804. Native individuals720p; comparison outputs3840x1440,3840x2160,3840x720.
- COMPLETE —source vocals preserved exactly versus prior successful29f0fca artifact:476 lead and494 harmony Faces events including clocks/settings/source fingerprints.
- COMPLETE —native channel proof verifies256 AC channels, spinner/two mouth banks, and all six varying band models.
- COMPLETE —2107 full tests,6 skips,24 subtests;39 final focused checks,1 receipt skip.
- COMPLETE —Windows7c1a248 build40010798813, packaged GUI/engine/nativeFSEQ passed. API30 Android passed; API36 pending. Release key/installed historical-key upgrade remains unverified.
- Final bundle: /workspace/scratch/b503538b9f0a/delivery-bright/Helix_Final_Beta_Approval_Bundle.zip. Featured videos in03_Band_Features; comparisons in02_Comparison_Videos. Final Native_Channel_Activity_Proof, Vocal_Compatibility_Proof, Instrument_Verification and complete test logs are included.
- Native geometric limits, unresolved tom localization, cymbal/snare staging assumptions, AC-band hardware equivalence, helix rotation, actual device/signing and owner visual approval remain explicit release blockers.
- No beta release orPR188 merge performed.

## Platform proof and package guard

- COMPLETE —Android40010798866 API30/API36 success; exact delivered API36 debug APK SHA256 d4b7b0f226a1693533615f5e7d01bfa26a129bae07e7aac0202d6aca8bc34b0e matches fresh install/launch/reinstall/data-preservation receipt. Historical installed-key upgrade NOT verified; unsigned release NOT installable.
- COMPLETE —current application-source7c1a248 Windows portable ZIP has valid Helix.exe/HelixCLI.exe and passed packaged GUI/engine/nativeFSEQ.
- Package count/CRC validation rejected an additional interrupted comparison staging file. Final atomic archive filter excludes .comparison/.tone/.graded temporary media and verifies stable source bytes plus ZIP CRC before publication. Actual final inventory must be exactly18 MP4s.
- Remaining: owner visual approval; unresolved tom localization/native source-art drummer contact/visibility review; AC-band hardware equivalence; geometric helix rotation; established release signing key and actual historical-key device update test; final release gates. No beta publication orPR188 merge.

## Delivery COMPLETE — owner review files saved

Application implementation:7c1a248c4f2907ea9b5168d12065f7574f1fd9e2.
Final artifact code:a04f2a24b128d462dc248b52eeb893315cd084ec. PR188 remains draft/unmerged; no release tag/public beta created.

All eight files below were saved successfully for the owner, with persistent file identity applied. Final local delivery folder: `/workspace/scratch/b503538b9f0a/final-delivery/`. The bundle's18 MP4s, actual movie hashes against the report, all JSON, everySHA256SUMS entry and ZIP CRC were verified before saving. Standalone featured downloads match the identical bytes inside the ZIP. Download links are in the delivery conversation; private storage identifiers are intentionally omitted from the public repository.

| File | Bytes | SHA256 |
|---|---:|---|
| Helix_Final_Beta_Approval_Bundle.zip | 228510164 | `8a224575c41c426170fb984bc68119c7c784135cbd3f3dc450aabcc58edcbb95` |
| Helix_Final_Snowman_Band_Closeup.mp4 | 4275414 | `66d52d36d8ae01c439dada83aec6815597e5224865be12ff5308f49d042e32c4` |
| Helix_Canonical_Solid_3D_Visualization.mp4 | 13867887 | `2545ce7765590b05cfa2737464e422a81b87ce8a4053ad3ad1f52f73dfab93fd` |
| Helix_6_Layout_Comparison.mp4 | 28864556 | `6f67d3a3ce5d6d90b2bf2d7a8d738a8f2cbad3e5bf48fb32dac3fc8a970feaf7` |
| Helix_12_Layout_Comparison.mp4 | 29778085 | `53c1e8bea2b701531be681c20eee2f575ac27091718ab0ee7561783e0f37dfd8` |
| Helix_Band_Integration_Comparison.mp4 | 16554129 | `6495719f008a40040c32e3d74d5bc5282a81a40a89c267a121994fca869ec07e` |
| Helix_Windows_Portable_7c1a248_Verified.zip | 191443651 | `f93220475e093f638465feeb74a278ded1599538cff04cb6786657ef702179d0` |
| Helix_Android_Debug_7c1a248_API36_Verified.apk | 144405881 | `d4b7b0f226a1693533615f5e7d01bfa26a129bae07e7aac0202d6aca8bc34b0e` |

### Current acceptance states

- COMPLETE —18 movies,12 individual native layouts, synchronized6/12/3-panel comparisons, native close-up/verification and separate solid OpenGL companion. Original full soundtrack, full decode, every final luma/motion/extent gate passed. Native video20fps/34.900s; original audio34.88s.
- COMPLETE —vocal compatibility proof:476 lead/494 backup event clocks/settings/fingerprints preserved exactly. Prior owner vocal-animation approval retained; no new visual approval presumed.
- COMPLETE —native256-channel spinner/face circuit proof and six active/varying performer channels; entire native edit-ready shows/models supplied.
- COMPLETE —2107 full Python3.12 tests,6 skips,24 subtests;39 focused media regressions,1 fixture skip. Final archive tests/actual CRC/checksum/count validation passed.
- COMPLETE —Windows7c1a248 packaged GUI/CLI/nativeFSEQ checks; delivered portable ZIP validated, including real PE executables.
- COMPLETE —Android7c1a248 API30 andAPI36 emulator offline/media/fresh install/launch/same-key reinstall/data-preservation checks. Delivered exact tested API36 SIGNED DEBUG APK, not unsigned release.
- BLOCKED —established production signing key and actual upgrade over the owner's installed historical-key APK. Current unsigned release cannot install. Fresh debug success does not establish old-install upgrade compatibility.
- BLOCKED —owner final canonical visual approval. Native output remains sampled surfaces/two-pose light banks; original drummer art is planar. OpenGL solid companion is explicitly separate.
- BLOCKED —unlocalized tom events/contact and native drummer visibility review, native/AC-band hardware equivalence, geometric helix rotation and remaining strict release acceptance gates. Independent source identity/lexical phones remain estimates, without revoking prior observed vocal approval.

### Exact next actions

1. Owner reviews `Helix_Canonical_Solid_3D_Visualization.mp4`, native close-up, then the6/12-layout comparisons. Record VISUAL approval separately from existing VOCAL behavior approval.
2. Preserve the original audio/cache and exact476/494 vocal cues while fixing any rejected geometry or musician behavior; do not restoreReview3DScene.
3. Resolve unlocalized drum/contact/native visibility and canonicalAC equivalence with source-grounded evidence; preserve failed gates rather than fabricate events. Implement real spatial helix animation before claiming rotation.
4. Supply the established signing identity through the existing private release-signing variables and test an actual data-preserving upgrade on the owner's device. Never distribute unsigned release as installable.
5. Inspect the latest source-specific CI/strict acceptance receipts; repeat only tests/renders affected by a new change. NoPR188 merge/public beta until explicit owner approval and all release gates pass. Post-beta roadmap remains deferred.

Reproduction commands remain above; final stages are:
```
python -m tools.build_approval_collection /absolute/prepared-show /absolute/fresh-layouts
python -m tools.render_approval_collection /absolute/fresh-layouts /absolute/output --xlights /absolute/patched/xLights --source-commit SOURCE_SHA
python -m tools.render_canonical_solid_candidate /absolute/prepared-show /absolute/solid/Helix_Canonical_Solid_3D_Visualization.mp4
python -m tools.finish_approval_presentation /absolute/output/Helix_Final_Beta_Approval_Bundle --audio fixtures/audio/Phoneme_Test_Hook.mp3 --solid /absolute/solid/Helix_Canonical_Solid_3D_Visualization.mp4 --commit SOURCE_SHA
```
