# Bass note accuracy — release/showcase acceptance gate (2026-10-17)

Owner requirement: bass performer must play the **correct musical pitches**, not merely pulse with bass energy.

Current code observation: `models/band_performance_scene.py` defines `TUNINGS['bass']=(28,33,38,43)` and `string_assignment(note,kind)`. These are note-to-string/fret helpers, **not proof** that the actual bass transcriber identifies pitches correctly or that exported animation follows the note. The rendered bass model includes independent plucking and fingerboard arms. Trace the entire signal chain before claiming accuracy.

## Required behavior
- Identify bass fundamental pitch and octave from the real recording; distinguish bass from kick, guitar, low keyboard and sub-bass effects. Handle harmonics and octave ambiguities explicitly.
- Maintain note-on/note-off timestamps, duration, velocity and confidence; avoid spurious notes during rests and sustained passages.
- Route only verified bass notes to the bass musician. Use `string_assignment` to select a playable string/fret with the instrument's established tuning; reject out-of-range notes rather than silently misrepresenting them.
- Animate left-hand fretting to the mapped string/fret and right-hand pluck at note onset; hold the left hand for sustained notes. A simple audio-energy flash is not sufficient evidence of pitch tracking.
- Compare reference pitch contours and note events with generated bass-note records, pose frames, native XSQ effects, FSEQ output and final MP4. Include timing tolerances and pitch/Octave correctness in automated tests.
- Test walking bass, repeated notes, octave jumps, held notes, bass + kick overlap, bass + low guitar overlap, silence and a deliberately detuned/noisy example. Include at least one real Drive song with an audible, independently verifiable bass line.
- If source separation is unreliable, report uncertainty and do not claim exact notes or animate fabricated fret positions.
- Keep 16-channel AC mappings, source audio and release hold unchanged.

Status: audit/acceptance requirement recorded; note detection and native performance correctness not yet verified.
