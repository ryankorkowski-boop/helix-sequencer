# Helix Active Handoff — Drummer Implementation

> **Authoritative handoff. Read this file before making changes.**
> This replaces manually pasted handoff prompts between runs.

## Mission
Continue implementing the Helix drummer/band sequencing system from the current repository state. Work incrementally, preserve working behavior, and do not skip validation.

## Current branch
- Repository: `ryankorkowski-boop/helix-sequencer`
- Working branch: `feature/drummer-virtual-xlights`
- Pull request: #122
- Base branch: `feature/audio-intelligence-musical-intelligence`
- Current known handoff state: see the latest commit on this branch.

## Immediate objective
Finish **Slice 1 drummer stabilization** before expanding into the larger band architecture. Do not jump to a new architecture merely because a broader feature is desirable.

## Completed in this slice
1. Drummer is modeled as a virtual xLights performer rather than consuming physical channels 257–264.
2. Drummer timing/events are represented through the existing XSQ/xLights element-effect path.
3. The preview path has already produced an audio-backed drummer MP4.
4. Fixed the XML `ElementEffects` lookup so an empty existing container is not mistaken for a missing container.
5. Added regression coverage for exactly one `ElementEffects` container, drummer component targets, simultaneous-event preservation, and hand-aware cue metadata.
6. Updated stale CI contract tests to match the current renderer/artifact workflow.

## Validation gate
Before declaring this slice complete:
1. Inspect the latest CI runs for the **current HEAD**, not an older SHA.
2. Run/fix relevant drummer tests.
3. Verify the XSQ remains structurally valid.
4. Verify no physical channel count is accidentally increased.
5. Verify the preview renderer still creates the drummer MP4.
6. If CI exposes a real regression, fix it in the smallest coherent commit and rerun validation.
7. Do not mark the slice complete merely because a workflow was queued.

## Drummer behavior requirements
The drummer should eventually express distinct musical actions including kick, snare, hi-hat, ride, crash, toms, left/right stick motion, foot/kick action, and simultaneous limbs/events. The visual result must be musically interpretable rather than simply flashing every drum component.

## Architectural constraints
- Preserve the 256-channel physical layout.
- Do not invent additional physical AC channels for the virtual drummer.
- Keep drummer/band logic composable with the existing Helix pipeline.
- Prefer deterministic output.
- Keep changes small and testable.
- Preserve existing working render paths.
- Do not copy naming patterns or proprietary implementation text from other auto-sequencing programs.
- Derive behavior from documented functionality and Helix's own architecture.

## Working procedure for every future run
1. Read this file.
2. Inspect the current branch and latest CI state.
3. Inspect relevant existing implementation/tests before editing.
4. Pick the smallest next slice.
5. Implement it.
6. Add/update regression tests.
7. Run the relevant workflow/tests.
8. Inspect generated XSQ/preview artifacts when applicable.
9. Update this handoff with current commit, completed work, remaining work, validation result, and next slice.
10. Stop at a clean slice boundary.

## Definition of done for Slice 1
- drummer generation is deterministic;
- virtual xLights mapping is preserved;
- component targeting is verified;
- simultaneous drum events are preserved;
- XML structure is valid;
- relevant CI is green;
- preview generation succeeds;
- no known regression remains from the stabilization work.

## Next planned direction
After Slice 1 is green, move to the next drummer-musical-intelligence slice: improve event interpretation and motion choreography while retaining the virtual xLights model and 256-channel physical constraint.

Do not merge automatically. Do not rewrite unrelated systems.

## Automation note
This file is the persistent handoff. Future agents/runs should read it directly from the repository instead of requiring the user to paste a handoff prompt.
