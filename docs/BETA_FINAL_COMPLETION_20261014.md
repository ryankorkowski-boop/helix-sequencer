# Helix Beta v1.0 final completion evidence

Candidate branch: `codex/beta-final-completion-20261014`, based on PR146
`cb6cff6bcf0227386a244b4bf2ea369ee9bab228`. The protected default branch is unchanged.
This document records acceptance gates; it does not declare the whole release green.

## Repository reconciliation

The 48-hour window starts 2026-10-12 16:49:34 UTC. The GitHub issue/PR listings
identify PR139–142/145/146 and issues143/144 as updated in this window. The earlier
PR134/137/138 stacks were also inspected because the task names them. All remain
unmerged drafts. Forty-two integration commits in the window were inspected,
including timed-correction94ddc56d, Infinite Symphony081b8f71, GUI a678b715,
Android31d2c860 and readable rig8c46f4ae. No entire development branch was blindly merged.

| Feature | Classification | Evidence / remaining gate |
|---|---|---|
| RGB palette repair, PR134 | Completed and verified in the prior source | Explicit neon opt-in; existing palette tests and previous native/package checks retained |
| AC-only XSQ, PR137 | Completed and verified in the prior source | Existing AC fence and structural/native output receipts; controller playback remains external |
| xLights/legacy LMS GUI modes, PR138 | Completed and verified in the prior source | Previous Windows launch and real sequencing; modern LOREDIT remains unsupported |
| Android muxer/recovery, PR139 | Completed and verified in the prior source | API30/API36 real MP3/WAV, decoded preview, export recovery and same-key reinstall in one run |
| Branding/help, PR141 | Completed and verified in the prior source | Integrated into PR146; new candidate builds must rerun platform checks |
| Separate keyboard and mallet performers, PR140 | Superseded for the final scene | Historical rig preserved; FinalBandScene has six visible members and one right-side pitched performer |
| Wire-contour second band, PR140/142 | Superseded for the final scene | Historical previews preserved; solid jackets, boots, heads and swept hair replace wire performers |
| Guitar motion and solid instrument meshes | Completed and verified locally | New regressions retain closed guitar/bass meshes and exact guitar string/contact coordinates |
| Unified pitched/mallet response | Implemented, verification in progress | Piano, screened ringing attacks and harmonic residual notes share a two-hand schedule; excess/unreachable chord contacts reported |
| Giant native layout / two pixel bands | Implemented, verification in progress | 1153 models, 1182750 channels, 18 houses, 9.102x XZ area; 88 disjoint ordered rungs; two six-performer stages |
| Native note props through GUI/CLI/Android | Implemented, verification in progress | Shared sequence_builder post-pass uses actual harmonic cues and reserved RGB submodels; original layout retained; opt-out flag; LOR/AC paths excluded |
| Original rapid-kick passage, issue144 | Implemented, source evidence verified; listening gate open | Exact WAV hash below; recording-specific low-band calibration recovers nine missed attacks, including eight rapid attacks; no count or beat filler |
| Independent overlapping singers | Implemented input support; external evidence missing | Independent source-bound mouth/energy lanes supported; no true independently separated opening voices are available/verified |
| Six-layout real sampler | Sequences generated; native/video verification in progress | Six independent Helix exports, 17236–17613 native effects each; no soundtrack is committed to validation inputs |
| Full LightsOutTheme giant movie | Blocked by missing original input | Full file absent in current/archived source audit; no different song is represented as it |
| Full-song public showcase ZIP | Blocked by track-specific rights evidence | Zero recordings have complete creation-account/date/entitlement/remix redistribution evidence |
| Fresh same-revision installers | Build/verification gate in progress | Candidate triggers Windows and Android builds; prior packages remain separately identified |
| Official PolyForm license | Completed and verified locally | Official 4563-byte text matches LICENSE byte for byte; historical MIT and third-party notices retained |
| Contributor/asset relicensing authority | Blocked by external provenance evidence | Public contributors: owner1104 commits, Actions bot2; commit attribution alone is not legal ownership evidence |
| Physical Samsung/ARM64/controllers/native vendor LOR | Blocked by unavailable hardware/software | No connected physical device or licensed LOR installation; emulator results cannot replace these checks |
| Google Play production readiness | Blocked by production dependencies | Debug signing, cross-build signing continuity, 16KB native wheels, store/privacy/testing gates remain separate |

## Exact original sampler and rapid kicks

Recovered reference WAV SHA256:
`0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb`.
It is the same 180.15-second WAV used by the earlier band movie, originally
recovered from prior comparison media. Original recording files are separate assets.

Unmodified ADTOF detects seven opening kicks at0.19,0.41,0.62,0.84,1.05,1.26,1.48s.
Within the explicitly reviewed0.15–2.72s drum-stem window, measured40–180Hz
attack/decay profiles matching those accepted references recover1.694,1.908,
2.013,2.118,2.227,2.332,2.442,2.547,2.656s. The final eight are approximately
105–110ms apart. Their source evidence retains RMS peak time, similarity,
reference amplitude and measured timing calibration. Similarity is not a class
probability; independent listening and tom/source identity remain acceptance gates.
The main detector thresholds and all events outside the explicit window are retained.

## Output boundaries

The animated GL band is a video/pixel-matrix visualization. Native bands use
finite RGB surface nodes and stationary addressable poses, not mechanical limbs
or guessed AC circuits. The existing twelve-circuit drummer contract stays intact.
Native tests explicitly distinguish authored diagnostic fixtures from real-song
transcription; six real-source light-cue sequences are rendered without copying audio.

Public audio/movie release requires a track-specific ledger. Different Suno
accounts and billing periods are not interchangeable. Local review media does not
establish redistribution rights. Physical upgrades across older debug signing keys
remain unverified; same-key reinstall within one emulator run proves only that run.

Community and support: https://Facebook.com/helixsequencer.
