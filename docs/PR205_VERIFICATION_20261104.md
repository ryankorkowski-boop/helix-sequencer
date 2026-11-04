# PR 205 verification — 4 November 2026

Implementation under verification: `37fb716cc9581cb1024760a23b53d65589496f02`.
Recovery control: `05c1de55d2e4d747652452ade0d9752d370b55d9`.
Evidence directory: `evidence/beta_completion/pr205_verification_20261104/`.

Decision: HOLD release-path signoff. The facade/cache changes preserve outputs and pass the Windows frozen-worker checks, but both hosted Python suites fail four CPU-kernel-dependent chroma cases and all three representative native movies fail existing visual acceptance thresholds. Native export compatibility and real soundtrack synchronization passed. No diagnostic is accepted as an approval video; PR188, beta publication and owner acceptance remain held.

| Proof | Completed result |
|---|---|
| Integration | Recovery changes incorporated into the feature branch; PR205 has no merge conflict. Protected drummer detector, mapper, motion, source geometry, original AC mapping and thresholds are preserved. |
| Local tests/ Python 3.11 | 2,349 passed + 24 passing subtests; 6 existing skips; 382.10 s. |
| Local tests/ Python 3.12 | 2,349 passed + 24 passing subtests; 6 existing skips; 377.29 s. |
| Numerical portability | Local default kernels pass. Hosted Python 3.11/3.12 each fail the short classifier case and three long tails at unchanged atol 1e-7/rtol 0. Haswell/Zen reproduction fails; recovery control fails identically. |
| Canonical drummer | 68 events/eight targets; exact ordered cue/motion/debug payload before/after extraction; 0 FP/FN and 0 ms time/target drift. |
| Exact original 237.44 s MP3 | Recovery control and candidate off/miss/hit each reproduce the historical 42,305-effect XSQ SHA258f03ef... and band SHA0d1c9c21... exactly. |
| Full 237.44 s PCM | Four fresh CLI processes: recovery control, candidate off/miss/hit. Each has 42,330 effects; exact XSQ 7da1338b... and band 8084c534... hashes. Valid declared targets and bounded finite times. |
| Real 34.88 s MP3 | Control/candidate source XSQ and band JSON match exactly; candidate cache-off/miss/hit all have 6,307 effects and exact outputs. |
| Windows frozen worker | Actual executable off/miss/hit outputs match XSQ 4be25e03... and band 8eca863e...; cache hit leaves NPZ bytes and mtimes unchanged. Packaged FSEQ/LOR/GUI checks pass. Run 41874095171; authenticated diagnostic artifact 13345378551 inspected and hash verified. |
| Preview selection | Tied numeric scores no longer compare dictionaries; existing ranking priorities/source-order ties retained. 7 local cases pass and remote preview 41874083876 succeeds. |
| Native compatibility | Actual current-source AC256, canonical dimensional band and RGB singing-face shows render native FSEQ and 1080p H.264/AAC at 20 fps movies. All 698 frames; full decode; original audio correlation 0.9968248; four 0 ms alignment windows each. |
| Native control comparison | All three derived native XSQs are byte-identical across recovery control, local candidate and the actual CI-rendered inputs. Native generator source was unchanged. |

The six local skips are five sandbox cases requiring unprovided 2.wav and the optional manifest-driven native integration case. The dedicated native job exercises real exports independently. Local suites omit optional Whisper/Torch. Three additional tools/preview tests collected by root-level pytest also pass on each local runtime. Hosted full CI completes with four failures per runtime; local passes do not supersede them.

## Remaining native visual failures

Existing floors are unchanged: median luminance 12, motion 0.65 and bright fraction 0.012.

| Show | Measured failure | Passing evidence |
|---|---|---|
| Original256AC | Luminance 9.466 | Motion 5.737; width 0.519; height 0.544; exact 256-channel FSEQ. |
| Canonical band | Luminance 8.963; motion 0.625 | Width0.569; height 0.356; opening cast framing passes; all 173,712 channels exported. |
| RGB singing faces | Bright fraction 0.01110 | Luminance 15.741; motion 1.427; width 0.519; height 0.578;12,198-channel FSEQ. |

