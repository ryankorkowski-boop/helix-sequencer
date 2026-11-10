# GUI preview repair

Source base: PR214 head64db83d. Branch: `codex/gui-real-variant-previews-20261109`.

The phone rendered only one variant, and its Band switch could not add performers. Legacy custom models were reduced to outlines; a Faces effect lit a whole model, and any unsupported effect became a fabricated full-brightness flash.

Both apps now default to the bundled four-panel layout sampler: 16-channel AC, 64-channel AC, RGB arches/trees, and a separate canonical six-member band stage. The original drummer node model/kit is reused; no xylophonist is added. Existing saved layout selections remain in effect. Band on adds the packaged cast when absent and replaces historical band stubs that have no authored geometry. Existing band geometry and unrelated imported props/addresses remain intact. LOR/AC compatibility does not gain RGB performers.

The sampler uses the current variant's retained production band plan through the existing source-spatial scheduler. Its native On effects, source timing metadata, fixed AC colors, instrument keys/strings, drummer components and independent Faces cues are written to the actual XSQ before preview and show packaging. This deliberately changes the sampler's effect vocabulary so the portable preview can render its real generated cues. It does not replace sequencing for arbitrary imported layouts. Model parsing of sampler node addresses is opt-in; the legacy layouts retain their engine behavior.

Preview geometry reads compressed/custom authored nodes and exact submodel node ranges. Native Faces selects the requested singer/definition/phoneme nodes without lighting its entire body. The preview does not draw wires connecting disconnected custom nodes or ghost every alternate mouth/arm pose. Compact controls leave the phone's display visible. Unsupported native effects are omitted and reported, rather than replaced with full brightness. This is still a Helix effect simulation, not native xLights/FSEQ or physical validation. The existing source drummer remains planar source artwork.

Android renders every generated variant sequentially, exposes each successful MP4 in Results, saves all successful movies in the show ZIP, and retains per-variant failure notes. A failure does not skip later variants or discard sequences. Preview matrices are bounded to one second while retaining original fade progress. Each movie keeps its own XSQ/layout/audio hashes and actual soundtrack. Android and desktop disable automatic winner promotion for manual multiple-variant comparison so the first candidate is retained. Windows already renders all new XSQs.

## Evidence

`evidence/beta_completion/gui_previews_20261109/verification.json` records an actual two-variant Helix run on the first ten seconds of repository real audio `Helix Audiolights.mp3`, each with a three-second MP4. Full decode, stream metadata, all four panel brightness samples, frame differences and exact hashes are recorded. These are application preview diagnostics; they are not owner approval videos or native xLights qualification.

Final focused host regressions:139 passed, zero failed; JUnit is preserved next to that receipt. The earlier run of138 tests had137 passes and one test expectation that omitted the genuine stage portal/apron source events; the corrected assertion includes that fourth source panel. Additional historical empty-band replacement is separately covered. Packaging tests verify the sampler and changed source bytes are included in the Android engine archive without private audio or videos. Hosted APK/EXE builds and device/Windows validation remain pending; older installers have not been relabeled.

No PR188 merge, release, issue199 closure, approval-count change or singer-identity claim is included. Regression risks: render speed of dense surface geometry, conservative omission of unsupported imported effects, and canonical RGB channel additions when Band is explicitly selected. A named/relative imported channel address requires the user to supply a compatible band-enabled layout; the adapter fails rather than guessing conflicting addresses.

## Delivery blocker

Automatic approval review rejected pushing this implementation to the verified public `ryankorkowski-boop/helix-sequencer` repository. The stated reason was that project fixes were authorized but public publication was not explicit. No alternative publication route was used. The implementation is committed locally; hosted APK/EXE builds cannot start until the owner explicitly authorizes the public push. The change is available as a reviewable patch.

Owner follow-up: explicit authorization received to push this change publicly and run Android/Windows builds. The prior automatic-review rejection is historical. Shell git has no write credentials, so the authorized publication uses connected GitHub Git-data operations.
