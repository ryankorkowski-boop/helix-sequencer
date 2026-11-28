# Infinity autonomous completion handoff
Status: NOT OWNER APPROVED. Draft PR #269. Canva reference: https://www.canva.com/d/T-_cgog2MqtLddO
## Baseline
- [x] Deterministic 35,888 spatial RGB nodes, 107,664 spatial channels, six canonical performers and native ornaments exported.
- [x] Native three-second XSQ/FSEQ engineering run 46079658266 completed; 1080p 30fps preview technically valid.
- [ ] Visual acceptance FAILED: approximate flat renderer, sparse lines/dots, inadequate architecture, drummer inactive. Do not promote this result.
## Execution queue (in order)
## Mandatory Canva-first design gate (owner directive 2026-11-27)
- [ ] Validate and refine the newly created Canva design as the **entire 3D architectural layout with a consistent dimensioned, multi-view visual specification first**, including aerial perspective, site plan, elevations, depth/height measurements, building types, 3D helix towers, every RGB attachment surface, and six-snowman stage. Do not mistake a single flat concept rendering for a 3D design.
- [x] Create dedicated Canva master-design draft: `DAHcJ403E-U` titled `HELIX INFINITY Master Plan`, edit https://www.canva.com/d/bpxCSwLLAwECRI1 , view https://www.canva.com/d/e62I3y1STrRXfN5 . The prior `DAHcJnXh8rw` remains the visual composition reference only. Draft generated with aerial and ground-plan labels; **NOT a real 3D mesh** and **NOT geometry-approved**. Preliminary readback has malformed/inconsistent XYZ annotations (e.g. merged x lists), so validate and repair dimensional coherence before conversion.
- [ ] Freeze one canonical XYZ coordinate system and unique component IDs in a machine-readable scene manifest. Generate/maintain **actual OBJ/MTL or GLB mesh assets from the approved Canva visual design and the same parameter manifest**, then import into xLights Mesh view objects; do not try to convert static Canva images into real meshes.
- [ ] Validate geometry consistency against the Canva plan using top/front/side/aerial orthographic render comparisons BEFORE native xLights conversion. Every physical house must be a volumetric building with walls/roof, not just a two-dimensional facade.
- [ ] **Technical limitation:** Canva's current 3D elements/export are static imagery, not native OBJ/GLB mesh export (official Canva help). A Canva visual-design step therefore MUST precede the genuine mesh-building step; calling the Canva drawing itself a native 3D file is prohibited.
- [ ] Only proceed to the 3-second native xLights animation after this Canva-to-actual-mesh design gate passes. No full song until native visual and engineering gates pass.

