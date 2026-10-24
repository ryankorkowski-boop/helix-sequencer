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
