# Snowman Band Audit

Date: 2026-04-22

## Current Output Status
- Source JSON: `gptseq\3_preview20,v27.3 (1).snowman_band.json`
- Enabled: `True`
- Performers detected: lead_singer, bassist, guitarist, drummer
- Cue counts: {'lead_singer': 0, 'background_vocals': 8, 'bassist': 16, 'guitarist': 62, 'drummer': 136}
- Lead face target (from sequence notes): `NBH_RIGHT_HELIXMASCOT_CUSTOM`
- Performer cue count (from sequence notes): `222`

## Progress Summary
- Snowman band export is active and generated on both full and 20s runs.
- Performer routing exists for lead singer, bassist, guitarist, and drummer.
- Drum kit mapping is present in generated notes (kick/snare/hihat/cymbal).

## Gaps Remaining
- Viseme depth is still low in the generated notes (lyric visemes reported as 0).
- Face routing is still sparse when explicit face props are missing in a layout.
- Motion nuance can be improved with stronger stem separation confidence.

## Recommended Next Pass
1. Add explicit viseme confidence scoring for singer/backing vocals.
2. Add stronger fallback face assignment logic when preferred targets are empty.
3. Add per-instrument gesture amplitude scaling by phrase energy.
