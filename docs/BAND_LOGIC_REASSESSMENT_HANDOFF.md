# Band logic reassessment handoff

Read [MASTER_TODO.md](../MASTER_TODO.md) first. Source branch: `feature/band-logic-reassessment`, based on `56477cb2dd20dabf3c507f2fd11503793528d89f`. This reassessment follows the published 21-movie instrument review; it preserves those movies and original analyses. Fresh working inputs/media are in `outputs/Band_Logic_Reassessment/`.

## Findings and changes

- Bass: 281 accepted note-onset frames were hidden behind louder old release tails across the five songs. Active holds now take precedence over releases. A quieter same-pitch retrigger owns its velocity instead of inheriting the old note's louder tail. Lower absolute pitches still move the left hand toward the sky; higher pitches toward the ground. The measured neck height survives rests.
- Guitar: averaging frets from different strings produced unsupported contact positions. The mitten now follows one supported dominant physical string/fret. Visible frets and contact use semitone spacing: the twelfth fret bisects the string. Six independently routed strings and explicit impossible-note omissions remain. This is one dominant contact, not a complete articulated finger model for every chord.
- Keyboard/mallets: actual hand contact now follows the depressed key top throughout held notes. Source-onset gestures use the triggering event's velocity, independent of louder held notes. Literal pitch/key mapping, separately screened mallet provenance, and single-hand versus spread-chord behavior remain.
- Member anatomy: ownership tags keep mouths, eyes, carrots, scarf tails, holly/berries and hats together with their head/body motion. The piano's previously unprefixed holly/berries now relocate with it. Arm roots track the moving torso. Mouth deformation remains independent and repeated/random-access poses do not accumulate displacement.
- Singers: both authored lanes are active in every song. Recognized lyrics, sustained wordless vowels and duet arrays are byte-preserved; identity/gender separation remains unimplemented. Quiet acoustic vocables are not erased merely because the normalized gesture-energy lane is zero.
- Drummer: the audit found six low-intensity accepted hi-hat hold frames hidden by a preview-only 0.16 cutoff. Any positive accepted strike now activates its canonical pose. Idle colors and cymbal decay still do not create strikes. Preserve the v7 outward/lower torso shoulders, all kit surfaces and original XSQ target/hand/hold schedules. Low holds occur at Wire Tree190.15/190.20s, 49 191.95/192.00s, Candy Cane Chaos4.95/5.00s.
- Older runtime/demo export: four members intentionally have no approved generic runtime states. Preserve that restriction. Direct compilation now gives an explicit error; the demo exports available drummer states and both vocal Faces instructions, and lists the four deferred runtime members rather than crashing or claiming full coverage. Stale tests now distinguish the active V3 drummer from the archived starter geometry.

The active review implementation remains the readable-band scene/performance adapter. Earlier render adapters/default paths are compatibility entrypoints for historical batches. Use the new reassessment driver and input namespace for this review; never overwrite historical analyses/media to make them appear upgraded.

## Reproduction and evidence

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m tools.rebuild_band_logic_review
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m tools.audit_band_logic_reassessment
LIBGL_ALWAYS_SOFTWARE=1 EGL_PLATFORM=surfaceless LP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m tools.render_band_logic_reassessment
python -m tools.package_band_logic_reassessment
```

The rebuild uses the accepted prior NoteEvent files, without re-estimating pitches or words. The audit additionally requires retained six-stem WAVs. Source/analysis inputs for rendering can be restored from the previous pinned input ZIP at media commit `a8f7e9ed3973774874d9f719cd0a7b38a245cc2a` (SHA256 `ac7c36b1a749aedf09d2de20681163e3ede052d2062466474f228919bdc6b2ec`), then recompiled, or use the analyses included in this new review ZIP. No raw stems are bundled in either ZIP.

Evidence lives in `evidence/band_logic_reassessment/`: recompiled input differences, source/event/pose checks, singer/face/shoulder/native-schedule coverage, regression log, encoded render proofs, archive hashes and publication receipt. 54 focused regressions pass. The source audit checks6,518 actual route/pose frames,3,449 face/shoulder frames,94 singer shape combinations and7,711 accepted drum target-hold frames. Both singers participate in both full-stage excerpts. Eight fresh1080p20fps movies contain1,620 checked frames;33 encoded own-instrument comparisons and all6 formerly hidden quiet drummer frames pass. All24 decoded review frames were visually inspected. Minimum original-excerpt audio correlation is0.9990036120018922. The ZIP passes CRC and every extracted SHA256; complete public downloads of the ZIP and all8 MP4s match local bytes.

Download index: [BAND_LOGIC_REASSESSMENT_DOWNLOADS.md](BAND_LOGIC_REASSESSMENT_DOWNLOADS.md). [Single ZIP](https://raw.githubusercontent.com/ryankorkowski-boop/helix-sequencer/e0ced9127e677cad2677dadda017a18f59ffd1b1/band_logic_reassessment/Snowman_Band_Logic_Reassessment.zip). Media commit: `e0ced9127e677cad2677dadda017a18f59ffd1b1`. ZIP SHA256: `3af81d048898c1fc1abfc690fce40fa31516b98a1cfc60e0d6fc13a00492706a`; size: 70574792 bytes. The three instrument studies last12s, full stages18s and targeted quiet-drum studies3s; they are diagnostic excerpts, not replacements for the earlier21 full42s samplers.

The initial38-pass/4-fail audit exposed stale V2/archived assertions and the empty-state crash, all now addressed. One member-auditor import was corrected, and float32 transform comparisons use1e-6 tolerance. The first movie pass was stopped after discovering the quiet-strike cutoff; every final movie was rerendered under the fixed code before packaging. No partial or superseded render is delivered.

## Limits and continuity

Separated stems, pitches and mallet labels remain estimates, not a verified score. A stem-wide attack cannot prove which individual held chord tones were replucked. Source-grid timing remains50ms. Detected/source-tagged drum holds are not exhaustive audible-hit ground truth. New native xLights/controller playback, full finger articulation, automatic voice identity separation and the empty generic runtime member states remain deferred. Do not promote the illustrative demo into a musical transcription path.

Regression risks: stale cached curves, release dominance, quieter retrigger gain, unsupported guitar contacts, head/accessory/root drift, key/hand gaps, silence motion, low-intensity strike filtering, and confusing an archived native contract with active V3. Keep the counterexample regressions and separate actual-source/encoded checks. Full-repository CI is not claimed by focused checks.
