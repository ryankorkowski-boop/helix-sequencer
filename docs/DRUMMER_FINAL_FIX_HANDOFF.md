# Drummer recovery candidate — 2026-10-07

**Status: engineering validation complete locally; remote CI and human acceptance pending at commit time. This is a recovery candidate, not a declaration that the drummer is finished.**

Branch: `fix/drummer-target-strikes`. Starting/rejected HEAD: `3e8605421990e435700da1a7470d13fd09d193bb`.
See `MASTER_TODO.md` and `DRUMMER_RECOVERY_CHECKLIST.md` for the running ledger.

## Historical reference recovered

The ledger's run `35486153096` was a Pages publication for a separate remote-preview run. The actual **Helix Full Current 256 + Drummer** run at `b27e8d77a63027ed32bcf6851dcff3925472c155` is:

- [Run 35485877322](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/35485877322).
- [Archived full-song artifact](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/35485877322/artifacts/10597736307).
- Job `106012031344` logs independently confirm raw counts 194 kick / 37 snare / 9 tom / 208 hat / 840 cymbal / 47 bus, and 1,315 scheduled events: 193 kick / 37 snare / 9 tom / 205 hat / 824 cymbal / 47 downbeat/bus.
- All 1,335 raw events were reproduced from the frozen source on the same song. All 400 available archived timeline rows match the reproduction exactly in millisecond timestamp and family. The archived rows are committed as a behavioral fixture, distinct from independent provisional audio anchors.
- The archived ZIP was located, but its 48 MB size exceeds the executor's 32 MiB transfer limit. The original MP4 has not been decoded/listened to here. The event reconstruction and archived logs are verified.

## Regression evidence

Rejected #217: 1,164 onset candidates, 339 accepted onsets, 405 typed/scheduled events. It rejected 577 for short-window quality, 128 for context quality, 64 for local support, 32 for attack contrast/release filtering, and 24 after classification/consensus.

Examples: 11.98s, 19.15s and 19.80s were detected, classified kick by **both** windows, and had strong waveform attacks, but context RMS quality deleted them. Historical 14.58s also has a strong attack, but short-window quality deletes it. Independent waveform/band plots show the missing pulse sequence. The rejected preview had only two kicks in roughly 11–18s.

Removing only context quality gives 518 events; removing only short quality gives 414. Thus another single threshold tweak cannot recover the historical performance. One-at-a-time historical ablations show HPSS margin 2 changes kick counts 194→133 and hat counts 208→368; resampling alone changes kicks 194→221; hop/wait/delta changes also alter the stream. These are diagnostic counts, not acceptance quotas.

The recovered candidate restores native-rate HPSS margin 1, 2048 FFT / 512 hop, .045 onset delta / wait 1, original bands/decay features, original principal-family classification, and original unrefined transient grid. It retains explicit safety decisions for harmonic dominance, supported entrance with 80 ms preroll, literal waveform cutoff, ambiguous bus, and unresolved tom pitch. It does not restore bus distribution or tom cycling.

Tom pitch comes from a prominent new post-attack resonance above the preceding mix; HPSS-family evidence originates the candidate. The historical kick/tom overlap is resolved only for strong low-mid dominance and almost no metal. This remains a relative pitch heuristic and requires auditory verification; it does not know the recording's drum tuning. No mid-tom quota is imposed.

## Candidate evidence

Full song: **1,182 scheduled physical hits** — 188 kick, 36 snare, 202 hat, 749 cymbal, 7 tom. The seven toms resolve as one floor / six high / zero mid. All eight targets remain defined; the mid target is not artificially exercised by this song. The deterministic 68-event physical fixture exercises all eight.

All 400 archived raw classifications remain in the candidate audit before documented safety rejection. A one-to-one timestamp/family comparison recovers 1,182 historical matches; the rejected stream retains 185. Historical agreement is not independently labelled instrument truth.

Timing anchors restored include 11.9893, 14.5813, 15.5733, 16.2240, 19.1573 and 19.8080 kicks. Nine independently signal-inspected sparse anchors cover kicks, a snare and hats; labels explicitly remain pending human listening. No events occur before 10s. First coincident opening metal is 10.9867s and kick 11.0080s.

No geometry, source artwork, PNG poses, xmodel, preview compositor, body keepalive or strike overlap code changed. Regeneration leaves approved assets byte-identical. Pedal remains 32%; kick and hat have no sticks. Unknown toms and bus never emit. Scheduler merge/clutter/repeat rules remain unchanged and simultaneous typed inputs survive.

