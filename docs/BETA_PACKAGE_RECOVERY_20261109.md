# Helix current runtime installers — 9 November 2026

APK and Windows EXE bundle verification is complete for runtime source `712b7ba45409f92f704d322440a76f4243090d2e`. PR #188 remains open because its native acceptance requirements are incomplete.

The runtime commit synchronizes both GUI sequencer/output selectors. LOR selects LMS unless Both is already selected; xLights selects XSQ. Run preserves the selected mode. All seven existing review findings now have checked fixes and regression coverage, and all seven review threads are resolved.

## Verified downloads

| Platform | Successful job and artifact | Payload SHA256 |
| --- | --- | --- |
| Android API 30, shipped debug APK | job 129348415473; artifact 13699791623 | `c0841aae4b570b4551e778e781a64b704c4b0c99bb9a8a7f0b802a6c5443b84a` |
| Android API 36, independent same-source build | job 129348450916; artifact 13699776977 | `8aa43fc12e9f4c2d446fabe628b04f09c171ed68d9621c766c39e3c61030512c` |
| Windows portable EXE folder | run 42672170196 attempt2, job 129352516584; artifact 13698673732 | `611aa87e2b29bc476b891f8d9ef4221328a68f3f794a7cafbb7cb0dfaf7cbbcc` |

- [Android API 30 artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/42671898667/artifacts/13699791623)
- [Android API 36 artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/42671884943/artifacts/13699776977)
- [Windows artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/42672170196/artifacts/13698673732)

Local extracted downloads are in `/workspace/helix-delivery/current-runtime-review/`: `Helix-Android-Beta-debug.apk`, `Helix-Windows-Portable.zip`, `VALIDATION_REPORT.json` and `SHA256SUMS.txt`. Keep the complete extracted Windows folder, including HelixCLI.exe and _internal. Android debug signing/install receipts pass; production signing and compatibility with an older installed beta key remain unverified. Each Android API job built its own APK; one APK binary was not installed on both APIs.

Each Android archive's digest/CRC, APK checksum, installation/signature receipt, embedded commit and 1,113 engine-file hashes were independently checked. Every engine file also matches the separately staged source 712b7ba inventory. All five decoded preview modes pass unchanged image/audio thresholds: xLights, LOR, real RGB, the 237-second full song and band disabled. Measured audio offsets are 0 ms and correlations exceed 0.9957. Windows embedded source/run identity, ZIP checksum/CRC, EXE/guide hashes and packaged GUI/xLights/LOR/native FSEQ checks pass.

## Tests and host verifier repair

Runtime source 712b7ba: full local Python 3.12 **2,386 passed, 24 subtests passed, six existing skips**, 224.26 seconds. Exact-source hosted Python 3.12 job 129348462226 passes the same counts in 322.25 seconds. The overall hosted run 42671885468 failed a separate GitHub internal server error; absent 3.11/lint jobs are not claimed as passing.

The host installer verifier still required exactly four Android media modes, while the current production decoder already emits five. It now requires all five exactly once, including band-off, and applies every existing image/audio threshold to all five. Missing band-off/full-song, duplicate modes and unknown extras fail. **63 focused installer/Android recovery/MP4 tests pass** after this repair. The later host-verifier/ledger commit changes no sequencing or GUI behavior; binaries retain their actual 712b7ba source identity. It is not a new full-suite or native-render claim.

## Outage recovery and historical fallback

Windows automatic 42671898984 and manual 42672170196 attempt1 failed before creating any job, with GitHub internal-server correlation IDs 1a9697c3-9925-4f37-891d-72b3d54feff4 and 92fea856-85b2-49f1-87e9-575c18d744db. GitHub independently confirmed Actions incident [tp8cghg7tlc4](https://stspg.io/7yw63xl9ztrv), started 18:12:37 UTC. The later successful Windows attempt supersedes this build blocker. Android job successes are distinct from overall workflow failures caused by missing companion jobs during the outage.

Earlier Windows 42645117790/artifact 13688270272 was recovered and independently verified as fallback source da5a7c6; its ZIP SHA 7243b4c41d5cd6cb3aa67ede3a3728548a918b9cbe319525bac3be90626ad302. It does not include the new GUI fix and is superseded by the 712b7ba Windows package above.

An attempted direct release-asset upload returned 401 Bad credentials on uploads.github.com, although release metadata access worked. The newly created empty draft 439493478 was deleted after verifying it contained no assets. No public release/tag was published or existing release assets replaced. Use the workspace downloads or the verified Actions artifacts.

## Remaining beta acceptance

PR #188 requires exactly nine qualified real-audio native MP4s and owner visual approval. Qualified current count remains zero. E14 producer 42645117700 rejects absent independently resolved lead/backing source. The actual native contact review fails motion (0.274 against 0.65); AC visibility, acoustic/lexical singer qualification, canonical solid drummer equivalence, four inherited Haswell bounded-chroma cases (unchanged 1e-7 tolerance) and physical Samsung/controller/vendor LOR acceptance remain open. Issue #199 is unchanged. The user has been asked where the independent vocal source/timing files are stored; package work did not depend on that answer.

No diagnostic video, prior-source binary, earlier green workflow or model-estimated vocal identity was relabeled as current qualified beta evidence. Continue from `MASTER_TODO.md` and `evidence/beta_completion/packages_20261109/VALIDATION_REPORT.json`.