- [ ] Inspect latest branch, CI, artifacts and existing upstream xLights 2026.18 source. Record commit, run and artifact IDs. Verify actual Mesh view-object XML, saved camera and exportVideoPreview/BatchVideoExport contracts against source; do not assume command syntax.
- [ ] Build deterministic OBJ/MTL architectural meshes matching Canva: distinct residential houses with walls, roofs, doors, windows, theater/storefront/tower, terrain and paths, two double-helix structures, spiral forest, cube, stage. Use portable relative asset paths; no baked animated lighting.
- [ ] Align native RGB nodes to mesh surfaces. Separate eaves, ridges, gables, windows, doors and facade segments into controllable models. Preserve true XYZ helix strands and cube coordinates, avoid channel overlap, verify native model mapping and strategic musical/spatial groups.
- [ ] Preserve exactly six canonical snowmen: drummer with approved nine cues and kit, guitar, upright bass, keyboard, lead, purple harmony. Verify realistic timing, no mallets absent stem, independent singers and silence suppression.
- [ ] Implement native xLights 3D House Preview video export on CI using supported automation and virtual display where required. Fixed elevated camera matching reference, all landmarks recognizable. Preserve real XSQ/FSEQ; no flat fallback, synthetic effects or Canva backdrop.
- [ ] Run a real three-second audio excerpt through Helix and native xLights. Record input hash, engine commit, camera, asset hashes, channel coverage, native logs, ffprobe and decoded frames. Repair failed runs before proceeding. Use Wub Wub only for short test.
- [ ] Visual gate: recognizable detailed architecture, two volumetric helixes, depth, spiral forest, visible canonical band, distinct musical roles, no global white or synchronized beat pulsing. Inspect frames and motion; automated brightness checks alone are insufficient. Select additional short real-audio passages for vocals/drums if needed. Do not mark owner approval.
- [x] Locate and authenticate original approximately 180-second HelixRemix source. Verified WAV is 180.224014 sec, 44.1kHz stereo signed 16-bit PCM, 31,791,594 bytes, SHA-256 efdfe69328b8458ff9b405d091af9d5cb9202e3f53846f1ac0de07814f28739d. Drive file ID 1usXEUMESsJGhioYaTgZKDMSOa9WSVr2s (`3minHelixRemix.wav`); identical bytes/hashes to older `helix3minuteshowcase.wav` ID 1bB_48UMUXC2tL325whoujVBqVw6SDHQk. Owner confirmed upload; treat first as canonical source. Do not substitute any alternate track.
- [ ] After short engineering and visual gates pass and source is verified, render full 180.224014 seconds using the same verified engine/layout/camera; verify audio sync, duration, H.264/AAC 1920x1080 30fps, complete decode, no blank frames or global flashes, representative musical sections and independent vocals where present.
- [ ] Deliver MP4, editable XSQ, native FSEQ, xlights_rgbeffects.xml, OBJ/MTL/textures, camera and channel mapping, reproducible workflow, manifest and direct artifact links. Verify downloadability. Update MASTER_TODO.md and docs/BETA_COMPLETION_LIVE_HANDOFF.md with actual evidence.
## Verified production-audio provenance (2026-11-27)
- Canonical source: [3minHelixRemix.wav](https://drive.google.com/file/d/1usXEUMESsJGhioYaTgZKDMSOa9WSVr2s/view), ID `1usXEUMESsJGhioYaTgZKDMSOa9WSVr2s`.
- Duration `180.224014 s` via ffprobe; stereo 44,100 Hz PCM s16le; byte size `31791594`.
- SHA-256 `efdfe69328b8458ff9b405d091af9d5cb9202e3f53846f1ac0de07814f28739d` verified from downloaded original.
- [helix3minuteshowcase.wav](https://drive.google.com/file/d/1bB_48UMUXC2tL325whoujVBqVw6SDHQk/view) is byte-for-byte identical (same SHA-256); no reason to transcode or substitute.
- Before full rendering, workflow MUST acquire the canonical original file (not public-unverified direct-link assumptions), validate SHA-256 and measured duration (allow <= 0.02s ffprobe discrepancy), and preserve full audio without trimming. Abort on mismatch; never fall back to Wub Wub.
- Missing-audio blocker cleared. Full render remains BLOCKED by incomplete true-3D visual acceptance and canonical drummer verification.

## 2026-11-27 Canva design-first cycle
- Canva generated an editable single-page master plan ID `DAHcJ403E-U`, title `HELIX INFINITY Master Plan`; view https://www.canva.com/d/e62I3y1STrRXfN5 .
- Readback confirms text for aerial perspective and ground plan, with mislabeled/merged XYZ coordinate annotations. It does NOT prove consistent four-view 3D construction or an OBJ/GLB mesh. **Visual/geometry approval: FAIL / PENDING REPAIR.**
- Next: inspect the Canva image at full resolution; repair plan/elevation/coordinates, ensure six band models and per-building surface controls, and use measured scene manifest for actual 3D mesh. Do not pretend native OBJ export is available from Canva.

## Running ledger
For each cycle append UTC timestamp, commit, action, run URL, artifact URL, tests, visual verdict, blocker, next action. Keep failed checks open. Never claim completion based on queued jobs or diagnostics.
## Guardrails
Inspect -> Implement -> Integrate -> Test -> Render -> Verify -> Repair -> Deliver. Continue autonomously on draft branch; no merge, release, owner approval, synthetic audio, or misleading preview. Ask only for indispensable unavailable input or permissions. Keep full render blocked until both short gates and exact sampler pass. 

## November 28 · Seven-district park rebuild

- [x] Inspect PR #269 at `0c3e4dd6a4e79145c31a7fd633ffbd52e44a1bd3`. V5 engineering run [46121735996](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/46121735996) produced artifact 15255430930. The owner's visual failure remains open.
- [x] Authenticate the original WAV again. SHA-256 and 180.224014-second duration match the directive. Preview uses the original Wub Wub Wonderland Remastered at 25–28 seconds.
- [x] Build and export the new seven-district dimensional site, GLB cameras, native OBJ/MTL, color bindings, XML and virtual channel configuration. Geometry export measured 8.332 seconds in the local environment. Two focused export tests passed.
- [x] Generate and inspect architectural overview, district, front, side and plan views. The next visual pass must inspect the native-lit motion and concert cast.
- [ ] Run and read back the new native xLights workflow, including channel activity per district, all three seconds of FSEQ, and decoded videos. The local execution environment cannot initialize the xLights X server, and the local master engine requires Demucs. The pinned review workflow installs both dependencies.
- [ ] Verify canonical drummer audio cues, guitar, upright bass, restrained keyboard, independent singers and silence against excerpts that contain the applicable sources. The exported native band is the repository's canonical surface/pose cast and planar drummer rig. Continuous articulated band mesh and separately verified harmony remain open.
- [ ] Enforce separate district musical roles with evidence from a quiet section, build and transition. Establish that the full show clears motion, brightness, color and composition review before rendering the production WAV.
- [ ] Render and validate the full 180.224014-second production show. Benchmark export/render CPU and memory on that source.
- [ ] Deliver and verify all links, including the concert and six district videos. Owner approval remains open.

Local day/night renders use architectural shading and a static district-colored fixture test. Native review movies read colors directly from xLights FSEQ. The virtual controller is for inspection and keeps hardware output disabled. Hardware identities remain installation-specific.

### Source-based district arrangement

- [x] Push dimensional rebuild to PR #269 at `4611e1d3288f3a8408dd662a518b8c888552e74b`. Native engineering run [46142907790](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/46142907790) passed dependency, geometry and source intake steps.
- [x] Wire district sound roles through the retained master-plan cache and the existing native source scheduler. Local banks follow district-specific physical axes. Canonical drum, string and keyboard adapters compile from the same plan. A supplied source-qualified vocal receipt can enable independent native harmony. Preview without that receipt leaves harmony inactive.
- [ ] Inspect the routed native render and decoded concert frames. Stage evidence must identify measured cues, animated parts and visual limitations. A correctly inactive harmony lane does not close the independent-vocal acceptance gate.

### Native baseline and arena alignment check

- [x] Baseline run [46142907790](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/46142907790), artifact 15262312216, produced eight 1080p xLights-FSEQ-driven MP4s. Native xLights 2026.18 rendered 60 FSEQ frames at 50 ms across 627,045 channels in 49.877 seconds. Decode, sync and whole-park white-channel checks passed. Visual review rejected the arena's largely empty stage and baseline drummer activity was zero.
- [x] Repair site-basis conversion of canonical pixels and add a test that binds every performer to its native world geometry inside the arena. Adjust the concert and Nexus framing. Binding correction changes render positions only. The native model addresses and source geometry below the scale/translation are preserved.
- [x] Compile the real local Wub Wub excerpt from Demucs/Whisper through the district router. It produced kick, snare, hi-hat and left/right crash cues. The excerpt has insufficient evidence for other kit components and independent singing.
- [ ] Render the aligned/capped version through pinned xLights and inspect each video. Intermediate routed run [46143233255](https://github.com/ryankorkowski-boop/helix-sequencer/actions/runs/46143233255) uses commit `9703f723815af072895f3dc0aa9ac61b946bc6cd`.