The separate drummer-only XSQ removes unrelated template effects, sets portable `Helix Audiolights.mp3` media, and corrects the obsolete 132.039s template duration to **237.440s**. Its logical performance matches the integration XSQ exactly. Native xLights import/playback is still unverified.

The encoded 25s preview (source 9.5–34.5s, 60 fps) was decoded at exact frames around known hits. Body visibility, independent lighting, complete strike poses and secondary hat pedal were inspected. Encoded soundtrack zero-lag correlation to the source at 9.5s is **0.99621464**. A full-song 60 fps H.264/AAC MP4 is also generated.

## Artifacts and reproduction

Local validation: **100 passed**, two preexisting deprecation warnings; asset regeneration and the 68-event WAV/XSQ oracle also passed.

Local directory: `test_runs/drummer_recovery/`.

- `Helix_Drummer_RECOVERY_25s.mp4` and `Helix_Drummer_RECOVERY_FULL.mp4` — actual song audio.
- `Helix_Drummer_ONLY_REAL_AUDIO.xsq` — isolated real-song sequence.
- `recovery_report.json` — accepted events and every candidate's spectral/quality/rejection/scheduler/target trace.
- `historical_events.json/.csv`, `rejected_events.json/.csv`, `recovery_events.json/.csv` — comparable streams.
- `comparison_summary.json`, `historical_disagreements.json`, `stage_ablation.json` — before/after and stage evidence.
- `comparison_*.png`, `decoded/decoded_hit_contact_sheet.png`, `decoded/preview_frame_evidence.json` — independent signal and encoded frame evidence.
- `*_clicks_with_song.wav` — diagnostic family tones over the same excerpt. Kick=90Hz, snare=700Hz, hat=6500Hz, cymbal=2400Hz; toms=480/310/150Hz. These are review aids, not independent labels.
- `final_tests.txt` — complete relevant local regression result.

Run from repository root with `PYTHONPATH=.`. Install the drummer workflow's declared dependencies, including matplotlib. The workflow now regenerates the historical/rejected comparisons, signal plots, clicks, isolated XSQ, full MP4 and exact decoded-frame evidence. It uploads `drummer-real-audio-proof` and `drummer-recovery-comparison`.

```sh
python tools/recover_drummer_reference.py
python tools/audit_rejected_drummer_217.py
python tools/integrate_drummer_v3_into_xsq.py template.xsq 'Helix Audiolights.mp3' --output test_runs/drummer_recovery/Helix_Drummer_RECOVERY.xsq --report test_runs/drummer_recovery/recovery_report.json
python tools/export_drummer_only_xsq.py test_runs/drummer_recovery/Helix_Drummer_RECOVERY.xsq --output test_runs/drummer_recovery/Helix_Drummer_ONLY_REAL_AUDIO.xsq --audio 'Helix Audiolights.mp3'
python tools/compare_drummer_recovery.py
python tools/ablate_drummer_history.py
python tools/plot_drummer_history.py
python tools/render_drummer_v3_preview.py test_runs/drummer_recovery/Helix_Drummer_ONLY_REAL_AUDIO.xsq --audio 'Helix Audiolights.mp3' --output test_runs/drummer_recovery/Helix_Drummer_RECOVERY_25s.mp4 --start 9.5 --duration 25 --fps 60
```

## Remaining gate / risks

The available tools permit audio signal and encoded-frame inspection but provide no auditory perception tool. No listening or human review has been claimed. The sparse fixture is provisional and explicitly names its provenance. The full mix remains intrinsically ambiguous: historical sustained-metal classifications can include ride/hat activity, principal-family detection can omit a co-occurring instrument, tom tuning is unknown, and mono cymbal side alternation is a physical convention. Inspect especially the 13.61s tom assignment, later 151–158s toms, and cymbal/hat distinction.

The former six-cymbals-per-second assertion rejects the accepted historical stream itself (nine per second); it is replaced by a documented broad sustained-metal burst guard plus sparse anchors. Unit tests preserve isolated family identity, cutoff rejection, native-rate timing tolerance and all three explicit tom pitches. They do not manufacture a current-output expected fixture.

**Do not mark finished until the user reviews the real-audio MP4, confirms what they hear matches the visible performance, and approves the sparse auditory anchors. If rejected, use the candidate traces and historical comparison to diagnose the cited moments; do not respond with another green-CI claim.**
