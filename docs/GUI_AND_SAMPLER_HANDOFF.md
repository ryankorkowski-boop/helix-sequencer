# Current GUI and sampler handoff — 2026-10-12

Review branch: `codex/gui-complete-integration-20261012`. It includes the preserved band implementation from `5c78ffa1`; primary remains unmerged.

Completed GUI source: `4bc7b222`, `856b74d2`, `fcdf94ce`, `0948a35c`, `dd0f2942`, `323b6cde`. Current GUI supports xLights XSQ and legacy LOR LMS modes; imported Unit/Circuit wiring; corrected musical neon table indexing and RGB target guards; native FSEQ preview and installed-xLights render tools; optional role mapping; queue-based bounded log processing; asynchronous layout building; and inactive Matrix/Birdsong controls disabled in LOR/AC modes.

65 focused GUI/export checks and 69 combined GUI/band regressions passed locally. Seven CI workflows at323b6cde succeeded, including actual Windows EXEs, GUI mode switching, real source-audio XSQ/LMS/MP4 generation and FSEQ decoding. Frozen distribution metadata, plugin/data resources and exact LOR swatches were fixed after real failures. The verified Windows release is `helix-gui-complete-20261012`; final source build:
https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38308843503

Native color probe: duplicate source palettes still produce intended RGB255/46/209, with neutral AC255, over10actual xLights2026.18frames. Root layout/template, original band scene/sampler logic and40protected source assets retain exact original Git blobs and SHA256.

The local execution workspace disconnected after both new180.15s movies had been rendered, fully decoded and inspected, before their final durable save. Do not provide unverified local download links. An isolated Actions rebuild now supplies durable public review downloads:
https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/38312641499

Temporary source access uses RSA3072-OAEP-SHA256 to an ephemeral runner key. Only ciphertext enters the public repository; private key and plaintext capabilities are not published. The authorized package yields only its exact WAV; the earlier private layout/package is not extracted or published.

Exact recovered WAV:7,944,585 stereoPCM16frames at44,100Hz,180.14931972789117s, including the earlier AAC recovery padding.
SHA256:`0fc2ab5dfee87d4af3e2ab326f76c7ee9cb3a5a893644487d2e7350a48cefafb`.
Nominal30s excerpts in order: Wire Tree151–181s; Tinsel Sawtooth94–124s; Frostbitten Fingerboard16–46s; Holly Steel Run67–97s; Bell Circuit Carol41–71s; Helix Audiolights46–76s. The WAV bytes remain the actual timeline authority.

The verified local run had3603frames per movie, shared source soundtrack correlations>=.9971829 at seven stereo sample windows, six native layouts activating all93/89/94/98/93/95RGB models with control channels dark, and a native384x216band matrix comparing3603frames at2.5108/255mean pixel difference. Fresh rebuilt outputs must be judged from their own reports, not assumed bit-identical to the local detections.

Issue132 was executed in a clean detached1f66f5d checkout with original256models/59groups preserved,80newRGB models, channels513–29648. The external runner required the actual main.py entrypoint and empty EffectLayer children in added template rows; missing layers caused zero discovered new targets. Existing role mappings are explicit and both lanes use the same master profile. Only preview duration is clipped, without injecting effects or modifying source. Two30s movies and their synchronized side-by-side comparison rendered locally; the Actions rebuild repeats them and preserves receipts. Their renderer simulates XSQ effects and is not native FSEQ parity.

Expected published review files, only after successful build/publication:
- Helix_Band_With_Singers_Same_Sampler.mp4
- Helix_Six_Layouts_Same_Real_Sampler.mp4
- Helix_Same_Sampler_XSQ_Layouts_And_Reports.zip
- Two decoded review contact sheets
- Three issue132 MP4s
- Helix_Sampler_Recovery_Report.md, archive_verification.json, soundtrack_audit.json, issue132_verification.json

The package contains seven portable show folders: six genuine Helix native lighting XSQs with local WAV/layouts/assets, and a separate Video-on-matrix band review. FSEQ files can be regenerated in xLights. Matrix playback does not demonstrate continuously articulated physical performer parity.

Musical limitations: source-bound ADTOF predictions are not independent ground truth; unknown toms abstain. Harmonic notes/velocity and screened mallet spectral peaks are estimates, not a labelled score or confirmed xylophone identity. Singers use screened word timing and authored duet casting; actual phone boundaries/voice separation are unverified. Stock model projection is approximate. Legacy LMS is supported; S5/S6 loredit and controller playback are unverified. Optional 3D/ML authoring dependencies remain source-runtime features.

Continuation if local runtime reconnects:
1. Fetch the review branch; preserve any uncommitted output/evidence before aligning code.
2. Locate `outputs/Prior_Sampler_Review`, `Helix_256_RGB_Showcase_Complete_20261012` and `verified_gui_release` under the existing scratch root.
3. Validate existing outputs and save through the unchanged Library helper if still present.
4. Prefer the independent Actions release if it has completed; inspect the newly decoded sheets, verify public asset hashes/links, and update the checklist before final delivery.
5. Never merge primary without user approval.
