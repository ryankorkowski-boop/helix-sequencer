# Helix four-performer execution checklist

Branch: codex/band-performance-refinement-20261012. Baseline: f0aca518f5a1dff15ab24eb8127d09cc26ea8990. Master continuity ledger: MASTER_TODO.md.

- [x] Check out requested branch; inspect shoulder, primary and newer band branches.
- [x] Inspect and selectively carry newer instrument/refinement code. No branch merge.
- [x] Preserve original audio, artwork, layouts, templates, and previous native shows.
- [x] Connect drummer joints with stable shoulders and fixed original shafts; idle/body/strike gains separate.
- [x] Separate source onsets from kick activity, note sustain and release tails.
- [x] Add fixed-length 3D bass/guitar/mallet joints; literal bass fret contact and held positions.
- [x] Retain piano; dedicated mallet rig uses screened estimates and literal bars.
- [x] Preserve exact mallet acoustic times; display contacts quantized within 25 ms.
- [x] Existing band renderer offers --performance-refinement.
- [x] Focused + sampler regressions: 52 passed.
- [x] Wider existing regressions:67passed;114unique checks with focused suite.
- [x] Complete dry A/B; six real-song excerpts; C/E montages.
- [x] Native xLights matrix rendering and pixel checks.
- [x] Fully decode videos; inspect quiet/strike/fill/string/mallet frames; verify source soundtracks.
- [ ] New phone-accessible downloads verified.
- [x] Implementation/evidence commits on requested branch.
- [ ] User artistic review. No primary merge authorized.

Limitations: raw separated WAV stems and exhaustive independent instrument labels are absent from recovered inputs. Counts are not accuracy scores. Mallet instrument identity and real guitar stroke directions remain estimates. Virtual matrix Video XSQs reproduce the rendered performance; individual physical-prop native animation parity is unfinished.
