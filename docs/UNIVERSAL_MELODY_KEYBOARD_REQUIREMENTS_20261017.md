# Universal melody performer — keyboard/mallet routing

Owner requirement (2026-10-17): the keyboard performer covers any detected pitched melodic instrument that lacks its own band performer, including trumpet, horn, trombone, saxophone, flute, strings and synthesizer lead. This extends, rather than replaces, piano/mallet performance.

## Functional contract
1. Route confidently estimated note onsets, pitches, durations and velocities from otherwise unrepresented melody sources to the unified keyboard/mallet performer. Musical timing and pitch drive the notes; amplitude-only flashing is not sufficient.
2. Existing dedicated guitar, bass and vocal parts retain their performers. Do not double-assign those notes to the keyboard when source identity is established.
3. Piano, keys, xylophone, marimba, bells and other pitched-percussion lines are eligible for the same performer. Resolve the current separate piano/xylophone native roles into one visible unified keyboard/mallet musician as requested by the owner, while preserving native export compatibility and existing layout references.
4. When simultaneous pitched lines are present, allocate available left/right hands and mallets by onset, voice continuity, pitch proximity and physical reach. Preserve chords when representable; otherwise prioritize dominant melody and report dropped/ambiguous notes. Do not animate impossible multi-hand contacts.
5. Sustain brass, woodwind and string notes for their measured duration; use distinct strike/contact behavior only for actual keyboard or mallet attacks. Unsupported timbre is expressed by the keyboard playing the corresponding notes, not by inventing a horn model or instrument-specific gesture.
6. Source separation / polyphonic transcription confidence gates are mandatory. Avoid assigning drum transients, vocal harmonics, bass bleed or noise to this performer. Ambiguous sources remain unassigned with diagnostic evidence.
7. Drive actual native NOTE_MIDI submodels, hand/mallet poses, XSQ effects and xLights FSEQ channels. Verify decoded MP4 contact frames and source-aligned audio for trumpet/horn melody, a keyboard passage, a mallet passage and a mixed-instrument passage.
8. Preserve original audio, AC16 physical channel budgets, source-event clocks, existing accepted sequencing behavior and the release approval hold.

## Required implementation and tests
- Audit the note/transcription and performer routing stages before changing code. Identify why the xylophone is omitted from recent videos; prove whether the problem is classification, scheduling, model presence, pose export, native FSEQ, brightness or camera.
- Add a deterministic role fallback for confidently identified unrepresented melodic notes, with traceable event provenance and duplicate suppression.
- Add regressions for horn-to-keyboard fallback, dedicated guitar/bass exclusion, simultaneous piano + trumpet, mallet articulation, pitch accuracy, no spurious notes from silence/percussion, and native render proof.
- Generate at least one authentic Drive excerpt with a verified horn/brass melody and show the keyboard performer tracking it. If no verified horn passage exists, do not claim horn acceptance; use an appropriately annotated test fixture plus a separate real-song musical example.
- Explicitly obtain owner approval from visible native videos before merging into release EXE/APK.

Status: requirement committed; implementation, tests and native video acceptance remain open.
