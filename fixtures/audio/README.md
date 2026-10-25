# Owner-authorized release test recording

`Phoneme_Test_Hook.mp3` is the complete original owner upload, retained for
reproducible Helix release tests at the owner's direction on 2026-10-23.
SHA-256: `19e90c273d0d747938f24b36586b50818c104cddffbefe4a4128927374301938`.
Decoded duration is approximately 34.88 seconds. No audio was generated,
trimmed, normalized or substituted. See MUSIC_PERMISSIONS.md for music policy.

This is a mixed stereo recording. Its presence does not establish independent
lead/backing stems, verified phoneme boundaries, or approved band artwork.

`phoneme_vocal_separation/` contains measured clocks from a two-stage UVR
separation, bound to this exact original and the recorded model/derivative
SHA256 values. Reproduce with `python -m tools.separate_phoneme_vocals OUTPUT
--models MODEL_CACHE` in an audio-separator0.47.1 CPU environment. Model weights
are not bundled. The first model extracts a vocal estimate; the karaoke model
then estimates lead and residual backing. Only broad acoustic AH/EE/OH colors
and source-timed rests are exported. Distinct outputs are not verified singer
identities; reverb/lead/instrument leakage remains possible. The gate requiring
independently verified backing is not closed by this analysis.

The latest cache uses per-source Silero VAD screening in addition to periodic
energy. Reproduce with `python -m tools.offline_vocal_candidates AUDIO OUTPUT
--models LOCAL_PINNED_WEIGHTS`. All weights must be present with the hashes
listed in that module. Linux seccomp denies networking during inference and
ONNX telemetry is disabled before sessions are created. The output binds the
candidate WAVs and detector probabilities to SHA256 receipts. Screening uses
the same rule throughout the recording; there is no ending-specific mute.
Speech VAD can miss singing, so the cache remains an estimate requiring review.

Other owner sources use the same offline pipeline with an explicit checksum:
`python -m tools.offline_vocal_candidates AUDIO OUTPUT --models LOCAL_PINNED_WEIGHTS
--expected-sha256 EXACT_SOURCE_SHA256`. Mono inputs are upmixed without inventing
independent singers. The pipeline also preserves the accompaniment candidate.
No Moises account or paid dependency is needed for this local path.

Export inspectable 10ms activity/phoneme estimates and speech-presence probabilities:
`python -m tools.vocal_diagnostic AUDIO CANDIDATE_FOLDER DIAGNOSTIC_FOLDER`.
The CSV and chart are bound to the exact source and clock checksums. Missing
probabilities remain blank; speech VAD is not singer-identity confidence.
For a matching native movie, add `--native-video NATIVE_MP4` to append the
timeline beneath the native footage. Full decode, original audio identity,
duration and interior/ending alignment are checked before atomic publication.
These diagnostics do not replace the strict independent-singer acceptance gate.
