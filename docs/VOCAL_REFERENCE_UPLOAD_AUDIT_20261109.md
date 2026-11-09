# Vocal-reference review — owner Drive uploads (2026-11-09)

## Grounded reference videos

All three were found in the connected Google Drive root on 2026-11-09 and inspected as original MP4 bytes:

| Source | SHA-256 | Runtime | Observation |
|---|---|---|---|
| [04_Phoneme_Test_Hook_Band.mp4](https://drive.google.com/file/d/1pN1sfmC7DiltPJYw4J7IJqKoEv-7l6fJ/view) | `744ce940303fa9cd64e2dcad640906f05ad84a13dda43019767e932d0499c2c1` | 34.95 s | Native-looking snowman faces move to the soundtrack; not proof of separately resolved lead/backing |
| [04_Phoneme_Test_Hook_Helix_Faces.mp4](https://drive.google.com/file/d/1oKPu5MXMcP5eyZhJttwM93Y46zB_2e1m/view) | `6b691724ad1283af8f23586ca0d0724b46a80500dfb0f292628774eb9fd3b157` | 34.95 s | Several distinct face props visibly change mouth shapes, often in sync |
| [04_faces_Refined_3D.mp4](https://drive.google.com/file/d/18Xolap0r8bZEj0MkaYi1xlMwqcXbdy_7/view) | `328c38ae9df6b91e7c98600608b54022edb9ed818d757454ab5be1fce509604f` | 34.95 s | Refined 3D face and snowman geometry; timed mouth changes |

Original media audio was decoded to mono PCM at 8 kHz for a reproducible rough comparison. The first two audio tracks have Pearson correlation **1.0000** and the third correlates **0.9994** with the first, without a fitted time offset. Therefore these are **three render variants of essentially the same vocal recording**, not three independent vocal separation ground-truth examples.

At approximate source times 2 s, 8 s, 15 s, 23 s and 31 s, the tree face and the purple snowman face in the dedicated faces render appear to use similar phoneme shapes. These sampled observations cannot establish whether the singer identities were separated correctly. Rendered MP4s do not expose source stems or isolated source-bound vocal clocks. The user reports that the backing vocals seem to work; treat this as useful visual feedback, not verification of separate voices.

## Implementation defects found and corrected in candidate branch

1. `music/vocal_qualification.py` previously suppressed only **exact** duplicated voice activity/shape/envelope clocks. Nearly gain-scaled mirrored mouth clocks could slip through and animate a false backing singer. Add a conservative near-mirror check for *unverified estimates only*. Genuine unison with independent dynamic envelopes or independent backing-only events is preserved.
2. `tools/build_approval_collection.py` previously passed **raw, unscreened** `estimated_backing` clocks to generic singing faces while the canonical band exported `screened_lanes`. This permitted inconsistent behavior across the same twelve-layout comparison. Route all generic faces and spatial export through the same qualified screening policy as the band's Faces effects. Preserve already-verified source clocks untouched and record the screening outcome in the layout manifest.

Tests: `tests/test_vocal_reference_mirror_guard.py`, `tests/test_approval_vocal_clock_screening.py`. Existing `tests/test_vocal_qualification.py` and `tests/test_phoneme_vocal_export.py` remain relevant regression gates.

## Remaining acceptance requirements

- Validate new tests in Python 3.11/3.12 and preserve existing passes.
- Rerender a **real source vocal reference** with updated clocks and native xLights XSQ/FSEQ. Verify both lead/backing active timelines, and reject phantom harmony during instrumental/silent segments.
- For true independent voice identity, require independently source-qualified stems or corroborated vocal separation; identical audible lyrics or simultaneous mouths do not establish separation.
- Preserve all current approved geometry and musical roles, no unwanted mallets or seven-member substitutions.
- Never merge PR #188 or release beta without owner approval.

This document is an evidence-based fix/handoff, **not** a claim that the updated vocal source has been approved.