These failures occur on byte-identical recovery/candidate native sequence inputs. They are existing presentation acceptance gaps, not evidence of changed sequencing from the facade. Beginning/middle/end acceptance is not inferred from a codec or channel-export pass. Representative actual native frames were inspected: the band remains small/dim in the frame and the lighting views have insufficient bright coverage.

Smallest remaining render work: repair native preview framing/visibility and genuine source-driven band motion while preserving source events, original AC wiring/colors and unchanged thresholds, then rerun only `Optimization native regression`. Record FSEQ comparisons when a change is intended to affect preview presentation alone. Independent singer identity/lexical timing, physical qualification and the owner's nine-video acceptance remain separate release gates. Do not add broad musical-engine integration to close this optimization PR.

## Measurement limits

The recovered 237.44 s PCM checkpoint is a different byte input from the historical original MP3. Do not compare its 42,330 count directly to the old 42,305 receipt. Its correctness-run CLI times were205.39 s control,180.92 s off,202.43 s miss and156.73 s hit; other verification overlapped. Candidate audio/harmonic feature stages fall from35.639 s off to0.923 s hit. These establish cache reuse and parity, not a controlled whole-engine speed claim. Candidate process peak RSS is1215279104bytes off,1213304832miss and1198190592hit.

The exact original MP3 SHA 8ced92ba... was also verified in the tracked checkout. Recovery control and candidate cache-off/miss/hit all recreate the historical 42,305-effect XSQ SHA 258f03ef... byte-for-byte and the same band SHA 0d1c9c21.... CLI times are 218.75 s cold control, 191.86 s off, 184.27 s miss and 151.20 s hit. Cold stem computation is included only in the first control; no controlled overall speedup is claimed. Original-input proof and reproduction script are committed alongside the other receipts.

## Current hosted runs and resume

- Full push CI 41874083597 and PR CI 41874095074: completed failure on both Python versions. Push jobs report 2,348 passed, four failed, six skipped and 24 passing subtests each; maximum entropy error 2.66020723e-7 exceeds the unchanged 1e-7 tolerance. See hosted_failure_summary.json and numeric_backend_reproduction.json.
- Windows 41874095171: completed success, including frozen-cache probe.
- Native 41874095353: export/decode/audio passes; visual gate fails as recorded above. Artifact13345767395, ZIP SHA25615058e104039d9b7700f6474dba6e9044173273e44559710a8d3fa4fb05b00dd.
- Source artifacts and failed native media remain diagnostics; no native owner approval or hardware-output acceptance.

Read MASTER_TODO.md first. Restore the checkout and declared dependencies, then use the committed receipt scripts; current local source tree is at `/workspace/scratch/78f26c400f5c/helix-sequencer`. Exact original-MP3 comparison completed under `/workspace/scratch/78f26c400f5c/original-mp3-verification`; its orchestration script is `/workspace/scratch/78f26c400f5c/verify_original_mp3.py`. Other restored source checkpoints and native artifacts are internal test inputs. Never substitute a prior failed movie or synthetic soundtrack.

## Numerical reproduction and minimum next verification

The bounded-background function AST is identical to recovery control. On this compatible local CPU, selecting the OpenBLAS Haswell or Zen kernel reproduces all four failures; the local default SkylakeX and Sandybridge kernels pass. This is a numerical-kernel selection experiment, not physical-device acceptance. Neither thread-count/overlap adjustments nor float64 probes established a repair at the existing tolerance, and none was applied to production.

```bash
OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=2 NUMBA_CACHE_DIR=/tmp/helix-pr205-repro python -m pytest -q tests/test_bounded_audio.py -k 'bounded_classifier or partial_blocks'
```

Repair the bounded transform's conformance across kernels while retaining sample clocks, global tuning, event assertions, the 16 MiB input ceiling and 1e-7 tolerance. Then run the focused backend cases and both hosted full suites. Preserve the proven original-MP3/cache/Windows receipts as controls, repeating affected production comparisons after a real DSP fix. Native presentation/source-motion changes need the three-show render gate; independent acoustic/lexical and owner approvals remain separate. The final receipt is metadata-only; implementation identity and module hashes remain 37fb716.
