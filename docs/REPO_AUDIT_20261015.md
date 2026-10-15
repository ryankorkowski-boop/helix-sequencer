# Helix 72-hour completion audit

Window: 2026-10-12 05:33:56 UTC through 2026-10-15 05:33:56 UTC.
Repository: ryankorkowski-boop/helix-sequencer. Implementation branch:
`codex/72h-completion-20261015`, starting at hardening `183057f59a7afd6ad9542017e45179e31f4be279`.

The repository contains unfinished work. No commits reached the default
`feature/restructure-core` branch during this window; its head remains
`1f66f5dfa09b3173f5cdfd33d28ab1b4421e11ad`. The latest engine, native bands,
platform repairs, licensing and physical contracts exist on development branches.
Open issue143 and issue144 cannot be closed on source changes alone.

| Work | Verified state at audit | Action / remaining gate |
|---|---|---|
| PR138, dual xLights/LMS workflow | Integrated through PR146/147 | Existing import/export regression coverage retained; actual LOR application/hardware playback remains open |
| PR139/141, Android recovery and GUI guidance | Integrated through PR146/147 | Prior exact-source Windows/API30/API36 CI succeeded; new branch must build again |
| PR140/142 and timed correction branch94ddc56 | Consolidated through PR147 | Final scene uses two solid six-member bands and one mallet player per band; original scenes and guitar performance retained |
| PR145 licensing | Official PolyForm text is present in integration source | Default still has old license; historical MIT/third-party grants retained; contributor/asset authority remains an external gate |
| PR147 final native bands, key routing, opening kicks | Native and platform runs on7a1ffa passed | Synthetic connectivity and source-bound light cues are not independent transcription/listening proof |
| PR148 short/silent kick-reference hardening | Four focused tests; full prior-source CI green | Included in this branch; full combined regression and new native checks are required |
| PR149 physical drummer/chorus/front projection | Fifteen code/test/document files existed separately despite stale documentation-only PR summary | Integrated92b3a47; connected cue compilation to real XSQ/LMS export with exact source addresses |
| Physical CTB16PC sequence output | Previously no adapter connected the helpers to exported sequences | Implemented opt-in16-output exporter, measured cymbal tails, exclusive chorus mouths, CSV/hash reports and native FSEQ regression |
| Native CI on hardening revisions | Push trigger only covered older completion branch; PR path filter missed audio hardening | Expanded branch/source coverage and added current kit's4,800-value native diagnostic |
| Full-song and original-sampler movies | Prior source reports show private180.15s movies; latest hardening log has no new playable movie/source analysis here | Do not represent prior movies or synthetic calibration as a fresh full-song delivery |
| Installer releases | Four recent beta release tags include actual APK/ZIP assets; they pin earlier source revisions | Current-source Windows/Android CI must pass before replacing installer assets |

## Executed implementation

The new opt-in exporter reads classified cue JSON and the user's original LMS,
requires an explicit actual Unit ID, and refuses absent/duplicate/mismatched
addresses. It emits a matching XSQ, editable legacy LMS, wiring CSV, source/cue
hashes and front-projection construction contracts into a fresh directory.
No source file, layout, audio or previous output is overwritten. Existing
twelve-circuit drummer output is unchanged. See CTB16PC_SEQUENCE_EXPORT.md.

The new regressions exercise every exported centisecond after actual LMS
reimport; both hands, eight rapid kick flashes, a measured cymbal tail, silence
and conflicting vocal poses are checked. A failed first test exposed a floating
point boundary that extended a cymbal tail by one tick; the implementation now
uses stable sample-boundary indexing. Invalid00Unit IDs and nonfinite shimmer
rates are also rejected.

## Validation receipts

Additional implementation: Android's purported full-song case only rendered
three seconds and the local/remote UI and bridges capped previews at120seconds.
These limits now match desktop600seconds; the actual-song device fixture asks
for600and must render the complete source beyond120seconds. The host checker
streams every decoded frame while retaining six samples, eliminating the prior
multi-gigabyte raw-frame allocation. It verifies full duration/frame count and
source audio alignment. Focused host verification passed57checks before the
additional remote-boundary cases; new exact-source API30/API36 checks are required.

Software source182c7c5passed the strict native workflow38688893171: all4,800kit
intensities within0.4of255, six native layouts, two six-member bands, and all16
source-bound opening kick rises including8rapid hits. Artifact11951446369's ZIP
SHA256 is194e61e65bbf8972a496a1fe378be0ecfdf10998820bac695379b4812c5b02dd;
CRC and declared source commit were independently verified after download.
Windows38688893139also passed build, packaged GUI/engine and native preview smoke;
its artifact11951946085is189140863bytes. The final local suite on that source
passed1515/5missing-fixture skips/36warnings in187.75s. Android long-preview changes
need their own current-source build and emulator results; do not reuse these
prior-source receipts as a full-song Android pass.

- Focused physical/output/hardening/LOR suite: **49 passed in1.43s** locally.
- Python compilation, changed workflow YAML parsing and git diff whitespace
  checks passed. Full combined regression: **1,515 passed, 5 skipped, 36 warnings
  in209.69s** onPython3.12. Skips all require the absent fixed2.wav fixture.
  No tests were excluded or weakened. Receipt:evidence/72h_completion/full_tests.txt.
- xLights2026.18 AppImage SHA256 matches the pinned CI runtime
  `62affb88b9a9b03cf5164974ac69bcefe35c559719d157b3364e4d4a5ab4214b`.
  Local native execution cannot connect GTK to an X display because this host
  denies the required socket operations. This failed attempt is not a native pass.
  The unchanged native gates plus the new kit proof run in GitHub Actions.
- Latest hardening183057f GitHub runs observed during this audit: Helix CI
  38687268892 and38687262647, Windows38687268816, Beta/Birdsong/Compliance all
  succeeded; Android38687268743 was still running when inspected. These are
  **prior-source** receipts and do not certify this branch.

## Remaining work requiring separate evidence

Native run38688520597 exposed an existing generated-LOR-layout brightness bug:
legacy ModelBrightness=100doubled dimmer values and clipped cymbal decay. The
new kit's4,800-value native assertion caught it after giant/twelve-string checks
passed. Generated workspace grids now use neutral0; original user layouts,
addresses, cue times and LMS intensities are preserved. The native assertion
remains unchanged; rerun evidence is required before claiming this fix passed.

- Independently review137uncertain tom labels and issue144's audible passages;
  acquire source-separated duet lanes rather than duplicating mixed vocals.
- Recover the complete original LightsOutTheme input and confirm its hash.
- Verify each recording's creation account/date/entitlement and redistribution
  permission; separate Suno accounts remain separate. Build authorized full-song
  showcase ZIPs only after those inputs are available.
- Complete Samsung/ARM64, controller and licensed LOR playback checks, full-length
  Android previews, production signing/16KB/store requirements and physical2D/3D
  fabrication checks. The new kit's front-view contract is not hardware proof.
- Rebuild/installers from the final approved revision, verify checksums and
  packaging, review the stacked PRs and integrate them into the default branch
  only after the applicable gates pass. No stable-release claim is made here.

This audit supersedes stale implementation-status statements only where it gives
new source or execution evidence. It does not remove earlier acceptance gates.
